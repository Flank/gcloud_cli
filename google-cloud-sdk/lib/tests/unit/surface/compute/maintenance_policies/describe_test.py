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
"""Tests for the maintenance policies describe command."""
from tests.lib import test_case
from tests.lib.surface.compute import maintenance_policies_base


class DescribeTest(maintenance_policies_base.TestBase):

  def testDescribe_Simple(self):
    policy = self.maintenance_policies[1]
    policy_ref = self.reg.Parse(
        'pol2', params={'project': self.Project(), 'region': self.region},
        collection='compute.maintenancePolicies')

    policy.kind = 'compute#maintenancePolicy'
    policy.selfLink = policy_ref.SelfLink()

    self.make_requests.side_effect = [[policy]]
    self.Run('compute maintenance-policies describe pol2 '
             '--region {}'.format(self.region))

    self.CheckRequests(
        [(self.compute.maintenancePolicies,
          'Get',
          self.messages.ComputeMaintenancePoliciesGetRequest(
              project=self.Project(),
              region=self.region,
              maintenancePolicy='pol2'))])

    self.AssertOutputEquals("""\
creationTimestamp: '2017-10-27T17:54:10.636-07:00'
description: desc
kind: compute#maintenancePolicy
name: pol2
region: {region}
selfLink: {uri}
vmMaintenancePolicy:
  maintenanceWindow:
    dailyMaintenanceWindow:
      daysInCycle: 3
      startTime: 08:00
""".format(region=self.region, uri=policy_ref.SelfLink()), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
