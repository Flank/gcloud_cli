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
"""Unit tests for auth_util module."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib.core.credentials import credentials_test_base

from google.auth import crypt as google_auth_crypt


class TestAuthUtils(cli_test_base.CliTestBase,
                    credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.adc_file_path = os.path.join(self.temp_path,
                                      'application_default_credentials.json')
    self.mock_prompt = self.StartObjectPatch(auth_util,
                                             'PromptIfADCEnvVarIsSet')
    self.StartObjectPatch(
        config, 'ADCFilePath', return_value=self.adc_file_path)
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(creds, 'GetQuotaProject', return_value='my project')

    # Mocks the signer of google-auth credentials.
    self.StartObjectPatch(google_auth_crypt.RSASigner,
                          'from_service_account_info')

  def testWriteGcloudCredentialsToADC_UserCreds(self):
    auth_util.WriteGcloudCredentialsToADC(
        creds.FromJson(self.USER_CREDENTIALS_JSON))
    self.AssertErrEquals('')
    self.AssertFileEquals(self.USER_CREDENTIALS_JSON, self.adc_file_path)
    self.mock_prompt.assert_called()

  def testWriteGcloudCredentialsToADC_GoogleAuthUserCreds(self):
    auth_util.WriteGcloudCredentialsToADC(
        self.MakeUserAccountCredentialsGoogleAuth())
    self.AssertErrEquals('')
    self.AssertFileEquals(self.USER_CREDENTIALS_JSON, self.adc_file_path)
    self.mock_prompt.assert_called()

  def testWriteGcloudCredentialsToADC_UserCredsWithQuotaProject(self):
    auth_util.WriteGcloudCredentialsToADC(
        creds.FromJson(self.USER_CREDENTIALS_JSON), add_quota_project=True)
    self.AssertErrEquals('')
    self.AssertFileEquals(self.EXTENDED_USER_CREDENTIALS_JSON,
                          self.adc_file_path)
    self.mock_prompt.assert_called()

  def testWriteGcloudCredentialsToADC_ServiceCreds(self):
    auth_util.WriteGcloudCredentialsToADC(
        creds.FromJson(self.SERVICE_ACCOUNT_CREDENTIALS_JSON))
    self.AssertErrContains('Credentials cannot be written')
    self.AssertFileNotExists(self.adc_file_path)
    self.mock_prompt.assert_not_called()

  def testWriteGcloudCredentialsToADC_GoogleAuthServiceCreds(self):
    auth_util.WriteGcloudCredentialsToADC(
        self.MakeServiceAccountCredentialsGoogleAuth())
    self.AssertErrContains('Credentials cannot be written')
    self.AssertFileNotExists(self.adc_file_path)
    self.mock_prompt.assert_not_called()

  def testGetQuotaProjectFromADC_NoADCFile(self):
    self.assertIsNone(auth_util.GetQuotaProjectFromADC())

  def testGetQuotaProjectFromADC_NoQuotaProject(self):
    creds.ADC(creds.FromJson(self.USER_CREDENTIALS_JSON)).DumpADCToFile()
    self.assertIsNone(auth_util.GetQuotaProjectFromADC())

  def testGetQuotaProjectFromADC_GoogleAuthNoQuotaProject(self):
    creds.ADC(self.MakeUserAccountCredentialsGoogleAuth()).DumpADCToFile()
    self.assertIsNone(auth_util.GetQuotaProjectFromADC())

  def testGetQuotaProjectFromADC_QuotaProjectExists(self):
    creds.ADC(creds.FromJson(
        self.USER_CREDENTIALS_JSON)).DumpExtendedADCToFile()
    self.assertEqual(auth_util.GetQuotaProjectFromADC(), 'my project')

  def testGetQuotaProjectFromADC_GoogleAuthQuotaProjectExists(self):
    creds.ADC(
        self.MakeUserAccountCredentialsGoogleAuth()).DumpExtendedADCToFile()
    self.assertEqual(auth_util.GetQuotaProjectFromADC(), 'my project')


class TestAdcPermissionValidation(cli_test_base.CliTestBase,
                                  credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.adc_file_path = os.path.join(self.temp_path,
                                      'application_default_credentials.json')
    self.StartObjectPatch(
        config, 'ADCFilePath', return_value=self.adc_file_path)
    self.StartObjectPatch(store, 'Refresh')
    self.fake_project = 'fake-project'

  def SetUpApitoolsClientMock(self):
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1'),
        real_client=core_apis.GetClientInstance(
            'cloudresourcemanager', 'v1', no_http=True))
    self.messages = core_apis.GetMessagesModule('cloudresourcemanager', 'v1')
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testAdcHasGivenPermissionOnQuotaProject_NoAdc(self):
    with self.AssertRaisesExceptionMatches(
        c_exc.BadFileException,
        'Application default credentials have not been set up.'):
      auth_util.AdcHasGivenPermissionOnProject(self.fake_project,
                                               ['permission1'])

  def testAdcHasGivenPermissionOnQuotaProject_MissingPermission(self):
    self.SetUpApitoolsClientMock()
    auth_util.WriteGcloudCredentialsToADC(
        creds.FromJson(self.USER_CREDENTIALS_JSON))
    requested_permissions = ['storage.buckets.create', 'storage.buckets.delete']
    returned_permissions = ['storage.buckets.create']

    self.mock_client.projects.TestIamPermissions.Expect(
        self.messages.CloudresourcemanagerProjectsTestIamPermissionsRequest(
            resource=self.fake_project,
            testIamPermissionsRequest=self.messages.TestIamPermissionsRequest(
                permissions=requested_permissions)),
        self.messages.TestIamPermissionsResponse(
            permissions=returned_permissions))
    res = auth_util.AdcHasGivenPermissionOnProject(self.fake_project,
                                                   requested_permissions)
    self.assertFalse(res)

  def testAdcHasGivenPermissionOnQuotaProject_HasPermission(self):
    self.SetUpApitoolsClientMock()
    auth_util.WriteGcloudCredentialsToADC(
        creds.FromJson(self.USER_CREDENTIALS_JSON))
    requested_permissions = ['storage.buckets.create']
    expected_permissions = ['storage.buckets.create']

    self.mock_client.projects.TestIamPermissions.Expect(
        self.messages.CloudresourcemanagerProjectsTestIamPermissionsRequest(
            resource=self.fake_project,
            testIamPermissionsRequest=self.messages.TestIamPermissionsRequest(
                permissions=requested_permissions)),
        self.messages.TestIamPermissionsResponse(
            permissions=expected_permissions))
    res = auth_util.AdcHasGivenPermissionOnProject(self.fake_project,
                                                   requested_permissions)
    self.assertTrue(res)

  def testAdcHasGivenPermissionOnQuotaProject_LoadCredsFromAdc(self):
    properties.VALUES.auth.credential_file_override.Set(None)
    with self.AssertRaisesExceptionMatches(store.InvalidCredentialFileException,
                                           ''):
      auth_util._AdcHasGivenPermissionOnProjectHelper(self.fake_project,
                                                      ['permission1'])
    self.assertIsNone(properties.VALUES.auth.credential_file_override.Get())


class TestDumpAdcWithQuotaProject(cli_test_base.CliTestBase,
                                  credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.adc_permission_checking = self.StartObjectPatch(
        auth_util, 'AdcHasGivenPermissionOnProject')

    self.adc_file_path = os.path.join(self.temp_path,
                                      'application_default_credentials.json')
    self.StartObjectPatch(
        config, 'ADCFilePath', return_value=self.adc_file_path)
    self.fake_project = 'fake-project'

  def AssertQuotaProjectEquals(self, expected_quota_project):
    quota_project_in_adc = auth_util.GetQuotaProjectFromADC()
    self.assertEqual(expected_quota_project, quota_project_in_adc)

  def testDumpADCOptionalQuotaProject_NoQuotaProject(self):
    self.StartObjectPatch(creds, 'GetQuotaProject').return_value = None
    auth_util.DumpADCOptionalQuotaProject(self.MakeUserCredentials())
    auth_util.AssertADCExists()
    self.AssertQuotaProjectEquals(None)
    self.AssertErrContains('Credentials saved to file')
    self.AssertErrContains('Cannot find a quota project')
    self.adc_permission_checking.assert_not_called()

  def testDumpADCOptionalQuotaProject_WithPermission(self):
    self.StartObjectPatch(creds,
                          'GetQuotaProject').return_value = self.fake_project
    self.adc_permission_checking.return_value = True
    auth_util.DumpADCOptionalQuotaProject(self.MakeUserCredentials())
    auth_util.AssertADCExists()
    self.AssertQuotaProjectEquals(self.fake_project)
    self.AssertErrContains('Credentials saved to file')
    self.AssertErrContains('Quota project "{}" was added to ADC'.format(
        self.fake_project))
    self.adc_permission_checking.assert_called()

  def testDumpADCOptionalQuotaProject_WithoutPermission(self):
    self.StartObjectPatch(creds,
                          'GetQuotaProject').return_value = self.fake_project
    self.adc_permission_checking.return_value = False
    auth_util.DumpADCOptionalQuotaProject(self.MakeUserCredentials())
    auth_util.AssertADCExists()
    self.AssertQuotaProjectEquals(None)
    self.AssertErrContains('Credentials saved to file')
    self.AssertErrContains('Cannot add the project "{}" to ADC'.format(
        self.fake_project))
    self.adc_permission_checking.assert_called()

  def testDumpADCRequiredQuotaProject_NoADC(self):
    with self.AssertRaisesExceptionMatches(
        c_exc.BadFileException,
        'Application default credentials have not been set up'):
      auth_util.AddQuotaProjectToADC(self.fake_project)

  def testDumpADCRequiredQuotaProject_NotUserAccount(self):
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    creds.ADC(self.MakeServiceAccountCredentials()).DumpADCToFile()
    with self.AssertRaisesExceptionMatches(
        c_exc.BadFileException,
        'The application default credentials are not user credentials'):
      auth_util.AddQuotaProjectToADC(self.fake_project)

  def testDumpADCRequiredQuotaProject_WithPermission(self):
    self.adc_permission_checking.return_value = True
    auth_util.WriteGcloudCredentialsToADC(
        creds.FromJson(self.USER_CREDENTIALS_JSON))
    auth_util.AddQuotaProjectToADC(self.fake_project)
    auth_util.AssertADCExists()
    self.AssertQuotaProjectEquals(self.fake_project)
    self.AssertErrContains('Credentials saved to file')
    self.AssertErrContains('Quota project "{}" was added to ADC'.format(
        self.fake_project))
    self.adc_permission_checking.assert_called()

  def testDumpADCRequiredQuotaProject_WithoutPermission(self):
    self.adc_permission_checking.return_value = False
    auth_util.WriteGcloudCredentialsToADC(
        creds.FromJson(self.USER_CREDENTIALS_JSON))
    with self.AssertRaisesExceptionMatches(
        auth_util.MissingPermissionOnQuotaProjectError,
        'Cannot add the project "{}" to application default credentials'.format(
            self.fake_project)):
      auth_util.AddQuotaProjectToADC(self.fake_project)
    self.adc_permission_checking.assert_called()
