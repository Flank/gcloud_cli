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
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class ListTest(unit_test_base.BaseTest):

  def testListServiceAccountKeys(self):
    self.client.projects_serviceAccounts_keys.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysListRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
            keyTypes=iam_util.ManagedByFromString('any')),
        response=self.msgs.ListServiceAccountKeysResponse(keys=[
            self.msgs.ServiceAccountKey(
                name=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'
                      '/keys/abcdef1234567890'),
                validAfterTime='2015-09-30T09:35:00Z'),  # pyformat break
            self.msgs.ServiceAccountKey(
                name=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'
                      '/keys/deadbeefdeadbeef'),
                validAfterTime='2015-09-30T09:39:49Z')
        ]))

    self.Run('iam service-accounts keys list '
             '--iam-account test@test-project.iam.gserviceaccount.com')

    self.AssertOutputContains('abcdef1234567890')
    self.AssertOutputContains('2015-09-30T09:35:00Z')

    self.AssertOutputContains('deadbeefdeadbeef')
    self.AssertOutputContains('2015-09-30T09:39:49Z')

  def testCreatedBefore(self):
    self.client.projects_serviceAccounts_keys.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysListRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
            keyTypes=iam_util.ManagedByFromString('system')),
        response=self.msgs.ListServiceAccountKeysResponse(keys=[
            self.msgs.ServiceAccountKey(
                name=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'
                      '/keys/abcdef1234567890'),
                validAfterTime='2015-09-30T09:35:00Z'),  # pyformat break
            self.msgs.ServiceAccountKey(
                name=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'
                      '/keys/deadbeefdeadbeef'),
                validAfterTime='2015-09-30T09:39:49Z')
        ]))

    self.Run('iam service-accounts keys list --managed-by system '
             '--created-before 2015-09-30T09:36:00Z '
             '--iam-account test@test-project.iam.gserviceaccount.com')

    self.AssertOutputContains('abcdef1234567890')
    self.AssertOutputContains('2015-09-30T09:35:00Z')

    self.AssertOutputNotContains('deadbeefdeadbeef')
    self.AssertOutputNotContains('2015-09-30T09:39:49Z')

  def testFilterAllResults(self):
    self.client.projects_serviceAccounts_keys.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysListRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
            keyTypes=iam_util.ManagedByFromString('system')),
        response=self.msgs.ListServiceAccountKeysResponse(keys=[
            self.msgs.ServiceAccountKey(
                name=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'
                      '/keys/abcdef1234567890'),
                validAfterTime='2015-09-30T09:35:00Z'),  # pyformat break
            self.msgs.ServiceAccountKey(
                name=('projects/-/serviceAccounts/'
                      'test@test-project.iam.gserviceaccount.com'
                      '/keys/deadbeefdeadbeef'),
                validAfterTime='2015-09-30T09:39:49Z')
        ]))

    self.Run('iam service-accounts keys list --managed-by system '
             '--created-before 2000-01-01T00:00:00Z '
             '--iam-account test@test-project.iam.gserviceaccount.com')

    self.AssertOutputNotContains('abcdef1234567890')
    self.AssertOutputNotContains('2015-09-30T09:35:00Z')

    self.AssertOutputNotContains('deadbeefdeadbeef')
    self.AssertOutputNotContains('2015-09-30T09:39:49Z')

  def testNoResults(self):
    self.client.projects_serviceAccounts_keys.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysListRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
            keyTypes=iam_util.ManagedByFromString('system')),
        response=self.msgs.ListServiceAccountKeysResponse(keys=[]))

    self.Run('iam service-accounts keys list --managed-by system '
             '--iam-account test@test-project.iam.gserviceaccount.com')

    self.AssertOutputNotContains('abcdef1234567890')
    self.AssertOutputNotContains('2015-09-30T09:35:00Z')

    self.AssertOutputNotContains('deadbeefdeadbeef')
    self.AssertOutputNotContains('2015-09-30T09:39:49Z')

  def testListAccountKeysInvalidAccount(self):
    with self.assertRaisesRegexp(
        cli_test_base.MockArgumentError,
        r'Not a valid service account identifier. It should be either a '
        r'numeric string representing the unique_id or an email of the form: '
        r'my-iam-account@somedomain.com or '
        r'my-iam-account@PROJECT_ID.iam.gserviceaccount.com'):
      self.Run('iam service-accounts keys list --iam-account testfoo')

  def testListAccountKeysValidUniqueId(self):
    self.client.projects_serviceAccounts_keys.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsKeysListRequest(
            name='projects/-/serviceAccounts/' + self.sample_unique_id),
        response=self.msgs.ListServiceAccountKeysResponse())

    try:
      self.Run('iam service-accounts keys list --iam-account '
               + self.sample_unique_id)
    except cli_test_base.MockArgumentError:
      self.fail('list should accept unique ids for service accounts.')

if __name__ == '__main__':
  test_case.main()
