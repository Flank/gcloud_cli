# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Tests for googlecloudsdk.core.credentials.creds."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import datetime
import json
import os
import textwrap

from googlecloudsdk.core import config
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case


from oauth2client import client
from oauth2client import crypt
from oauth2client import service_account


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


def _GetJsonP12ServiceADC():
  # Note that there is no such format, this is what gcloud uses to store it.
  return textwrap.dedent("""\
      {
        "client_email": "p12owner@developer.gserviceaccount.com",
        "password": "key-password",
        "private_key": "QkFTRTY0RU5DT0RFRA==",
        "type": "service_account_p12"
      }""")


class CredsSerializationTests(test_case.Base):

  def testToJson_UserAccount(self):
    json_data = _GetJsonUserADC()
    credentials = creds.FromJson(json_data)
    self.assertMultiLineEqual(json_data, creds.ToJson(credentials))

  def testToJson_ServiceAccount(self):
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    json_data = _GetJsonServiceADC()
    with files.TemporaryDirectory() as tmp_dir:
      cred_file = self.Touch(tmp_dir, contents=json_data)
      credentials = client.GoogleCredentials.from_stream(cred_file)

    self.assertMultiLineEqual(json_data, creds.ToJson(credentials))

  def testToJson_P12ServiceAccount(self):
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)
    json_data = _GetJsonP12ServiceADC()
    json_key = json.loads(json_data)

    credentials = (
        service_account.ServiceAccountCredentials._from_p12_keyfile_contents(
            service_account_email=json_key['client_email'],
            private_key_pkcs12=base64.b64decode(json_key['private_key']),
            private_key_password=json_key['password']))

    self.assertMultiLineEqual(json_data, creds.ToJson(credentials))

  def testFromJson_UserAccount(self):
    credentials = creds.FromJson(_GetJsonUserADC())
    self.assertEqual('foo.apps.googleusercontent.com', credentials.client_id)
    self.assertEqual('file-secret', credentials.client_secret)
    self.assertEqual('file-token', credentials.refresh_token)
    creds_type = creds.CredentialType.FromCredentials(credentials)
    self.assertEqual(creds.CredentialType.USER_ACCOUNT, creds_type)

  def testFromJson_ServiceAccount(self):
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    credentials = creds.FromJson(_GetJsonServiceADC())
    self.assertEqual('bar.apps.googleusercontent.com', credentials.client_id)
    self.assertEqual('bar@developer.gserviceaccount.com',
                     credentials._service_account_email)
    self.assertEqual('key-id', credentials._private_key_id)
    self.assertEqual(
        '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        credentials._private_key_pkcs8_pem)
    creds_type = creds.CredentialType.FromCredentials(credentials)
    self.assertEqual(creds.CredentialType.SERVICE_ACCOUNT, creds_type)

  def testFromJson_P12ServiceAccount(self):
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)

    credentials = creds.FromJson(_GetJsonP12ServiceADC())
    self.assertEqual('p12owner@developer.gserviceaccount.com',
                     credentials._service_account_email)
    self.assertEqual('key-password', credentials._private_key_password)
    self.assertEqual(b'BASE64ENCODED', credentials._private_key_pkcs12)

    creds_type = creds.CredentialType.FromCredentials(credentials)
    self.assertEqual(creds.CredentialType.P12_SERVICE_ACCOUNT, creds_type)


class StoreTests(sdk_test_base.SdkBase):

  def SetUp(self):
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)

  def _MakeCredentials(self):
    expiry = datetime.datetime(2001, 2, 3, 14, 15, 16)
    # client.GoogleCredentials cannot serialize token-expiry.
    # use OAuth2Credentials. We generaly do not store GoogleCredentials.
    # credentials = creds.FromJson(_GetJsonUserADC())
    return client.OAuth2Credentials(
        'access-token', 'client_id', 'client_secret',
        'fake-token', expiry, 'token_uri', 'user_agent',
        rapt_token='rapt_token5')

  def _MakeServiceAccountCredentials(self):
    expiry = datetime.datetime(2001, 2, 3, 14, 15, 16)
    credentials = creds.FromJson(_GetJsonServiceADC())
    credentials.access_token = 'access_token'
    credentials.token_expiry = expiry
    return credentials

  def _MakeP12ServiceAccountCredentials(self):
    expiry = datetime.datetime(2001, 2, 3, 14, 15, 16)
    credentials = creds.FromJson(_GetJsonP12ServiceADC())
    credentials.access_token = 'access_token'
    credentials.token_expiry = expiry
    return credentials

  def checkCredentialStore(self, expected_type):
    store_file = os.path.join(self.temp_path, 'credentials.db')
    access_token_file = os.path.join(self.temp_path, 'access_token.db')
    store = creds.GetCredentialStore(store_file, access_token_file)
    self.assertIsInstance(store, expected_type)
    self.assertEqual(set([]), store.GetAccounts())
    self.assertIsNone(store.Load('test_account'))
    store.Remove('test_account')  # Does nothing, does not fail.

    credentials = self._MakeCredentials()
    store.Store('test_account', credentials)
    service_account_credentials = self._MakeServiceAccountCredentials()
    store.Store('service_account', service_account_credentials)

    self.assertEqual({'test_account', 'service_account'}, store.GetAccounts())

    loaded_credentials = store.Load('test_account')
    self.assertEqual(credentials.client_id, loaded_credentials.client_id)
    self.assertEqual(credentials.client_secret,
                     loaded_credentials.client_secret)
    self.assertEqual('access-token', loaded_credentials.access_token)

    self.assertEqual(credentials.token_expiry, loaded_credentials.token_expiry)
    self.assertEqual('rapt_token5', loaded_credentials.rapt_token)

    store.Remove('test_account')
    self.assertEqual(set(['service_account']), store.GetAccounts())
    self.assertIsNone(store.Load('test_account'))
    loaded_service_account_credentials = store.Load('service_account')
    self.assertFalse(hasattr(loaded_service_account_credentials, 'rapt_token'))

  def AssertCredentialsEqual(self, expected_cred, actual_cred):
    self.assertEqual(type(expected_cred), type(actual_cred))
    fields = [
        'access_token',
        'client_id',
        'client_secret',
        'id_token',
        'invalid',
        'rapt_token',
        'refresh_token',
        'revoke_uri',
        'token_expiry',
        'token_response',
        'token_uri',
        'user_agent'
    ]
    for f in fields:
      expected_has, actual_has = (hasattr(expected_cred, f),
                                  hasattr(actual_cred, f))
      self.assertEqual(expected_has, actual_has, f)
      if expected_has:
        self.assertEqual(getattr(expected_cred, f), getattr(actual_cred, f), f)

  def testCredentialStoreWithCache(self):
    self.checkCredentialStore(creds.CredentialStoreWithCache)

  @test_case.Filters.DoNotRunOnWindows(
      'Checking file permissions in the Windows test env is non-trivial')
  def testCredentialStoreCreatedPrivate(self):
    """Tests that reading credentials creates the credential files private."""
    store_file = os.path.join(self.temp_path, 'credentials.db')
    access_token_file = os.path.join(self.temp_path, 'access_token.db')
    for path in (store_file, access_token_file):
      self.assertFalse(
          os.path.exists(path),
          'File [{}] should not exist already (test error)'.format(
              os.path.basename(path)))

    creds.GetCredentialStore(store_file, access_token_file)

    for path in (store_file, access_token_file):
      self.assertEqual(
          os.stat(store_file).st_mode & 0o777, 0o600,
          'File [{}] file should be created with 0o600 permissions'.format(
              os.path.basename(path)))

  @test_case.Filters.DoNotRunOnWindows(
      'Checking file permissions in the Windows test env is non-trivial')
  def testCredentialStoreChangesToPrivate(self):
    """Tests that reading credentials turns the credential files private."""
    store_file = os.path.join(self.temp_path, 'credentials.db')
    access_token_file = os.path.join(self.temp_path, 'access_token.db')
    creds.GetCredentialStore(store_file, access_token_file)

    for path in (store_file, access_token_file):
      # Open up the permissions to verify that they get changed back
      os.chmod(path, 0o777)

    creds.GetCredentialStore(store_file, access_token_file)

    for path in (store_file, access_token_file):
      self.assertEqual(
          os.stat(store_file).st_mode & 0o777, 0o600,
          'File [{}] should be changed back to 0o600 permissions'.format(
              os.path.basename(path)))

  def testMigrateMultistore2Sqlite(self):
    store = creds.Oauth2ClientCredentialStore(config.Paths().credentials_path)
    credentials = self._MakeCredentials()
    store.Store('test_account', credentials)

    service_account_credentials = self._MakeServiceAccountCredentials()
    store.Store('service_account', service_account_credentials)

    p12_service_account_credentials = self._MakeP12ServiceAccountCredentials()
    store.Store('p12_service_account', p12_service_account_credentials)
    self.AssertFileExists(config.Paths().credentials_path)

    store = creds.GetCredentialStore()
    self.AssertFileNotExists(config.Paths().credentials_path)
    self.AssertFileExists(config.Paths().credentials_db_path)

    self.AssertCredentialsEqual(credentials,
                                store.Load('test_account'))
    self.AssertCredentialsEqual(service_account_credentials,
                                store.Load('service_account'))
    self.AssertCredentialsEqual(p12_service_account_credentials,
                                store.Load('p12_service_account'))


class Sqlite3Tests(sdk_test_base.SdkBase, test_case.WithOutputCapture):

  def SetUp(self):
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)

  def testNoWarnMessage(self):
    creds.GetCredentialStore()
    self.AssertErrEquals('')

  def testSqliteBusyTimeoutSetting(self):
    store = creds.GetCredentialStore()
    with store._access_token_cache._cursor as cur:
      time_out = cur.Execute('PRAGMA busy_timeout;').fetchone()[0]
    self.assertEqual(1000, time_out)

  def testAttachAccessTokenCacheStore(self):
    access_token_cache = creds.AccessTokenCache(
        config.Paths().access_token_db_path)
    credentials = creds.FromJson(_GetJsonServiceADC())
    self.assertIsNone(credentials.access_token)
    access_token_cache.Store(
        credentials.service_account_email,
        access_token='token1',
        token_expiry=datetime.datetime.utcnow() +
        datetime.timedelta(seconds=3600),
        rapt_token=None)
    self.assertIsNone(credentials.access_token)
    new_cred = creds.MaybeAttachAccessTokenCacheStore(credentials)
    self.assertEqual('token1', new_cred.access_token)


if __name__ == '__main__':
  test_case.main()
