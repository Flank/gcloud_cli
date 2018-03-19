# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Base class for instances tests."""

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.surface.app import api_test_util


class InstancesTestBase(cli_test_base.CliTestBase,
                        sdk_test_base.WithFakeAuth):
  """Base class for instances tests."""

  PROJECT = 'fakeproject'

  COMPUTE_INSTANCES = None

  def _FormatApp(self):
    return 'apps/{0}'.format(self.PROJECT)

  def _FormatService(self, service):
    return 'apps/{0}/services/{1}'.format(self.PROJECT, service)

  def _FormatVersion(self, service, version):
    return 'apps/{0}/services/{1}/versions/{2}'.format(
        self.PROJECT, service, version)

  def _FormatInstance(self, service, version, instance):
    return 'apps/{0}/services/{1}/versions/{2}/instances/{3}'.format(
        self.PROJECT, service, version, instance)

  def _GetVMName(self, instance):
    """Use different VM name than instance id."""
    return 'vm-{0}'.format(instance)

  def _MakeService(self, service):
    return self.messages.Service(id=service, name=self._FormatService(service))

  def _MakeVersion(self, service, version):
    """Make a version message object.

    If version contains "flex" or "mvm", fields will be populated accordingly.

    Args:
      service: str, service id
      version: str, version id

    Returns:
      A Version API message object.
    """
    env = 'flexible' if 'flex' in version else None
    vm = 'mvm' in version
    return self.messages.Version(id=version,
                                 name=self._FormatVersion(service, version),
                                 vm=vm, env=env)

  def _MakeInstance(self, service, version, instance, vm_name=None):
    """Create an instance API messages object.

    If instance contains "debug", fields for indicating debug mode enabled will
    be populated accordingly.

    Args:
      service: str, service id
      version: str, version id
      instance: str, instance id
      vm_name: str, vm_name to populate on the instance

    Returns:
      An Instance API message object.
    """
    debug_enabled = 'debug' in instance
    return self.messages.Instance(
        id=instance, name=self._FormatInstance(service, version, instance),
        vmName=vm_name,
        vmStatus='RUNNING',
        vmDebugEnabled=debug_enabled)

  def _MakeUtilInstance(self, service, version, instance):
    """Make an instances_util.Instance object, populated with API message."""
    vm_name = self._GetVMName(instance)
    instance_msg = self._MakeInstance(service, version, instance, vm_name)
    return instances_util.Instance(service, version, instance, instance_msg)

  def _ExpectListServicesCall(self, services):
    services = map(self._MakeService, services)
    self.mocked_client.apps_services.List.Expect(
        request=self.messages.AppengineAppsServicesListRequest(
            parent=self._FormatApp(), pageSize=100),
        response=self.messages.ListServicesResponse(services=services))

  def _ExpectListVersionsCall(self, service, versions):
    versions = [self._MakeVersion(service, version) for version in versions]
    self.mocked_client.apps_services_versions.List.Expect(
        request=self.messages.AppengineAppsServicesVersionsListRequest(
            parent=self._FormatService(service), pageSize=100),
        response=self.messages.ListVersionsResponse(versions=versions))

  def _ExpectListInstancesCall(self, service, version, instances):
    instances = [self._MakeInstance(service, version, i, self._GetVMName(i))
                 for i in instances]
    self.mocked_client.apps_services_versions_instances.List.Expect(
        request=self.messages.AppengineAppsServicesVersionsInstancesListRequest(
            parent=self._FormatVersion(service, version), pageSize=100),
        response=self.messages.ListInstancesResponse(instances=instances))

  def _InstanceOperationName(self, service, version, instance):
    return ('apps/{app}/operations/{s}-{v}-{i}'
            .format(app=self.PROJECT, s=service, v=version, i=instance))

  def _ExpectDebugInstanceCall(self, service, version, instance, ssh_key=None):
    """Creates dummy responses for the Instances.Debug API call."""

    op_name = self._InstanceOperationName(service, version, instance)
    instance_msg = self._MakeInstance(service, version, instance)

    debug_request = self.messages.DebugInstanceRequest(sshKey=ssh_key)
    req = self.messages.AppengineAppsServicesVersionsInstancesDebugRequest(
        name=self._FormatInstance(service, version, instance),
        debugInstanceRequest=debug_request)
    self.mocked_client.apps_services_versions_instances.Debug.Expect(
        request=req,
        response=self.messages.Operation(
            name=op_name,
            done=True,
            response=encoding.JsonToMessage(
                self.messages.Operation.ResponseValue,
                encoding.MessageToJson(instance_msg))))

  def _ExpectDeleteInstanceCall(self, service, version, instance):
    """Creates dummy responses for the Instances.Delete API call."""

    op_name = self._InstanceOperationName(service, version, instance)
    instance_msg = self._MakeInstance(service, version, instance)

    req = self.messages.AppengineAppsServicesVersionsInstancesDeleteRequest(
        name=self._FormatInstance(service, version, instance))
    self.mocked_client.apps_services_versions_instances.Delete.Expect(
        request=req,
        response=self.messages.Operation(
            name=op_name,
            done=True,
            response=encoding.JsonToMessage(
                self.messages.Operation.ResponseValue,
                encoding.MessageToJson(instance_msg))))

  def _ExpectGetInstanceCall(self, service, version, instance,
                             debug_enabled=None):
    """Creates dummy responses for the Instances.Get API call."""

    req = self.messages.AppengineAppsServicesVersionsInstancesGetRequest(
        name=self._FormatInstance(service, version, instance))
    self.mocked_client.apps_services_versions_instances.Get.Expect(
        request=req,
        response=self.messages.Instance(
            id=instance,
            availability=self.messages.Instance.AvailabilityValueValuesEnum(
                'RESIDENT'),
            vmIp='127.0.0.1',
            vmName=self._GetVMName(instance),
            vmZoneName='us-central',
            startTime='2016-07-06T22:01:12.117Z',
            qps=8.4042234,
            vmStatus='RUNNING',
            vmDebugEnabled=debug_enabled))

  def _ExpectCalls(self, service_map):
    self._ExpectListServicesCall([service for service, _ in service_map])
    for service, version_map in service_map:
      if version_map:
        self._ExpectListVersionsCall(service,
                                     [version for version, _ in version_map])
    for service, version_map in service_map:
      for version, instances in version_map:
        if instances:
          self._ExpectListInstancesCall(service, version, instances)

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT)
    self.messages = core_apis.GetMessagesModule(
        'appengine', api_test_util.APPENGINE_API_VERSION)
    self.mocked_client = mock.Client(
        core_apis.GetClientClass(
            'appengine', api_test_util.APPENGINE_API_VERSION),
        real_client=core_apis.GetClientInstance(
            'appengine', api_test_util.APPENGINE_API_VERSION,
            no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
