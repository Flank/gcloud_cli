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
"""Tests for Org Policy disable-inherit command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.org_policies import test_base


class DisableInheritTest(test_base.OrgPolicyUnitTestBase):

  def testDisableInherit_InheritUnset_SetsInheritFalse(self):
    get_response_policy = self.Policy(rule_data=[{}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(
        inherit_from_parent=False, rule_data=[{}])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDisableInheritCommand()

    self.assertEqual(response, update_response_policy)

  def testDisableInherit_InheritTrue_SetsInheritFalse(self):
    get_response_policy = self.Policy(inherit_from_parent=True, rule_data=[{}])
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(
        inherit_from_parent=False, rule_data=[{}])
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunDisableInheritCommand()

    self.assertEqual(response, update_response_policy)

  def testDisableInherit_InheritFalse_KeepsInheritFalse(self):
    get_response_policy = self.Policy(inherit_from_parent=False, rule_data=[{}])
    self.ExpectGetPolicy(get_response_policy)

    response = self.RunDisableInheritCommand()

    self.assertEqual(response, get_response_policy)

  def RunDisableInheritCommand(self, *args):
    return self.RunOrgPolicyCommand(*(
        ('disable-inherit', self.CONSTRAINT_A) + args +
        (self.RESOURCE_FLAG, self.RESOURCE_ID)))


if __name__ == '__main__':
  test_case.main()
