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
"""Tests for Org Policy list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.org_policies import test_base


class ListTest(test_base.OrgPolicyUnitTestBase):

  def testList_ReturnsPolicies(self):
    list_response_policies = [
        self.Policy(name=self.POLICY_NAME_A),
        self.Policy(name=self.POLICY_NAME_B)
    ]
    self.ExpectListPolicies(list_response_policies)

    response = self.RunListCommand()

    self.assertEqual(response, list_response_policies)

  def testList_ShowUnsetSpecified_ReturnsPoliciesForAllConstraints(self):
    list_response_policies = [self.Policy(name=self.POLICY_NAME_A)]
    self.ExpectListPolicies(list_response_policies)
    list_response_constraints = [
        self.Constraint(name=self.CONSTRAINT_NAME_A),
        self.Constraint(name=self.CONSTRAINT_NAME_B)
    ]
    self.ExpectListConstraints(list_response_constraints)
    all_policies = [
        self.Policy(name=self.POLICY_NAME_A),
        self.Policy(name=self.POLICY_NAME_B, etag=None, update_time=None)
    ]

    response = self.RunListCommand(self.SHOW_UNSET_FLAG)

    self.assertEqual(response, all_policies)

  def RunListCommand(self, *args):
    return self.RunOrgPolicyCommand(*(('list',) + args +
                                      (self.RESOURCE_FLAG, self.RESOURCE_ID)))


if __name__ == '__main__':
  test_case.main()
