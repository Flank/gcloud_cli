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
"""Tests for Org Policy allow command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.org_policies import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.org_policies import test_base


class AllowTest(test_base.OrgPolicyUnitTestBase):

  def testAllow_NoValuesSpecifiedAndRemoveSpecified_ThrowsError(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidInputError,
        'One or more values need to be specified if --remove is specified.'):
      self.RunAllowCommand(self.REMOVE_FLAG)

  def testAllow_AddValues_NoExistingPolicy_CreatesPolicyWithValues(self):
    get_exception = http_error.MakeHttpError(code=404, message='Not found.')
    self.ExpectGetPolicyWithException(get_exception)
    create_response_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }])
    self.ExpectCreatePolicy(create_response_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B)

    self.assertEqual(response, create_response_policy)

  def testAllow_AddValues_NoMatchingRules_CreatesRuleWithValues(self):
    get_response_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A
    }, {
        'condition': self.CONDITION_EXPRESSION_B,
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B,
                                    self.CONDITION_FLAG,
                                    self.CONDITION_EXPRESSION_B)

    self.assertEqual(response, update_response_policy)

  def testAllow_AddValues_UnsetValuesField_AddsValues(self):
    get_response_policy = self.Policy(rule_data=[{}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B)

    self.assertEqual(response, update_response_policy)

  def testAllow_AddValues_EmptyAllowedValuesField_AddsValues(self):
    get_response_policy = self.Policy(rule_data=[{'allowed_values': []}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B)

    self.assertEqual(response, update_response_policy)

  def testAllow_AddValues_ValuesPresent_DoesNotAddValues(self):
    get_response_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_C]
    }, {
        'allowed_values': [self.VALUE_B]
    }])
    self.ExpectGetPolicy(get_response_policy)

    response = self.RunAllowCommand(self.VALUE_B, self.VALUE_C)

    self.assertEqual(response, get_response_policy)

  def testAllow_AddValues_AllowAllTrue_SkipsUpdate(self):
    get_response_policy = self.Policy(rule_data=[{'allow_all': True}])
    self.ExpectGetPolicy(get_response_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B)

    self.assertEqual(response, get_response_policy)

  def testAllow_AddValues_DenyAllTrue_ThrowsError(self):
    get_response_policy = self.Policy(rule_data=[{'deny_all': True}])
    self.ExpectGetPolicy(get_response_policy)

    with self.AssertRaisesExceptionMatches(
        exceptions.OperationNotSupportedError,
        'Values cannot be allowed if denyAll is set on the policy.'):
      self.RunAllowCommand(self.VALUE_A)

  def testAllow_AddValues_AllowAllFalse_UnsetsAllowAllAndAddsValues(self):
    get_response_policy = self.Policy(rule_data=[{'allow_all': False}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B)

    self.assertEqual(response, update_response_policy)

  def testAllow_AddValues_DenyAllFalse_UnsetsDenyAllAndAddsValues(self):
    get_response_policy = self.Policy(rule_data=[{'deny_all': False}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B)

    self.assertEqual(response, update_response_policy)

  def testAllow_AddValues_RepeatedValues_AddsOnlyUniqueValues(self):
    get_response_policy = self.Policy(rule_data=[{}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B, self.VALUE_B)

    self.assertEqual(response, update_response_policy)

  def testAllow_AddValues_MultipleEligibleRules_AddsValuesToFirst(self):
    get_response_policy = self.Policy(rule_data=[{}, {}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }, {}])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_A, self.VALUE_B)

    self.assertEqual(response, update_response_policy)

  def testAllow_AddValues_MultipleMatchingRulesWithDeniedValues_RemovesValuesFromAllAndAddsValues(
      self):
    get_response_policy = self.Policy(rule_data=[{
        'denied_values': [self.VALUE_A, self.VALUE_D]
    }, {
        'denied_values': [self.VALUE_B, self.VALUE_D]
    }, {
        'denied_values':
            [self.VALUE_A, self.VALUE_B, self.VALUE_C, self.VALUE_D]
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_B, self.VALUE_C],
        'denied_values': [self.VALUE_A, self.VALUE_D]
    }, {
        'denied_values': [self.VALUE_D]
    }, {
        'denied_values': [self.VALUE_A, self.VALUE_D]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_B, self.VALUE_C)

    self.assertEqual(response, update_response_policy)

  def testAllow_AddValues_ValuesNotPresent_AddsMissingValues(self):
    get_response_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A]
    }, {
        'allowed_values': [self.VALUE_B]
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_C]
    }, {
        'allowed_values': [self.VALUE_B]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_B, self.VALUE_C)

    self.assertEqual(response, update_response_policy)

  def testAllow_AllowAllValues_NoExistingPolicy_CreatesPolicyWithAllowAllTrue(
      self):
    get_exception = http_error.MakeHttpError(code=404, message='Not found.')
    self.ExpectGetPolicyWithException(get_exception)
    create_response_policy = self.Policy(rule_data=[{'allow_all': True}])
    self.ExpectCreatePolicy(create_response_policy)

    response = self.RunAllowCommand()

    self.assertEqual(response, create_response_policy)

  def testAllow_AllowAllValues_NoMatchingRules_CreatesRuleWithAllowAllTrue(
      self):
    get_response_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A,
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{}, {
        'condition': self.CONDITION_EXPRESSION_A,
    }, {
        'condition': self.CONDITION_EXPRESSION_B,
        'allow_all': True
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.CONDITION_FLAG,
                                    self.CONDITION_EXPRESSION_B)

    self.assertEqual(response, update_response_policy)

  def testAllow_AllowAllValues_AllowAllUnset_SetsAllowAllTrue(self):
    get_response_policy = self.Policy(rule_data=[{}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{'allow_all': True}])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand()

    self.assertEqual(response, update_response_policy)

  def testAllow_AllowAllValues_AllowAllFalse_SetsAllowAllTrue(self):
    get_response_policy = self.Policy(rule_data=[{'allow_all': False}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{'allow_all': True}])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand()

    self.assertEqual(response, update_response_policy)

  def testAllow_AllowAllValues_AllowAllTrue_KeepsAllowAllTrue(self):
    get_response_policy = self.Policy(rule_data=[{'allow_all': True}])
    self.ExpectGetPolicy(get_response_policy)

    response = self.RunAllowCommand()

    self.assertEqual(response, get_response_policy)

  def testAllow_AllowAllValues_MultipleMatchingRules_DeletesAllAndCreatesRuleWithAllowAllTrue(
      self):
    get_response_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A,
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A,
        'allow_all': True
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.CONDITION_FLAG,
                                    self.CONDITION_EXPRESSION_A)

    self.assertEqual(response, update_response_policy)

  def testAllow_RemoveValues_NoExistingPolicy_ThrowsError(self):
    get_exception = http_error.MakeHttpError(code=404, message='Not found.')
    self.ExpectGetPolicyWithException(get_exception)

    with self.AssertRaisesHttpExceptionMatches('Not found.'):
      self.RunAllowCommand(self.VALUE_A, self.REMOVE_FLAG)

  def testAllow_RemoveValues_MultipleMatchingRules_RemovesValuesFromAll(self):
    get_response_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_D]
    }, {
        'allowed_values': [self.VALUE_B, self.VALUE_D]
    }, {
        'allowed_values':
            [self.VALUE_A, self.VALUE_B, self.VALUE_C, self.VALUE_D]
    }])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_D]
    }, {
        'allowed_values': [self.VALUE_D]
    }, {
        'allowed_values': [self.VALUE_A, self.VALUE_D]
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunAllowCommand(self.VALUE_B, self.VALUE_C,
                                    self.REMOVE_FLAG)

    self.assertEqual(response, update_response_policy)

  def RunAllowCommand(self, *args):
    return self.RunOrgPolicyCommand(*(('allow', self.CONSTRAINT_A) + args +
                                      (self.RESOURCE_FLAG, self.RESOURCE_ID)))


if __name__ == '__main__':
  test_case.main()
