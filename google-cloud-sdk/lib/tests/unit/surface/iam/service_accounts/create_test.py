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

from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class CreateTest(unit_test_base.BaseTest):

  def testCreateServiceAccount(self):
    self.client.projects_serviceAccounts.Create.Expect(
        request=self.msgs.IamProjectsServiceAccountsCreateRequest(
            name='projects/test-project',
            createServiceAccountRequest=self.msgs.CreateServiceAccountRequest(
                accountId='test-account',
                serviceAccount=self.msgs.ServiceAccount(displayName='Test'))),
        response=self.msgs.ServiceAccount(
            name=('projects/test-project/serviceAccounts/'
                  'test-account@test-project.iam.gserviceaccount.com'),
            projectId='test-project',
            displayName='Test',
            email='test-account@test-project.iam.gserviceaccount.com'))
    self.Run('iam service-accounts create --display-name Test test-account')

    self.AssertOutputEquals('')
    self.AssertErrEquals('Created service account [test-account].\n')

  def testCreateServiceAccountFormat(self):
    self.client.projects_serviceAccounts.Create.Expect(
        request=self.msgs.IamProjectsServiceAccountsCreateRequest(
            name='projects/test-project',
            createServiceAccountRequest=self.msgs.CreateServiceAccountRequest(
                accountId='test-account',
                serviceAccount=self.msgs.ServiceAccount(displayName='Test'))),
        response=self.msgs.ServiceAccount(
            name=('projects/test-project/serviceAccounts/'
                  'test-account@test-project.iam.gserviceaccount.com'),
            projectId='test-project',
            displayName='Test',
            email='test-account@test-project.iam.gserviceaccount.com'))
    self.Run(
        'iam service-accounts create --display-name Test test-account '
        '--format=yaml')

    self.AssertOutputContains('projectId: test-project')
    self.AssertOutputContains('displayName: Test')
    self.AssertOutputContains(
        'name: projects/test-project/serviceAccounts/'
        'test-account@test-project.iam.gserviceaccount.com')
    self.AssertOutputContains(
        'email: test-account@test-project.iam.gserviceaccount.com')
    self.AssertErrEquals('Created service account [test-account].\n')


if __name__ == '__main__':
  test_case.main()
