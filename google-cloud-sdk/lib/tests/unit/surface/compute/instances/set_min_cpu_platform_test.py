# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the instances set-min-cpu-platform subcommand."""

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


_DEFAULT_CPU_PLATFORM = 'CpuPlatform'


class SetMinCpuPlatformTest(sdk_test_base.WithFakeAuth,
                            cli_test_base.CliTestBase, waiter_test_base.Base):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.client_class = core_apis.GetClientClass('compute', 'alpha')
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

  def Client(self):
    return api_mock.Client(
        self.client_class,
        real_client=core_apis.GetClientInstance(
            'compute', 'alpha', no_http=True))

  def _GetOperationRef(self, name, zone):
    return self.resources.Parse(
        name,
        params={'project': self.Project(),
                'zone': zone},
        collection='compute.zoneOperations')

  def _GetInstanceRef(self, name, zone):
    return self.resources.Parse(
        name,
        params={'project': self.Project(),
                'zone': zone},
        collection='compute.instances')

  def _GetOperationMessage(self, operation_ref, status, resource_ref=None):
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=status,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def ExpectSetMinCpuPlatform(self, client, cpu_platform=_DEFAULT_CPU_PLATFORM):
    messages = self.messages
    client.instances.SetMinCpuPlatform.Expect(
        messages.ComputeInstancesSetMinCpuPlatformRequest(
            instancesSetMinCpuPlatformRequest=
            messages.InstancesSetMinCpuPlatformRequest(
                minCpuPlatform=cpu_platform),
            project=self.Project(),
            zone='central2-a',
            instance='instance-1'),
        self._GetOperationMessage(
            self._GetOperationRef('operation-X', 'central2-a'),
            messages.Operation.StatusValueValuesEnum.PENDING))

  def _MakeSetMinCpuPlatformRequest(self, cpu_platform=_DEFAULT_CPU_PLATFORM):
    request = self.messages.InstancesSetMinCpuPlatformRequest(
        minCpuPlatform=cpu_platform)
    return (self.compute.instances, 'SetMinCpuPlatform',
            self.messages.ComputeInstancesSetMinCpuPlatformRequest(
                instancesSetMinCpuPlatformRequest=request,
                instance='instance-1',
                project='my-project',
                zone='central2-a'))

  def testWithOperationPolling(self):
    with self.Client() as client:
      self.ExpectSetMinCpuPlatform(client)

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self.Run("""
          compute instances set-min-cpu-platform instance-1
            --zone central2-a
            --min-cpu-platform CpuPlatform
          """)
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Changing minimum CPU platform of instance [instance-1]')

  def testAsync(self):
    with self.Client() as client:
      self.ExpectSetMinCpuPlatform(client)
      result = self.Run("""
          compute instances set-min-cpu-platform instance-1
            --zone central2-a
            --min-cpu-platform CpuPlatform
            --async
            --format=disable
          """)

    self.assertEqual('operation-X', result.name)

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'WARNING: This command is deprecated. Use $ gcloud alpha compute '
        'instances update --set-min-cpu-platform instead.\n'
        'Update in progress for gce instance [instance-1] '
        '[https://www.googleapis.com/compute/alpha/'
        'projects/fake-project/zones/central2-a/operations/operation-X] '
        'Use [gcloud compute operations describe] command to check the status '
        'of this operation.\n')

  def testNoMinCpuPlatformDefaults(self):
    with self.Client() as client:
      self.ExpectSetMinCpuPlatform(client, None)
      result = self.Run("""
          compute instances set-min-cpu-platform instance-1
            --zone central2-a
            --min-cpu-platform ""
            --async
            --format=disable
          """)
      self.assertEqual('operation-X', result.name)


if __name__ == '__main__':
  test_case.main()
