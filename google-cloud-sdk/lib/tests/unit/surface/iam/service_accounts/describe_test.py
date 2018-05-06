# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests that ensure deserialization of server responses work properly."""


from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class DescribeTest(unit_test_base.BaseTest):

  def testDescribeServiceAccount(self):
    self.client.projects_serviceAccounts.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com')),
        response=self.msgs.ServiceAccount(
            name=('projects/test-project/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
            projectId='test-project',
            displayName='Test',
            email='test@test-project.iam.gserviceaccount.com'))
    self.Run(
        'iam service-accounts describe '
        'test@test-project.iam.gserviceaccount.com')

    self.AssertOutputContains('projectId: test-project')
    self.AssertOutputContains('displayName: Test')
    self.AssertOutputContains(
        'email: test@test-project.iam.gserviceaccount.com')
    self.AssertOutputContains('name: projects/test-project/serviceAccounts/'
                              'test@test-project.iam.gserviceaccount.com')

  def testDescribeServiceAccountWithServiceAccount(self):
    self.client.projects_serviceAccounts.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com')),
        response=self.msgs.ServiceAccount(
            name=('projects/test-project/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
            projectId='test-project',
            displayName='Test',
            email='test@test-project.iam.gserviceaccount.com'))
    self.Run(
        'iam service-accounts describe '
        'test@test-project.iam.gserviceaccount.com '
        '--account test2@test-project.iam.gserviceaccount.com')

    self.AssertOutputContains('projectId: test-project')
    self.AssertOutputContains('displayName: Test')
    self.AssertOutputContains(
        'email: test@test-project.iam.gserviceaccount.com')
    self.AssertOutputContains('name: projects/test-project/serviceAccounts/'
                              'test@test-project.iam.gserviceaccount.com')
    self.AssertOutputNotContains(
        'test2@test-project.iam.gserviceaccount.com')

  def testDescribeInvalidName(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'Not a valid service account identifier. It should be either a '
        r'numeric string representing the unique_id or an email of the form: '
        r'my-iam-account@somedomain.com or '
        r'my-iam-account@PROJECT_ID.iam.gserviceaccount.com'):
      self.Run('iam service-accounts describe test')

  def testDescribeValidUniqueId(self):
    self.client.projects_serviceAccounts.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetRequest(
            name=('projects/-/serviceAccounts/' + self.sample_unique_id)),
        response=self.msgs.ServiceAccount())
    try:
      self.Run('iam service-accounts describe ' + self.sample_unique_id)
    except cli_test_base.MockArgumentError:
      self.fail('describe should accept unique ids for service accounts.')


if __name__ == '__main__':
  test_case.main()
