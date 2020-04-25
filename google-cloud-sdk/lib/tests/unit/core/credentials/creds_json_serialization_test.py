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
"""Tests for credentials serialization & deserialization to and from JSON."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import json
import textwrap

from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import reauth
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

from oauth2client import client
from oauth2client import crypt
from oauth2client import service_account
from google.auth import crypt as google_auth_crypt
from google.oauth2 import service_account as google_auth_service_account


class CredsSerializationTests(credentials_test_base.CredentialsTestBase):

  def testToJson_UserAccount(self):
    json_data = self.USER_CREDENTIALS_JSON
    credentials = creds.FromJson(json_data)
    self.assertMultiLineEqual(json_data, creds.ToJson(credentials))

  def testToJson_UserAccountGoogleAuth(self):
    credentials = self.MakeUserAccountCredentialsGoogleAuth()
    expected_json = textwrap.dedent("""\
        {
          "client_id": "foo.apps.googleusercontent.com",
          "client_secret": "file-secret",
          "refresh_token": "file-token",
          "revoke_uri": "https://accounts.google.com/o/oauth2/revoke",
          "scopes": [
            "scope1"
          ],
          "token_uri": "https://oauth2.googleapis.com/token",
          "type": "authorized_user"
        }""")

    self.assertMultiLineEqual(expected_json,
                              creds.ToJsonGoogleAuth(credentials))

  def testToJson_ServiceAccount(self):
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    json_data = self.SERVICE_ACCOUNT_CREDENTIALS_JSON
    with files.TemporaryDirectory() as tmp_dir:
      cred_file = self.Touch(tmp_dir, contents=json_data)
      credentials = client.GoogleCredentials.from_stream(cred_file)

    self.assertMultiLineEqual(json_data, creds.ToJson(credentials))

  def testToJson_ServiceAccountGoogleAuth(self):
    self.StartObjectPatch(google_auth_crypt.RSASigner,
                          'from_service_account_info')

    json_data = self.EXTENDED_SERVICE_ACCOUNT_CREDENTIALS_JSON

    # Generates google-auth credentials from json_data
    with files.TemporaryDirectory() as tmp_dir:
      cred_file = self.Touch(tmp_dir, contents=json_data)
      service_account_credentials = (
          google_auth_service_account.Credentials.from_service_account_file)
      credentials = service_account_credentials(cred_file)
      json_key = json.loads(json_data)
      # In the production code, the following fields are set by GCloud rather
      # by the google-auth lib.
      credentials.private_key = json_key.get('private_key')
      credentials.private_key_id = json_key.get('private_key_id')
      credentials.client_id = json_key.get('client_id')

    self.assertMultiLineEqual(json_data, creds.ToJsonGoogleAuth(credentials))

  def testToJson_P12ServiceAccount(self):
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)
    json_data = self.P12_SERVICE_ACCOUNT_CREDENTIALS_JSON
    json_key = json.loads(json_data)

    credentials = (
        service_account.ServiceAccountCredentials._from_p12_keyfile_contents(
            service_account_email=json_key['client_email'],
            private_key_pkcs12=base64.b64decode(json_key['private_key']),
            private_key_password=json_key['password']))

    self.assertMultiLineEqual(json_data, creds.ToJson(credentials))

  def testFromJson_UserAccount(self):
    credentials = creds.FromJson(self.USER_CREDENTIALS_JSON)

    self.AssertCredentialsEqual(
        credentials, {
            'client_id': 'foo.apps.googleusercontent.com',
            'client_secret': 'file-secret',
            'refresh_token': 'file-token'
        })

    creds_type = creds.CredentialType.FromCredentials(credentials)
    self.assertEqual(creds.CredentialType.USER_ACCOUNT, creds_type)

  def testFromJson_UserAccountGoogleAuth(self):
    json_blob = textwrap.dedent("""\
        {
          "client_id": "foo.apps.googleusercontent.com",
          "client_secret": "file-secret",
          "refresh_token": "file-token",
          "scopes": [
            "scope1"
          ],
          "token_uri": "https://oauth2.googleapis.com/token",
          "type": "authorized_user"
        }""")
    expected_credentials = creds.FromJsonGoogleAuth(json_blob)
    expected_credentials_dict = json.loads(json_blob)
    del expected_credentials_dict['type']
    self.assertIsInstance(expected_credentials, reauth.UserCredWithReauth)
    self.AssertCredentialsEqual(expected_credentials, expected_credentials_dict)

  def testFromJson_ServiceAccount(self):
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    credentials = creds.FromJson(self.SERVICE_ACCOUNT_CREDENTIALS_JSON)

    self.AssertCredentialsEqual(
        credentials, {
            'client_id':
                'bar.apps.googleusercontent.com',
            '_service_account_email':
                'bar@developer.gserviceaccount.com',
            '_private_key_id':
                'key-id',
            '_private_key_pkcs8_pem':
                '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        })

    creds_type = creds.CredentialType.FromCredentials(credentials)
    self.assertEqual(creds.CredentialType.SERVICE_ACCOUNT, creds_type)

  def testFromJson_ServiceAccountGoogleAuth(self):
    self.StartObjectPatch(google_auth_crypt.RSASigner,
                          'from_service_account_info')
    credentials = creds.FromJsonGoogleAuth(
        self.EXTENDED_SERVICE_ACCOUNT_CREDENTIALS_JSON)

    self.AssertCredentialsEqual(
        credentials, {
            'client_id':
                'bar.apps.googleusercontent.com',
            'service_account_email':
                'bar@developer.gserviceaccount.com',
            'private_key_id':
                'key-id',
            'private_key':
                '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
            'project_id':
                'bar-test',
            '_token_uri':
                'https://oauth2.googleapis.com/token',
        })

    creds_type = creds.CredentialTypeGoogleAuth.FromCredentials(credentials)
    self.assertEqual(creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT, creds_type)

  def testFromJson_P12ServiceAccount(self):
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)

    credentials = creds.FromJson(self.P12_SERVICE_ACCOUNT_CREDENTIALS_JSON)

    self.AssertCredentialsEqual(
        credentials, {
            '_service_account_email': 'p12owner@developer.gserviceaccount.com',
            '_private_key_password': 'key-password',
            '_private_key_pkcs12': b'BASE64ENCODED',
        })

    creds_type = creds.CredentialType.FromCredentials(credentials)
    self.assertEqual(creds.CredentialType.P12_SERVICE_ACCOUNT, creds_type)


if __name__ == '__main__':
  test_case.main()
