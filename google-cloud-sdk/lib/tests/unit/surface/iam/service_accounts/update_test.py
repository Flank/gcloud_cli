# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from tests.lib import cli_test_base
from tests.lib.surface.iam import unit_test_base


class UpdateTestGA(unit_test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _DoUpdateServiceAccount(self, command, service_account, run_asserts=True):
    service_account_name = self.get_service_account_name(
        self.Project(), service_account)
    self.client.projects_serviceAccounts.Patch.Expect(
        request=self.msgs.IamProjectsServiceAccountsPatchRequest(
            name=service_account_name,
            patchServiceAccountRequest=self.msgs.PatchServiceAccountRequest(
                updateMask='displayName',
                serviceAccount=self.msgs.ServiceAccount(
                    displayName='New Name'))),
        response=self.msgs.ServiceAccount(
            name=service_account_name, displayName='New Name'))

    self.Run(command)

    if run_asserts:
      self.AssertOutputContains('displayName: New Name')
      self.AssertOutputContains('name: ' + service_account_name)
      self.AssertErrEquals('Updated serviceAccount [%s].\n' % service_account)

  def get_service_account_name(self, project, service_account):
    return 'projects/{0}/serviceAccounts/{1}'.format(project, service_account)

  def testUpdateServiceAccount(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    command = ('iam service-accounts update --display-name "New Name" ' +
               service_account)
    self._DoUpdateServiceAccount(command, service_account)

  def testUpdateServiceAccountWithServiceAccount(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    command = ('iam service-accounts update --display-name "New Name" '
               '%s --account test2@test-project.iam.gserviceaccount.com' %
               service_account)
    self._DoUpdateServiceAccount(command, service_account)

  def testUpdateServiceAccountValidUniqueId(self):
    service_account = self.sample_unique_id
    command = ('iam service-accounts update --display-name "New Name" ' +
               service_account)
    try:
      self._DoUpdateServiceAccount(command, service_account, run_asserts=False)
    except cli_test_base.MockArgumentError:
      self.fail('update should accept unique ids for service accounts.')

  def testUpdateServiceAccountWithDisplayName(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    service_account_name = self.get_service_account_name(
        self.Project(), service_account)
    command = ('iam service-accounts update --display-name "New Name" ' +
               service_account)

    self.client.projects_serviceAccounts.Patch.Expect(
        request=self.msgs.IamProjectsServiceAccountsPatchRequest(
            name=service_account_name,
            patchServiceAccountRequest=self.msgs.PatchServiceAccountRequest(
                updateMask='displayName',
                serviceAccount=self.msgs.ServiceAccount(
                    displayName='New Name'))),
        response=self.msgs.ServiceAccount(
            name=service_account_name, displayName='New Name'))

    self.Run(command)

    self.AssertOutputContains('displayName: New Name')
    self.AssertOutputContains('name: ' + service_account_name)
    self.AssertErrEquals('Updated serviceAccount [%s].\n' % service_account)

  def testUpdateServiceAccountWithDescription(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    service_account_name = self.get_service_account_name(
        self.Project(), service_account)
    command = ('iam service-accounts update --description "New Description" ' +
               service_account)

    self.client.projects_serviceAccounts.Patch.Expect(
        request=self.msgs.IamProjectsServiceAccountsPatchRequest(
            name=service_account_name,
            patchServiceAccountRequest=self.msgs.PatchServiceAccountRequest(
                updateMask='description',
                serviceAccount=self.msgs.ServiceAccount(
                    description='New Description'))),
        response=self.msgs.ServiceAccount(
            name=service_account_name, description='New Description'))

    self.Run(command)

    self.AssertOutputContains('description: New Description')
    self.AssertOutputContains('name: ' + service_account_name)
    self.AssertErrEquals('Updated serviceAccount [%s].\n' % service_account)

  def testUpdateServiceAccountWithDisplayNameAndDescription(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    service_account_name = self.get_service_account_name(
        self.Project(), service_account)
    command = ('iam service-accounts update --display-name "New Name" '
               '--description "New Description" ' + service_account)

    self.client.projects_serviceAccounts.Patch.Expect(
        request=self.msgs.IamProjectsServiceAccountsPatchRequest(
            name=service_account_name,
            patchServiceAccountRequest=self.msgs.PatchServiceAccountRequest(
                updateMask='description,displayName',
                serviceAccount=self.msgs.ServiceAccount(
                    description='New Description', displayName='New Name'))),
        response=self.msgs.ServiceAccount(
            name=service_account_name,
            description='New Description',
            displayName='New Name'))

    self.Run(command)

    self.AssertOutputContains('displayName: New Name')
    self.AssertOutputContains('description: New Description')
    self.AssertOutputContains('name: ' + service_account_name)
    self.AssertErrEquals('Updated serviceAccount [%s].\n' % service_account)

  def testUpdateServiceAccountWithNoArgumentsShouldFail(self):
    service_account = 'test@test-project.iam.gserviceaccount.com'
    command = ('iam service-accounts update ' + service_account)

    with self.assertRaisesRegexp(
        gcloud_exceptions.OneOfArgumentsRequiredException,
        'Specify at least one field to update.'):
      self.Run(command)


class UpdateTestBeta(UpdateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class UpdateTestAlpha(UpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
