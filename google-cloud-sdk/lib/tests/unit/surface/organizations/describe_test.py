# Copyright 2016 Google Inc. All Rights Reserved.
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
from tests.lib.surface.organizations import testbase


class OrganizationsDescribeTest(testbase.OrganizationsUnitTestBase):

  def testDescribeValidOrganization(self):
    self.mock_client.organizations.Get.Expect(self.ExpectedRequest(),
                                              self.TEST_ORGANIZATION)
    self.assertEqual(self.DoRequest(), self.TEST_ORGANIZATION)

  def testDescribeNonexistantOrganization(self):
    self.SetupGetOrganizationFailure(self.HTTP_404_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'Organization [BAD_ID] not found: Resource not found.'):
      self.DoRequest()

  def testDescribeSecretOrganization(self):
    self.SetupGetOrganizationFailure(self.HTTP_403_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access organization [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount())):
      self.DoRequest()

  def ExpectedRequest(self):
    return self.messages.CloudresourcemanagerOrganizationsGetRequest(
        organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):])

  def SetupGetOrganizationFailure(self, exception):
    self.mock_client.organizations.Get.Expect(self.ExpectedRequest(),
                                              exception=exception)

  def DoRequest(self):
    return self.RunOrganizations(
        'describe', self.TEST_ORGANIZATION.name[len('organizations/'):])


if __name__ == '__main__':
  test_case.main()
