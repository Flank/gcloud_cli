# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for the instance-groups managed update-autoscaling subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
import random

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import scope as scope_util
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


@parameterized.parameters(list(itertools.product(
    [calliope_base.ReleaseTrack.ALPHA],
    [scope_util.ScopeEnum.REGION, scope_util.ScopeEnum.ZONE])))
class InstanceGroupManagersSetAutoscalingZonalTest(test_base.BaseTest,
                                                   parameterized.TestCase):

  def _SetUpForTrack(self, track):
    self.track = track
    if track is calliope_base.ReleaseTrack.ALPHA:
      self.SelectApi('alpha')
    else:
      raise ValueError('Unrecognized API version.')

  def _SetUpForScope(self, scope):
    self.scope = scope
    if scope is scope_util.ScopeEnum.REGION:
      self.location = 'us-central1'
      self.location_flag = '--region'
      self.scope_string = 'region'
    elif scope is scope_util.ScopeEnum.ZONE:
      self.location = 'us-central1-a'
      self.location_flag = '--zone'
      self.scope_string = 'zone'
    else:
      raise ValueError('Unrecognized scope.')

  def _ExpectRequest(self, request, response):
    self.expected_requests.append(request)
    self.expected_responses.append(response)

  def _MakeGetManagedInstanceGroupRegionRequest(self):
    get_request = self.messages.ComputeRegionInstanceGroupManagersGetRequest(
        instanceGroupManager='group-1',
        region=self.location,
        project='my-project')
    return [(self.compute.regionInstanceGroupManagers, 'Get', get_request)]

  def _MakeGetManagedInstanceGroupZoneRequest(self):
    get_request = self.messages.ComputeInstanceGroupManagersGetRequest(
        instanceGroupManager='group-1',
        zone=self.location,
        project='my-project')
    return [(self.compute.instanceGroupManagers, 'Get', get_request)]

  def _ExpectGetManagedInstanceGroup(self):
    if self.scope is scope_util.ScopeEnum.REGION:
      request = self._MakeGetManagedInstanceGroupRegionRequest()
    if self.scope is scope_util.ScopeEnum.ZONE:
      request = self._MakeGetManagedInstanceGroupZoneRequest()
    instance_group_managers = test_resources.MakeInstanceGroupManagers(self.api)
    self._ExpectRequest(request, instance_group_managers[:1])

  def _MakeListAutoscalersZoneRequest(self):
    return [(self.compute.autoscalers,
             'List', self.messages.ComputeAutoscalersListRequest(
                 maxResults=500,
                 project='my-project',
                 zone=self.location))]

  def _MakeListAutoscalersRegionRequest(self):
    return [(self.compute.regionAutoscalers,
             'List', self.messages.ComputeRegionAutoscalersListRequest(
                 maxResults=500,
                 project='my-project',
                 region=self.location))]

  def _ExpectListAutoscalers(self, group_name=None):
    autoscalers = test_resources.MakeAutoscalers(
        self.api, scope_name=self.location, scope_type=self.scope_string)
    if self.scope is scope_util.ScopeEnum.REGION:
      request = self._MakeListAutoscalersRegionRequest()
    if self.scope is scope_util.ScopeEnum.ZONE:
      request = self._MakeListAutoscalersZoneRequest()
    autoscaler = autoscalers[0]
    if group_name:
      autoscaler.target = autoscaler.target.replace('group-1', group_name)
    self._ExpectRequest(request, [autoscaler])

  def _MakePatchAutoscalersZoneRequest(self, autoscaler):
    return [(self.compute.autoscalers,
             'Patch', self.messages.ComputeAutoscalersPatchRequest(
                 project='my-project',
                 zone=self.location,
                 autoscaler='autoscaler-1',
                 autoscalerResource=autoscaler))]

  def _MakePatchAutoscalersRegionRequest(self, autoscaler):
    return [(self.compute.regionAutoscalers,
             'Patch', self.messages.ComputeRegionAutoscalersPatchRequest(
                 project='my-project',
                 region=self.location,
                 autoscaler='autoscaler-1',
                 autoscalerResource=autoscaler))]

  def _ExpectPatchAutoscalers(self, autoscaler):
    if self.scope is scope_util.ScopeEnum.REGION:
      request = self._MakePatchAutoscalersRegionRequest(autoscaler)
    if self.scope is scope_util.ScopeEnum.ZONE:
      request = self._MakePatchAutoscalersZoneRequest(autoscaler)
    self._ExpectRequest(request, [])

  def SetUp(self):
    self.expected_requests = []
    self.expected_responses = []

    self.StartObjectPatch(random, 'choice').return_value = 'a'

  def testNoInstanceGroupFound(self, track, scope):
    self._SetUpForTrack(track)
    self._SetUpForScope(scope)
    self._ExpectGetManagedInstanceGroup()
    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      yield
    self.make_requests.side_effect = MakeRequests

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        'Could not fetch resource:'):
      self.Run('compute instance-groups managed update-autoscaling group-1 '
               '{} {}'.format(self.location_flag, self.location))

    self.CheckRequests(*self.expected_requests)

  def testNoMatchingAutoscaler(self, track, scope):
    self._SetUpForTrack(track)
    self._SetUpForScope(scope)
    self._ExpectGetManagedInstanceGroup()
    self._ExpectListAutoscalers(group_name='group-2')
    self.make_requests.side_effect = iter(self.expected_responses)

    with self.AssertRaisesExceptionMatches(
        exceptions.Error, '[group-1] has no existing autoscaler'):
      self.Run('compute instance-groups managed update-autoscaling group-1 '
               '{} {}'.format(self.location_flag, self.location))

    self.CheckRequests(*self.expected_requests)

  def testNoOp(self, track, scope):
    self._SetUpForTrack(track)
    self._SetUpForScope(scope)
    self._ExpectGetManagedInstanceGroup()
    self._ExpectListAutoscalers()
    self._ExpectPatchAutoscalers(self.messages.Autoscaler(
        name='autoscaler-1',
        autoscalingPolicy=self.messages.AutoscalingPolicy()
    ))
    self.make_requests.side_effect = iter(self.expected_responses)

    self.Run('compute instance-groups managed update-autoscaling group-1 '
             '{} {}'.format(self.location_flag, self.location))

    self.CheckRequests(*self.expected_requests)

  def testUpdateMode(self, track, scope):
    self._SetUpForTrack(track)
    self._SetUpForScope(scope)
    self._ExpectGetManagedInstanceGroup()
    self._ExpectListAutoscalers()
    self._ExpectPatchAutoscalers(self.messages.Autoscaler(
        name='autoscaler-1',
        autoscalingPolicy=self.messages.AutoscalingPolicy(
            mode=self.messages.AutoscalingPolicy.ModeValueValuesEnum.ONLY_UP
        )
    ))
    self.make_requests.side_effect = iter(self.expected_responses)

    self.Run('compute instance-groups managed update-autoscaling group-1 '
             '--mode only-up '
             '{} {}'.format(self.location_flag, self.location))

    self.CheckRequests(*self.expected_requests)

if __name__ == '__main__':
  test_case.main()
