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
"""Tests for the instance-groups managed abandon-instances subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instance_groups import test_resources
from mock import patch

API_VERSION = 'v1'


class InstanceGroupManagersAbandonInstancesZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [],
    ])

  def testWithTwoInstances(self):
    result = list(self.Run(
        'compute instance-groups managed abandon-instances group-1 '
        '--zone central2-a --instances instance1,instance2 --format=disable'
    ))

    instance1_self_link = ('{0}/projects/my-project/zones/central2-a/instances/'
                           'instance1'.format(self.compute_uri))
    instance2_self_link = ('{0}/projects/my-project/zones/central2-a/instances/'
                           'instance2'.format(self.compute_uri))

    request = self.messages.InstanceGroupManagersAbandonInstancesRequest(
        instances=[instance1_self_link, instance2_self_link])
    abandon_request = (
        self.messages.ComputeInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersAbandonInstancesRequest=request,
            project='my-project',
            zone='central2-a'))
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'AbandonInstances',
          abandon_request)],)

    self.assertEqual(len(result), 2)
    self.assertEqual(result[0]['selfLink'], instance1_self_link)
    self.assertEqual(result[0]['status'], 'SUCCESS')
    self.assertEqual(result[1]['selfLink'], instance2_self_link)
    self.assertEqual(result[1]['status'], 'SUCCESS')

  def testWithUri(self):
    self.Run('compute instance-groups managed abandon-instances group-1 '
             '--zone central2-a --instances {0}/projects/my-project/zones/'
             'central2-a/instances/instance1'.format(self.compute_uri))

    request = self.messages.InstanceGroupManagersAbandonInstancesRequest(
        instances=[
            self.compute_uri + ('/projects/my-project/zones/central2-a/'
                                'instances/instance1')
        ])
    abandon_request = (
        self.messages.ComputeInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersAbandonInstancesRequest=request,
            project='my-project',
            zone='central2-a'))
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'AbandonInstances',
          abandon_request)],)

  def testScopePrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter([[
        self.messages.Region(name='central1'),
        self.messages.Region(name='central2'),
    ], [
        self.messages.Zone(name='central1-a'),
        self.messages.Zone(name='central1-b'),
        self.messages.Zone(name='central2-a'),
    ], []])
    self.WriteInput('5\n')
    self.Run('compute instance-groups managed abandon-instances group-1 '
             '--instances instance1')
    request = self.messages.InstanceGroupManagersAbandonInstancesRequest(
        instances=[
            self.compute_uri + ('/projects/my-project/zones/central2-a/'
                                'instances/instance1')
        ])
    abandon_request = (
        self.messages.ComputeInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='group-1',
            instanceGroupManagersAbandonInstancesRequest=request,
            project='my-project',
            zone='central2-a'))
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.instanceGroupManagers, 'AbandonInstances',
          abandon_request)],)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run('compute instance-groups managed abandon-instances group-1 '
               '--zone central2-a --instances instance1')


class InstanceGroupManagersAbandonInstancesRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        test_resources.MakeInstancesInManagedInstanceGroup(
            self.messages, API_VERSION),
        [],
    ])
    self.list_instances_request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListManagedInstancesRequest(
            instanceGroupManager='group-1',
            region='central2',
            project='my-project'))

  def testWithTwoInstances(self):
    self.Run("""
        compute instance-groups managed abandon-instances group-1
            --region central2
            --instances inst-1,inst-2
        """)

    request = self.messages.RegionInstanceGroupManagersAbandonInstancesRequest(
        instances=[
            self.compute_uri + ('/projects/my-project/zones/central2-a/'
                                'instances/inst-1'),
            self.compute_uri + ('/projects/my-project/zones/central2-a/'
                                'instances/inst-2'),
        ])
    abandon_request = (
        self.messages.ComputeRegionInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersAbandonInstancesRequest=request,
            project='my-project',
            region='central2'))
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'ListManagedInstances',
          self.list_instances_request)],
        [(self.compute.regionInstanceGroupManagers, 'AbandonInstances',
          abandon_request)],)

  def testWithUri(self):
    self.Run("""
        compute instance-groups managed abandon-instances group-1
            --region central2
            --instances
                {0}/projects/my-project/zones/central2-a/instances/inst-1
        """.format(self.compute_uri))

    request = self.messages.RegionInstanceGroupManagersAbandonInstancesRequest(
        instances=[
            self.compute_uri + ('/projects/my-project/zones/central2-a/'
                                'instances/inst-1')
        ])
    abandon_request = (
        self.messages.ComputeRegionInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersAbandonInstancesRequest=request,
            project='my-project',
            region='central2'))
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'ListManagedInstances',
          self.list_instances_request)],
        [(self.compute.regionInstanceGroupManagers, 'AbandonInstances',
          abandon_request)],)

  def testScopePrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='central1'),
            self.messages.Region(name='central2'),
        ], [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        test_resources.MakeInstancesInManagedInstanceGroup(
            self.messages, API_VERSION)
        , []
    ])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups managed abandon-instances group-1
             --instances inst-1
         """)
    request = self.messages.RegionInstanceGroupManagersAbandonInstancesRequest(
        instances=[
            self.compute_uri + ('/projects/my-project/zones/central2-a/'
                                'instances/inst-1')
        ])
    abandon_request = (
        self.messages.ComputeRegionInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersAbandonInstancesRequest=request,
            project='my-project',
            region='central2'))
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers, 'ListManagedInstances',
          self.list_instances_request)],
        [(self.compute.regionInstanceGroupManagers, 'AbandonInstances',
          abandon_request)],)

  def testNotFoundRegionalResource(self):

    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      return []

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp('Could not fetch resource:'):
      self.Run("""
          compute instance-groups managed abandon-instances group-1
              --instances inst-1
              --region us-central1
          """)


if __name__ == '__main__':
  test_case.main()
