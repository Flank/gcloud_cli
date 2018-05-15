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
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class OrgPoliciesDeleteTest(testbase.OrgPoliciesUnitTestBase):

  def testDeleteOrgPolicy(self):
    test_policy = self.TestPolicy()

    self.mock_projects.ClearOrgPolicy.Expect(
        self.ExpectedClearRequest(self.PROJECT_ARG), test_policy)
    self.mock_organizations.ClearOrgPolicy.Expect(
        self.ExpectedClearRequest(self.ORG_ARG), test_policy)
    self.mock_folders.ClearOrgPolicy.Expect(
        self.ExpectedClearRequest(self.FOLDER_ARG), test_policy)
    self.assertEqual(self.DoRequest(self.PROJECT_ARG), None)
    self.assertEqual(self.DoRequest(self.ORG_ARG), None)
    self.assertEqual(self.DoRequest(self.FOLDER_ARG), None)
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments:\n  --No-SuCh-FlAg\n  no-such-flag'):
      self.DoRequest(self.WRONG_ARG)

  def ExpectedClearRequest(self, arg):
    messages = self.messages
    if arg == self.PROJECT_ARG:
      return messages.CloudresourcemanagerProjectsClearOrgPolicyRequest(
          projectsId=self.PROJECT_ARG[1],
          clearOrgPolicyRequest=messages.ClearOrgPolicyRequest(
              constraint=self.TEST_CONSTRAINT))
    elif arg == self.ORG_ARG:
      return messages.CloudresourcemanagerOrganizationsClearOrgPolicyRequest(
          organizationsId=self.ORG_ARG[1],
          clearOrgPolicyRequest=messages.ClearOrgPolicyRequest(
              constraint=self.TEST_CONSTRAINT))
    elif arg == self.FOLDER_ARG:
      return messages.CloudresourcemanagerFoldersClearOrgPolicyRequest(
          foldersId=self.FOLDER_ARG[1],
          clearOrgPolicyRequest=messages.ClearOrgPolicyRequest(
              constraint=self.TEST_CONSTRAINT))

  def DoRequest(self, args):
    return self.RunOrgPolicies('delete', self.TEST_CONSTRAINT, *args)


if __name__ == '__main__':
  test_case.main()
