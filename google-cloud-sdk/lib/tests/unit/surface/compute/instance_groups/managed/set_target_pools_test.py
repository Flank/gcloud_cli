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
"""Tests for the instance-groups managed set-target-pools subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from mock import patch


class _InstanceGroupManagersSetTargetPoolsZonalTestBase(object):

  def testWithName(self):
    self.Run('compute instance-groups managed set-target-pools group-1 --zone '
             'central2-a --target-pools target-pool-1,target-pool-2')

    request = self.GetRequest(
        project='my-project',
        zone='central2-a',
        instance_group_manager='group-1',
        target_pools=[
            self.compute_uri + '/projects/my-project/regions'
            '/central2/targetPools/target-pool-1',
            self.compute_uri + '/projects/my-project/'
            'regions/central2/targetPools/target-pool-2'
        ])
    self.CheckRequests([(self.compute.instanceGroupManagers,
                         self.GetRequestName(), request)])

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/zones/central2-a/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    target_pool_uri = (self.compute_uri + '/projects/my-project/regions'
                       '/central2/targetPools/target-pool-1')
    self.Run('compute instance-groups managed set-target-pools {0} --zone '
             'central2-a --target-pools {1}'.format(
                 igm_uri, target_pool_uri))

    request = self.GetRequest(
        project='my-project',
        zone='central2-a',
        instance_group_manager='group-1',
        target_pools=[
            self.compute_uri + '/projects/my-project/regions'
            '/central2/targetPools/target-pool-1'
        ])
    self.CheckRequests([(self.compute.instanceGroupManagers,
                         self.GetRequestName(), request)])

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

    request = self.GetRequest(
        project='my-project',
        zone='central2-a',
        instance_group_manager='group-1',
        target_pools=[
            self.compute_uri + '/projects/my-project/regions'
            '/central2/targetPools/target-pool-1',
            self.compute_uri + '/projects/my-project/'
            'regions/central2/targetPools/target-pool-2'
        ])
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.instanceGroupManagers, self.GetRequestName(), request)],
    )

  def testClearTargetPools(self):
    self.Run('compute instance-groups managed set-target-pools group-1 --zone '
             'central2-a --target-pools ""')

    request = self.GetRequest(
        project='my-project',
        zone='central2-a',
        instance_group_manager='group-1',
        target_pools=[])
    self.CheckRequests([(self.compute.instanceGroupManagers,
                         self.GetRequestName(), request)])

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run('compute instance-groups managed set-target-pools group-1 '
               '--zone central2-a --target-pools target-pool-1,target-pool-2')


class InstanceGroupManagersSetTargetPoolsZonalTestV1(
    test_base.BaseTest, _InstanceGroupManagersSetTargetPoolsZonalTestBase):

  def SetUp(self):
    self.SelectApi('v1')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
    ])

  def GetRequest(self, project, zone, instance_group_manager, target_pools):
    return (self.messages.ComputeInstanceGroupManagersSetTargetPoolsRequest(
        project=project,
        zone=zone,
        instanceGroupManager=instance_group_manager,
        instanceGroupManagersSetTargetPoolsRequest=(
            self.messages.InstanceGroupManagersSetTargetPoolsRequest(
                targetPools=target_pools,))))

  def GetRequestName(self):
    return 'SetTargetPools'


class InstanceGroupManagersSetTargetPoolsZonalTestBeta(
    test_base.BaseTest, _InstanceGroupManagersSetTargetPoolsZonalTestBase):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
    ])

  def GetRequest(self, project, zone, instance_group_manager, target_pools):
    return (self.messages.ComputeInstanceGroupManagersPatchRequest(
        project=project,
        zone=zone,
        instanceGroupManager=instance_group_manager,
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            targetPools=target_pools))))

  def GetRequestName(self):
    return 'Patch'


class InstanceGroupManagersSetTargetPoolsRegionalTest(object):

  def testWithName(self):
    self.Run("""
        compute instance-groups managed set-target-pools group-1
            --region central2
            --target-pools target-pool-1,target-pool-2
        """)

    request = self.GetRequest(
        project='my-project',
        region='central2',
        instance_group_manager='group-1',
        target_pools=[
            self.compute_uri + '/projects/my-project/regions'
            '/central2/targetPools/target-pool-1',
            self.compute_uri + '/projects/my-project/'
            'regions/central2/targetPools/target-pool-2'
        ])
    self.CheckRequests([(self.compute.regionInstanceGroupManagers,
                         self.GetRequestName(), request)],)

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

    request = self.GetRequest(
        project='my-project',
        region='central2',
        instance_group_manager='group-1',
        target_pools=[
            self.compute_uri + '/projects/my-project/regions'
            '/central2/targetPools/target-pool-1'
        ])
    self.CheckRequests([(self.compute.regionInstanceGroupManagers,
                         self.GetRequestName(), request)],)

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

    request = self.GetRequest(
        project='my-project',
        region='central2',
        instance_group_manager='group-1',
        target_pools=[
            self.compute_uri + '/projects/my-project/regions'
            '/central2/targetPools/target-pool-1',
            self.compute_uri + '/projects/my-project/'
            'regions/central2/targetPools/target-pool-2'
        ])
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers, self.GetRequestName(),
          request)],
    )

  def testClearTargetPools(self):
    self.Run("""
        compute instance-groups managed set-target-pools group-1
            --region central2
            --target-pools ""
        """)

    request = self.GetRequest(
        project='my-project',
        region='central2',
        instance_group_manager='group-1',
        target_pools=[])
    self.CheckRequests([(self.compute.regionInstanceGroupManagers,
                         self.GetRequestName(), request)])


class InstanceGroupManagersSetTargetPoolsRegionalTestV1(
    test_base.BaseTest, InstanceGroupManagersSetTargetPoolsRegionalTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.make_requests.side_effect = iter([[]])

  def GetRequest(self, project, region, instance_group_manager, target_pools):
    return (
        self.messages.ComputeRegionInstanceGroupManagersSetTargetPoolsRequest(
            project=project,
            region=region,
            instanceGroupManager=instance_group_manager,
            regionInstanceGroupManagersSetTargetPoolsRequest=(
                self.messages.RegionInstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=target_pools,))))

  def GetRequestName(self):
    return 'SetTargetPools'


class InstanceGroupManagersSetTargetPoolsRegionalTestBeta(
    test_base.BaseTest, InstanceGroupManagersSetTargetPoolsRegionalTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.make_requests.side_effect = iter([[]])

  def GetRequest(self, project, region, instance_group_manager, target_pools):
    return (self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
        project=project,
        region=region,
        instanceGroupManager=instance_group_manager,
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            targetPools=target_pools))))

  def GetRequestName(self):
    return 'Patch'


if __name__ == '__main__':
  test_case.main()
