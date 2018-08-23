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
"""Tests for the instance-groups managed delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'v1'


class InstanceGroupManagersDeleteZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [],  # Listed 0 Autoscalers.
        test_resources.MakeInstanceGroupManagers(API_VERSION),
        [],
    ])
    self.autoscalers_list_request_zone_1 = [(
        self.compute.autoscalers, 'List',
        self.messages.ComputeAutoscalersListRequest(
            maxResults=500,
            project='my-project',
            zone='zone-1',
        ),
    )]
    self.autoscalers_list_request_zone_2 = [(
        self.compute.autoscalers, 'List',
        self.messages.ComputeAutoscalersListRequest(
            maxResults=500,
            project='my-project',
            zone='zone-2',
        ),
    )]

  def testBasicDelete(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run('compute instance-groups managed delete group-1 --zone zone-1')

    self.CheckRequests(
        self.autoscalers_list_request_zone_1,
        [(self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              zone='zone-1')
         )],
    )

  def testPromptingWithYes(self):
    self.make_requests.side_effect = iter([
        test_resources.MakeAutoscalers(API_VERSION),
        test_resources.MakeInstanceGroupManagers(API_VERSION),
        [],
    ])
    self.WriteInput('y')
    self.Run("""
        compute instance-groups managed delete group-1 group-2 group-3
          --zone zone-1
        """)
    self.CheckRequests(
        self.autoscalers_list_request_zone_1,
        [(self.compute.autoscalers,
          'Delete',
          self.messages.ComputeAutoscalersDeleteRequest(
              autoscaler='autoscaler-1',
              project='my-project',
              zone='zone-1')),
         (self.compute.autoscalers,
          'Delete',
          self.messages.ComputeAutoscalersDeleteRequest(
              autoscaler='autoscaler-2',
              project='my-project',
              zone='zone-1')),
         (self.compute.autoscalers,
          'Delete',
          self.messages.ComputeAutoscalersDeleteRequest(
              autoscaler='autoscaler-3',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              zone='zone-1')),
         (self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-2',
              project='my-project',
              zone='zone-1')),
         (self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-3',
              project='my-project',
              zone='zone-1'))],)
    self.AssertErrContains(
        r'The following instance group managers will be deleted:\n'
        r' - [group-1] in [zone-1]\n'
        r' - [group-2] in [zone-1]\n'
        r' - [group-3] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.WriteInput('n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute instance-groups managed delete group-1
            --zone zone-1
          """)

    self.CheckRequests()

  def testScopePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='region-1')],
        [self.messages.Zone(name='zone-2'),
         self.messages.Zone(name='zone-1')],
        test_resources.MakeAutoscalers(API_VERSION),
        test_resources.MakeInstanceGroupManagers(API_VERSION),
        [],  # Deleting 0 Autoscalers.
    ])
    self.WriteInput('2\ny')
    self.Run("""
        compute instance-groups managed delete group-1 group-2
        """)

    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        self.autoscalers_list_request_zone_1,
        [(self.compute.autoscalers,
          'Delete',
          self.messages.ComputeAutoscalersDeleteRequest(
              autoscaler='autoscaler-1',
              project='my-project',
              zone='zone-1')),
         (self.compute.autoscalers,
          'Delete',
          self.messages.ComputeAutoscalersDeleteRequest(
              autoscaler='autoscaler-2',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              zone='zone-1')
         ),
         (self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-2',
              project='my-project',
              zone='zone-1')
         )],
    )

  def testMultipleZonesUri(self):
    self.make_requests.side_effect = iter([
        [],  # No Autoscalers in zone-1 and zone-2
        test_resources.MakeInstanceGroupManagers(API_VERSION),
    ])
    self.WriteInput('y')
    self.Run("""
        compute instance-groups managed delete
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-2/instanceGroupManagers/group-1
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroupManagers/group-2
        """.format(API_VERSION))

    self.CheckRequests(
        self.autoscalers_list_request_zone_1
        + self.autoscalers_list_request_zone_2,
        [(self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              zone='zone-2')
         ),
         (self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-2',
              project='my-project',
              zone='zone-1')
         )],
    )
    self.AssertErrContains(
        r'The following instance group managers will be deleted:\n'
        r' - [group-1] in [zone-2]\n'
        r' - [group-2] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testMultipleZonesUriAndFlag(self):
    self.make_requests.side_effect = iter([
        [],  # No Autoscalers in zone-1 and zone-2
        test_resources.MakeInstanceGroupManagers(API_VERSION),
    ])
    self.WriteInput('y')
    self.Run("""
        compute instance-groups managed delete
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-2/instanceGroupManagers/group-1
          group-2
          --zone zone-1
        """.format(API_VERSION))

    self.CheckRequests(
        self.autoscalers_list_request_zone_1
        + self.autoscalers_list_request_zone_2,
        [(self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              zone='zone-2')
         ),
         (self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-2',
              project='my-project',
              zone='zone-1')
         )],
    )
    self.AssertErrContains(
        r'The following instance group managers will be deleted:\n'
        r' - [group-1] in [zone-2]\n'
        r' - [group-2] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')


class InstanceGroupManagersDeleteRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [],  # Listed 0 Autoscalers.
        test_resources.MakeInstanceGroupManagers(
            API_VERSION, scope_type='region', scope_name='region-1'),
        [],
    ])
    self.autoscalers_list_request_zone_1 = [(
        self.compute.autoscalers, 'List',
        self.messages.ComputeAutoscalersListRequest(
            maxResults=500,
            project='my-project',
            zone='zone-1',
        ),
    )]
    self.autoscalers_list_request_region_1 = [(
        self.compute.regionAutoscalers, 'List',
        self.messages.ComputeRegionAutoscalersListRequest(
            maxResults=500,
            project='my-project',
            region='region-1',
        ),
    )]
    self.autoscalers_list_request_region_2 = [(
        self.compute.regionAutoscalers, 'List',
        self.messages.ComputeRegionAutoscalersListRequest(
            maxResults=500,
            project='my-project',
            region='region-2',
        ),
    )]

  def testBasicDelete(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute instance-groups managed delete group-1 --region region-1
        """)

    self.CheckRequests(
        self.autoscalers_list_request_region_1,
        [(self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              region='region-1')
         )],
    )

  def testPromptingWithYes(self):
    self.make_requests.side_effect = iter([
        test_resources.MakeAutoscalers(
            API_VERSION, scope_type='region', scope_name='region-1'),
        test_resources.MakeInstanceGroupManagers(
            API_VERSION, scope_type='region', scope_name='region-1'),
        [],
    ])
    self.WriteInput('y')
    self.Run("""
        compute instance-groups managed delete group-1 group-2 group-3
          --region region-1
        """)
    self.CheckRequests(
        self.autoscalers_list_request_region_1,
        [(self.compute.regionAutoscalers,
          'Delete',
          self.messages.ComputeRegionAutoscalersDeleteRequest(
              autoscaler='autoscaler-1',
              project='my-project',
              region='region-1')),
         (self.compute.regionAutoscalers,
          'Delete',
          self.messages.ComputeRegionAutoscalersDeleteRequest(
              autoscaler='autoscaler-2',
              project='my-project',
              region='region-1')),
         (self.compute.regionAutoscalers,
          'Delete',
          self.messages.ComputeRegionAutoscalersDeleteRequest(
              autoscaler='autoscaler-3',
              project='my-project',
              region='region-1'))],
        [(self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              region='region-1')),
         (self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-2',
              project='my-project',
              region='region-1')),
         (self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-3',
              project='my-project',
              region='region-1'))],)
    self.AssertErrContains(
        r'The following region instance group managers will be deleted:\n'
        r' - [group-1] in [region-1]\n'
        r' - [group-2] in [region-1]\n'
        r' - [group-3] in [region-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.WriteInput('n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute instance-groups managed delete group-1
            --region region-1
          """)

    self.CheckRequests()

  def testScopePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='region-1')],
        [self.messages.Zone(name='zone-2'),
         self.messages.Zone(name='zone-1')],
        test_resources.MakeAutoscalers(
            API_VERSION, scope_type='region', scope_name='region-1'),
        test_resources.MakeInstanceGroupManagers(
            API_VERSION, scope_type='region', scope_name='region-1'),
        [],  # Deleting 0 Autoscalers.
    ])
    self.WriteInput('1\ny')
    self.Run("""
        compute instance-groups managed delete group-1
        """)

    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        self.autoscalers_list_request_region_1,
        [(self.compute.regionAutoscalers,
          'Delete',
          self.messages.ComputeRegionAutoscalersDeleteRequest(
              autoscaler='autoscaler-1',
              project='my-project',
              region='region-1'))],
        [(self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              region='region-1')
         )],
    )

  def testScopePromptingWithDefaultZone(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    properties.VALUES.compute.zone.Set('zone-1')
    self.make_requests.side_effect = iter([
        test_resources.MakeAutoscalers(
            API_VERSION, scope_type='zone', scope_name='zone-1'),
        [self.messages.Region(name='region-1')],
        [self.messages.Zone(name='zone-2'),
         self.messages.Zone(name='zone-1')],
        test_resources.MakeInstanceGroupManagers(
            API_VERSION, scope_type='region', scope_name='region-1'),
        [],  # Deleting 0 Autoscalers.
    ])
    self.WriteInput('1\ny')
    self.Run("""
        compute instance-groups managed delete group-1
        """)

    self.CheckRequests(
        self.autoscalers_list_request_zone_1,
        [(self.compute.autoscalers,
          'Delete',
          self.messages.ComputeAutoscalersDeleteRequest(
              autoscaler='autoscaler-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.instanceGroupManagers,
          'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              zone='zone-1')
         )],
    )

  def testMultipleZonesUri(self):
    self.make_requests.side_effect = iter([
        [],  # No Autoscalers in any region
        test_resources.MakeInstanceGroupManagers(
            API_VERSION, scope_type='region', scope_name='region-1'),
    ])
    self.WriteInput('y')
    self.Run("""
        compute instance-groups managed delete
          https://www.googleapis.com/compute/{0}/projects/my-project/regions/region-2/instanceGroupManagers/group-1
          https://www.googleapis.com/compute/{0}/projects/my-project/regions/region-1/instanceGroupManagers/group-2
        """.format(API_VERSION))

    self.CheckRequests(
        self.autoscalers_list_request_region_1
        + self.autoscalers_list_request_region_2,
        [(self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              region='region-2')
         ),
         (self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-2',
              project='my-project',
              region='region-1')
         )],
    )
    self.AssertErrContains(
        r'The following region instance group managers will be deleted:\n'
        r' - [group-1] in [region-2]\n'
        r' - [group-2] in [region-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testMultipleZonesUriAndFlag(self):
    self.make_requests.side_effect = iter([
        [],  # No Autoscalers in any region
        test_resources.MakeInstanceGroupManagers(
            API_VERSION, scope_type='region', scope_name='region-1'),
    ])
    self.WriteInput('y')
    self.Run("""
        compute instance-groups managed delete
          https://www.googleapis.com/compute/{0}/projects/my-project/regions/region-2/instanceGroupManagers/group-1
          group-2
          --region region-1
        """.format(API_VERSION))

    self.CheckRequests(
        self.autoscalers_list_request_region_1
        + self.autoscalers_list_request_region_2,
        [(self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              region='region-2')
         ),
         (self.compute.regionInstanceGroupManagers,
          'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-2',
              project='my-project',
              region='region-1')
         )],
    )
    self.AssertErrContains(
        r'The following region instance group managers will be deleted:\n'
        r' - [group-1] in [region-2]\n'
        r' - [group-2] in [region-1]')
    self.AssertErrContains('PROMPT_CONTINUE')


class InstanceGroupManagersDeleteBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.autoscalers_list_request_zone_1 = [(
        self.compute.autoscalers,
        'List',
        self.messages.ComputeAutoscalersListRequest(
            maxResults=500,
            project='my-project',
            zone='zone-1',),)]
    self.autoscalers_list_request_region_1 = [(
        self.compute.regionAutoscalers,
        'List',
        self.messages.ComputeRegionAutoscalersListRequest(
            maxResults=500,
            project='my-project',
            region='region-1',),)]

  def testZoneAndRegion(self):
    self.make_requests.side_effect = iter([
        test_resources.MakeAutoscalers(
            'beta', scope_type='zone', scope_name='zone-1'),
        test_resources.MakeAutoscalers(
            'beta', scope_type='region', scope_name='region-1'),
        test_resources.MakeInstanceGroupManagers(
            'beta', scope_type='zone', scope_name='zone-1'),
        test_resources.MakeInstanceGroupManagers(
            'beta', scope_type='region', scope_name='region-1'),
        [],  # Deleting 0 Autoscalers.
    ])
    self.WriteInput('y')
    self.Run("""
        beta compute instance-groups managed delete
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroupManagers/group-1
          https://www.googleapis.com/compute/{0}/projects/my-project/regions/region-1/instanceGroupManagers/group-2
        """.format(API_VERSION))

    self.AssertErrContains(
        r'The following instance group managers will be deleted:\n'
        r' - [group-1]\n'
        r' - [group-2] in [region-1]')
    self.AssertErrContains('PROMPT_CONTINUE')
    self.CheckRequests(
        self.autoscalers_list_request_zone_1 +
        self.autoscalers_list_request_region_1,
        [(self.compute.autoscalers, 'Delete',
          self.messages.ComputeAutoscalersDeleteRequest(
              autoscaler='autoscaler-1', project='my-project', zone='zone-1'))],
        [(self.compute.instanceGroupManagers, 'Delete',
          self.messages.ComputeInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-1',
              project='my-project',
              zone='zone-1')),
         (self.compute.regionInstanceGroupManagers, 'Delete',
          self.messages.ComputeRegionInstanceGroupManagersDeleteRequest(
              instanceGroupManager='group-2',
              project='my-project',
              region='region-1'))],)

if __name__ == '__main__':
  test_case.main()
