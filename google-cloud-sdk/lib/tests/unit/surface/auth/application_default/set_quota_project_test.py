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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.core import config
from googlecloudsdk.core.credentials import creds
from tests.lib import cli_test_base
from tests.lib import test_case


def _GetJsonUserADC():
  return textwrap.dedent("""\
    {
      "client_id": "foo.apps.googleusercontent.com",
      "client_secret": "file-secret",
      "refresh_token": "file-token",
      "type": "authorized_user"
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


def _GetJsonServiceADC():
  return textwrap.dedent("""\
      {
        "client_email": "bar@developer.gserviceaccount.com",
        "client_id": "bar.apps.googleusercontent.com",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
        "private_key_id": "key-id",
        "type": "service_account"
      }""")


class SetQuotaProjectTests(cli_test_base.CliTestBase):

  def RunSetQuotaProject(self):
    self.Run('auth application-default set-quota-project fake-project')

  def SetUp(self):
    self.adc_file_path = os.path.join(self.temp_path,
                                      'application_default_credentials.json')
    self.StartObjectPatch(
        config, 'ADCFilePath', return_value=self.adc_file_path)
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.adc_permission_checking = self.StartObjectPatch(
        auth_util, 'AdcHasGivenPermissionOnProject', return_value=True)

  def testSetQuotaProject_NonExistingADC(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.BadFileException,
        'Application default credentials have not been set up'):
      self.RunSetQuotaProject()

  def testSetQuotaProject_ExistingUserCreds(self):
    creds.ADC(creds.FromJson(_GetJsonUserADC())).DumpADCToFile()
    self.RunSetQuotaProject()
    self.AssertFileEquals(_GetJsonUserExtendedADC(), self.adc_file_path)
    self.AssertErrContains('Quota project "fake-project" was added to ADC')

  def testSetQuotaProject_ExistingUserCreds_NoPermission(self):
    creds.ADC(creds.FromJson(_GetJsonUserADC())).DumpADCToFile()
    self.adc_permission_checking.return_value = False
    with self.AssertRaisesExceptionMatches(
        auth_util.MissingPermissionOnQuotaProjectError,
        'ADC does not have the "serviceusage.services.use" permission'):
      self.RunSetQuotaProject()

  def testSetQuotaProject_ExistingServiceCreds(self):
    creds.ADC(creds.FromJson(_GetJsonServiceADC())).DumpADCToFile()
    with self.AssertRaisesExceptionMatches(
        exceptions.BadFileException,
        'The application default credentials are not user credentials'):
      self.RunSetQuotaProject()


if __name__ == '__main__':
  test_case.main()
