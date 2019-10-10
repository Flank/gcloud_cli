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
"""Tests for Org Policy disable-enforce command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.org_policies import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.org_policies import test_base


class DisableEnforceTest(test_base.OrgPolicyUnitTestBase):

  def testDisableEnforce_NoExistingPolicy_CreatesPolicyWithEnforceFalse(self):
    get_exception = http_error.MakeHttpError(code=404, message='Not found.')
    self.ExpectGetPolicyWithException(get_exception)
    create_response_policy = self.Policy(rule_data=[{'enforce': False}])
    self.ExpectCreatePolicy(create_response_policy)

    response = self.RunDisableEnforceCommand()

    self.assertEqual(response, create_response_policy)

  def testDisableEnforce_NoConditionSpecifiedAndNoRules_CreatesRuleWithEnforceFalse(
      self):
    get_response_policy = self.Policy()
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{'enforce': False}])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDisableEnforceCommand()

    self.assertEqual(response, update_response_policy)

  def testDisableEnforce_ConditionSpecifiedAndNoRules_CreatesTwoRulesWithOppositeEnforceValues(
      self):
    get_response_policy = self.Policy()
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDisableEnforceCommand(self.CONDITION_FLAG,
                                             self.CONDITION_EXPRESSION_A)

    self.assertEqual(response, update_response_policy)

  def testDisableEnforce_OnlyConditionalRules_ThrowsError(self):
    get_response_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A,
    }])
    self.ExpectGetPolicy(get_response_policy)

    with self.AssertRaisesExceptionMatches(
        exceptions.BooleanPolicyValidationError,
        'An unconditional enforce value does not exist on the nonempty policy.'
    ):
      self.RunDisableEnforceCommand()

  def testDisableEnforce_NoConditionSpecifiedAndMultipleRulesAndUnconditionalEnforceTrue_ThrowsError(
      self):
    get_response_policy = self.Policy(rule_data=[{
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }])
    self.ExpectGetPolicy(get_response_policy)

    with self.AssertRaisesExceptionMatches(
        exceptions.BooleanPolicyValidationError,
        'Unconditional enforce value cannot be the same as a conditional enforce value on the policy.'
    ):
      self.RunDisableEnforceCommand()

  def testDisableEnforce_ConditionSpecifiedAndUnconditionalEnforceFalse_ThrowsError(
      self):
    get_response_policy = self.Policy(rule_data=[{'enforce': False}])
    self.ExpectGetPolicy(get_response_policy)

    with self.AssertRaisesExceptionMatches(
        exceptions.BooleanPolicyValidationError,
        'Conditional enforce value cannot be the same as the unconditional enforce value on the policy.'
    ):
      self.RunDisableEnforceCommand(self.CONDITION_FLAG,
                                    self.CONDITION_EXPRESSION_A)

  def testDisableEnforce_NoMatchingConditionalRules_CreatesRuleWithEnforceFalse(
      self):
    get_response_policy = self.Policy(rule_data=[{
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }, {
        'condition': self.CONDITION_EXPRESSION_B,
        'enforce': False
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDisableEnforceCommand(self.CONDITION_FLAG,
                                             self.CONDITION_EXPRESSION_B)

    self.assertEqual(response, update_response_policy)

  def testDisableEnforce_EnforceTrue_SetsEnforceFalse(self):
    get_response_policy = self.Policy(rule_data=[{'enforce': True}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{'enforce': False}])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDisableEnforceCommand()

    self.assertEqual(response, update_response_policy)

  def testDisableEnforce_EnforceFalse_KeepsEnforceFalse(self):
    get_response_policy = self.Policy(rule_data=[{'enforce': False}])
    self.ExpectGetPolicy(get_response_policy)

    response = self.RunDisableEnforceCommand()

    self.assertEqual(response, get_response_policy)

  def testDisableEnforce_MultipleMatchingRules_DeletesAllAndCreatesRuleWithEnforceFalse(
      self):
    get_response_policy = self.Policy(rule_data=[{
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDisableEnforceCommand(self.CONDITION_FLAG,
                                             self.CONDITION_EXPRESSION_A)

    self.assertEqual(response, update_response_policy)

  def RunDisableEnforceCommand(self, *args):
    return self.RunOrgPolicyCommand(*(
        ('disable-enforce', self.CONSTRAINT_A) + args +
        (self.RESOURCE_FLAG, self.RESOURCE_ID)))


if __name__ == '__main__':
  test_case.main()
