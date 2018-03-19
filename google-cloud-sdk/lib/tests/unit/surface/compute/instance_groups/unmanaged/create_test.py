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
"""Tests for the instance-groups unmanaged create subcommand."""
from tests.lib import test_case
from tests.lib.surface.compute import test_base

API_VERSION = 'v1'


class UnmanagedInstanceGroupsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        []
    ])

  def testDefaultOptions(self):
    self.Run("""
        compute instance-groups unmanaged create group-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))],
        [(self.compute.instanceGroups,
          'Insert',
          self.messages.ComputeInstanceGroupsInsertRequest(
              instanceGroup=self.messages.InstanceGroup(name='group-1'),
              project='my-project',
              zone='central2-a'))],
    )

  def testWithDescription(self):
    self.Run("""
        compute instance-groups unmanaged create group-1
          --zone central2-a
          --description "Test group"
        """)

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))],
        [(self.compute.instanceGroups,
          'Insert',
          self.messages.ComputeInstanceGroupsInsertRequest(
              instanceGroup=self.messages.InstanceGroup(
                  name='group-1',
                  description='Test group'),
              project='my-project',
              zone='central2-a'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute instance-groups unmanaged create
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instanceGroups/group-1
        """.format(API_VERSION))

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))],
        [(self.compute.instanceGroups,
          'Insert',
          self.messages.ComputeInstanceGroupsInsertRequest(
              instanceGroup=self.messages.InstanceGroup(name='group-1'),
              project='my-project',
              zone='central2-a'))],
    )

  def testZonePrompting(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Zone(name='central2-a'),
        ],
        []
    ])
    self.WriteInput('3\n')
    self.Run("""
        compute instance-groups unmanaged create group-1
        """)

    self.CheckRequests(
        self.zones_list_request,
        [(self.compute.zones,
          'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project',
              zone='central2-a'))],
        [(self.compute.instanceGroups,
          'Insert',
          self.messages.ComputeInstanceGroupsInsertRequest(
              instanceGroup=self.messages.InstanceGroup(name='group-1'),
              project='my-project',
              zone='central2-a'))],
    )

    self.AssertErrContains('group-1')
    self.AssertErrContains('central1-a')
    self.AssertErrContains('central1-b')
    self.AssertErrContains('central2-a')


if __name__ == '__main__':
  test_case.main()
