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
"""Tests for Org Policy interfaces module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.orgpolicy import utils as org_policy_utils
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import interfaces
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.calliope import util as calliope_util
from tests.lib.surface.org_policies import test_base


class OrgPolicyGetAndUpdateCommandTest(test_base.OrgPolicyUnitTestBase):

  def SetUp(self):
    self.command = _GetAndUpdateCommand()

    parser = calliope_util.ArgumentParser()
    arguments.AddConstraintArgToParser(parser)
    arguments.AddResourceFlagsToParser(parser)
    arguments.AddConditionFlagToParser(parser)
    self.args_without_condition = parser.parse_args(
        [self.CONSTRAINT_A, self.RESOURCE_FLAG, self.RESOURCE_ID])
    self.args_with_condition = parser.parse_args([
        self.CONSTRAINT_A, self.RESOURCE_FLAG, self.RESOURCE_ID,
        self.CONDITION_FLAG, self.CONDITION_EXPRESSION_A
    ])

  def testRun_NoExistingPolicy_CreatesPolicy(self):
    get_exception = http_error.MakeHttpError(code=404)
    self.ExpectGetPolicyWithException(get_exception)
    create_response_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A
    }])
    self.ExpectCreatePolicy(create_response_policy)

    response = self.command.Run(self.args_with_condition)

    self.assertEqual(response, create_response_policy)

  def testRun_NoExistingPolicyAndNoUpdate_SkipsCreate(self):
    get_exception = http_error.MakeHttpError(code=404)
    self.ExpectGetPolicyWithException(get_exception)
    empty_response = self.org_policy_messages.GoogleProtobufEmpty()

    response = self.command.Run(self.args_without_condition)

    self.assertEqual(response, empty_response)

  def testRun_ExistingPolicy_UpdatesPolicy(self):
    get_response_policy = self.Policy()
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(rule_data=[{
        'condition': self.CONDITION_EXPRESSION_A
    }])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.command.Run(self.args_with_condition)

    self.assertEqual(response, update_response_policy)

  def testRun_ExistingPolicyAndNoUpdate_SkipsUpdate(self):
    get_response_policy = self.Policy(rule_data=[{}])
    self.ExpectGetPolicy(get_response_policy)

    response = self.command.Run(self.args_with_condition)

    self.assertEqual(response, get_response_policy)

  def testRun_ExistingPolicyWithNonEmptyRulesAndEmptyPolicyCreated_DeletesPolicy(
      self):
    get_response_policy = self.Policy(rule_data=[{}])
    self.ExpectGetPolicy(get_response_policy)
    delete_response = self.ExpectDeletePolicy()

    response = self.command.Run(self.args_without_condition)

    self.assertEqual(response, delete_response)

  def testRun_ExistingPolicyWithInheritFromParentTrueAndEmptyPolicyCreated_DeletesPolicy(
      self):
    get_response_policy = self.Policy(inherit_from_parent=True)
    self.ExpectGetPolicy(get_response_policy)
    delete_response = self.ExpectDeletePolicy()

    response = self.command.Run(self.args_without_condition)

    self.assertEqual(response, delete_response)

  def testRun_ExistingPolicyWithResetTrueAndEmptyPolicyCreated_DeletesPolicy(
      self):
    get_response_policy = self.Policy(reset=True)
    self.ExpectGetPolicy(get_response_policy)
    delete_response = self.ExpectDeletePolicy()

    response = self.command.Run(self.args_without_condition)

    self.assertEqual(response, delete_response)


class _GetAndUpdateCommand(interfaces.OrgPolicyGetAndUpdateCommand):
  """Test command class that implements the OrgPolicyGetAndUpdateCommand interface."""

  def __init__(self):
    super(_GetAndUpdateCommand, self).__init__(None, None)

  def UpdatePolicy(self, policy, args):
    """Updates the policy for tests.

    If --condition is specified, an empty policy is returned.

    If --condition is not specified, this first checks if there are any rules on
    the policy. If there are, the policy is returned as is. If not, a new rule
    with the specified condition is added.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    new_policy = copy.deepcopy(policy)

    if args.condition is None:
      new_policy.rules = []
      new_policy.inheritFromParent = False
      new_policy.reset = False
      return new_policy

    if new_policy.rules:
      return new_policy

    _, new_policy = org_policy_utils.CreateRuleOnPolicy(new_policy,
                                                        args.condition)
    return new_policy


if __name__ == '__main__':
  test_case.main()
