# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests of the events iam_util package."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.events import iam_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
import mock


class TestIAMAPICalls(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.msgs = apis.GetMessagesModule('iam', 'v1')

    self.client = apitools_mock.Client(
        client_class=apis.GetClientClass('iam', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

  def testProjectAndAccountNameToResource(self):
    self.assertEqual(
        iam_util._ProjectAndAccountNameToResource('myproject', 'myaccount'),
        'projects/myproject/serviceAccounts/myaccount@myproject.iam.gserviceaccount.com',
    )

  def testGetServiceAccountWhenExists(self):
    self.client.projects_serviceAccounts.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetRequest(
            name=('projects/fake-project/serviceAccounts/'
                  'test-account@fake-project.iam.gserviceaccount.com')),
        response=self.msgs.ServiceAccount(
            name=('projects/fake-project/serviceAccounts/'
                  'test-account@fake-project.iam.gserviceaccount.com'),
            projectId='fake-project',
            displayName='Test',
            email='test-account@fake-project.iam.gserviceaccount.com'))
    result = iam_util._GetServiceAccount('test-account')
    self.assertEqual(
        result.email, 'test-account@fake-project.iam.gserviceaccount.com')

  def testGetServiceAccountWhenMissing(self):
    self.client.projects_serviceAccounts.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetRequest(
            name=('projects/fake-project/serviceAccounts/'
                  'test-account@fake-project.iam.gserviceaccount.com')),
        exception=exceptions.HttpNotFoundError('', '', ''))
    result = iam_util._GetServiceAccount('test-account')
    self.assertIsNone(result)

  def testGetServiceAccountPropagatesOtherErrors(self):
    self.client.projects_serviceAccounts.Get.Expect(
        request=self.msgs.IamProjectsServiceAccountsGetRequest(
            name=('projects/fake-project/serviceAccounts/'
                  'test-account@fake-project.iam.gserviceaccount.com')),
        exception=exceptions.HttpError('', '', ''))
    with self.assertRaises(exceptions.HttpError):
      iam_util._GetServiceAccount('test-account')

  def testCreateServiceAccount(self):
    self.client.projects_serviceAccounts.Create.Expect(
        request=self.msgs.IamProjectsServiceAccountsCreateRequest(
            name='projects/fake-project',
            createServiceAccountRequest=self.msgs.CreateServiceAccountRequest(
                accountId='test-account',
                serviceAccount=self.msgs.ServiceAccount(
                    displayName='display name',
                    description='description'))),
        response=self.msgs.ServiceAccount(
            name=('projects/fake-project/serviceAccounts/'
                  'test-account@fake-project.iam.gserviceaccount.com'),
            projectId='fake-project',
            displayName='display name',
            email='test-account@fake-project.iam.gserviceaccount.com'))

    result = iam_util._CreateServiceAccount(
        'test-account', 'display name', 'description')
    self.assertEqual(
        result.email, 'test-account@fake-project.iam.gserviceaccount.com')


class TestGetOrCreateServiceAccountWithPrompt(cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_service_account = mock.Mock(
        email='test-account@fake-project.iam.gserviceaccount.com'
    )
    self.get_service_account = self.StartObjectPatch(
        iam_util,
        '_GetServiceAccount',
    )
    self.create_service_account = self.StartObjectPatch(
        iam_util,
        '_CreateServiceAccount',
    )
    self.can_prompt = self.StartObjectPatch(
        console_io,
        'CanPrompt',
        return_value=False,
    )
    self.prompt_continue = self.StartObjectPatch(
        console_io,
        'PromptContinue',
    )

  def testGetsExistingAccount(self):
    self.get_service_account.return_value = self.mock_service_account

    result = iam_util.GetOrCreateEventingServiceAccountWithPrompt()
    self.get_service_account.assert_called_once_with('cloud-run-events')
    self.assertFalse(self.create_service_account.called)
    self.assertEqual(result, self.mock_service_account.email)

  def testCreatesNewAccountWithoutPrompt(self):
    self.get_service_account.return_value = None
    self.create_service_account.return_value = self.mock_service_account

    result = iam_util.GetOrCreateEventingServiceAccountWithPrompt()
    self.get_service_account.assert_called_once_with('cloud-run-events')
    self.create_service_account.assert_called_once_with(
        'cloud-run-events', 'Cloud Run Events for Anthos',
        'Cloud Run Events on-cluster infrastructure')
    self.assertEqual(result, self.mock_service_account.email)

  def testCreatesNewAccountWithPrompt(self):
    self.get_service_account.return_value = None
    self.create_service_account.return_value = self.mock_service_account
    self.can_prompt.return_value = True

    result = iam_util.GetOrCreateEventingServiceAccountWithPrompt()
    email = 'cloud-run-events@fake-project.iam.gserviceaccount.com'
    self.prompt_continue.assert_called_once_with(
        message='\nThis will create service account [{}]'.format(email),
        cancel_on_no=True)

    self.get_service_account.assert_called_once_with('cloud-run-events')
    self.create_service_account.assert_called_once_with(
        'cloud-run-events', 'Cloud Run Events for Anthos',
        'Cloud Run Events on-cluster infrastructure')
    self.assertEqual(result, self.mock_service_account.email)


class TestBindMissingRolesWithPrompt(cli_test_base.CliTestBase):

  def SetUp(self):
    self.email = 'test-account@fake-project.iam.gserviceaccount.com'
    self.service_account_ref = resources.REGISTRY.Parse(
        self.email,
        params={'projectsId': '-'},
        collection='iam.projects.serviceAccounts'
    )

    self.get_roles = self.StartObjectPatch(
        iam_util,
        '_GetProjectRolesForServiceAccount',
    )
    self.bind_roles = self.StartObjectPatch(
        iam_util,
        '_BindProjectRolesForServiceAccount',
    )
    self.can_prompt = self.StartObjectPatch(
        console_io,
        'CanPrompt',
        return_value=False,
    )

  def accountHasOwnerRole(self):
    self.get_roles.return_value = {'roles/owner'}
    iam_util.BindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/pubsub.editor'])
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.assertFalse(self.bind_roles.called)

  def testHasAllRoles(self):
    self.get_roles.return_value = {'roles/role1', 'roles/role2'}
    iam_util.BindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/role1'])
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.assertFalse(self.bind_roles.called)

  def testRolesNeedBindingNoPrompt(self):
    self.get_roles.return_value = {'roles/role1', 'roles/role2'}
    iam_util.BindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/role1', 'roles/role3'])
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.bind_roles.assert_called_once_with(
        self.service_account_ref, {'roles/role3'})

  def testRolesNeedBindingWithPrompt(self):
    self.can_prompt.return_value = True

    self.get_roles.return_value = {'roles/role1', 'roles/role2'}
    iam_util.BindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/role1', 'roles/role3', 'roles/role4'])
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.bind_roles.assert_called_once_with(
        self.service_account_ref, {'roles/role3', 'roles/role4'})
    self.AssertErrContains(
        'This will bind the following project roles to the service account [test-account@fake-project.iam.gserviceaccount.com]:\\n'
        '- roles/role3\\n'
        '- roles/role4', normalize_space=True)

  def testPubsubAdminCountsForPubsubEditor(self):
    self.get_roles.return_value = {'roles/pubsub.admin'}
    iam_util.BindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/pubsub.editor'])
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.assertFalse(self.bind_roles.called)
