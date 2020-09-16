# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.auth import service_account
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

from google.oauth2 import service_account as google_auth_service_account


class ServiceAccountTest(credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.creds_dict = {
        'type': 'service_account',
        'client_email': 'bar@developer.gserviceaccount.com',
        'private_key_id': 'fake-private-key-id',
        'private_key': 'fake-private-key',
        'client_id': 'bar.apps.googleusercontent.com',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'project_id': 'fake-project-id'
    }

  def testCredentialsFromAdcDictGoogleAuth(self):
    creds = service_account.CredentialsFromAdcDictGoogleAuth(self.creds_dict)

    self.assertIsInstance(creds, google_auth_service_account.Credentials)
    self.AssertCredentialsEqual(
        creds, {
            'client_id': 'bar.apps.googleusercontent.com',
            'service_account_email': 'bar@developer.gserviceaccount.com',
            'private_key_id': 'fake-private-key-id',
            'private_key': 'fake-private-key',
            'project_id': 'fake-project-id',
            '_token_uri': 'https://oauth2.googleapis.com/token',
        })

  def testCredentialsFromAdcDictGoogleAuth_TokenUriNotProvided(self):
    """Verifies that missing 'token_uri' should not throw the creds creation."""
    del self.creds_dict['token_uri']
    creds = service_account.CredentialsFromAdcDictGoogleAuth(self.creds_dict)

    self.assertIsInstance(creds, google_auth_service_account.Credentials)
    self.AssertCredentialsEqual(
        creds, {
            'client_id': 'bar.apps.googleusercontent.com',
            'service_account_email': 'bar@developer.gserviceaccount.com',
            'private_key_id': 'fake-private-key-id',
            'private_key': 'fake-private-key',
            'project_id': 'fake-project-id',
            '_token_uri': 'https://oauth2.googleapis.com/token',
        })

  def testCredentialsFromAdcDictGoogleAuth_InputMissClientEmail(self):
    """Verifies that missing 'client_email' should fail the creds creation."""
    del self.creds_dict['client_email']

    with self.assertRaisesRegex(service_account.BadCredentialJsonFileException,
                                'The .json key file is not in a valid format.'):
      service_account.CredentialsFromAdcDictGoogleAuth(self.creds_dict)


if __name__ == '__main__':
  test_case.main()
