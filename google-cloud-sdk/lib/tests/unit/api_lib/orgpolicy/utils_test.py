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
"""Tests for Org Policy utilities module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.orgpolicy import utils
from googlecloudsdk.command_lib.org_policies import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.org_policies import test_base


class UtilsTest(test_base.OrgPolicyUnitTestBase, parameterized.TestCase):

  @parameterized.named_parameters(
      ('Missing policy name tokens', 'organizations/12345678/policies'),
      ('Additional policy name tokens',
       'organizations/12345678/policies/testService.testRestrictionB/policy'),
  )
  def testGetConstraintFromPolicyName_InvalidPolicyName_ThrowsError(
      self, policy_name):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidInputError,
        "Invalid policy name '{}': Name must be in the form [projects|folders|organizations]/{{resource_id}}/policies/{{constraint_name}}."
        .format(policy_name)):
      utils.GetConstraintFromPolicyName(policy_name)

  def testGetConstraintFromPolicyName_ValidPolicyName_ReturnsConstraint(self):
    constraint = utils.GetConstraintFromPolicyName(self.POLICY_NAME_A)

    self.assertEqual(constraint, self.CONSTRAINT_A)

  @parameterized.named_parameters(
      ('Missing policy name tokens', 'organizations/12345678/policies'),
      ('Additional policy name tokens',
       'organizations/12345678/policies/testService.testRestrictionB/policy'),
  )
  def testGetResourceFromPolicyName_InvalidPolicyName_ThrowsError(
      self, policy_name):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidInputError,
        "Invalid policy name '{}': Name must be in the form [projects|folders|organizations]/{{resource_id}}/policies/{{constraint_name}}."
        .format(policy_name)):
      utils.GetResourceFromPolicyName(policy_name)

  def testGetResourceFromPolicyName_ValidPolicyName_ReturnsResource(self):
    resource = utils.GetResourceFromPolicyName(self.POLICY_NAME_A)

    self.assertEqual(resource, self.RESOURCE)

  @parameterized.named_parameters(
      ('Missing constraint name tokens', 'organizations/12345678/constraints'),
      ('Additional constraint name tokens',
       'organizations/12345678/constraints/testService.testRestrictionB/constraint'
      ),
  )
  def testGetPolicyNameFromConstraintName_InvalidConstraintName_ThrowsError(
      self, constraint_name):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidInputError,
        "Invalid constraint name '{}': Name must be in the form [projects|folders|organizations]/{{resource_id}}/constraints/{{constraint_name}}."
        .format(constraint_name)):
      utils.GetPolicyNameFromConstraintName(constraint_name)

  def testGetPolicyNameFromConstraintName_ValidConstraintName_ReturnsPolicyName(
      self):
    policy_name = utils.GetPolicyNameFromConstraintName(self.CONSTRAINT_NAME_A)

    self.assertEqual(policy_name, self.POLICY_NAME_A)

  def testGetMatchingRulesFromPolicy_NoConditionSpecified_ReturnsMatchingRules(
      self):
    policy = self.Policy(rule_data=[{
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_A
    }, {
        'enforce': False
    }, {
        'condition': self.CONDITION_EXPRESSION_B
    }])
    filtered_policy = self.Policy(rule_data=[{
        'enforce': True
    }, {
        'enforce': False
    }])

    rules = utils.GetMatchingRulesFromPolicy(policy, None)

    self.assertEqual(rules, filtered_policy.rules)

  def testGetMatchingRulesFromPolicy_ConditionSpecified_ReturnsMatchingRules(
      self):
    policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_B
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }])
    filtered_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': True
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'enforce': False
    }])

    rules = utils.GetMatchingRulesFromPolicy(policy,
                                             self.CONDITION_EXPRESSION_A)

    self.assertEqual(rules, filtered_policy.rules)

  def testGetNonMatchingRulesFromPolicy_NoConditionSpecified_ReturnsNonMatchingRules(
      self):
    policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A
    }, {}, {
        'condition': self.CONDITION_EXPRESSION_B
    }])
    filtered_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A
    }, {
        'condition': self.CONDITION_EXPRESSION_B
    }])

    rules = utils.GetNonMatchingRulesFromPolicy(policy, None)

    self.assertEqual(rules, filtered_policy.rules)

  def testGetNonMatchingRulesFromPolicy_ConditionSpecified_ReturnsNonMatchingRules(
      self):
    policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A,
    }, {
        'condition': self.CONDITION_EXPRESSION_B
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
    }])
    filtered_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_B,
    }])

    rules = utils.GetNonMatchingRulesFromPolicy(policy,
                                                self.CONDITION_EXPRESSION_A)

    self.assertEqual(rules, filtered_policy.rules)

  def testCreateRuleOnPolicy_NoConditionSpecified_CreatesRule(self):
    policy = self.Policy(rule_data=[{'condition': self.CONDITION_EXPRESSION_A}])
    updated_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A
    }, {}])

    rule, returned_policy = utils.CreateRuleOnPolicy(policy, None)

    self.assertIsNotNone(rule)
    self.assertIsNone(rule.condition)
    self.assertEqual(returned_policy, updated_policy)

  def testCreateRuleOnPolicy_ConditionSpecified_CreatesRule(self):
    policy = self.Policy(rule_data=[{}])
    updated_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A
    }])

    rule, returned_policy = utils.CreateRuleOnPolicy(
        policy, self.CONDITION_EXPRESSION_A)

    self.assertIsNotNone(rule)
    self.assertIsNotNone(rule.condition)
    self.assertEqual(rule.condition.expression, self.CONDITION_EXPRESSION_A)
    self.assertEqual(returned_policy, updated_policy)


if __name__ == '__main__':
  test_case.main()
