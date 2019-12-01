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
"""Tests for Org Policy set-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.command_lib.org_policies import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.org_policies import test_base


class SetPolicyTest(test_base.OrgPolicyUnitTestBase):

  def testSetPolicy_NameNotProvided_ThrowsError(self):
    policy = self.Policy(name=None)
    json_str = encoding.MessageToJson(policy)
    filepath = self.Touch(self.temp_path, contents=json_str)

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidInputError,
        'Name field not present in the organization policy.'):
      self.RunSetPolicyCommand(filepath)

  def testSetPolicy_NoExistingPolicy_CreatesPolicy(self):
    policy = self.Policy(rule_data=[{'condition': self.CONDITION_EXPRESSION_A}])
    json_str = encoding.MessageToJson(policy)
    filepath = self.Touch(self.temp_path, contents=json_str)
    get_exception = http_error.MakeHttpError(code=404)
    self.ExpectGetPolicyWithException(get_exception)
    self.ExpectCreatePolicy(
        policy, request_etag=self.ETAG_A, request_update_time=self.TIMESTAMP_A)

    response = self.RunSetPolicyCommand(filepath)

    self.assertEqual(response, policy)

  def testSetPolicy_ExistingPolicy_UpdatesPolicy(self):
    policy = self.Policy(rule_data=[{'condition': self.CONDITION_EXPRESSION_A}])
    json_str = encoding.MessageToJson(policy)
    filepath = self.Touch(self.temp_path, contents=json_str)
    get_response_policy = self.Policy()
    self.ExpectGetPolicy(get_response_policy)
    update_response_policy = self.ExpectUpdatePolicy(policy)

    response = self.RunSetPolicyCommand(filepath)

    self.assertEqual(response, update_response_policy)

  def testRun_NoChangesRequired_SkipsUpdate(self):
    policy = self.Policy(rule_data=[{'condition': self.CONDITION_EXPRESSION_A}])
    json_str = encoding.MessageToJson(policy)
    filepath = self.Touch(self.temp_path, contents=json_str)
    self.ExpectGetPolicy(policy)

    response = self.RunSetPolicyCommand(filepath)

    self.assertEqual(response, policy)

  def RunSetPolicyCommand(self, filepath, *args):
    return self.RunOrgPolicyCommand('set-policy', filepath, *args)


if __name__ == '__main__':
  test_case.main()
