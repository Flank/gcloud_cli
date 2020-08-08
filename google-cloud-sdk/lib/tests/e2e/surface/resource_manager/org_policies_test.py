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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import test_case

messages = org_policies.OrgPoliciesMessages()

TEST_ORGANIZATION_ID = '1054311078602'
TEST_CONSTRAINT = 'constraints/compute.disableSerialPortAccess'


class OrgPoliciesIntegrationTest(e2e_base.WithServiceAuth):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def GetIntegrationTestOrgPolicy(self):
    return messages.OrgPolicy(
        constraint=TEST_CONSTRAINT,
        booleanPolicy=messages.BooleanPolicy(enforced=True))

  def AssertOrgPoliciesEqual(self, expected, policy):
    self.assertEqual(expected.constraint, policy.constraint)
    self.assertEqual(expected.booleanPolicy.enforced,
                     policy.booleanPolicy.enforced)

  def testListOrgPoliciesConstraints(self):
    result = self.RunOrgPolicies('list', '--organization', TEST_ORGANIZATION_ID,
                                 '--show-unset')
    self.assertGreater(len(result), 0)

  def testSetDescribeDeleteOrgPolicies(self):
    result = self.RunOrgPolicies('enable-enforce', '--organization',
                                 TEST_ORGANIZATION_ID, TEST_CONSTRAINT)
    self.AssertOrgPoliciesEqual(self.GetIntegrationTestOrgPolicy(), result)

    result = self.RunOrgPolicies('describe', '--organization',
                                 TEST_ORGANIZATION_ID, TEST_CONSTRAINT)
    self.AssertOrgPoliciesEqual(self.GetIntegrationTestOrgPolicy(), result)

    result = self.RunOrgPolicies('delete', '--organization',
                                 TEST_ORGANIZATION_ID, TEST_CONSTRAINT)
    self.assertIsNone(result)

  def RunOrgPolicies(self, *command):
    return self.Run(['resource-manager', 'org-policies'] +
                    list(command))


if __name__ == '__main__':
  test_case.main()
