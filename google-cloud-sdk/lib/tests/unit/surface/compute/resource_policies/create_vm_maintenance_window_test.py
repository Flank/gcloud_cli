# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the resource policies create-vm-maintenance command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import resource_policies_base


class CreateVmMaintenanceAlphaTest(resource_policies_base.TestBase,
                                   parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.day_enum = (
        self.messages.ResourcePolicyWeeklyCycleDayOfWeek.DayValueValuesEnum)

  def _ExpectCreate(self, policy):
    request = self.messages.ComputeResourcePoliciesInsertRequest(
        project=self.Project(),
        region=self.region,
        resourcePolicy=policy)
    self.make_requests.side_effect = [[policy]]
    return request

  def testCreate_Simple(self):
    window = self.messages.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
        dailyMaintenanceWindow=self.messages.ResourcePolicyDailyCycle(
            daysInCycle=1,
            startTime='04:00'))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        vmMaintenancePolicy=self.messages.ResourcePolicyVmMaintenancePolicy(
            maintenanceWindow=window))

    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create vm-maintenance maintenance-window '
        'pol1 --start-time 04:00 --region {} --daily-window '
        .format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_Description(self):
    description = 'This is a maintenance policy.'
    window = self.messages.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
        dailyMaintenanceWindow=self.messages.ResourcePolicyDailyCycle(
            daysInCycle=1,
            startTime='04:00'))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        description=description,
        vmMaintenancePolicy=self.messages.ResourcePolicyVmMaintenancePolicy(
            maintenanceWindow=window))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create vm-maintenance maintenance-window '
        'pol1 --start-time 04:00 --region {} --description "{}" '
        '--daily-window '.format(self.region, description))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_StartTime(self):
    window = self.messages.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
        dailyMaintenanceWindow=self.messages.ResourcePolicyDailyCycle(
            daysInCycle=1,
            startTime='04:00'))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        vmMaintenancePolicy=self.messages.ResourcePolicyVmMaintenancePolicy(
            maintenanceWindow=window))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create vm-maintenance maintenance-window '
        'pol1 --start-time 03:00.52-1:00 --region {} --daily-window '
        .format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_NoDailyCycleShouldFail(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'cannot request a non-daily cycle.'):
      self.Run(
          'compute resource-policies create vm-maintenance maintenance-window '
          'pol1 --region {0} --no-daily-window  --start-time 04:00'
          .format(self.region))

  def testCreate_StartTimeIsRequired(self):
    with self.AssertRaisesArgumentError():
      self.Run(
          'compute resource-policies create vm-maintenance maintenance-window '
          'pol1 --region {0} --daily-window'.format(self.region))


if __name__ == '__main__':
  test_case.main()
