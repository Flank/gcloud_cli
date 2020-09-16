# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the resource policies create instance-schedule command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib.surface.compute import resource_policies_base


class CreateGroupPlacementGaTest(resource_policies_base.TestBase,
                                 parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _CreateInstanceSchedulePolicy(self, name, vm_start_cron, vm_stop_cron,
                                    timezone):
    instance_schedule_policy = self.messages.ResourcePolicyInstanceSchedulePolicy(
        timeZone=timezone,
        vmStartSchedule=self.messages
        .ResourcePolicyInstanceSchedulePolicySchedule(schedule=vm_start_cron),
        vmStopSchedule=self.messages
        .ResourcePolicyInstanceSchedulePolicySchedule(schedule=vm_stop_cron))

    policy = self.messages.ResourcePolicy(
        name=name,
        region=self.region,
        instanceSchedulePolicy=instance_schedule_policy)
    return policy

  def _ExpectCreate(self, policy):
    request = self.messages.ComputeResourcePoliciesInsertRequest(
        project=self.Project(), region=self.region, resourcePolicy=policy)
    self.make_requests.side_effect = [[policy]]
    return request

  def testCreate_Simple(self):

    name = 'test-schedule'
    vm_start_cron = '30 5 * * *'
    vm_stop_cron = '30 10 * * *'
    timezone = 'EST'

    schedule_policy = self._CreateInstanceSchedulePolicy(
        name=name,
        vm_start_cron=vm_start_cron,
        vm_stop_cron=vm_stop_cron,
        timezone=timezone)

    request = self._ExpectCreate(schedule_policy)

    result = self.Run(
        'compute resource-policies create instance-schedule {name} '
        '--vm-start-schedule="{vm_start_cron}" --vm-stop-schedule="{vm_stop_cron}" '
        '--timezone={timezone} --region {region}'.format(
            name=name,
            vm_start_cron=vm_start_cron,
            vm_stop_cron=vm_stop_cron,
            timezone=timezone,
            region=self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, schedule_policy)
