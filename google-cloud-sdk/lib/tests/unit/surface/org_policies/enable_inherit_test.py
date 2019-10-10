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
"""Tests for Org Policy enable-inherit command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.org_policies import test_base


class EnableInheritTest(test_base.OrgPolicyUnitTestBase):

  def testEnableInherit_InheritUnset_SetsInheritTrue(self):
    get_response_policy = self.Policy()
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(inherit_from_parent=True)
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunEnableInheritCommand()

    self.assertEqual(response, update_response_policy)

  def testEnableInherit_InheritFalse_SetsInheritTrue(self):
    get_response_policy = self.Policy(inherit_from_parent=False)
    self.ExpectGetPolicy(get_response_policy)
    update_request_policy = self.Policy(inherit_from_parent=True)
    update_response_policy = self.ExpectUpdatePolicy(update_request_policy)

    response = self.RunEnableInheritCommand()

    self.assertEqual(response, update_response_policy)

  def testEnableInherit_InheritTrue_KeepsInheritTrue(self):
    get_response_policy = self.Policy(inherit_from_parent=True)
    self.ExpectGetPolicy(get_response_policy)

    response = self.RunEnableInheritCommand()

    self.assertEqual(response, get_response_policy)

  def RunEnableInheritCommand(self, *args):
    return self.RunOrgPolicyCommand(*(
        ('enable-inherit', self.CONSTRAINT_A) + args +
        (self.RESOURCE_FLAG, self.RESOURCE_ID)))


if __name__ == '__main__':
  test_case.main()
