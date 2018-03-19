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


class UpdateTest(unit_test_base.BaseTest):

  def _DoUpdateServiceAccount(self, command, service_account, run_asserts=True):
    self.client.projects_serviceAccounts.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetRequest(
            name='projects/-/serviceAccounts/' + service_account),
        response=self.msgs.ServiceAccount(etag='etag'))

    self.client.projects_serviceAccounts.Update.Expect(
        request=self.msgs.ServiceAccount(
            name=('projects/-/serviceAccounts/' + service_account),
            etag='etag',
            displayName='New Name'),
        response=
        self.msgs.ServiceAccount(
            email=service_account,
            name=('projects/-/serviceAccounts/' + service_account),
            projectId='test-project',
            displayName='New Name'))

    self.Run(command)

    if run_asserts:
      self.AssertOutputContains('projectId: test-project')
      self.AssertOutputContains('displayName: New Name')
      self.AssertOutputContains('email: ' + service_account)
      self.AssertOutputContains('name: projects/-/serviceAccounts/' +
                                service_account)
      self.AssertErrEquals('Updated service account [%s].\n' % service_account)

  def testUpdateServiceAccount(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    command = ('iam service-accounts update --display-name "New Name" '
               + service_account)
    self._DoUpdateServiceAccount(command, service_account)

  def testUpdateServiceAccountWithServiceAccount(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    command = ('iam service-accounts update --display-name "New Name" '
               '%s --account test2@test-project.iam.gserviceaccount.com'
               % service_account)
    self._DoUpdateServiceAccount(command, service_account)

  def testUpdateServiceAccountValidUniqueId(self):
    service_account = self.sample_unique_id
    command = ('iam service-accounts update --display-name "New Name" '
               + service_account)
    try:
      self._DoUpdateServiceAccount(command, service_account, run_asserts=False)
    except cli_test_base.MockArgumentError:
      self.fail('update should accept unique ids for service accounts.')

if __name__ == '__main__':
  test_case.main()
