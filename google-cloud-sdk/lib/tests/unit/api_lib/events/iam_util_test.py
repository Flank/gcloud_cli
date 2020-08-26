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
    self.account = 'test-account'
    self.mock_service_account = mock.Mock(
        email='test-account@fake-project.iam.gserviceaccount.com')
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

  def getOrCreate(self):
    return iam_util.GetOrCreateServiceAccountWithPrompt(
        self.account, 'Display Name', 'Description')

  def testGetsExistingAccount(self):
    self.get_service_account.return_value = self.mock_service_account

    result = self.getOrCreate()
    self.get_service_account.assert_called_once_with(self.account)
    self.assertFalse(self.create_service_account.called)
    self.assertEqual(result, self.mock_service_account.email)

  def testCreatesNewAccountWithoutPrompt(self):
    self.get_service_account.return_value = None
    self.create_service_account.return_value = self.mock_service_account

    result = self.getOrCreate()
    self.get_service_account.assert_called_once_with(self.account)
    self.create_service_account.assert_called_once_with(
        self.account, 'Display Name', 'Description')
    self.assertEqual(result, self.mock_service_account.email)

  def testCreatesNewAccountWithPrompt(self):
    self.get_service_account.return_value = None
    self.create_service_account.return_value = self.mock_service_account
    self.can_prompt.return_value = True

    result = self.getOrCreate()
    self.prompt_continue.assert_called_once_with(
        message='This will create service account [{}]'.format(
            self.mock_service_account.email),
        cancel_on_no=True)

    self.get_service_account.assert_called_once_with(self.account)
    self.create_service_account.assert_called_once_with(
        self.account, 'Display Name', 'Description')
    self.assertEqual(result, self.mock_service_account.email)


class TestPrintOrBindMissingRolesWithPrompt(cli_test_base.CliTestBase):

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
    iam_util.PrintOrBindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/pubsub.editor'], True)
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.assertFalse(self.bind_roles.called)

  def testHasAllRoles(self):
    self.get_roles.return_value = {'roles/role1', 'roles/role2'}
    iam_util.PrintOrBindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/role1'], True)
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.assertFalse(self.bind_roles.called)

  def testRolesNeedBindingNoPrompt(self):
    self.get_roles.return_value = {'roles/role1', 'roles/role2'}
    iam_util.PrintOrBindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/role1', 'roles/role3'], True)
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.bind_roles.assert_called_once_with(
        self.service_account_ref, {'roles/role3'})

  def testRolesNeedBindingOnlyPrintsWhenToldNotToBind(self):
    self.get_roles.return_value = {'roles/role1', 'roles/role2'}
    iam_util.PrintOrBindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/role1', 'roles/role3'], False)
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.assertFalse(self.bind_roles.called)
    self.AssertErrContains(
        'Service account [{}] is missing the following recommended roles:\n'
        '- roles/role3'.format(self.email, normalize_space=True))

  def testRolesNeedBindingWithPrompt(self):
    self.can_prompt.return_value = True

    self.get_roles.return_value = {'roles/role1', 'roles/role2'}
    iam_util.PrintOrBindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/role1', 'roles/role3', 'roles/role4'],
        True)
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.bind_roles.assert_called_once_with(
        self.service_account_ref, {'roles/role3', 'roles/role4'})
    self.AssertErrContains(
        'Service account [{}] is missing the following recommended roles:\n'
        '- roles/role3\n'
        '- roles/role4\n'.format(self.email), normalize_space=True)

  def testPubsubAdminCountsForPubsubEditor(self):
    self.get_roles.return_value = {'roles/pubsub.admin'}
    iam_util.PrintOrBindMissingRolesWithPrompt(
        self.service_account_ref, ['roles/pubsub.editor'], True)
    self.get_roles.assert_called_once_with(self.service_account_ref)
    self.assertFalse(self.bind_roles.called)
