# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Helper class for commands which use the deployment API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib
import operator
import time

from apitools.base.py import encoding
from apitools.base.py import extra_types
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.app.api import appengine_api_client_base as api_client
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files as file_utils
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.apitools import retry
import six


APPENGINE_API = 'appengine'
APPENGINE_API_VERSION = api_client.AppengineApiClientBase.ApiVersion()


class ApiTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                  test_case.WithOutputCapture):
  """Mocks the appengine API client."""

  DEFAULT_SERVICE_CONFIG = {'runtime': 'python27', 'api_version': '1'}
  DEFAULT_FILES = ['app.yaml',
                   'dos.yaml',
                   'mod1.yaml',
                   'queue.yaml',
                   'start.py',
                   'dispatch.yaml',
                   'cron.yaml',
                   'index.yaml']
  DEFAULT_URL = 'https://storage.googleapis.com/default-bucket/'

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule(APPENGINE_API,
                                                APPENGINE_API_VERSION)
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass(APPENGINE_API, APPENGINE_API_VERSION),
        real_client=core_apis.GetClientInstance(
            APPENGINE_API, APPENGINE_API_VERSION, no_http=True))
    self.mock_client.Mock()
    # If any API calls were made but weren't expected, this will throw an error
    self.addCleanup(self.mock_client.Unmock)
    # Mock time.sleep in order to test polling / retry methods.
    self.StartObjectPatch(time, 'sleep')

  def UnsetProject(self):
    """Set core/project property to None."""
    # Due to a weird interaction with the self.Project() setup in CliTestBase,
    # both of these are required to reset the project property to None.
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    properties.VALUES.core.project.Set(None)

  def GetApplicationCall(self, app):
    """Helper Function to create expected GetApplication API call."""
    return self.messages.AppengineAppsGetRequest(
        name='apps/{0}'.format(app))

  def GetApplicationResponse(self, app, gcr_domain=None,
                             code_bucket=None, hostname=None,
                             location_id=None, serving_status='SERVING',
                             split_health_checks=None,
                             track=base.ReleaseTrack.GA):
    """Helper function to create response for GetApplication API call."""
    if code_bucket is None:
      code_bucket = '{0}-staging.appspot.com'.format(app)
    if hostname is None:
      hostname = '{0}.appspot.com'.format(app)
    serving_status = self.messages.Application.ServingStatusValueValuesEnum(
        serving_status)
    application = self.messages.Application(
        name='apps/{0}'.format(app),
        id=app,
        codeBucket=code_bucket,
        gcrDomain=gcr_domain,
        defaultHostname=hostname,
        locationId=location_id,
        servingStatus=serving_status
    )

    if track == base.ReleaseTrack.BETA:
      if split_health_checks is None:
        application.featureSettings = self.messages.FeatureSettings()
      else:
        application.featureSettings = self.messages.FeatureSettings(
            splitHealthChecks=split_health_checks)

    return application

  def ExpectGetApplicationRequest(self, app, gcr_domain=None, code_bucket=None,
                                  exception=None, hostname=None,
                                  location_id=None, serving_status='SERVING',
                                  split_health_checks=None,
                                  track=base.ReleaseTrack.GA):
    """Adds expected get-application call and response to mock client."""
    if exception:
      self.mock_client.apps.Get.Expect(
          self.GetApplicationCall(app), exception=exception)
    else:
      self.mock_client.apps.Get.Expect(
          self.GetApplicationCall(app),
          response=self.GetApplicationResponse(
              app, gcr_domain=(gcr_domain or 'us.gcr.io'),
              code_bucket=code_bucket, hostname=hostname,
              location_id=location_id, serving_status=serving_status,
              split_health_checks=split_health_checks, track=track))

  def GetServiceResponse(self, app, service, split_list):
    """Creates dummy responses for the Services.Get call.

    Args:
      app: String representing project id.
      service: String representing service id.
      split_list: List of tuples containing version name and traffic split.

    Returns:
      A messages.Service response object.
    """
    # For convenience.
    split = self.messages.TrafficSplit(
        allocations=self.messages.TrafficSplit.AllocationsValue(
            additionalProperties=[]))
    for version, traffic in split_list:
      # The server only returns versions with traffic.
      if traffic > 0:
        split.allocations.additionalProperties.append(
            self.messages.TrafficSplit.AllocationsValue.AdditionalProperty(
                key=version, value=traffic))
    return self.messages.Service(
        name='apps/{0}/services/{1}'.format(app, service),
        id=service,
        split=split)

  def ExpectGetServiceRequest(self, app, service, split):
    """Adds expected get-service call and response to mock client."""
    request = self.messages.AppengineAppsServicesGetRequest(
        name='apps/{0}/services/{1}'.format(app, service))
    response = self.GetServiceResponse(app, service, split)
    self.mock_client.apps_services.Get.Expect(request, response=response)

  def VmBetaSettings(self, vm_runtime='java'):
    """Helper function, creates beta settings for a vm runtime."""
    beta_properties = {
        'module_yaml_path': 'app.yaml',
        'vm_runtime': vm_runtime
    }
    return self.messages.Version.BetaSettingsValue(
        additionalProperties=[
            self.messages.Version.BetaSettingsValue.AdditionalProperty(
                key=key, value=value)
            for (key, value) in sorted(beta_properties.items())
        ]
    )

  def DefaultHandlers(self, with_static=False):
    """Helper function to create the basic handlers message."""
    handlers = [self.messages.UrlMap(
        script=self.messages.ScriptHandler(scriptPath='home.app'),
        securityLevel=self.messages.UrlMap.SecurityLevelValueValuesEnum(3),
        urlRegex='/'
    )]
    if with_static:
      handlers.append(self.messages.UrlMap(
          staticFiles=self.messages.StaticFilesHandler(
              path='foo/\\1',
              uploadPathRegex='foo/.*'),
          urlRegex='/static/(.*)',
          securityLevel=self.messages.UrlMap.SecurityLevelValueValuesEnum(3)))
    return handlers

  def GetDeploymentMessage(self, filenames=None,
                           source_url_base=DEFAULT_URL,
                           container_image_url=None,
                           directory=None):
    """Gets deployment message for version Create call.

    Args:
      filenames: None or [str], the filenames to use to create the message.
          Filenames must be the names of existing files. If "None" given,
          self.DEFAULT_FILES is used.
      source_url_base: str, base of sourceUrl for each filename in message
      container_image_url: str, URL of image to be used in deployment
      directory: str, directory where filenames are located

    Returns:
      (appengine_v1_messages.Deployment) the deployment message to be used
          in a version create request.
    """
    if filenames is None:  # Allow someone to pass empty list for no files.
      filenames = self.DEFAULT_FILES
    if filenames:
      expected_manifest = {}
      for filename in filenames:
        expected_manifest[filename.replace('\\', '/')] = {
            'sourceUrl': (
                source_url_base + file_utils.Checksum.HashSingleFile(
                    self.FullPath(filename.replace('\\', '/'),
                                  directory=directory),
                    algorithm=hashlib.sha1)),
            'sha1Sum': file_utils.Checksum.HashSingleFile(
                self.FullPath(filename.replace('\\', '/'), directory=directory),
                algorithm=hashlib.sha1)}
      deployment_message = encoding.PyValueToMessage(
          self.messages.Deployment, {'files': expected_manifest})
      deployment_message.files.additionalProperties.sort(
          key=operator.attrgetter('key'))
    else:
      deployment_message = self.messages.Deployment()
    if container_image_url:
      deployment_message.container = self.messages.ContainerInfo(
          image=container_image_url)
    return deployment_message

  def GetCreateVersionCall(self, project, service, version_id,
                           beta_settings=None, deployment=None, handlers=None,
                           api_version=None, threadsafe=True,
                           **version_call_args):
    """Helper function to create a create version call."""
    if handlers is None:
      handlers = self.DefaultHandlers()
    version = self.messages.Version(
        id=version_id,
        betaSettings=beta_settings,
        deployment=deployment,
        handlers=handlers,
        threadsafe=threadsafe,
        runtimeApiVersion=api_version,
        **version_call_args
    )
    return self.messages.AppengineAppsServicesVersionsCreateRequest(
        parent='apps/{0}/services/{1}'.format(project, service),
        version=version)

  def ExpectCreateVersion(self, project, service, version_id, num_attempts=1,
                          success=True, deployment=None,
                          handlers=None, beta_settings=None,
                          version_call_args=None,
                          operation_metadata=None):
    """Adds expected version create call and response to mock client.

    Args:
      project: str, the project ID
      service: str, the name of the service being updated.
      version_id: str, the ID of the version being created.
      num_attempts: int, the number of total attempts to be expected
      success: bool, whether operation should succeed
      deployment: appengine_v1_messages.Deployment, the expected
          deployment manifest message.
      handlers: [handler] the list of handlers expected in the create version
          call.
      beta_settings: appengine_v1_messages.Version.BetaSettingsValue,
          the beta settings in the app.yaml if any.
      version_call_args: kwargs to be added to the Version message, if any
          (e.g. {'vm': True}.
      operation_metadata: Metadata to be returned in the operation.
    """
    version_call_args = version_call_args or self.DEFAULT_SERVICE_CONFIG
    op_name = VersionOperationName(project, service)
    version_call = self.GetCreateVersionCall(
        project, service, version_id, beta_settings, deployment, handlers,
        **version_call_args)
    polling_call = self.messages.AppengineAppsOperationsGetRequest(
        name=VersionOperationName(project, service))
    version_not_created_response = self.messages.Operation(name=op_name,
                                                           done=False)
    if success:
      final_response = self.messages.Operation(
          name=op_name,
          done=True,
          metadata=operation_metadata,
          response=encoding.JsonToMessage(
              self.messages.Operation.ResponseValue,
              encoding.MessageToJson(version_call.version)))
    else:
      final_response = version_not_created_response
    retry.ExpectWithRetries(
        method=self.mock_client.apps_services_versions.Create,
        polling_method=self.mock_client.apps_operations.Get,
        request=version_call,
        polling_request=polling_call,
        response=version_not_created_response,
        final_response=final_response,
        num_retries=num_attempts-1)

  def CreateVersionErrorResponse(self, app, service, message=None):
    """Helper function to get error response on create version attempt."""
    return self.messages.Operation(
        name=VersionOperationName(app, service),
        done=True,
        error=self.messages.Status(message=message))

  def ExpectMigrateTraffic(self, project, service, version):
    """Adds the appropriate set traffic call and response to mock client.

    Args:
      project: str, the project ID.
      service: str, the name of the service being updated.
      version: str, the version ID that will now be receiving traffic.
    """
    traffic_split = {version: 1.0}
    self.ExpectSetTraffic(project, service, traffic_split, migrate=True,
                          shard_by=None)

  def ExpectSetTraffic(self, project, service, allocations, shard_by='IP',
                       migrate=False, exception=None):
    """Expects a set traffic call.

    Args:
      project: str, the project ID.
      service: str, the name of the service being updated.
      allocations: dict, the dict of versions to desired traffic split, such as
          {'version1': 1.0, 'version2': 0.0}.
      shard_by: str, the desired value for the shardBy field in the split.
      migrate: bool, whether to migrate traffic.
      exception: None|apitools.base.py.exceptions.HttpError, the expected error,
          if any.
    """
    traffic_split = encoding.PyValueToMessage(
        self.messages.TrafficSplit,
        {'allocations': allocations,
         'shardBy': shard_by})
    patch_call = self.messages.AppengineAppsServicesPatchRequest(
        name='apps/{0}/services/{1}'.format(project, service),
        updateMask='split',
        migrateTraffic=migrate,
        service=self.messages.Service(
            split=traffic_split))
    if not exception:
      # TODO(b/30739284): Use resource parsing.
      op_name = 'apps/{0}/operations/{1}'.format(project, service)
      final_response = self.messages.Operation(
          name=op_name,
          done=True,
          response=encoding.JsonToMessage(
              self.messages.Operation.ResponseValue,
              encoding.MessageToJson(patch_call)))
    else:
      final_response = None
    self.mock_client.apps_services.Patch.Expect(
        patch_call, response=final_response, exception=exception)

  def ExpectSetDefault(self, project, service, version, num_tries=1,
                       success=True):
    """Adds expected set-default call and response to mock client.

    Args:
      project: str, the project ID
      service: str, the name of the service being updated.
      version: str, the ID of the version being created.
      num_tries: int, number of times that setting default will be attempted.
      success: bool, whether operation is expected to succeed.
    """
    op_name = 'apps/{0}/services/{1}/versions/{2}'.format(project,
                                                          service,
                                                          version)
    traffic_split = encoding.PyValueToMessage(
        self.messages.TrafficSplit,
        {'allocations': {version: 1.0},
         'shardBy': 'UNSPECIFIED'})
    patch_call = self.messages.AppengineAppsServicesPatchRequest(
        name='apps/{0}/services/{1}'.format(project, service),
        updateMask='split',
        migrateTraffic=False,
        service=self.messages.Service(
            split=traffic_split))
    err = http_error.MakeDetailedHttpError(
        message='Service does not exist',
        details=http_error.ExampleErrorDetails())
    if success:
      final_response = self.messages.Operation(
          name=op_name,
          done=True,
          response=encoding.JsonToMessage(
              self.messages.Operation.ResponseValue,
              encoding.MessageToJson(patch_call)))
    else:
      final_response = err
    retry.ExpectWithRetries(
        method=self.mock_client.apps_services.Patch,
        request=patch_call,
        response=err,
        final_response=final_response,
        num_retries=num_tries - 1)

  def _ExpectPatchVersionRequest(self, project, service, version,
                                 serving_status, num_retries=0):
    """Helper function for stopping and starting versions."""
    version_message = self.messages.Version(
        servingStatus=serving_status
    )
    version_name = 'apps/{0}/services/{1}/versions/{2}'.format(project, service,
                                                               version)
    stop_version_call = self.messages.AppengineAppsServicesVersionsPatchRequest(
        name=version_name,
        updateMask='servingStatus',
        version=version_message)
    op_name = VersionOperationName(project, service, version)
    req = self.messages.AppengineAppsServicesVersionsPatchRequest(
        name=version_name)
    done_message = self.messages.Operation(
        name=op_name,
        done=True,
        response=encoding.JsonToMessage(
            self.messages.Operation.ResponseValue,
            encoding.MessageToJson(req)))
    not_done_message = self.messages.Operation(
        name=op_name, done=False)
    polling_request = self.messages.AppengineAppsOperationsGetRequest(
        name=op_name)
    retry.ExpectWithRetries(
        method=self.mock_client.apps_services_versions.Patch,
        polling_method=self.mock_client.apps_operations.Get,
        request=stop_version_call,
        polling_request=polling_request,
        response=not_done_message,
        final_response=done_message,
        num_retries=num_retries)

  def ExpectStopVersionRequest(self, project, service, version,
                               num_retries=0):
    """Adds expected stop-version call and response to mock client.

    Args:
      project: str, the project ID
      service: str, the name of the service being updated.
      version: str, the ID of the version being created.
      num_retries: int, the number of tries it is expected to take.
    """
    serving_status = self.messages.Version.ServingStatusValueValuesEnum.STOPPED
    self._ExpectPatchVersionRequest(project, service, version,
                                    serving_status, num_retries=num_retries)

  def ExpectStartVersionRequest(self, project, service, version, num_retries=0):
    """Adds expected start-version call and response to mock client.

    Args:
      project: str, the project ID
      service: str, the name of the service being updated.
      version: str, the ID of the version being created.
      num_retries: int, the number of tries it is expected to take.
    """
    serving_status = self.messages.Version.ServingStatusValueValuesEnum.SERVING
    self._ExpectPatchVersionRequest(project, service, version,
                                    serving_status, num_retries=num_retries)

  def GetListServicesResponse(self, project, services, with_split=True):
    """Helper function to create dummy responses for the Services.List call."""
    services_responses = []
    for service, versions in sorted(six.iteritems(services)):
      if with_split:
        split = self.messages.TrafficSplit(
            allocations=self.messages.TrafficSplit.AllocationsValue(
                additionalProperties=[]))
        for version, version_info in six.iteritems(versions):
          # The server only adds a version to this field if split is non-zero.
          traffic = version_info.get('traffic_split', 0)
          if traffic > 0:
            split.allocations.additionalProperties.append(
                self.messages.TrafficSplit.AllocationsValue.AdditionalProperty(
                    key=version, value=traffic))
      else:
        split = None
      services_responses.append(self.messages.Service(
          name='apps/{0}/services/{1}'.format(project, service),
          id=service,
          split=split))
    response = self.messages.ListServicesResponse(
        services=services_responses)
    return response

  def ExpectListServicesRequest(self, project, services=None, with_split=True):
    """Adds expected list services request and response.

    Args:
      project: str, the project ID.
      services: {str: {}}, dict of service names to lookups of version name to
          version information (e.g. {'traffic_split': 1.0})
      with_split: bool, if the response should include split fields.
    """
    services = services or {}
    request = self.messages.AppengineAppsServicesListRequest(
        parent='apps/{}'.format(project), pageSize=100)
    response = self.GetListServicesResponse(project, services,
                                            with_split=with_split)
    self.mock_client.apps_services.List.Expect(request,
                                               response=response)

  def GetListVersionsResponse(self, project, service, existing_services):
    """Creates dummy responses for the Versions.List call."""
    serving_status = self.messages.Version.ServingStatusValueValuesEnum.SERVING
    versions_responses = []
    service_info = existing_services.get(service, {})
    for version, version_info in six.iteritems(service_info):
      versions_responses.append(
          self.messages.Version(
              id=version,
              name='apps/{0}/services/{1}/versions/{2}'.format(
                  project, service, version),
              servingStatus=serving_status,
              env=version_info.get('env', None),
              vm=version_info.get('vm', None),
              manualScaling=version_info.get('manual_scaling', None),
              basicScaling=version_info.get('basic_scaling', None),
              createTime=version_info.get('creation_time', None),
              versionUrl='https://{0}-dot-{1}-dot-{2}.appspot.com'.format(
                  version, service, project)))

    return self.messages.ListVersionsResponse(versions=versions_responses)

  def ExpectListVersionsRequest(self, project, service, existing_services):
    """Adds expected list versions request and response to mock client.

    Args:
      project: str, the project ID.
      service: str, the service ID to request versions for.
      existing_services: {str: {}}, dict of service names to lookups of version
          name to version information (e.g. {'traffic_split': 1.0})
    """
    request = self.messages.AppengineAppsServicesVersionsListRequest(
        parent='apps/{0}/services/{1}'.format(project, service), pageSize=100)
    response = self.GetListVersionsResponse(project, service, existing_services)
    self.mock_client.apps_services_versions.List.Expect(request,
                                                        response=response)

  def ExpectDeleteServiceRequest(self, project, service, exception=None,
                                 retries=0):
    """Adds expected delete services request and response to mock client.

    Args:
      project: str, the project ID.
      service: str, the service ID to delete.
      exception: None|apitools.base.py.exceptions.HttpError, the error to be
          returned, if any.
      retries: Number of retries required to succeed.
    """
    request = self.messages.AppengineAppsServicesDeleteRequest(
        name='apps/{0}/services/{1}'.format(project, service)
    )
    op_name = ServiceOperationName(project, service)
    service = self.messages.Service(
        name='apps/{0}/services/{1}'.format(project, service),
        id=service)
    if not exception:
      polling_request = self.messages.AppengineAppsOperationsGetRequest(
          name=op_name)
      intermediate_response = self.messages.Operation(
          name=op_name,
          done=False)
      response = self.messages.Operation(
          name=op_name,
          done=True,
          response=encoding.JsonToMessage(
              self.messages.Operation.ResponseValue,
              encoding.MessageToJson(service)))
      retry.ExpectWithRetries(
          method=self.mock_client.apps_services.Delete,
          polling_method=self.mock_client.apps_operations.Get,
          request=request,
          polling_request=polling_request,
          response=intermediate_response,
          final_response=response,
          num_retries=retries)
    else:
      self.mock_client.apps_services.Delete.Expect(request, exception=exception)

  def ExpectDeleteVersionRequest(self, project, service, version,
                                 exception=None):
    """Adds expected delete version request and response to mock client.

    Args:
      project: str, the project ID.
      service: str, the service ID.
      version: str, the version ID to delete.
      exception: None|apitools.base.py.exceptions.HttpError, the error to be
          returned, if any.
    """
    request = self.messages.AppengineAppsServicesVersionsDeleteRequest(
        name='apps/{0}/services/{1}/versions/{2}'.format(project, service,
                                                         version)
    )
    op_name = VersionOperationName(project, service, version)
    version = self.messages.Version(
        name='apps/{0}/services/{1}/versions/{2}'.format(project, service,
                                                         version),
        id=version)
    if not exception:
      response = self.messages.Operation(
          name=op_name,
          done=True,
          response=encoding.JsonToMessage(
              self.messages.Operation.ResponseValue,
              encoding.MessageToJson(version)))
      self.mock_client.apps_services_versions.Delete.Expect(request,
                                                            response=response)
    else:
      self.mock_client.apps_services_versions.Delete.Expect(request,
                                                            exception=exception)

  def _GetRepairApplicationRequest(self, project):
    return self.messages.AppengineAppsRepairRequest(
        name='apps/{0}'.format(project),
        repairApplicationRequest=self.messages.RepairApplicationRequest())

  def ExpectRepairApplicationRequest(self, project, num_retries=0):
    op_name = AppOperationName(project)
    method = self.mock_client.apps.Repair
    request = self._GetRepairApplicationRequest(self.Project())
    response = self.messages.Operation(name=op_name, done=False)
    final_response = self.messages.Operation(name=op_name, done=True)
    polling_method = self.mock_client.apps_operations.Get
    polling_request = self.messages.AppengineAppsOperationsGetRequest(
        name=op_name)
    retry.ExpectWithRetries(
        method, request, response, polling_method=polling_method,
        polling_request=polling_request, final_response=final_response,
        num_retries=num_retries)

  def GetListRegionsResponse(self, regions, project):
    """Helper function to build an apps_locations.List response.

    Args:
      regions: A dict mapping string region names to an array of
     (<string>, <bool>) tuples, in which <string> is one of
     'standardEnvironmentAvailable' or 'flexibleEnvironmentAvailable'.
      project: str, the project ID.
    Returns:
      A google.cloud.location.ListLocationsResponse message.
    """
    regions_responses = []
    meta_type = 'type.googleapis.com/google.appengine.v1.LocationMetadata'

    for region, environments in six.iteritems(regions):
      response_type = self.messages.Location.MetadataValue.AdditionalProperty(
          key='@type',
          value=extra_types.JsonValue(string_value=meta_type))

      env_availability = [
          self.messages.Location.MetadataValue.AdditionalProperty(
              key=environment,
              value=extra_types.JsonValue(
                  boolean_value=availability))
          for environment, availability in environments]
      env_availability.append(response_type)

      regions_responses.append(
          self.messages.Location(
              name='apps/{0}/locations/{1}'.format(project, region),
              labels=self.messages.Location.LabelsValue(
                  additionalProperties=[
                      self.messages.Location.LabelsValue.AdditionalProperty(
                          key='cloud.googleapis.com/region',
                          value=region
                      )]
              ),
              metadata=self.messages.Location.MetadataValue(
                  additionalProperties=env_availability
              )
          )
      )
    response = self.messages.ListLocationsResponse(locations=regions_responses)
    return response

  def ExpectListRegionsRequest(self, regions, project):
    """Sets up expected request and response for regions.List call.

    Args:
      regions: A dict mapping string region names to an array of
      (<string>, <bool>) tuples, in which <string> is one of
      'standardEnvironmentAvailable' or 'flexibleEnvironmentAvailable'.
      project: str, the project ID.
    """
    response = self.GetListRegionsResponse(regions, project)
    request = self.messages.AppengineAppsLocationsListRequest(
        name='apps/{0}'.format(project), pageSize=100)
    self.mock_client.apps_locations.List.Expect(request, response)


def VersionOperationName(app, service, version='1234'):
  return 'apps/{0}/operations/{1}-{2}'.format(app, service, version)


def ServiceOperationName(app, service):
  return 'apps/{0}/operations/{1}'.format(app, service)


def AppOperationName(app, operation_id='12345'):
  return 'apps/{0}/operations/{1}'.format(app, operation_id)
