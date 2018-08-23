# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import exceptions
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class OrgPoliciesAllowTest(testbase.OrgPoliciesUnitTestBase):

  def testAllowOrgPolicyProject(self):
    self.mock_projects.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.PROJECT_ARG, self.WHITELIST_CONSTRAINT),
        self.WhitelistPolicy(self.ORIGINAL_VALUES))
    self.mock_projects.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.PROJECT_ARG,
                                self.WhitelistPolicy(self.NEW_VALUES)),
        self.WhitelistPolicy(self.NEW_VALUES))
    self.assertEqual(
        self.DoRequest(self.PROJECT_ARG), self.WhitelistPolicy(self.NEW_VALUES))

  def testAllowOrgPolicyOrg(self):
    self.mock_organizations.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.ORG_ARG, self.WHITELIST_CONSTRAINT),
        self.WhitelistPolicy(self.ORIGINAL_VALUES))
    self.mock_organizations.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.ORG_ARG,
                                self.WhitelistPolicy(self.NEW_VALUES)),
        self.WhitelistPolicy(self.NEW_VALUES))
    self.assertEqual(
        self.DoRequest(self.ORG_ARG), self.WhitelistPolicy(self.NEW_VALUES))

  def testAllowOrgPolicyFolder(self):
    self.mock_folders.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.FOLDER_ARG, self.WHITELIST_CONSTRAINT),
        self.WhitelistPolicy(self.ORIGINAL_VALUES))
    self.mock_folders.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.FOLDER_ARG,
                                self.WhitelistPolicy(self.NEW_VALUES)),
        self.WhitelistPolicy(self.NEW_VALUES))
    self.assertEqual(
        self.DoRequest(self.FOLDER_ARG), self.WhitelistPolicy(self.NEW_VALUES))

  def testAllowOrgPolicyNoExistingPolicy(self):
    self.mock_projects.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.PROJECT_ARG, self.WHITELIST_CONSTRAINT),
        self.messages.OrgPolicy(constraint=self.WHITELIST_CONSTRAINT))
    self.mock_projects.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.PROJECT_ARG,
                                self.WhitelistPolicy(
                                    [self.VALUE_A, self.VALUE_B])),
        self.WhitelistPolicy([self.VALUE_A, self.VALUE_B]))
    self.assertEqual(
        self.DoRequest(self.PROJECT_ARG),
        self.WhitelistPolicy([self.VALUE_A, self.VALUE_B]))

  def testAllowOrgPolicyDeniedValues(self):
    self.mock_projects.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.PROJECT_ARG, self.BLACKLIST_CONSTRAINT),
        self.BlacklistPolicy(self.ORIGINAL_VALUES))
    with self.AssertRaisesExceptionMatches(
        exceptions.ResourceManagerError,
        'Cannot add values to a non-allowed_values list policy.'):
      self.DoRequest(self.PROJECT_ARG, self.BLACKLIST_CONSTRAINT)

  def testAllowOrgPolicyAllValues(self):
    self.mock_projects.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.PROJECT_ARG, self.WHITELIST_CONSTRAINT),
        self.DenyAllPolicy())
    with self.AssertRaisesExceptionMatches(
        exceptions.ResourceManagerError,
        'Cannot add values if all_values is already specified.'):
      self.DoRequest(self.PROJECT_ARG, self.WHITELIST_CONSTRAINT)

  def DoRequest(self,
                args,
                constraint='constraints/goodService.betterWhitelist'):
    return self.RunOrgPolicies('allow', constraint, self.VALUE_A, self.VALUE_B,
                               *args)


if __name__ == '__main__':
  test_case.main()
