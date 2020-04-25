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

from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.core import config
from googlecloudsdk.core.credentials import creds
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
