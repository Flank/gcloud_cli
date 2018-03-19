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
"""Tests for the instance-groups managed set-target-pools subcommand."""

from tests.lib import test_case
from tests.lib.surface.compute import test_base

API_VERSION = 'v1'


class InstanceGroupManagersSetTargetPoolsZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
    ])

  def testWithName(self):
    self.Run('compute instance-groups managed set-target-pools group-1 --zone '
             'central2-a --target-pools target-pool-1,target-pool-2')

    request = (
        self.messages.ComputeInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersSetTargetPoolsRequest=(
                self.messages.InstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=[
                        self.compute_uri + '/projects/my-project/regions'
                        '/central2/targetPools/target-pool-1',
                        self.compute_uri + '/projects/my-project/'
                        'regions/central2/targetPools/target-pool-2'],
                )
            ),
            project='my-project',
            zone='central2-a'
        )
    )
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'SetTargetPools', request)],
    )

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/zones/central2-a/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    target_pool_uri = (self.compute_uri + '/projects/my-project/regions'
                       '/central2/targetPools/target-pool-1')
    self.Run('compute instance-groups managed set-target-pools {0} --zone '
             'central2-a --target-pools {1}'.format(
                 igm_uri, target_pool_uri))

    request = (
        self.messages.ComputeInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersSetTargetPoolsRequest=(
                self.messages.InstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=[
                        self.compute_uri + '/projects/my-project/regions'
                        '/central2/targetPools/target-pool-1']
                )
            ),
            project='my-project',
            zone='central2-a'
        )
    )
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'SetTargetPools', request)],
    )

  def testZonePrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='central1'),
            self.messages.Region(name='central2'),
        ],
        [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        [],
    ])
    self.WriteInput('5\n')
    self.Run('compute instance-groups managed set-target-pools group-1 '
             '--target-pools target-pool-1,target-pool-2')

    request = (
        self.messages.ComputeInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersSetTargetPoolsRequest=(
                self.messages.InstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=[
                        self.compute_uri + '/projects/my-project/regions'
                        '/central2/targetPools/target-pool-1',
                        self.compute_uri + '/projects/my-project/'
                        'regions/central2/targetPools/target-pool-2'],
                )
            ),
            project='my-project',
            zone='central2-a'
        )
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.instanceGroupManagers, 'SetTargetPools', request)],
    )

  def testClearTargetPools(self):
    self.Run('compute instance-groups managed set-target-pools group-1 --zone '
             'central2-a --target-pools ""')

    request = (
        self.messages.ComputeInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersSetTargetPoolsRequest=(
                self.messages.InstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=[],
                )
            ),
            project='my-project',
            zone='central2-a'
        )
    )
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'SetTargetPools', request)],
    )


class InstanceGroupManagersSetTargetPoolsRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [],
    ])

  def testWithName(self):
    self.Run("""
        compute instance-groups managed set-target-pools group-1
            --region central2
            --target-pools target-pool-1,target-pool-2
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersSetTargetPoolsRequest=(
                self.messages.RegionInstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=[
                        self.compute_uri + '/projects/my-project/regions'
                        '/central2/targetPools/target-pool-1',
                        self.compute_uri + '/projects/my-project/'
                        'regions/central2/targetPools/target-pool-2'],
                )
            ),
            project='my-project',
            region='central2'
        )
    )
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'SetTargetPools', request)],
    )

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/regions/central2/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    target_pool_uri = (self.compute_uri + '/projects/my-project/regions'
                       '/central2/targetPools/target-pool-1')
    self.Run("""
        compute instance-groups managed set-target-pools {0}
            --region central2
            --target-pools {1}
        """.format(igm_uri, target_pool_uri))

    request = (
        self.messages.ComputeRegionInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersSetTargetPoolsRequest=(
                self.messages.RegionInstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=[
                        self.compute_uri + '/projects/my-project/regions'
                        '/central2/targetPools/target-pool-1']
                )
            ),
            project='my-project',
            region='central2'
        )
    )
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'SetTargetPools', request)],
    )

  def testZonePrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='central1'),
            self.messages.Region(name='central2'),
        ],
        [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        [],
    ])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups managed set-target-pools group-1
            --target-pools target-pool-1,target-pool-2
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersSetTargetPoolsRequest=(
                self.messages.RegionInstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=[
                        self.compute_uri + '/projects/my-project/regions'
                        '/central2/targetPools/target-pool-1',
                        self.compute_uri + '/projects/my-project/'
                        'regions/central2/targetPools/target-pool-2'],
                )
            ),
            project='my-project',
            region='central2'
        )
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers, 'SetTargetPools', request)],
    )

  def testClearTargetPools(self):
    self.Run("""
        compute instance-groups managed set-target-pools group-1
            --region central2
            --target-pools ""
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersSetTargetPoolsRequest=(
                self.messages.RegionInstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=[],
                )
            ),
            project='my-project',
            region='central2'
        )
    )
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'SetTargetPools', request)],
    )

if __name__ == '__main__':
  test_case.main()
