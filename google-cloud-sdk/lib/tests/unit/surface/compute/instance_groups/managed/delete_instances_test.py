# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the instance-groups managed delete-instances subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instance_groups import test_resources
from mock import patch

API_VERSION = 'v1'


class InstanceGroupManagersDeleteInstancesZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
    ])
    self.template_1_uri = (
        '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
            self.compute_uri))

  def testWithTwoInstances(self):
    result = list(self.Run(
        'compute instance-groups managed delete-instances group-1 '
        '--zone central2-a --instances instance1,instance2 --format=disable'
    ))

    instance1_self_link = ('{0}/projects/my-project/zones/central2-a/instances/'
                           'instance1'.format(self.compute_uri))
    instance2_self_link = ('{0}/projects/my-project/zones/central2-a/instances/'
                           'instance2'.format(self.compute_uri))

    instances = self.messages.InstanceGroupManagersDeleteInstancesRequest(
        instances=[instance1_self_link, instance2_self_link])
    delete_request = (
        self.messages.ComputeInstanceGroupManagersDeleteInstancesRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersDeleteInstancesRequest=instances,
            project='my-project',
            zone='central2-a')
    )
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'DeleteInstances',
          delete_request)],
    )

    self.assertEqual(len(result), 2)
    self.assertEqual(result[0]['selfLink'], instance1_self_link)
    self.assertEqual(result[0]['status'], 'SUCCESS')
    self.assertEqual(result[1]['selfLink'], instance2_self_link)
    self.assertEqual(result[1]['status'], 'SUCCESS')

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/zones/central2-a/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    instance_uri = ('{0}/projects/my-project/zones/central2-a/instances/'
                    'instance1'.format(self.compute_uri))
    self.Run('compute instance-groups managed delete-instances {0} --zone '
             'central2-a --instances {1}'.format(
                 igm_uri, instance_uri))

    instances = self.messages.InstanceGroupManagersDeleteInstancesRequest(
        instances=['{0}/projects/my-project/zones/central2-a/instances/'
                   'instance1'.format(self.compute_uri)])
    delete_request = (
        self.messages.ComputeInstanceGroupManagersDeleteInstancesRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersDeleteInstancesRequest=instances,
            project='my-project',
            zone='central2-a')
    )
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'DeleteInstances',
          delete_request)],
    )

  def testScopePrompt(self):
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
        []
    ])
    self.WriteInput('5\n')
    self.Run('compute instance-groups managed delete-instances group-1 '
             '--instances instance1')

    instances = self.messages.InstanceGroupManagersDeleteInstancesRequest(
        instances=[
            '{0}/projects/my-project/zones/central2-a/instances/instance1'
            .format(self.compute_uri)])
    delete_request = (
        self.messages.ComputeInstanceGroupManagersDeleteInstancesRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersDeleteInstancesRequest=instances,
            project='my-project',
            zone='central2-a')
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.instanceGroupManagers, 'DeleteInstances',
          delete_request)],
    )

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run('compute instance-groups managed delete-instances group-1 '
               '--zone central2-a --instances instance1')


class InstanceGroupManagersDeleteInstancesRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        test_resources.MakeInstancesInManagedInstanceGroup(
            self.messages, API_VERSION),
        [],
    ])
    self.template_1_uri = (
        '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
            self.compute_uri))
    self.list_instances_request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListManagedInstancesRequest(
            instanceGroupManager='group-1',
            region='central2',
            project='my-project'))

  def testWithTwoInstances(self):
    self.Run("""
        compute instance-groups managed delete-instances group-1
            --region central2
            --instances inst-1,inst-2
        """)

    instances = self.messages.RegionInstanceGroupManagersDeleteInstancesRequest(
        instances=[
            '{0}/projects/my-project/zones/central2-a/instances/inst-1'
            .format(self.compute_uri),
            '{0}/projects/my-project/zones/central2-a/instances/inst-2'
            .format(self.compute_uri)])
    delete_request = (
        self.messages.ComputeRegionInstanceGroupManagersDeleteInstancesRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersDeleteInstancesRequest=instances,
            project='my-project',
            region='central2')
    )
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'ListManagedInstances',
          self.list_instances_request)],
        [(self.compute.regionInstanceGroupManagers, 'DeleteInstances',
          delete_request)],
    )

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/regions/central2/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    instance_uri = ('{0}/projects/my-project/zones/central2-a/instances/'
                    'inst-1'.format(self.compute_uri))
    self.Run("""
        compute instance-groups managed delete-instances {0}
            --region central2
            --instances {1}
        """.format(igm_uri, instance_uri))

    instances = self.messages.RegionInstanceGroupManagersDeleteInstancesRequest(
        instances=['{0}/projects/my-project/zones/central2-a/instances/'
                   'inst-1'.format(self.compute_uri)])
    delete_request = (
        self.messages.ComputeRegionInstanceGroupManagersDeleteInstancesRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersDeleteInstancesRequest=instances,
            project='my-project',
            region='central2')
    )
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'ListManagedInstances',
          self.list_instances_request)],
        [(self.compute.regionInstanceGroupManagers, 'DeleteInstances',
          delete_request)],
    )

  def testScopePrompt(self):
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
        test_resources.MakeInstancesInManagedInstanceGroup(
            self.messages, API_VERSION),
        []
    ])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups managed delete-instances group-1
            --instances inst-1
        """)

    instances = self.messages.RegionInstanceGroupManagersDeleteInstancesRequest(
        instances=[
            '{0}/projects/my-project/zones/central2-a/instances/inst-1'
            .format(self.compute_uri)])
    delete_request = (
        self.messages.ComputeRegionInstanceGroupManagersDeleteInstancesRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersDeleteInstancesRequest=instances,
            project='my-project',
            region='central2')
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers, 'ListManagedInstances',
          self.list_instances_request)],
        [(self.compute.regionInstanceGroupManagers, 'DeleteInstances',
          delete_request)],
    )

  def testNotFoundRegionalResource(self):
    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      return []
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp('Could not fetch resource:'):
      self.Run("""
          compute instance-groups managed delete-instances group-1
              --instances inst-1
              --region us-central1
          """)


if __name__ == '__main__':
  test_case.main()
