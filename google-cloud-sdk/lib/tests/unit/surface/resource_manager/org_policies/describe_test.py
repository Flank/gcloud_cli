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

from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class OrgPoliciesDescribeTest(testbase.OrgPoliciesUnitTestBase):

  def testDescribeOrgPolicy(self):
    test_policy = self.TestPolicy()

    self.mock_projects.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.PROJECT_ARG, self.TEST_CONSTRAINT),
        test_policy)
    self.mock_organizations.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.ORG_ARG, self.TEST_CONSTRAINT),
        test_policy)
    self.mock_folders.GetOrgPolicy.Expect(
        self.ExpectedGetRequest(self.FOLDER_ARG, self.TEST_CONSTRAINT),
        test_policy)
    self.assertEqual(self.DoRequest(self.PROJECT_ARG), test_policy)
    self.assertEqual(self.DoRequest(self.ORG_ARG), test_policy)
    self.assertEqual(self.DoRequest(self.FOLDER_ARG), test_policy)
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments:\n  --No-SuCh-FlAg\n  no-such-flag'):
      self.DoRequest(self.WRONG_ARG)

  def testDescribeEffectiveOrgPolicy(self):
    test_policy = self.TestPolicy()

    self.mock_projects.GetEffectiveOrgPolicy.Expect(
        self.ExpectedEffectiveRequest(self.PROJECT_ARG), test_policy)
    self.mock_organizations.GetEffectiveOrgPolicy.Expect(
        self.ExpectedEffectiveRequest(self.ORG_ARG), test_policy)
    self.mock_folders.GetEffectiveOrgPolicy.Expect(
        self.ExpectedEffectiveRequest(self.FOLDER_ARG), test_policy)
    self.assertEqual(self.DoEffectiveRequest(self.PROJECT_ARG), test_policy)
    self.assertEqual(self.DoEffectiveRequest(self.ORG_ARG), test_policy)
    self.assertEqual(self.DoEffectiveRequest(self.FOLDER_ARG), test_policy)

  def ExpectedEffectiveRequest(self, arg):
    m = self.messages
    if arg == self.PROJECT_ARG:
      return m.CloudresourcemanagerProjectsGetEffectiveOrgPolicyRequest(
          projectsId=self.PROJECT_ARG[1],
          getEffectiveOrgPolicyRequest=m.GetEffectiveOrgPolicyRequest(
              constraint=self.TEST_CONSTRAINT))
    elif arg == self.ORG_ARG:
      return m.CloudresourcemanagerOrganizationsGetEffectiveOrgPolicyRequest(
          organizationsId=self.ORG_ARG[1],
          getEffectiveOrgPolicyRequest=m.GetEffectiveOrgPolicyRequest(
              constraint=self.TEST_CONSTRAINT))
    elif arg == self.FOLDER_ARG:
      return m.CloudresourcemanagerFoldersGetEffectiveOrgPolicyRequest(
          foldersId=self.FOLDER_ARG[1],
          getEffectiveOrgPolicyRequest=m.GetEffectiveOrgPolicyRequest(
              constraint=self.TEST_CONSTRAINT))

  def DoRequest(self, args):
    return self.RunOrgPolicies('describe', self.TEST_CONSTRAINT, *args)

  def DoEffectiveRequest(self, args):
    return self.RunOrgPolicies('describe', '--effective', self.TEST_CONSTRAINT,
                               *args)


if __name__ == '__main__':
  test_case.main()
