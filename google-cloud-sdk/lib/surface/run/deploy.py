# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Deploy a container to Cloud Run."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Deploy(base.Command):
  """Deploy a container to Cloud Run."""

  detailed_help = {
      'DESCRIPTION': """\
          Deploys container images to Google Cloud Run.
          """,
      'EXAMPLES': """\
          To deploy a container to the service `my-backend` on Cloud Run:

              $ {command} my-backend --image gcr.io/my/image

          You may also omit the service name. Then a prompt will be displayed
          with a suggested default value:

              $ {command} --image gcr.io/my/image

          To deploy to Cloud Run on Kubernetes Engine, you need to specify a cluster:

              $ {command} --image gcr.io/my/image --cluster my-cluster
          """,
  }

  @staticmethod
  def Args(parser):
    service_presentation = presentation_specs.ResourcePresentationSpec(
        'SERVICE',
        resource_args.GetServiceResourceSpec(prompt=True),
        'Service to deploy to.',
        required=True,
        prefixes=False)
    flags.AddSourceRefFlags(parser)
    flags.AddRegionArg(parser)
    flags.AddFunctionArg(parser)
    flags.AddMutexEnvVarsFlags(parser)
    flags.AddCpuFlag(parser)
    flags.AddMemoryFlag(parser)
    flags.AddConcurrencyFlag(parser)
    flags.AddTimeoutFlag(parser)
    flags.AddAsyncFlag(parser)
    flags.AddEndpointVisibilityEnum(parser)
    flags.AddCloudSQLFlags(parser)
    flags.AddAllowUnauthenticatedFlag(parser)
    concept_parsers.ConceptParser([
        resource_args.CLUSTER_PRESENTATION,
        service_presentation]).AddToParser(parser)

  def Run(self, args):
    """Deploy a container to Cloud Run."""
    source_ref = flags.GetSourceRef(args.source, args.image)

    conn_context = connection_context.GetConnectionContext(args)
    config_changes = flags.GetConfigurationChanges(args)

    if conn_context.supports_one_platform:
      flags.VerifyOnePlatformFlags(args)
    else:
      flags.VerifyGKEFlags(args)

    service_ref = flags.GetService(args)
    function_entrypoint = flags.GetFunction(args.function)

    with serverless_operations.Connect(conn_context) as operations:
      if not (source_ref.source_type is source_ref.SourceType.IMAGE
              or operations.IsSourceBranch()):
        raise exceptions.SourceNotSupportedError()
      new_deployable = operations.Detect(service_ref.Parent(),
                                         source_ref, function_entrypoint)
      operations.Upload(new_deployable)
      changes = [new_deployable]
      if config_changes:
        changes.extend(config_changes)
      if args.connectivity == 'internal':
        private_endpoint = True
      elif args.connectivity == 'external':
        private_endpoint = False
      else:
        private_endpoint = None
      exists = operations.GetService(service_ref)

      if (not exists and not args.allow_unauthenticated and
          conn_context.supports_one_platform):

        if operations.CanAddIamPolicyBinding(service_ref):
          allow_unauth = console_io.PromptContinue(
              prompt_string=(
                  'Allow unauthenticated invocations '
                  'to new service [{}]?'.format(
                      service_ref.servicesId)),
              default=False)
        else:
          allow_unauth = False
          pretty_print.Info(
              'This new service will require authentication to be invoked.')
      else:
        allow_unauth = False

      msg = ('Deploying {dep_type} to {operator} '
             'service [{{bold}}{service}{{reset}}]'
             ' in {ns_label} [{{bold}}{ns}{{reset}}]')
      msg += conn_context.location_label

      if function_entrypoint:
        dep_type = 'function [{{bold}}{}{{reset}}]'.format(function_entrypoint)
        pretty_print.Info(msg.format(
            operator=conn_context.operator,
            ns_label=conn_context.ns_label,
            dep_type=dep_type,
            function=function_entrypoint,
            service=service_ref.servicesId,
            ns=service_ref.namespacesId))
      elif source_ref.source_type is source_ref.SourceType.IMAGE:
        pretty_print.Info(msg.format(
            operator=conn_context.operator,
            ns_label=conn_context.ns_label,
            dep_type='container',
            service=service_ref.servicesId,
            ns=service_ref.namespacesId))
      else:
        pretty_print.Info(msg.format(
            operator=conn_context.operator,
            ns_label=conn_context.ns_label,
            dep_type='app',
            service=service_ref.servicesId,
            ns=service_ref.namespacesId))

      deployment_stages = stages.ServiceStages(
          allow_unauth or args.allow_unauthenticated)
      header = 'Deploying...' if exists else 'Deploying new service...'
      with progress_tracker.StagedProgressTracker(
          header,
          deployment_stages,
          failure_message='Deployment failed',
          suppress_output=args.async) as tracker:
        operations.ReleaseService(
            service_ref,
            changes,
            tracker,
            asyn=args.async,
            private_endpoint=private_endpoint,
            allow_unauthenticated=allow_unauth or args.allow_unauthenticated)
      if args.async:
        pretty_print.Success(
            'Service [{{bold}}{serv}{{reset}}] is deploying '
            'asynchronously.'.format(serv=service_ref.servicesId))
      else:
        url = operations.GetServiceUrl(service_ref)
        conf = operations.GetConfiguration(service_ref)
        msg = (
            'Service [{{bold}}{serv}{{reset}}] '
            'revision [{{bold}}{rev}{{reset}}] '
            'has been deployed and is serving traffic at '
            '{{bold}}{url}{{reset}}')
        msg = msg.format(
            serv=service_ref.servicesId,
            rev=conf.status.latestReadyRevisionName,
            url=url)
        pretty_print.Success(msg)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaDeploy(Deploy):

  @staticmethod
  def Args(parser):
    Deploy.Args(parser)
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddServiceAccountFlag(parser)

AlphaDeploy.__doc__ = Deploy.__doc__
