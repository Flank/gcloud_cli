# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class DeleteTest(unit_test_base.BaseTest):

  def testDeleteServiceAccount(self):
    self.client.projects_serviceAccounts.Delete.Expect(
        request=self.msgs.IamProjectsServiceAccountsDeleteRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com')),
        response=())

    self.Run(
        'iam service-accounts delete '
        'test@test-project.iam.gserviceaccount.com')

    self.AssertErrContains(
        'deleted service account [test@test-project.iam.gserviceaccount.com]')
    self.AssertErrNotContains('Not found: service account '
                              '[test@test-project.iam.gserviceaccount.com]')

  def testDeleteServiceAccountWithServiceAccount(self):
    self.client.projects_serviceAccounts.Delete.Expect(
        request=self.msgs.IamProjectsServiceAccountsDeleteRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com')),
        response=())

    self.Run(
        'iam service-accounts delete '
        'test@test-project.iam.gserviceaccount.com '
        '--account test2@test-project.iam.gserviceaccount.com')

    self.AssertErrContains(
        'deleted service account [test@test-project.iam.gserviceaccount.com]')
    self.AssertErrNotContains(
        'deleted service account [test2@test-project.iam.gserviceaccount.com]')
    self.AssertErrNotContains('Not found: service account '
                              '[test@test-project.iam.gserviceaccount.com]')

  def testDeleteInvalidName(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'Not a valid service account identifier. It should be either a '
        r'numeric string representing the unique_id or an email of the form: '
        r'my-iam-account@somedomain.com or '
        r'my-iam-account@PROJECT_ID.iam.gserviceaccount.com'):
      self.Run('iam service-accounts delete test')

  def testDeleteValidUniqueId(self):
    self.client.projects_serviceAccounts.Delete.Expect(
        request=self.msgs.IamProjectsServiceAccountsDeleteRequest(
            name='projects/-/serviceAccounts/' + self.sample_unique_id),
        response=())

    try:
      self.Run('iam service-accounts delete ' + self.sample_unique_id)
    except cli_test_base.MockArgumentError:
      self.fail('delete should accept unique ids for service accounts.')


if __name__ == '__main__':
  test_case.main()
