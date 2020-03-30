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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import test_case


class RevokeTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_get_wkf = self.StartPatch(
        'oauth2client.client._get_well_known_file')
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.mock_revoke_creds = self.StartObjectPatch(
        store, 'RevokeCredentials', autospec=True)

  def TempADCFile(self, test_filename):
    key_file_path = self.Resource('tests', 'unit', 'surface', 'auth',
                                  'test_data', test_filename)
    with open(key_file_path) as f:
      contents = f.read()
    return  self.Touch(self.root_path, contents=contents)

  def testRevokeNoADCFile(self):
    self.mock_get_wkf.return_value = 'NON_EXISTENT_FILE'

    self.Run('beta auth application-default revoke')
    self.AssertErrContains('nothing to revoke')

  def testRevokeServiceAccount(self):
    adcfilename = self.TempADCFile('adc_service_account.json')
    self.mock_get_wkf.return_value = adcfilename
    self.assertTrue(os.path.isfile(adcfilename))
    with self.assertRaises(c_exc.BadFileException):
      self.Run('beta auth application-default revoke')
    self.assertTrue(os.path.isfile(adcfilename))
    self.AssertErrContains('cannot be revoked')

  def testRevokeUserAccount(self):
    adcfilename = self.TempADCFile('adc_user_account.json')
    self.mock_get_wkf.return_value = adcfilename
    self.assertTrue(os.path.isfile(adcfilename))
    self.WriteInput('y\n')
    self.Run('beta auth application-default revoke')
    self.assertFalse(os.path.isfile(adcfilename))
    self.AssertErrContains('Credentials revoked.')


if __name__ == '__main__':
  test_case.main()
