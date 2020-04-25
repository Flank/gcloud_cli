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
"""Tests for SqliteCredentialStore."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import os

from googlecloudsdk.core.credentials import creds
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

from oauth2client import crypt
from google.auth import crypt as google_auth_crypt


class SqliteCredentialStoreTests(sdk_test_base.SdkBase,
                                 credentials_test_base.CredentialsTestBase):
  """Tests for SqliteCredentialStore.

  Tests of this class cover 4 cases:
  1. Stores with oauth2client creds and loads into oauth2client creds: an
     example of this case is gcloud reuses the same database entry before the
     store upgrades to support google-auth and runs commands that use
     oauth2client creds.
  2. Stores with oauth2client creds and loads into google-auth creds: an example
     of this case is gcloud reuses the same database entry before the store
     upgrades to support google-auth and runs commands that use google-auth
     creds.
  3. Stores with google-auth creds and loads into google-auth creds: an example
     of this case is gcloud re-signin after the store upgrades to support
     google-auth and runs commands that use google-auth creds.
  4. Stores with google-auth creds and loads into oauth2client creds: an example
     of this case is gcloud re-signin after the store upgrades to support
     google-auth and runs commands that use oauth2client creds.
  """

  def SetUp(self):
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)
    self.rsa_mock = self.StartObjectPatch(google_auth_crypt.RSASigner,
                                          'from_service_account_info')
    store_file = os.path.join(self.temp_path, 'credentials.db')
    self.store = creds.SqliteCredentialStore(store_file)
    self.fake_account = 'fake-account'

  def TestStoreOperations(self, creds_stored, load_google_auth,
                          creds_verification_func):
    """Test store operations.

    This test runs through the following steps:
    1. Verifies the store is intially empty.
    2. Stores credentials of an account and loads them back.
    3. Verifies the loaded credentials with the input verification function.
    4. Removes the credentials from the store and then verifies the store is
       empty.

    Args:
      creds_stored: google.auth.credentials.Credentials or
        client.OAuth2Credentials, The credentials to be stored.
      load_google_auth: bool, True to load google-auth credentials. False to
        load oauth2client credentials.
      creds_verification_func: function, The custom logic to verify the loaded
        credentials.
    """
    # Verifies that store is initially empty
    self.assertIsNone(self.store.Load(self.fake_account))
    self.assertCountEqual(self.store.GetAccounts(), set())

    # Stores the creds and loads it back
    self.store.Store(self.fake_account, creds_stored)
    creds_loaded = self.store.Load(self.fake_account, load_google_auth)

    # Verifies the loaded creds
    creds_verification_func(creds_loaded)
    self.assertCountEqual(self.store.GetAccounts(), set([self.fake_account]))

    # Removes the creds and verifies the store is empty
    self.store.Remove(self.fake_account)
    self.assertIsNone(self.store.Load(self.fake_account))
    self.assertCountEqual(self.store.GetAccounts(), set())

  def testStoreOauth2clientLoadOauth2client_UserAccountCreds(self):
    creds_stored = self.MakeUserCredentials()

    def VerifiyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialType.FromCredentials(creds_loaded)
      self.assertEqual(creds_type, creds.CredentialType.USER_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'client_id': 'client_id',
              'client_secret': 'client_secret',
              'refresh_token': 'fake-token',
              'token_uri': 'token_uri',
              'rapt_token': 'rapt_token5',
              'user_agent': 'user_agent',
          })

    self.TestStoreOperations(creds_stored, False, VerifiyLoadedCredentials)

  def testStoreOauth2clientLoadOauth2client_ServiceAccountCreds(self):
    creds_stored = self.MakeServiceAccountCredentials()

    def VerifiyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialType.FromCredentials(creds_loaded)
      self.assertEqual(creds_type, creds.CredentialType.SERVICE_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'client_id':
                  'bar.apps.googleusercontent.com',
              '_service_account_email':
                  'bar@developer.gserviceaccount.com',
              '_private_key_id':
                  'key-id',
              '_private_key_pkcs8_pem':
                  '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
          })

    self.TestStoreOperations(creds_stored, False, VerifiyLoadedCredentials)

  def testStoreOauth2clientLoadOauth2client_ServiceAccountP12Creds(self):
    creds_stored = self.MakeP12ServiceAccountCredentials()

    def VerifiyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialType.FromCredentials(creds_loaded)
      self.assertEqual(creds_type, creds.CredentialType.P12_SERVICE_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'service_account_email': 'p12owner@developer.gserviceaccount.com',
              '_private_key_password': 'key-password',
              '_private_key_pkcs12': base64.b64decode('QkFTRTY0RU5DT0RFRA=='),
          })

    self.TestStoreOperations(creds_stored, False, VerifiyLoadedCredentials)

  def testStoreOauth2clientLoadGoogleAuth_UserAccountCreds(self):
    creds_stored = self.MakeUserCredentials()

    def VerifiyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialTypeGoogleAuth.FromCredentials(creds_loaded)
      self.assertEqual(creds_type, creds.CredentialTypeGoogleAuth.USER_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'client_id': 'client_id',
              'client_secret': 'client_secret',
              'refresh_token': 'fake-token',
              'token_uri': creds._TOKEN_URI,
          })

    self.TestStoreOperations(creds_stored, True, VerifiyLoadedCredentials)

  def testStoreGoogleAuthLoadOauth2client_UserAccountCreds(self):
    creds_stored = self.MakeUserAccountCredentialsGoogleAuth()

    def VerifyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialType.FromCredentials(creds_loaded)
      self.assertEqual(creds_type, creds.CredentialType.USER_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'client_id': 'foo.apps.googleusercontent.com',
              'client_secret': 'file-secret',
              'refresh_token': 'file-token',
              'token_uri': creds._TOKEN_URI,
          })

    self.TestStoreOperations(creds_stored, False, VerifyLoadedCredentials)

  def testStoreGoogleAuthLoadGoogleAuth_UserAccountCreds(self):
    creds_stored = self.MakeUserAccountCredentialsGoogleAuth()

    def VerifyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialTypeGoogleAuth.FromCredentials(creds_loaded)
      self.assertEqual(creds_type, creds.CredentialTypeGoogleAuth.USER_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'client_id': 'foo.apps.googleusercontent.com',
              'client_secret': 'file-secret',
              'refresh_token': 'file-token',
              'token_uri': creds._TOKEN_URI,
          })

    self.TestStoreOperations(creds_stored, True, VerifyLoadedCredentials)

  def testStoreOauth2clientLoadGoogleAuth_ServiceAccountCreds(self):
    creds_stored = self.MakeServiceAccountCredentials()

    def VerifiyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialTypeGoogleAuth.FromCredentials(creds_loaded)
      self.assertEqual(creds_type,
                       creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'client_id':
                  'bar.apps.googleusercontent.com',
              'service_account_email':
                  'bar@developer.gserviceaccount.com',
              'private_key_id':
                  'key-id',
              'private_key':
                  '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
          })

    self.TestStoreOperations(creds_stored, True, VerifiyLoadedCredentials)

  def testStoreOauth2clientLoadGoogleAuth_ServiceAccountP12Creds(self):
    creds_stored = self.MakeP12ServiceAccountCredentials()

    def VerifiyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialType.FromCredentials(creds_loaded)
      self.assertEqual(creds_type, creds.CredentialType.P12_SERVICE_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'service_account_email': 'p12owner@developer.gserviceaccount.com',
              '_private_key_password': 'key-password',
              '_private_key_pkcs12': base64.b64decode('QkFTRTY0RU5DT0RFRA=='),
          })

    self.TestStoreOperations(creds_stored, True, VerifiyLoadedCredentials)

  def testStoreGoogleAuthLoadGoogleAuth_ServiceAccountCreds(self):
    creds_stored = self.MakeServiceAccountCredentialsGoogleAuth()

    def VerifiyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialTypeGoogleAuth.FromCredentials(creds_loaded)
      self.assertEqual(creds_type,
                       creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'client_id':
                  'bar.apps.googleusercontent.com',
              'service_account_email':
                  'bar@developer.gserviceaccount.com',
              'private_key_id':
                  'key-id',
              'private_key':
                  '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
              '_token_uri':
                  'https://oauth2.googleapis.com/token',
              'project_id':
                  'bar-test',
          })

    self.TestStoreOperations(creds_stored, True, VerifiyLoadedCredentials)

  def testStoreGoogleAuthLoadOauth2client_ServiceAccountCreds(self):
    creds_stored = self.MakeServiceAccountCredentialsGoogleAuth()

    def VerifiyLoadedCredentials(creds_loaded):
      creds_type = creds.CredentialType.FromCredentials(creds_loaded)
      self.assertEqual(creds_type, creds.CredentialType.SERVICE_ACCOUNT)
      self.AssertCredentialsEqual(
          creds_loaded, {
              'client_id':
                  'bar.apps.googleusercontent.com',
              '_service_account_email':
                  'bar@developer.gserviceaccount.com',
              '_private_key_id':
                  'key-id',
              '_private_key_pkcs8_pem':
                  '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
          })

    self.TestStoreOperations(creds_stored, False, VerifiyLoadedCredentials)


if __name__ == '__main__':
  test_case.main()
