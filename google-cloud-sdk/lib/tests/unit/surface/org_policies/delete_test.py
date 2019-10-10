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
"""Tests for Org Policy delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.org_policies import test_base


class DeleteTest(test_base.OrgPolicyUnitTestBase):

  def testDelete_NoConditionSpecified_DeletesPolicy(self):
    delete_response = self.ExpectDeletePolicy()

    response = self.RunDeleteCommand()

    self.assertEqual(response, delete_response)

  def testDelete_ConditionSpecifiedAndNoMatchingRules_SkipsUpdateOrDelete(self):
    get_response_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A
    }])
    self.ExpectGetPolicy(get_response_policy)

    response = self.RunDeleteCommand(self.CONDITION_FLAG,
                                     self.CONDITION_EXPRESSION_B)

    self.assertEqual(response, get_response_policy)

  def testDelete_ConditionSpecifiedAndMultipleMatchingRules_DeletesAll(self):
    get_response_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A
    }, {
        'condition': self.CONDITION_EXPRESSION_B
    }, {
        'condition': self.CONDITION_EXPRESSION_A
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_B
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDeleteCommand(self.CONDITION_FLAG,
                                     self.CONDITION_EXPRESSION_A)

    self.assertEqual(response, update_response_policy)

  def testDelete_ConditionSpecifiedAndEmptyPolicyCreated_DeletesPolicy(self):
    get_response_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A
    }, {
        'condition': self.CONDITION_EXPRESSION_A
    }])
    self.ExpectGetPolicy(get_response_policy)
    delete_response = self.ExpectDeletePolicy()

    response = self.RunDeleteCommand(self.CONDITION_FLAG,
                                     self.CONDITION_EXPRESSION_A)

    self.assertEqual(response, delete_response)

  def testDelete_ConditionSpecifiedAndEmptyPolicyCreatedWithInheritFromParentTrue_UpdatesPolicy(
      self):
    get_response_policy = self.Policy(
        inherit_from_parent=True,
        rule_data=[{
            'condition': self.CONDITION_EXPRESSION_A
        }, {
            'condition': self.CONDITION_EXPRESSION_A
        }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(inherit_from_parent=True)
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDeleteCommand(self.CONDITION_FLAG,
                                     self.CONDITION_EXPRESSION_A)

    self.assertEqual(response, update_response_policy)

  def RunDeleteCommand(self, *args):
    return self.RunOrgPolicyCommand(*(('delete', self.CONSTRAINT_A) + args +
                                      (self.RESOURCE_FLAG, self.RESOURCE_ID)))


if __name__ == '__main__':
  test_case.main()
