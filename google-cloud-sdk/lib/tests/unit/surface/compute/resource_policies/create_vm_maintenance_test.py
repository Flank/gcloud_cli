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
"""Tests for the resource policies create-vm-maintenance command."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import resource_policies_base


class CreateVmMaintenanceTest(resource_policies_base.TestBase,
                              parameterized.TestCase):

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
        'compute resource-policies create-vm-maintenance pol1 '
        '--start-time 04:00Z --region {} --daily-window '
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
        'compute resource-policies create-vm-maintenance pol1 '
        '--start-time 04:00Z --region {} --description "{}" --daily-window '
        .format(self.region, description))

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
        'compute resource-policies create-vm-maintenance pol1'
        ' --start-time 03:00.52-1:00 --region {} --daily-window '
        .format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_WeeklyWindow(self):
    window = self.messages.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
        weeklyMaintenanceWindow=self.messages.ResourcePolicyWeeklyCycle(
            dayOfWeeks=[
                self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                    day=self.day_enum.MONDAY,
                    startTime='04:00')]))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        vmMaintenancePolicy=self.messages.ResourcePolicyVmMaintenancePolicy(
            maintenanceWindow=window))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create-vm-maintenance pol1 --region {} '
        ' --start-time 04:00Z --weekly-window monday '
        .format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_WeeklyWindowFromFile(self):
    window = self.messages.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
        weeklyMaintenanceWindow=self.messages.ResourcePolicyWeeklyCycle(
            dayOfWeeks=[
                self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                    day=self.day_enum.MONDAY,
                    startTime='04:00'),
                self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                    day=self.day_enum.WEDNESDAY,
                    startTime='10:00')]))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        vmMaintenancePolicy=self.messages.ResourcePolicyVmMaintenancePolicy(
            maintenanceWindow=window))
    request = self._ExpectCreate(policy)

    contents = ('[{"day": "MONDAY", "startTime": "04:00Z"}, '
                '{"day": "WEDNESDAY", "startTime": "02:00-8:00"}]')
    window_file = self.Touch(self.temp_path, 'my-window.json',
                             contents=contents)
    result = self.Run(
        'compute resource-policies create-vm-maintenance pol1 --region {0} '
        '--weekly-window-from-file {1}'
        .format(self.region, window_file))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_NoDailyCycleShouldFail(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'cannot request a non-daily cycle.'):
      self.Run(
          'compute resource-policies create-vm-maintenance pol1 --region {0} '
          '--no-daily-window  --start-time 04:00Z'
          .format(self.region))

  @parameterized.parameters(
      ('--start-time 04:00Z --weekly-window-from-file myfile.txt'),
      ('--weekly-window'),
      ('--daily-window'))
  def testCreate_FreqGroupValidation(self, flags):
    with self.AssertRaisesArgumentError():
      self.Run(
          'compute resource-policies create-vm-maintenance pol1 --region {0} '
          '{1}'.format(self.region, flags))

  @parameterized.parameters(
      ('[{"day": "MONDAY"}]',
       'Each JSON/YAML object in the list must have the following keys: '
       '[day, startTime].'),
      ('[{"startTime": "04:00Z"}]',
       'Each JSON/YAML object in the list must have the following keys: '
       '[day, startTime].'),
      ('[{}]',
       'Each JSON/YAML object in the list must have the following keys: '
       '[day, startTime].'),
      ('[{"day": "CATURDAY", "startTime": "04:00Z"}]',
       'Invalid value for `day`: [CATURDAY]'),
      ('', 'File cannot be empty.'))
  def testCreate_InvalidWeeklyFileError(self, contents, message):
    window_file = self.Touch(self.temp_path, 'my-window.json',
                             contents=contents)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException, message):
      self.Run(
          'compute resource-policies create-vm-maintenance pol1 --region {0} '
          '--weekly-window-from-file {1}'
          .format(self.region, window_file))


if __name__ == '__main__':
  test_case.main()
