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
"""Tests for Org Policy command utilities module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import exceptions
from googlecloudsdk.command_lib.org_policies import utils
from googlecloudsdk.core import yaml
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope import util as calliope_util
from tests.lib.surface.org_policies import test_base


class UtilsTest(test_base.OrgPolicyUnitTestBase, parameterized.TestCase):

  CONSTRAINT_WITHOUT_PREFIX = 'testService.testRestriction'
  CONSTRAINT_WITH_PREFIX = 'constraints/testService.testRestriction'
  POLICY_NAME = 'organizations/12345678/policies/testService.testRestriction'

  def SetUp(self):
    self.parser = calliope_util.ArgumentParser()
    arguments.AddConstraintArgToParser(self.parser)
    arguments.AddResourceFlagsToParser(self.parser)
    arguments.AddConditionFlagToParser(self.parser)
    arguments.AddValueArgToParser(self.parser)

  def testGetConstraintFromArgs_ConstraintPrefixNotPresent_AddsPrefix(self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_WITHOUT_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    constraint = utils.GetConstraintFromArgs(args)

    self.assertEqual(constraint, self.CONSTRAINT_WITH_PREFIX)

  def testGetConstraintFromArgs_ConstraintPrefixPresent_SkipsAddingPrefix(self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_WITH_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    constraint_name = utils.GetConstraintFromArgs(args)

    self.assertEqual(constraint_name, self.CONSTRAINT_WITH_PREFIX)

  def testGetConstraintNameFromArgs_ConstraintPrefixNotPresent_SkipsRemovingPrefix(
      self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_WITHOUT_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    constraint = utils.GetConstraintNameFromArgs(args)

    self.assertEqual(constraint, self.CONSTRAINT_WITHOUT_PREFIX)

  def testGetConstraintNameFromArgs_ConstraintPrefixPresent_RemovesPrefix(self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_WITH_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    constraint_name = utils.GetConstraintNameFromArgs(args)

    self.assertEqual(constraint_name, self.CONSTRAINT_WITHOUT_PREFIX)

  def testGetResourceFromArgs_OrganizationResourceSpecified_ReturnsResource(
      self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_A, self.ORGANIZATION_FLAG, self.ORGANIZATION_ID])

    resource = utils.GetResourceFromArgs(args)

    self.assertEqual(resource, self.ORGANIZATION_RESOURCE)

  def testGetResourceFromArgs_FolderResourceSpecified_ReturnsResource(self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_A, self.FOLDER_FLAG, self.FOLDER_ID])

    resource = utils.GetResourceFromArgs(args)

    self.assertEqual(resource, self.FOLDER_RESOURCE)

  def testGetResourceFromArgs_ProjectResourceSpecified_ReturnsResource(self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_A, self.PROJECT_FLAG, self.PROJECT_ID])

    resource = utils.GetResourceFromArgs(args)

    self.assertEqual(resource, self.PROJECT_RESOURCE)

  def testGetPolicyNameFromArgs_ConstraintPrefixNotPresent_ReturnsName(self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_WITHOUT_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    name = utils.GetPolicyNameFromArgs(args)

    self.assertEqual(name, self.POLICY_NAME)

  def testGetPolicyNameFromArgs_ConstraintPrefixPresent_ReturnsName(self):
    args = self.parser.parse_args(
        [self.CONSTRAINT_WITH_PREFIX, self.RESOURCE_FLAG, self.RESOURCE_ID])

    name = utils.GetPolicyNameFromArgs(args)

    self.assertEqual(name, self.POLICY_NAME)

  @parameterized.named_parameters(('Empty file', ''),
                                  ('Badly formatted file', '?:?:?'))
  def testGetMessageFromFile_InvalidFile_ThrowsError(self, file_contents):
    filepath = self.Touch(self.temp_path, contents=file_contents)

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidInputError,
        'Unable to parse file [{}]'.format(filepath)):
      utils.GetMessageFromFile(
          filepath, self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1Policy)

  def testGetMessageFromFile_JsonFile_ReturnsMessage(self):
    policy = self.Policy(rule_data=[{'condition': self.CONDITION_EXPRESSION_A}])
    json_str = encoding.MessageToJson(policy)
    filename = self.Touch(self.temp_path, contents=json_str)

    message = utils.GetMessageFromFile(
        filename, self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1Policy)

    self.assertEqual(policy, message)

  def testGetMessageFromFile_YamlFile_ReturnsMessage(self):
    policy = self.Policy(rule_data=[{'condition': self.CONDITION_EXPRESSION_A}])
    json_str = encoding.MessageToJson(policy)
    json_obj = json.loads(json_str)
    yaml_str = yaml.dump(json_obj)
    filename = self.Touch(self.temp_path, contents=yaml_str)

    message = utils.GetMessageFromFile(
        filename, self.org_policy_messages.GoogleCloudOrgpolicyV2alpha1Policy)

    self.assertEqual(policy, message)

  def testRemoveAllowedValuesFromPolicy_NoMatchingRule_ThrowsError(self):
    policy = self.Policy(rule_data=[{'condition': self.CONDITION_EXPRESSION_A}])
    args = self.parser.parse_args(
        [self.CONSTRAINT_A, self.VALUE_A, self.RESOURCE_FLAG, self.RESOURCE_ID])

    new_policy = utils.RemoveAllowedValuesFromPolicy(policy, args)

    self.assertEqual(new_policy, policy)

  def testRemoveAllowedValuesFromPolicy_RemovesValuesFromAll(self):
    policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_D]
    }, {
        'allowed_values': [self.VALUE_B, self.VALUE_D]
    }, {
        'allowed_values':
            [self.VALUE_A, self.VALUE_B, self.VALUE_C, self.VALUE_D]
    }])
    args = self.parser.parse_args([
        self.CONSTRAINT_A, self.VALUE_B, self.VALUE_C, self.RESOURCE_FLAG,
        self.RESOURCE_ID
    ])
    updated_policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_D]
    }, {
        'allowed_values': [self.VALUE_D]
    }, {
        'allowed_values': [self.VALUE_A, self.VALUE_D]
    }])

    new_policy = utils.RemoveAllowedValuesFromPolicy(policy, args)

    self.assertEqual(new_policy, updated_policy)

  def testRemoveAllowedValuesFromPolicy_NoConditionSpecifiedAndMultipleMatchingEmptyRulesCreated_DeletesAll(
      self):
    policy = self.Policy(rule_data=[{
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }, {
        'allowed_values': [self.VALUE_C]
    }, {
        'allowed_values': [self.VALUE_B, self.VALUE_D]
    }])
    args = self.parser.parse_args([
        self.CONSTRAINT_A, self.VALUE_A, self.VALUE_B, self.VALUE_D,
        self.RESOURCE_FLAG, self.RESOURCE_ID
    ])
    updated_policy = self.Policy(rule_data=[{'allowed_values': [self.VALUE_C]}])
    new_policy = utils.RemoveAllowedValuesFromPolicy(policy, args)

    self.assertEqual(new_policy, updated_policy)

  def testRemoveAllowedValuesFromPolicy_ConditionSpecifiedAndMultipleMatchingEmptyRulesCreated_DeletesAll(
      self):
    policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A,
        'allowed_values': [self.VALUE_A, self.VALUE_B]
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'allowed_values': [self.VALUE_C]
    }, {
        'condition': self.CONDITION_EXPRESSION_A,
        'allowed_values': [self.VALUE_B, self.VALUE_D]
    }])
    args = self.parser.parse_args([
        self.CONSTRAINT_A, self.VALUE_A, self.VALUE_B, self.VALUE_D,
        self.CONDITION_FLAG, self.CONDITION_EXPRESSION_A, self.RESOURCE_FLAG,
        self.RESOURCE_ID
    ])
    updated_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A,
        'allowed_values': [self.VALUE_C]
    }])
    new_policy = utils.RemoveAllowedValuesFromPolicy(policy, args)

    self.assertEqual(new_policy, updated_policy)


if __name__ == '__main__':
  test_case.main()
