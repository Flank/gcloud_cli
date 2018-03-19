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
"""Tests for the maintenance policies delete command."""
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import maintenance_policies_base


class DeleteTest(maintenance_policies_base.TestBase):

  def testDelete_Simple(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run('compute maintenance-policies delete pol1 '
             '--region {}'.format(self.region))

    self.CheckRequests(
        [(self.compute.maintenancePolicies,
          'Delete',
          self.messages.ComputeMaintenancePoliciesDeleteRequest(
              project=self.Project(),
              region=self.region,
              maintenancePolicy='pol1'))])


if __name__ == '__main__':
  test_case.main()
