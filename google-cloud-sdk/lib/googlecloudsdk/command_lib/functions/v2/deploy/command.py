# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file provides the implementation of the `functions deploy` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import random
import re
import string

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import http_wrapper
from apitools.base.py import transfer
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.functions.v2 import exceptions
from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import transports
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files as file_utils

import six

_MISSING_SOURCE_ERROR_MESSAGE = 'Please provide the `--source` flag.'
_SIGNED_URL_UPLOAD_ERROR_MESSSAGE = (
    'There was a problem uploading the source code to a signed Cloud Storage '
    'URL. Please try again.')

_GCS_SOURCE_REGEX = re.compile('gs://([^/]+)/(.*)')
_GCS_SOURCE_ERROR_MESSAGE = (
    'Invalid Cloud Storage URL. Must match the following format: '
    'gs://bucket/object')

# https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions#sourcerepository
_CSR_SOURCE_REGEX = re.compile(
    # Minimally required fields
    r'https://source\.developers\.google\.com'
    r'/projects/(?P<project_id>[^/]+)/repos/(?P<repo_name>[^/]+)'
    # Optional oneof revision/alias
    r'(((/revisions/(?P<commit>[^/]+))|'
    r'(/moveable-aliases/(?P<branch>[^/]+))|'
    r'(/fixed-aliases/(?P<tag>[^/]+)))'
    # Optional path
    r'(/paths/(?P<path>[^/]+))?)?'
    # Optional ending forward slash and enforce regex matches end of string
    r'/?$')
_CSR_SOURCE_ERROR_MESSAGE = (
    'Invalid Cloud Source Repository URL provided. Must match the '
    'following format: https://source.developers.google.com/projects/'
    '<projectId>/repos/<repoName>. Specify the desired branch by appending '
    '/moveable-aliases/<branchName>, the desired tag with '
    '/fixed-aliases/<tagName>, or the desired commit with /revisions/<commit>. '
)

_INVALID_NON_HTTP_SIGNATURE_TYPE_ERROR_MESSAGE = (
    'When `--trigger_http` is provided, `--signature-type` must be omitted '
    'or set to `http`.')
_INVALID_HTTP_SIGNATURE_TYPE_ERROR_MESSAGE = (
    'When an event trigger is provided, `--signature-type` cannot be set to '
    '`http`.')
_SIGNATURE_TYPE_ENV_VAR_COLLISION_ERROR_MESSAGE = (
    '`GOOGLE_FUNCTION_SIGNATURE_TYPE` is a reserved build environment variable.'
)

_LEGACY_V1_FLAGS = [
    ('security_level', '--security-level'),
    ('trigger_event', '--trigger-event'),
    ('trigger_resource', '--trigger-resource'),
]
_LEGACY_V1_FLAG_ERROR = '`%s` is only supported in Cloud Functions V1.'

_UNSUPPORTED_V2_FLAGS = [
    # TODO(b/192479883): Support --retry flag.
    ('retry', '--retry'),
    # TODO(b/192480007): Add support for secrets.
    ('set_secrets', '--set-secrets'),
    ('update_secrets', '--update-secrets'),
    ('remove_secrets', '--remove-secrets'),
    ('clear_secrets', '--clear-secrets'),
    # TODO(b/184877044): Add support when Eventarc gets GCS support
    ('trigger_bucket', '--trigger-bucket'),
]
_UNSUPPORTED_V2_FLAG_ERROR = '`%s` is not yet supported in Cloud Functions V2.'

_EVENT_TYPE_PUBSUB_MESSAGE_PUBLISHED = 'google.cloud.pubsub.topic.v1.messagePublished'

_CLOUD_RUN_SERVICE_COLLECTION_K8S = 'run.namespaces.services'
_CLOUD_RUN_SERVICE_COLLECTION_ONE_PLATFORM = 'run.projects.locations.services'

_DEFAULT_IGNORE_FILE = gcloudignore.DEFAULT_IGNORE_FILE + '\nnode_modules\n'

_ZIP_MIME_TYPE = 'application/zip'


def _IsHttpTriggered(args):
  return args.IsSpecified('trigger_http') or not (args.trigger_topic or
                                                  args.trigger_event_filters)


def _GcloudIgnoreCreationPredicate(directory):
  return gcloudignore.AnyFileOrDirExists(
      directory, gcloudignore.GIT_FILES + ['node_modules'])


def _GetSourceGCS(messages, source):
  """Constructs a `Source` message from a Cloud Storage object.

  Args:
    messages: messages module, the GCFv2 message stubs
    source: str, the Cloud Storage URL

  Returns:
    function_source: cloud.functions.v2main.Source
  """
  match = _GCS_SOURCE_REGEX.match(source)
  if not match:
    raise exceptions.FunctionsError(_GCS_SOURCE_ERROR_MESSAGE)

  return messages.Source(
      storageSource=messages.StorageSource(
          bucket=match.group(1), object=match.group(2)))


def _GetSourceCSR(messages, source):
  """Constructs a `Source` message from a Cloud Source Repository reference.

  Args:
    messages: messages module, the GCFv2 message stubs
    source: str, the Cloud Source Repository reference

  Returns:
    function_source: cloud.functions.v2main.Source
  """
  match = _CSR_SOURCE_REGEX.match(source)

  if match is None:
    raise exceptions.FunctionsError(_CSR_SOURCE_ERROR_MESSAGE)

  repo_source = messages.RepoSource(
      projectId=match.group('project_id'),
      repoName=match.group('repo_name'),
      dir=match.group('path'),  # Optional
  )

  # Optional oneof revision field
  commit = match.group('commit')
  branch = match.group('branch')
  tag = match.group('tag')

  if commit:
    repo_source.commitSha = commit
  elif tag:
    repo_source.tagName = tag
  else:
    # Default to 'master' branch if no revision/alias provided.
    repo_source.branchName = branch or 'master'

  return messages.Source(repoSource=repo_source)


def _UploadToStageBucket(region, function_name, zip_file_path, stage_bucket):
  """Uploads a ZIP file to a user-provided stage bucket.

  Args:
    region: str, the region to deploy the function to
    function_name: str, the name of the function
    zip_file_path: str, the path to the ZIP file
    stage_bucket: str, the name of the stage bucket

  Returns:
    dest_object: storage_util.ObjectReference, a reference to the uploaded
                 Cloud Storage object
  """
  dest_object = storage_util.ObjectReference.FromBucketRef(
      storage_util.BucketReference.FromArgument(stage_bucket),
      '{}-{}-{}.zip'.format(
          region, function_name,
          ''.join(random.choice(string.ascii_lowercase) for _ in range(12))))
  storage_api.StorageClient().CopyFileToGCS(zip_file_path, dest_object)
  return dest_object


def _UploadToGeneratedUrl(zip_file_path, url):
  """Uploads a ZIP file to a signed Cloud Storage URL.

  Args:
    zip_file_path: str, the path to the ZIP file
    url: str, the signed Cloud Storage URL
  """
  upload = transfer.Upload.FromFile(zip_file_path, mime_type=_ZIP_MIME_TYPE)
  try:
    request = http_wrapper.Request(
        url, http_method='PUT', headers={'content-type': upload.mime_type})
    request.body = upload.stream.read()
    upload.stream.close()
    response = http_wrapper.MakeRequest(transports.GetApitoolsTransport(),
                                        request)
  finally:
    upload.stream.close()
  if response.status_code // 100 != 2:
    raise exceptions.FunctionsError(_SIGNED_URL_UPLOAD_ERROR_MESSSAGE)


def _GetSourceLocal(client, messages, region, function_name, source,
                    stage_bucket_arg, ignore_file_arg):
  """Constructs a `Source` message from a local file system path.

  Args:
    client: The GCFv2 API client
    messages: messages module, the GCFv2 message stubs
    region: str, the region to deploy the function to
    function_name: str, the name of the function
    source: str, the path
    stage_bucket_arg: str, the passed in --stage-bucket flag argument
    ignore_file_arg: str, the passed in --ignore-file flag argument

  Returns:
    function_source: cloud.functions.v2main.Source
  """
  with file_utils.TemporaryDirectory() as tmp_dir:
    zip_file_path = os.path.join(tmp_dir, 'fun.zip')
    chooser = gcloudignore.GetFileChooserForDir(
        source,
        default_ignore_file=_DEFAULT_IGNORE_FILE,
        gcloud_ignore_creation_predicate=_GcloudIgnoreCreationPredicate,
        ignore_file=ignore_file_arg)
    archive.MakeZipFromDir(zip_file_path, source, predicate=chooser.IsIncluded)

    if stage_bucket_arg:
      dest_object = _UploadToStageBucket(region, function_name, zip_file_path,
                                         stage_bucket_arg)
      return messages.Source(
          storageSource=messages.StorageSource(
              bucket=dest_object.bucket, object=dest_object.name))
    else:
      dest = client.projects_locations_functions.GenerateUploadUrl(
          messages
          .CloudfunctionsProjectsLocationsFunctionsGenerateUploadUrlRequest(
              generateUploadUrlRequest=messages.GenerateUploadUrlRequest(),
              parent='projects/%s/locations/%s' %
              (properties.VALUES.core.project.GetOrFail(), region)))

      _UploadToGeneratedUrl(zip_file_path, dest.uploadUrl)

      return messages.Source(storageSource=dest.storageSource)


def _GetSource(client, messages, region, function_name, source_arg,
               stage_bucket_arg, ignore_file_arg, existing_function):
  """Parses the source bucket and object from the --source flag.

  Args:
    client: The GCFv2 API client
    messages: messages module, the GCFv2 message stubs
    region: str, the region to deploy the function to
    function_name: str, the name of the function
    source_arg: str, the passed in --source flag argument
    stage_bucket_arg: str, the passed in --stage-bucket flag argument
    ignore_file_arg: str, the passed in --ignore-file flag argument
    existing_function: cloudfunctions_v2alpha_messages.Function | None

  Returns:
    function_source: cloud.functions.v2main.Source
    update_field_set: frozenset, set of update mask fields
  """
  if existing_function is not None and source_arg is None:
    if existing_function.buildConfig.source.repoSource is not None:
      return None, frozenset()

    # We don't know if the function was originally deployed from local source
    # files or from Cloud Storage. Ask the user to clarify.
    raise exceptions.FunctionsError(_MISSING_SOURCE_ERROR_MESSAGE)

  source = source_arg or '.'

  if source.startswith('gs://'):
    return _GetSourceGCS(messages, source), frozenset(['build_config.source'])
  elif source.startswith('https://'):
    return _GetSourceCSR(messages, source), frozenset(['build_config.source'])
  else:
    return _GetSourceLocal(client, messages, region, function_name, source,
                           stage_bucket_arg,
                           ignore_file_arg), frozenset(['build_config.source'])


def _GetServiceConfig(args, messages, existing_function):
  """Constructs a ServiceConfig message from the command-line arguments.

  Args:
    args: argparse.Namespace, arguments that this command was invoked with
    messages: messages module, the GCFv2 message stubs
    existing_function: cloudfunctions_v2alpha_messages.Function | None

  Returns:
    vpc_connector: str, the vpc connector name
    vpc_egress_settings: VpcConnectorEgressSettingsValueValuesEnum, the vpc
      enum value
    updated_fields_set: frozenset, set of update mask fields
  """

  old_env_vars = {}
  if (existing_function and existing_function.serviceConfig and
      existing_function.serviceConfig.environmentVariables and
      existing_function.serviceConfig.environmentVariables.additionalProperties
     ):
    for additional_property in (existing_function.serviceConfig
                                .environmentVariables.additionalProperties):
      old_env_vars[additional_property.key] = additional_property.value

  env_var_flags = map_util.GetMapFlagsFromArgs('env-vars', args)
  env_vars = map_util.ApplyMapFlags(old_env_vars, **env_var_flags)

  vpc_connector, vpc_egress_settings, vpc_updated_fields = (
      _GetVpcAndVpcEgressSettings(args, messages, existing_function))

  ingress_settings, ingress_updated_fields = _GetIngressSettings(args, messages)

  updated_fields = set()

  if args.memory is not None:
    updated_fields.add('service_config.available_memory_mb')
  if args.max_instances is not None or args.clear_max_instances:
    updated_fields.add('service_config.max_instance_count')
  if args.min_instances is not None or args.clear_min_instances:
    updated_fields.add('service_config.min_instance_count')
  if args.run_service_account is not None or args.service_account is not None:
    updated_fields.add('service_config.service_account_email')
  if args.timeout is not None:
    updated_fields.add('service_config.timeout_seconds')
  if env_vars != old_env_vars:
    updated_fields.add('service_config.environment_variables')

  service_updated_fields = frozenset.union(vpc_updated_fields,
                                           ingress_updated_fields,
                                           updated_fields)

  return messages.ServiceConfig(
      availableMemoryMb=utils.BytesToMb(args.memory) if args.memory else None,
      maxInstanceCount=None if args.clear_max_instances else args.max_instances,
      minInstanceCount=None if args.clear_min_instances else args.min_instances,
      serviceAccountEmail=args.run_service_account or args.service_account,
      timeoutSeconds=args.timeout,
      ingressSettings=ingress_settings,
      vpcConnector=vpc_connector,
      vpcConnectorEgressSettings=vpc_egress_settings,
      environmentVariables=messages.ServiceConfig.EnvironmentVariablesValue(
          additionalProperties=[
              messages.ServiceConfig.EnvironmentVariablesValue
              .AdditionalProperty(key=key, value=value)
              for key, value in sorted(env_vars.items())
          ])), service_updated_fields


def _GetEventTrigger(args, messages):
  """Constructs an EventTrigger message from the command-line arguments.

  Args:
    args: argparse.Namespace, arguments that this command was invoked with
    messages: messages module, the GCFv2 message stubs

  Returns:
    event_trigger: cloudfunctions_v2alpha_messages.EventTrigger, used to request
      events sent from another service
    updated_fields_set: frozenset, set of update mask fields
  """
  if _IsHttpTriggered(args):
    return None, frozenset()

  event_type = None
  pubsub_topic = None

  if args.trigger_topic:
    event_type = _EVENT_TYPE_PUBSUB_MESSAGE_PUBLISHED
    pubsub_topic = 'projects/{}/topics/{}'.format(
        properties.VALUES.core.project.GetOrFail(), args.trigger_topic)

  event_trigger = messages.EventTrigger(
      eventType=event_type,
      pubsubTopic=pubsub_topic,
      serviceAccountEmail=args.trigger_service_account or args.service_account,
      triggerRegion=args.trigger_location)

  if args.trigger_event_filters:
    for attribute, value in args.trigger_event_filters.items():
      if attribute == 'type':
        event_trigger.eventType = value
      else:
        event_trigger.eventFilters.append(
            messages.EventFilter(attribute=attribute, value=value))

  return event_trigger, frozenset(['event_trigger'])


def _GetSignatureType(args, event_trigger):
  """Determines the function signature type from the command-line arguments.

  Args:
    args: argparse.Namespace, arguments that this command was invoked with
    event_trigger: one

  Returns:
    signature_type: str, the desired functions signature type
    updated_fields_set: frozenset[str], set of update mask fields
  """
  if args.trigger_http or not event_trigger:
    if args.signature_type and args.signature_type != 'http':
      raise exceptions.FunctionsError(
          _INVALID_NON_HTTP_SIGNATURE_TYPE_ERROR_MESSAGE)
    if args.trigger_http:
      return 'http', frozenset(['build_config.environment_variables'])
    else:
      # do not add to update_mask if --trigger-http flag not provided
      # as it is only implied to be 'http'
      return 'http', frozenset()
  elif args.signature_type:
    if args.signature_type == 'http':
      raise exceptions.FunctionsError(
          _INVALID_HTTP_SIGNATURE_TYPE_ERROR_MESSAGE)
    return args.signature_type, frozenset(
        ['build_config.environment_variables'])
  else:
    return 'cloudevent', frozenset()


def _GetBuildConfig(args, client, messages, region, function_name,
                    event_trigger, existing_function):
  """Constructs a BuildConfig message from the command-line arguments.

  Args:
    args: argparse.Namespace, arguments that this command was invoked with
    client: The GCFv2 API client
    messages: messages module, the GCFv2 message stubs
    region: str, the region to deploy the function to
    function_name: str, the name of the function
    event_trigger: cloudfunctions_v2alpha_messages.EventTrigger, used to request
      events sent from another service
    existing_function: cloudfunctions_v2alpha_messages.Function | None

  Returns:
    build_config: cloudfunctions_v2alpha_messages.BuildConfig, describes the
      build step for the function
    updated_fields_set: frozenset[str], set of update mask fields
  """
  function_source, source_updated_fields = _GetSource(
      client, messages, region, function_name, args.source, args.stage_bucket,
      args.ignore_file, existing_function)

  old_build_env_vars = {}
  if (existing_function and existing_function.buildConfig and
      existing_function.buildConfig.environmentVariables and
      existing_function.buildConfig.environmentVariables.additionalProperties):
    for additional_property in (existing_function.buildConfig
                                .environmentVariables.additionalProperties):
      old_build_env_vars[additional_property.key] = additional_property.value

  build_env_var_flags = map_util.GetMapFlagsFromArgs('build-env-vars', args)
  build_env_vars = map_util.ApplyMapFlags(old_build_env_vars,
                                          **build_env_var_flags)

  signature_type, signature_updated_fields = _GetSignatureType(
      args, event_trigger)

  if ('GOOGLE_FUNCTION_SIGNATURE_TYPE' in build_env_vars and
      'GOOGLE_FUNCTION_SIGNATURE_TYPE' not in old_build_env_vars):
    raise exceptions.FunctionsError(
        _SIGNATURE_TYPE_ENV_VAR_COLLISION_ERROR_MESSAGE)
  build_env_vars['GOOGLE_FUNCTION_SIGNATURE_TYPE'] = signature_type

  updated_fields = set()

  if build_env_vars != old_build_env_vars:
    updated_fields.add('build_config.environment_variables')

  if args.entry_point is not None:
    updated_fields.add('build_config.entry_point')
  if args.runtime is not None:
    updated_fields.add('build_config.runtime')

  worker_pool = (None
                 if args.clear_build_worker_pool else args.build_worker_pool)

  if args.build_worker_pool is not None or args.clear_build_worker_pool:
    updated_fields.add('build_config.worker_pool')

  build_updated_fields = frozenset.union(signature_updated_fields,
                                         source_updated_fields, updated_fields)
  return messages.BuildConfig(
      entryPoint=args.entry_point,
      runtime=args.runtime,
      source=function_source,
      workerPool=worker_pool,
      environmentVariables=messages.BuildConfig.EnvironmentVariablesValue(
          additionalProperties=[
              messages.BuildConfig.EnvironmentVariablesValue.AdditionalProperty(
                  key=key, value=value)
              for key, value in sorted(build_env_vars.items())
          ])), build_updated_fields


def _GetIngressSettings(args, messages):
  """Constructs ingress setting enum from command-line arguments.

  Args:
    args: argparse.Namespace, arguments that this command was invoked with
    messages: messages module, the GCFv2 message stubs

  Returns:
    ingress_settings_enum: ServiceConfig.IngressSettingsValueValuesEnum, the
      ingress setting enum value
    updated_fields_set: frozenset[str], set of update mask fields
  """
  if args.ingress_settings:
    ingress_settings_enum = arg_utils.ChoiceEnumMapper(
        arg_name='ingress_settings',
        message_enum=messages.ServiceConfig.IngressSettingsValueValuesEnum,
        custom_mappings=flags.INGRESS_SETTINGS_MAPPING).GetEnumForChoice(
            args.ingress_settings)
    return ingress_settings_enum, frozenset(['service_config.ingress_settings'])
  else:
    return None, frozenset()


def _GetVpcAndVpcEgressSettings(args, messages, existing_function):
  """Constructs vpc connector and egress settings from command-line arguments.

  Args:
    args: argparse.Namespace, arguments that this command was invoked with
    messages: messages module, the GCFv2 message stubs
    existing_function: cloudfunctions_v2alpha_messages.Function | None

  Returns:
    vpc_connector: str, name of the vpc connector
    vpc_egress_settings:
    ServiceConfig.VpcConnectorEgressSettingsValueValuesEnum,
      the egress settings for the vpc connector
    vpc_updated_fields_set: frozenset[str], set of update mask fields
  """

  egress_settings = None
  if args.egress_settings:
    egress_settings = arg_utils.ChoiceEnumMapper(
        arg_name='egress_settings',
        message_enum=messages.ServiceConfig
        .VpcConnectorEgressSettingsValueValuesEnum,
        custom_mappings=flags.EGRESS_SETTINGS_MAPPING).GetEnumForChoice(
            args.egress_settings)

  if args.clear_vpc_connector:
    return None, None, frozenset([
        'service_config.vpc_connector',
        'service_config.vpc_connector_egress_settings'
    ])
  elif args.vpc_connector:
    if args.egress_settings:
      return args.vpc_connector, egress_settings, frozenset([
          'service_config.vpc_connector',
          'service_config.vpc_connector_egress_settings'
      ])
    else:
      return args.vpc_connector, None, frozenset(
          ['service_config.vpc_connector'])
  elif args.egress_settings:
    if existing_function and existing_function.vpc_connector:
      return existing_function.vpc_connector, egress_settings, frozenset(
          ['service_config.vpc_connector_egress_settings'])
    else:
      raise exceptions.RequiredArgumentException(
          'vpc-connector', 'Flag `--vpc-connector` is '
          'required for setting `egress-settings`.')
  else:
    return None, None, frozenset()


def _ValidateLegacyV1Flags(args):
  for flag_variable, flag_name in _LEGACY_V1_FLAGS:
    if args.IsSpecified(flag_variable):
      raise exceptions.FunctionsError(_LEGACY_V1_FLAG_ERROR % flag_name)


def _ValidateUnsupportedV2Flags(args):
  for flag_variable, flag_name in _UNSUPPORTED_V2_FLAGS:
    if args.IsSpecified(flag_variable):
      raise exceptions.FunctionsError(_UNSUPPORTED_V2_FLAG_ERROR % flag_name)


def _GetLabels(args, messages, existing_function):
  """Constructs labels from command-line arguments.

  Args:
    args: argparse.Namespace, arguments that this command was invoked with
    messages: messages module, the GCFv2 message stubs
    existing_function: cloudfunctions_v2alpha_messages.Function | None

  Returns:
    labels: Function.LabelsValue, functions labels metadata
    updated_fields_set: frozenset[str], list of update mask fields
  """
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  labels_update = labels_diff.Apply(
      messages.Function.LabelsValue,
      existing_function.labels if existing_function else None)
  if labels_update.needs_update:
    return labels_update.labels, frozenset(['labels'])
  else:
    return None, frozenset()


def _SetInvokerPermissions(args, function, is_new_function):
  """Add the IAM binding for the invoker role on the Cloud Run service, if applicable.

  Args:
    args: argparse.Namespace, arguments that this command was invoked with
    function: cloudfunctions_v2alpha_messages.Function, recently created or
      updated GCF function
    is_new_function: bool, true if the function is being created

  Returns:
    None
  """
  service_ref_one_platform = resources.REGISTRY.ParseRelativeName(
      function.serviceConfig.service,
      _CLOUD_RUN_SERVICE_COLLECTION_ONE_PLATFORM)

  if not _IsHttpTriggered(args):
    return

  # This condition will be truthy if the user provided either
  # `--allow-unauthenticated` or `--no-allow-unauthenticated`. In other
  # words, it is only falsey when neither of those two flags is provided.
  if args.IsSpecified('allow_unauthenticated'):
    allow_unauthenticated = args.allow_unauthenticated
  else:
    if is_new_function:
      allow_unauthenticated = console_io.PromptContinue(
          prompt_string=(
              'Allow unauthenticated invocations of new function [{}]?'.format(
                  args.NAME)),
          default=False)
    else:
      # The function already exists, and the user didn't request any change to
      # the permissions. There is nothing to do in this case.
      return

  run_connection_context = connection_context.RegionalConnectionContext(
      service_ref_one_platform.locationsId, global_methods.SERVERLESS_API_NAME,
      global_methods.SERVERLESS_API_VERSION)

  with serverless_operations.Connect(run_connection_context) as operations:
    service_ref_k8s = resources.REGISTRY.ParseRelativeName(
        'namespaces/{}/services/{}'.format(
            properties.VALUES.core.project.GetOrFail(),
            service_ref_one_platform.Name()), _CLOUD_RUN_SERVICE_COLLECTION_K8S)

    if allow_unauthenticated:
      operations.AddOrRemoveIamPolicyBinding(
          service_ref_k8s,
          add_binding=True,
          member=serverless_operations.ALLOW_UNAUTH_POLICY_BINDING_MEMBER,
          role=serverless_operations.ALLOW_UNAUTH_POLICY_BINDING_ROLE)
    elif not is_new_function:
      operations.AddOrRemoveIamPolicyBinding(
          service_ref_k8s,
          add_binding=False,
          member=serverless_operations.ALLOW_UNAUTH_POLICY_BINDING_MEMBER,
          role=serverless_operations.ALLOW_UNAUTH_POLICY_BINDING_ROLE)


def _GetFunction(client, messages, function_ref):
  """Get function and return None if doesn't exist.

  Args:
    client: apitools client, the GCFv2 API client
    messages: messages module, the GCFv2 message stubs
    function_ref: GCFv2 functions resource reference

  Returns:
    function: cloudfunctions_v2alpha_messages.Function, fetched GCFv2 function
  """
  try:
    # We got response for a GET request, so a function exists.
    return client.projects_locations_functions.Get(
        messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=function_ref.RelativeName()))
  except apitools_exceptions.HttpError as error:
    if error.status_code == six.moves.http_client.NOT_FOUND:
      return None
    raise


def _CreateAndWait(client, messages, function_ref, function):
  """Create a function.

  This does not include setting the invoker permissions.

  Args:
    client: The GCFv2 API client.
    messages: The GCFv2 message stubs.
    function_ref: The GCFv2 functions resource reference.
    function: The function to create.

  Returns:
    None
  """
  function_parent = 'projects/%s/locations/%s' % (
      properties.VALUES.core.project.GetOrFail(), function_ref.locationsId)

  create_request = messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
      parent=function_parent, functionId=function_ref.Name(), function=function)
  operation = client.projects_locations_functions.Create(create_request)
  operation_description = 'Deploying function (may take a while)'

  api_util.WaitForOperation(client, messages, operation, operation_description)


def _UpdateAndWait(client, messages, function_ref, function,
                   updated_fields_set):
  """Update a function.

  This does not include setting the invoker permissions.

  Args:
    client: The GCFv2 API client.
    messages: The GCFv2 message stubs.
    function_ref: The GCFv2 functions resource reference.
    function: The function to update.
    updated_fields_set: A set of update mask fields.

  Returns:
    None
  """
  if updated_fields_set:
    updated_fields = list(updated_fields_set)
    updated_fields.sort()
    update_mask = ','.join(updated_fields)

    update_request = messages.CloudfunctionsProjectsLocationsFunctionsPatchRequest(
        name=function_ref.RelativeName(),
        updateMask=update_mask,
        function=function)

    operation = client.projects_locations_functions.Patch(update_request)
    operation_description = 'Updating function (may take a while)'

    api_util.WaitForOperation(client, messages, operation,
                              operation_description)
  else:
    log.status.Print('Nothing to update.')


def Run(args, release_track):
  """Runs a function deployment with the given args."""
  client = api_util.GetClientInstance(release_track=release_track)
  messages = api_util.GetMessagesModule(release_track=release_track)

  function_ref = args.CONCEPTS.name.Parse()

  _ValidateLegacyV1Flags(args)
  _ValidateUnsupportedV2Flags(args)

  existing_function = _GetFunction(client, messages, function_ref)
  is_new_function = existing_function is None

  event_trigger, trigger_updated_fields = _GetEventTrigger(args, messages)
  build_config, build_updated_fields = _GetBuildConfig(args, client, messages,
                                                       function_ref.locationsId,
                                                       function_ref.Name(),
                                                       event_trigger,
                                                       existing_function)

  service_config, service_updated_fields = _GetServiceConfig(
      args, messages, existing_function)

  labels_value, labels_updated_fields = _GetLabels(args, messages,
                                                   existing_function)

  # cs/symbol:google.cloud.functions.v2main.Function$
  function = messages.Function(
      name=function_ref.RelativeName(),
      buildConfig=build_config,
      eventTrigger=event_trigger,
      serviceConfig=service_config,
      labels=labels_value)

  if is_new_function:
    _CreateAndWait(client, messages, function_ref, function)
  else:
    _UpdateAndWait(
        client, messages, function_ref, function,
        frozenset.union(trigger_updated_fields, build_updated_fields,
                        service_updated_fields, labels_updated_fields))

  function = client.projects_locations_functions.Get(
      messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
          name=function_ref.RelativeName()))

  _SetInvokerPermissions(args, function, is_new_function)

  log.status.Print(
      'You can view your function in the Cloud Console here: ' +
      'https://console.cloud.google.com/functions/details/{}/{}?project={}\n'
      .format(function_ref.locationsId, function_ref.Name(),
              properties.VALUES.core.project.GetOrFail()))

  return function
