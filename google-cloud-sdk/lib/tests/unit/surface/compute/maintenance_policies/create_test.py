# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the maintenance policies create command."""
from tests.lib import test_case
from tests.lib.surface.compute import maintenance_policies_base


class CreateTest(maintenance_policies_base.TestBase):

  def _ExpectCreate(self, policy):
    request = self.messages.ComputeMaintenancePoliciesInsertRequest(
        project=self.Project(),
        region=self.region,
        maintenancePolicy=policy)
    self.make_requests.side_effect = [[policy]]
    return request

  def testCreate_Simple(self):
    policy = self.MakeMaintenancePolicy('pol1', 1, '04:00')
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute maintenance-policies create pol1 --start-time 04:00Z '
        '--region {}'.format(self.region))

    self.CheckRequests([(self.compute.maintenancePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_Description(self):
    description = 'This is a maintenance policy.'
    policy = self.MakeMaintenancePolicy(
        'pol1', 1, '04:00', description=description)
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute maintenance-policies create pol1 --start-time 04:00Z '
        '--region {} --description "{}"'
        .format(self.region, description))

    self.CheckRequests([(self.compute.maintenancePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_StartTime(self):
    policy = self.MakeMaintenancePolicy('pol1', 1, '04:00')
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute maintenance-policies create pol1 --start-time 03:00.52-1:00 '
        '--region {}'.format(self.region))

    self.CheckRequests([(self.compute.maintenancePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_HiddenFlag(self):
    policy = self.MakeMaintenancePolicy('pol1', 2, '04:00')
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute maintenance-policies create pol1 --start-time 04:00Z '
        '--region {} --days-in-cycle 2'.format(self.region))

    self.CheckRequests([(self.compute.maintenancePolicies, 'Insert', request)])
    self.assertEqual(result, policy)


if __name__ == '__main__':
  test_case.main()
