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
import textwrap

from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.core import config
from googlecloudsdk.core.credentials import creds
from tests.lib import cli_test_base


def _GetJsonUserADC():
  return textwrap.dedent("""\
      {
        "client_id": "foo.apps.googleusercontent.com",
        "client_secret": "file-secret",
        "refresh_token": "file-token",
        "type": "authorized_user"
      }""")


def _GetJsonServiceADC():
  return textwrap.dedent("""\
      {
        "client_email": "bar@developer.gserviceaccount.com",
        "client_id": "bar.apps.googleusercontent.com",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
        "private_key_id": "key-id",
        "type": "service_account"
      }""")


def _GetJsonUserExtendedADC():
  return textwrap.dedent("""\
      {
        "client_id": "foo.apps.googleusercontent.com",
        "client_secret": "file-secret",
        "quota_project_id": "fake-project",
        "refresh_token": "file-token",
        "type": "authorized_user"
      }""")


class TestAuthUtils(cli_test_base.CliTestBase):

  def SetUp(self):
    self.adc_file_path = os.path.join(self.temp_path,
                                      'application_default_credentials.json')
    self.mock_prompt = self.StartObjectPatch(auth_util,
                                             'PromptIfADCEnvVarIsSet')
    self.StartObjectPatch(
        config, 'ADCFilePath', return_value=self.adc_file_path)
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)

  def testWriteGcloudCredentialsToADC_UserCreds(self):
    auth_util.WriteGcloudCredentialsToADC(creds.FromJson(_GetJsonUserADC()))
    self.AssertErrEquals('')
    self.AssertFileEquals(_GetJsonUserADC(), self.adc_file_path)
    self.mock_prompt.assert_called()

  def testWriteGcloudCredentialsToADC_UserCredsWithQuotaProject(self):
    auth_util.WriteGcloudCredentialsToADC(
        creds.FromJson(_GetJsonUserADC()), add_quota_project=True)
    self.AssertErrEquals('')
    self.AssertFileEquals(_GetJsonUserExtendedADC(), self.adc_file_path)
    self.mock_prompt.assert_called()

  def testWriteGcloudCredentialsToADC_ServiceCreds(self):
    auth_util.WriteGcloudCredentialsToADC(creds.FromJson(_GetJsonServiceADC()))
    self.AssertErrContains('Credentials cannot be written')
    self.AssertFileNotExists(self.adc_file_path)
    self.mock_prompt.assert_not_called()

  def testGetQuotaProjectFromADC_NoADCFile(self):
    self.assertIsNone(auth_util.GetQuotaProjectFromADC())

  def testGetQuotaProjectFromADC_NoQuotaProject(self):
    creds.ADC(creds.FromJson(_GetJsonUserADC())).DumpADCToFile()
    self.assertIsNone(auth_util.GetQuotaProjectFromADC())

  def testGetQuotaProjectFromADC_QuotaProjectExists(self):
    creds.ADC(creds.FromJson(_GetJsonUserADC())).DumpExtendedADCToFile()
    self.assertEqual(auth_util.GetQuotaProjectFromADC(), 'fake-project')
