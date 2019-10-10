# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for instance-groups managed rolling-action stop-proactive-update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
from mock import patch


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  test_obj.PROJECT_NAME = 'my-project'
  test_obj.REGION = 'central2'
  test_obj.ZONE = 'central2-a'
  test_obj.IGM_NAME_A = 'group-1'
  test_obj.IGM_NAME_B = 'group-2'
  test_obj.IGM_NAME_C = 'group-3'

  test_obj.FixedOrPercent = test_obj.messages.FixedOrPercent

  test_obj.default_update_policy = (
      test_obj.messages.InstanceGroupManagerUpdatePolicy(
          type=(test_obj.messages.InstanceGroupManagerUpdatePolicy
                .TypeValueValuesEnum.OPPORTUNISTIC)))


class InstanceGroupManagersRollingActionStopProactiveUpdateZonalTest(
    test_base.BaseTest):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    SetUp(self, self.api_version)
    self.igms = test_resources.MakeInstanceGroupManagersWithVersions(
        self.api_version, self.ZONE)

  def generateUpdateRequestStub(self, igm_name):
    return self.messages.ComputeInstanceGroupManagersPatchRequest(
        project=self.PROJECT_NAME,
        zone=self.ZONE,
        instanceGroupManager=igm_name,
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            updatePolicy=self.default_update_policy,)))

  def checkStopUpdateRequest(self, expected_update_request):
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch',
                         expected_update_request)])

  def testStopOneVersion(self):
    self.make_requests.side_effect = [[self.igms[0]], []]
    self.Run(
        'compute instance-groups managed rolling-action stop-proactive-update '
        '{0} --zone {1}'.format(self.IGM_NAME_A, self.ZONE))

    self.checkStopUpdateRequest(self.generateUpdateRequestStub(self.IGM_NAME_A))

  def testStopTwoVersionsStop(self):
    self.make_requests.side_effect = [[self.igms[1]], []]
    self.Run(
        'compute instance-groups managed rolling-action stop-proactive-update '
        '{0} --zone {1}'.format(self.IGM_NAME_B, self.ZONE))

    self.checkStopUpdateRequest(self.generateUpdateRequestStub(self.IGM_NAME_B))

  def testStopInstanceTemplate(self):
    self.make_requests.side_effect = [[self.igms[2]], []]
    self.Run(
        'compute instance-groups managed rolling-action stop-proactive-update '
        '{0} --zone {1}'.format(self.IGM_NAME_C, self.ZONE))

    self.checkStopUpdateRequest(self.generateUpdateRequestStub(self.IGM_NAME_C))

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run('compute instance-groups managed rolling-action '
               'stop-proactive-update {0} --zone {1}'.format(
                   self.IGM_NAME_C, self.ZONE))


class InstanceGroupManagersRollingActionStopProactiveUpdateRegionalTest(
    test_base.BaseTest):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    SetUp(self, self.api_version)
    self.igms = test_resources.MakeInstanceGroupManagersWithVersions(
        self.api_version, self.ZONE)

  def generateUpdateRequestStub(self, igm_name):
    return self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
        project=self.PROJECT_NAME,
        region=self.REGION,
        instanceGroupManager=igm_name,
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            updatePolicy=self.default_update_policy,)))

  def checkStopUpdateRequest(self, expected_update_request):
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Patch',
                         expected_update_request)])

  def testStopOneVersion(self):
    self.make_requests.side_effect = [[self.igms[0]], []]
    self.Run(
        'compute instance-groups managed rolling-action stop-proactive-update '
        '{0} --region {1}'.format(self.IGM_NAME_A, self.REGION))

    self.checkStopUpdateRequest(self.generateUpdateRequestStub(self.IGM_NAME_A))

  def testStopTwoVersionsStop(self):
    self.make_requests.side_effect = [[self.igms[1]], []]
    self.Run(
        'compute instance-groups managed rolling-action stop-proactive-update '
        '{0} --region {1}'.format(self.IGM_NAME_B, self.REGION))

    self.checkStopUpdateRequest(self.generateUpdateRequestStub(self.IGM_NAME_B))

  def testStopInstanceTemplate(self):
    self.make_requests.side_effect = [[self.igms[2]], []]
    self.Run(
        'compute instance-groups managed rolling-action stop-proactive-update '
        '{0} --region {1}'.format(self.IGM_NAME_C, self.REGION))

    self.checkStopUpdateRequest(self.generateUpdateRequestStub(self.IGM_NAME_C))


class InstanceGroupManagersRollingActionStopProactiveUpdateBetaZonalTest(
    InstanceGroupManagersRollingActionStopProactiveUpdateZonalTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupManagersRollingActionStopProactiveUpdateBetaRegionalTest(
    InstanceGroupManagersRollingActionStopProactiveUpdateRegionalTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupManagersRollingActionStopProactiveUpdateAlphaZonalTest(
    InstanceGroupManagersRollingActionStopProactiveUpdateBetaZonalTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


class InstanceGroupManagersRollingActionStopProactiveUpdateAlphaRegionalTest(
    InstanceGroupManagersRollingActionStopProactiveUpdateBetaRegionalTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
