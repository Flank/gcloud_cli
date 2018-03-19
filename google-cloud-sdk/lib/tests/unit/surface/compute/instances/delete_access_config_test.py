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
"""Tests for the instances delete-access-config subcommand."""
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class InstancesDeleteAccessConfigTest(test_base.BaseTest):

  def testWithDefaults(self):
    self.Run("""
        compute instances delete-access-config instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'DeleteAccessConfig',
          messages.ComputeInstancesDeleteAccessConfigRequest(
              accessConfig='external-nat',
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithAllArgs(self):
    self.Run("""
        compute instances delete-access-config instance-1
          --access-config-name config
          --network-interface nic123
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'DeleteAccessConfig',
          messages.ComputeInstancesDeleteAccessConfigRequest(
              accessConfig='config',
              instance='instance-1',
              networkInterface='nic123',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithConfigFlag(self):
    self.Run("""
        compute instances delete-access-config instance-1
          --access-config-name config
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'DeleteAccessConfig',
          messages.ComputeInstancesDeleteAccessConfigRequest(
              accessConfig='config',
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithNetworkInterfaceFlag(self):
    self.Run("""
        compute instances delete-access-config instance-1
          --network-interface nic123
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'DeleteAccessConfig',
          messages.ComputeInstancesDeleteAccessConfigRequest(
              accessConfig='external-nat',
              instance='instance-1',
              networkInterface='nic123',
              project='my-project',
              zone='central2-a'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute instances delete-access-config
          https://www.googleapis.com/compute/v1/projects/my-project/zones/central2-a/instances/instance-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'DeleteAccessConfig',
          messages.ComputeInstancesDeleteAccessConfigRequest(
              accessConfig='external-nat',
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central2-a'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='instance-1', zone='central1-a'),
            messages.Instance(name='instance-1', zone='central1-b'),
            messages.Instance(name='instance-1', zone='central2-a'),
        ],

        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute instances delete-access-config instance-1
        """)

    self.AssertErrContains('instance-1')
    self.AssertErrContains('central1-a')
    self.AssertErrContains('central1-b')
    self.AssertErrContains('central2-a')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute_v1.instances,
          'DeleteAccessConfig',
          messages.ComputeInstancesDeleteAccessConfigRequest(
              accessConfig='external-nat',
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central1-a'))],
    )

  def testRepeadedNetworkInterface(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
          compute instances delete-access-config instance-1
          --access-config-name config
          --network-interface nic123
          --network-interface nic124
          --zone central2-a
          """)

if __name__ == '__main__':
  test_case.main()
