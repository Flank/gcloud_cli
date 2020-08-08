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
"""Tests for the instance-groups managed stop-autoscaling subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instance_groups import test_resources

API_VERSION = 'v1'


class InstanceGroupManagersStopAutoscalingZonalTest(test_base.BaseTest):

  INSTANCE_GROUP_MANAGERS = test_resources.MakeInstanceGroupManagers(
      api=API_VERSION)
  AUTOSCALERS = test_resources.MakeAutoscalers(
      api=API_VERSION)

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.autoscalers_list_request = [
        (
            self.compute.autoscalers,
            'List', self.messages.ComputeAutoscalersListRequest(
                maxResults=500,
                project='my-project',
                zone='zone-1',
            ),
        ),
    ]
    self.managed_instance_group_get_request = [
        (
            self.compute.instanceGroupManagers,
            'Get', self.messages.ComputeInstanceGroupManagersGetRequest(
                instanceGroupManager='group-1',
                project='my-project',
                zone='zone-1',
            ),
        )
    ]

  def testStopAutoscalingNotAutoscaledManagedInstanceGroup(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],
        self.AUTOSCALERS[1:],
    ])

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        r'The managed instance group is not autoscaled\.'):
      self.Run('compute instance-groups managed stop-autoscaling group-1 '
               '--zone zone-1')
    self.CheckRequests(self.managed_instance_group_get_request,
                       self.autoscalers_list_request)

  def testStopAutoscalingAutoscaledManagedInstanceGroupWithPrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='region-1')],
        [self.messages.Zone(name='zone-1'), self.messages.Zone(name='zone-2')],
        [self.INSTANCE_GROUP_MANAGERS[0]],
        self.AUTOSCALERS,
        []  # Delete Autoscaler.
    ])

    self.Run('compute instance-groups managed stop-autoscaling group-1')
    delete_request = self.messages.ComputeAutoscalersDeleteRequest(
        project='my-project',
        zone='zone-1',
        autoscaler='autoscaler-1'
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.autoscalers, 'Delete', delete_request)],
    )

  def testAssertsIgmExists(self):
    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      yield
    self.make_requests.side_effect = MakeRequests

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        'Could not fetch resource:'):
      self.Run('compute instance-groups managed stop-autoscaling group-1 '
               '--zone zone-1')

    self.CheckRequests(self.managed_instance_group_get_request)


class InstanceGroupManagersStopAutoscalingRegionalTest(test_base.BaseTest):

  INSTANCE_GROUP_MANAGERS = test_resources.MakeInstanceGroupManagers(
      api=API_VERSION, scope_name='region-1', scope_type='region')
  AUTOSCALERS = test_resources.MakeAutoscalers(
      api=API_VERSION, scope_name='region-1', scope_type='region')

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.autoscalers_list_request = [
        (
            self.compute.regionAutoscalers,
            'List', self.messages.ComputeRegionAutoscalersListRequest(
                maxResults=500,
                project='my-project',
                region='region-1',
            ),
        ),
    ]
    self.managed_instance_group_get_request = [
        (
            self.compute.regionInstanceGroupManagers,
            'Get', self.messages.ComputeRegionInstanceGroupManagersGetRequest(
                instanceGroupManager='group-1',
                project='my-project',
                region='region-1',
            ),
        )
    ]

  def testStopAutoscalingNotAutoscaledManagedInstanceGroup(self):
    self.make_requests.side_effect = iter([
        [self.INSTANCE_GROUP_MANAGERS[0]],
        self.AUTOSCALERS[1:],
    ])

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        r'The managed instance group is not autoscaled\.'):
      self.Run("""
          compute instance-groups managed stop-autoscaling group-1
              --region region-1
          """)
    self.CheckRequests(self.managed_instance_group_get_request,
                       self.autoscalers_list_request)

  def testStopAutoscalingAutoscaledManagedInstanceGroupWithPrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='region-1')],
        [self.messages.Zone(name='zone-1'), self.messages.Zone(name='zone-2')],
        [self.INSTANCE_GROUP_MANAGERS[0]],
        self.AUTOSCALERS,
        []  # Delete Autoscaler.
    ])

    self.Run('compute instance-groups managed stop-autoscaling group-1')
    delete_request = self.messages.ComputeRegionAutoscalersDeleteRequest(
        project='my-project',
        region='region-1',
        autoscaler='autoscaler-1'
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        self.managed_instance_group_get_request,
        self.autoscalers_list_request,
        [(self.compute.regionAutoscalers, 'Delete', delete_request)],
    )

  def testAssertsIgmExists(self):
    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      yield
    self.make_requests.side_effect = MakeRequests

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        'Could not fetch resource:'):
      self.Run('compute instance-groups managed stop-autoscaling group-1 '
               '--region region-1')

    self.CheckRequests(self.managed_instance_group_get_request)


if __name__ == '__main__':
  test_case.main()
