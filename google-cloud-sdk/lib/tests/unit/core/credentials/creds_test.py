# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

import datetime
import json
import os

from googlecloudsdk.core import config
from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import devshell
from googlecloudsdk.core.credentials import google_auth_credentials
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

import httplib2
import mock
from oauth2client import client
from oauth2client.contrib import gce
from six.moves import http_client as httplib
import sqlite3
from google.auth import compute_engine as google_auth_gce
from google.auth import crypt as google_auth_crypt
from google.oauth2 import service_account as google_auth_service_account


_FAKE_CREDENTIALS_REFRESH_RESPONSE_CONTENT = (
    b'{"access_token": "REFRESHED-ACCESS-TOKEN","expires_in": 3599}')


def _MakeFakeOauth2clientCredsRefreshResponse():
  """Returns a fake response for oauth2client credentials refresh."""
  response = httplib2.Response({'status': httplib.OK})
  content = _FAKE_CREDENTIALS_REFRESH_RESPONSE_CONTENT
  return response, content


def _MakeFakeGoogleAuthCredsRefreshResponse():
  """Returns a fake response for google-auth credentials refresh."""
  return mock.Mock(
      status_code=httplib.OK,
      content=_FAKE_CREDENTIALS_REFRESH_RESPONSE_CONTENT)


def _RefreshCredentials(credentials):
  """Refreshes the input credentials.

  Different logic will be executed for oauth2client and google-auth
  credentials.

  Args:
    credentials: google.auth.credentials.Credentials or
      client.OAuth2Credentials, the credentials to refresh.
  """
  if isinstance(credentials, client.OAuth2Credentials):
    credentials.refresh(httplib2.Http())
  else:
    credentials.refresh(http.GoogleAuthRequest())


def _RefreshCredentialsDict(creds_dict):
  """Updates the credentials dict with the refreshed access token."""
  if 'access_token' in creds_dict:  # oauth2client credentials
    creds_dict['access_token'] = 'REFRESHED-ACCESS-TOKEN'
  else:  # google-auth credentials
    creds_dict['token'] = 'REFRESHED-ACCESS-TOKEN'


class StoreOperationsTests(sdk_test_base.SdkBase,
                           credentials_test_base.CredentialsTestBase):
  """Tests for credentials store operations.

  The store that is tested by this class is built by creds.GetCredentialStore(),
  and is an instance of CredentialStoreWithCache. This class covers the
  following 4 cases,
  1. Stores oauth2client creds and refreshes the creds loaded with
     'use_google_auth' to be False.
  2. Stores oauth2client creds and refreshes the creds loaded with
     'use_google_auth' to be True.
  3. Stores google-auth creds and refreshes the creds loaded with
     'use_google_auth' to be True.
  4. Stores google-auth creds and refreshes the creds loaded with
     'use_google_auth' to be False.
  """

  def SetUp(self):
    store_file = os.path.join(self.temp_path, 'credentials.db')
    access_token_file = os.path.join(self.temp_path, 'access_token.db')
    self.store = creds.GetCredentialStore(store_file, access_token_file)
    self.fake_account = 'test_account'

    # Mocks the refresh of oauth2client credentials.
    self.StartObjectPatch(
        httplib2.Http,
        'request',
        return_value=_MakeFakeOauth2clientCredsRefreshResponse())

  def TestStoreOperations(self, creds_stored, expected_loaded_type,
                          expected_loaded_type_google_auth,
                          expected_loaded_dict,
                          expected_loaded_dict_google_auth,
                          refresh_google_auth):
    """Tests credentials store operations.

    This test runs through the following steps:
    1. Creates a credentials store and verifies it is initially empty.
    2. Stores creds_stored and verifies.
    3. Loads two credentials from the store with 'use_google_auth' to be False
       and True respectively. Verifies the loaded credentials.
    4. Refreshes one of the loaded credentials which will populate the access
       token cache with the refreshed access token.
    5. Loads another two credentials from the store and verifies the access
       tokens of both are updated correctly.
    6. Removes the credentials from the store and verifies the store is empty.

    Args:
      creds_stored: google.auth.credentials.Credentials or
        client.OAuth2Credentials, the credentials to be stored.
      expected_loaded_type: creds.CredentialType, the expected type of the
        credentials loaded with 'use_google_auth' to be False.
      expected_loaded_type_google_auth: creds.CredentialTypeGoogleAuth or
        creds.CredentialType, the expected type of the credentials loaded with
        'use_google_auth' to be True. If the credentials type is not supported
        in the cache, for example, P12 service account credentials, the value of
        this argument will be creds.CredentialType. Otherwise, the argument will
        be creds.CredentialTypeGoogleAuth.
      expected_loaded_dict: dict, the expected values of the credentials loaded
        with 'use_google_auth' to be False, in the form of a dict.
      expected_loaded_dict_google_auth: dict, the expected values of the
        credentials loaded with 'use_google_auth' to be True, in the form of a
        dict.
      refresh_google_auth: bool, True to refresh the credentials loaded with
        'use_google_auth' to be True. False to refresh the credentials loaded
        with 'use_google_auth' to be False.
    """
    # Verifies the store is initially empty.
    self.assertIsInstance(self.store, creds.CredentialStoreWithCache)
    self.assertEqual(self.store.GetAccounts(), set([]))
    self.assertIsNone(self.store.Load(self.fake_account))
    self.store.Remove(self.fake_account)  # Verifies removal does not throws

    # Stores credentials and verifies.
    self.store.Store(self.fake_account, creds_stored)
    self.assertEqual(self.store.GetAccounts(), {self.fake_account})

    # Loads two credentials with 'use_google_auth' to be False and True
    # respectively. Verifies the loaded credentials against the expectations.
    creds_loaded = self.store.Load(self.fake_account)
    creds_loaded_use_google_auth = self.store.Load(self.fake_account, True)
    self.AssertCredentials(creds_loaded, expected_loaded_type,
                           expected_loaded_dict, True)
    self.AssertCredentials(creds_loaded_use_google_auth,
                           expected_loaded_type_google_auth,
                           expected_loaded_dict_google_auth, True)

    # Refreshes loaded credentials. This will update the access token cache
    # with the refreshed access token.
    if refresh_google_auth:
      _RefreshCredentials(creds_loaded_use_google_auth)
    else:
      _RefreshCredentials(creds_loaded)

    # Loads another two credentials with 'use_google_auth' to be False and True
    # respectively. Verifies the both credentials have the refreshed access
    # token.
    creds_loaded = self.store.Load(self.fake_account)
    creds_loaded_use_google_auth = self.store.Load(self.fake_account, True)
    _RefreshCredentialsDict(expected_loaded_dict)
    _RefreshCredentialsDict(expected_loaded_dict_google_auth)
    self.AssertCredentials(creds_loaded, expected_loaded_type,
                           expected_loaded_dict, False)
    self.AssertCredentials(creds_loaded_use_google_auth,
                           expected_loaded_type_google_auth,
                           expected_loaded_dict_google_auth, False)

    # Removes the credentials from the store and verifies.
    self.store.Remove(self.fake_account)
    self.assertEqual(self.store.GetAccounts(), set([]))
    self.assertIsNone(self.store.Load(self.fake_account))

  def testStoreOauth2client_RefreshOauth2client_UserCreds(self):
    creds_stored = self.MakeUserCredentials()
    expected_loaded_type = creds.CredentialType.USER_ACCOUNT
    expected_loaded_type_google_auth = creds.CredentialTypeGoogleAuth.USER_ACCOUNT
    expected_loaded_dict = {
        'access_token': 'access-token',
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'fake-token',
        'token_uri': 'token_uri',
        'rapt_token': 'rapt_token5',
        'user_agent': 'user_agent',
    }
    expected_loaded_dict_google_auth = {
        'token': 'access-token',
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'fake-token',
        'token_uri': 'token_uri',
        'rapt_token': 'rapt_token5',
    }
    refresh_google_auth = False

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreOauth2client_RefreshOauth2client_ServiceAccountCreds(self):
    creds_stored = self.MakeServiceAccountCredentials()
    expected_loaded_type = creds.CredentialType.SERVICE_ACCOUNT
    expected_loaded_type_google_auth = (
        creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT)
    expected_loaded_dict = {
        'access_token':
            'access_token',
        'service_account_email':
            'bar@developer.gserviceaccount.com',
        'client_id':
            'bar.apps.googleusercontent.com',
        '_private_key_id':
            'key-id',
        '_private_key_pkcs8_pem':
            '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        'token_uri':
            'https://oauth2.googleapis.com/token'
    }
    expected_loaded_dict_google_auth = {
        'token':
            'access_token',
        'service_account_email':
            'bar@developer.gserviceaccount.com',
        'client_id':
            'bar.apps.googleusercontent.com',
        'private_key':
            '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        'private_key_id':
            'key-id',
        '_token_uri':
            'https://oauth2.googleapis.com/token'
    }
    refresh_google_auth = False

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreOauth2client_RefreshOauth2client_P12ServiceAccountCreds(self):
    creds_stored = self.MakeP12ServiceAccountCredentials()
    expected_loaded_type = creds.CredentialType.P12_SERVICE_ACCOUNT
    # P12 servivce account creds are not supported by google-auth.
    expected_loaded_type_google_auth = (
        creds.CredentialType.P12_SERVICE_ACCOUNT)
    expected_loaded_dict = {
        'access_token': 'access_token',
        'service_account_email': 'p12owner@developer.gserviceaccount.com',
        '_private_key_pkcs12': b'BASE64ENCODED',
        '_private_key_password': 'key-password',
        'token_uri': 'https://oauth2.googleapis.com/token'
    }
    expected_loaded_dict_google_auth = expected_loaded_dict.copy()
    refresh_google_auth = False

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreOauth2client_RefreshGoogleAuth_UserCreds(self):
    creds_stored = self.MakeUserCredentials()
    expected_loaded_type = creds.CredentialType.USER_ACCOUNT
    expected_loaded_type_google_auth = creds.CredentialTypeGoogleAuth.USER_ACCOUNT
    expected_loaded_dict = {
        'access_token': 'access-token',
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'fake-token',
        'token_uri': 'token_uri',
        'rapt_token': 'rapt_token5',
        'user_agent': 'user_agent',
    }
    expected_loaded_dict_google_auth = {
        'token': 'access-token',
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'fake-token',
        'token_uri': 'token_uri',
        'rapt_token': 'rapt_token5',
    }
    refresh_google_auth = True

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreGoogleAuth_RefreshOauth2client_UserCreds(self):
    creds_stored = self.MakeUserAccountCredentialsGoogleAuth()
    expected_loaded_type = creds.CredentialType.USER_ACCOUNT
    expected_loaded_type_google_auth = creds.CredentialTypeGoogleAuth.USER_ACCOUNT
    expected_loaded_dict = {
        'access_token': None,
        'client_id': 'foo.apps.googleusercontent.com',
        'client_secret': 'file-secret',
        'refresh_token': 'file-token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'scopes': set(['scope1'])
    }
    expected_loaded_dict_google_auth = {
        'token': None,
        'client_id': 'foo.apps.googleusercontent.com',
        'client_secret': 'file-secret',
        'refresh_token': 'file-token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'scopes': ['scope1']
    }
    refresh_google_auth = False

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreGoogleAuth_RefreshGoogleAuth_UserCreds(self):
    creds_stored = self.MakeUserAccountCredentialsGoogleAuth()
    expected_loaded_type = creds.CredentialType.USER_ACCOUNT
    expected_loaded_type_google_auth = creds.CredentialTypeGoogleAuth.USER_ACCOUNT
    expected_loaded_dict = {
        'access_token': None,
        'client_id': 'foo.apps.googleusercontent.com',
        'client_secret': 'file-secret',
        'refresh_token': 'file-token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'scopes': set(['scope1'])
    }
    expected_loaded_dict_google_auth = {
        'token': None,
        'client_id': 'foo.apps.googleusercontent.com',
        'client_secret': 'file-secret',
        'refresh_token': 'file-token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'scopes': ['scope1']
    }
    refresh_google_auth = True

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreOauth2client_RefreshGoogleAuth_ServiceAccountCreds(self):
    creds_stored = self.MakeServiceAccountCredentials()
    expected_loaded_type = creds.CredentialType.SERVICE_ACCOUNT
    expected_loaded_type_google_auth = (
        creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT)
    expected_loaded_dict = {
        'access_token':
            'access_token',
        'service_account_email':
            'bar@developer.gserviceaccount.com',
        'client_id':
            'bar.apps.googleusercontent.com',
        '_private_key_id':
            'key-id',
        '_private_key_pkcs8_pem':
            '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        'token_uri':
            'https://oauth2.googleapis.com/token'
    }
    expected_loaded_dict_google_auth = {
        'token':
            'access_token',
        'service_account_email':
            'bar@developer.gserviceaccount.com',
        'client_id':
            'bar.apps.googleusercontent.com',
        'private_key':
            '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        'private_key_id':
            'key-id',
        '_token_uri':
            'https://oauth2.googleapis.com/token'
    }
    refresh_google_auth = True

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreOauth2client_RefreshGoogleAuth_P12ServiceAccountCreds(self):
    creds_stored = self.MakeP12ServiceAccountCredentials()
    expected_loaded_type = creds.CredentialType.P12_SERVICE_ACCOUNT
    # P12 servivce account creds are not supported by google-auth.
    expected_loaded_type_google_auth = (
        creds.CredentialType.P12_SERVICE_ACCOUNT)
    expected_loaded_dict = {
        'access_token': 'access_token',
        'service_account_email': 'p12owner@developer.gserviceaccount.com',
        '_private_key_pkcs12': b'BASE64ENCODED',
        '_private_key_password': 'key-password',
        'token_uri': 'https://oauth2.googleapis.com/token'
    }
    expected_loaded_dict_google_auth = expected_loaded_dict.copy()
    refresh_google_auth = True

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreGoogleAuth_RefreshGoogleAuth_ServiceAccountCreds(self):
    creds_stored = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_loaded_type = creds.CredentialType.SERVICE_ACCOUNT
    expected_loaded_type_google_auth = (
        creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT)
    expected_loaded_dict = {
        'access_token':
            'access_token',
        'id_tokenb64':
            'id-token',
        'service_account_email':
            'bar@developer.gserviceaccount.com',
        'client_id':
            'bar.apps.googleusercontent.com',
        '_private_key_id':
            'key-id',
        '_private_key_pkcs8_pem':
            '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        'token_uri':
            'https://oauth2.googleapis.com/token'
    }
    expected_loaded_dict_google_auth = {
        'token':
            'access_token',
        'id_tokenb64':
            'id-token',
        '_id_token':
            'id-token',
        'service_account_email':
            'bar@developer.gserviceaccount.com',
        'client_id':
            'bar.apps.googleusercontent.com',
        'private_key':
            '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        'private_key_id':
            'key-id',
        'project_id':
            'bar-test',
        '_token_uri':
            'https://oauth2.googleapis.com/token'
    }
    refresh_google_auth = True

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)

  def testStoreGoogleAuth_RefreshOauth2client_ServiceAccountCreds(self):
    creds_stored = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_loaded_type = creds.CredentialType.SERVICE_ACCOUNT
    expected_loaded_type_google_auth = (
        creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT)
    expected_loaded_dict = {
        'access_token':
            'access_token',
        'service_account_email':
            'bar@developer.gserviceaccount.com',
        'client_id':
            'bar.apps.googleusercontent.com',
        '_private_key_id':
            'key-id',
        '_private_key_pkcs8_pem':
            '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        'token_uri':
            'https://oauth2.googleapis.com/token'
    }
    expected_loaded_dict_google_auth = {
        'token':
            'access_token',
        'service_account_email':
            'bar@developer.gserviceaccount.com',
        'client_id':
            'bar.apps.googleusercontent.com',
        'private_key':
            '-----BEGIN PRIVATE KEY-----\nasdf\n-----END PRIVATE KEY-----\n',
        'private_key_id':
            'key-id',
        'project_id':
            'bar-test',
        '_token_uri':
            'https://oauth2.googleapis.com/token'
    }
    refresh_google_auth = False

    self.TestStoreOperations(creds_stored, expected_loaded_type,
                             expected_loaded_type_google_auth,
                             expected_loaded_dict,
                             expected_loaded_dict_google_auth,
                             refresh_google_auth)


class StoreCreationConcurrencyTests(sdk_test_base.SdkBase):
  """Concurrency tests of credentials store creation process.

  The store that is tested by this class is built by creds.GetCredentialStore().
  """

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


class Sqlite3Tests(sdk_test_base.WithLogCapture,
                   credentials_test_base.CredentialsTestBase):

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
    credentials = creds.FromJson(self.SERVICE_ACCOUNT_CREDENTIALS_JSON)
    credentials.token_response = json.loads("""{"id_token": "woweee"}""")
    self.assertIsNone(credentials.access_token)
    access_token_cache.Store(
        credentials.service_account_email,
        access_token='token1',
        token_expiry=datetime.datetime.utcnow() +
        datetime.timedelta(seconds=3600),
        rapt_token=None,
        id_token=None)
    self.assertIsNone(credentials.access_token)
    new_cred = creds.MaybeAttachAccessTokenCacheStore(credentials)
    self.assertIsNone(new_cred.token_response)
    self.assertEqual('token1', new_cred.access_token)

  def testAttachAccessTokenCacheStoreGoogleAuth(self):
    # Create credentials.
    credentials = google_auth_service_account.Credentials(
        None, 'email', 'token_uri')
    self.assertIsNone(credentials.token)

    # Create access token cache.
    access_token_cache = creds.AccessTokenCache(
        config.Paths().access_token_db_path)
    access_token_cache.Store(
        credentials.service_account_email,
        access_token='token1',
        token_expiry=datetime.datetime.utcnow() +
        datetime.timedelta(seconds=3600),
        rapt_token=None,
        id_token=None)

    # Attach access token cache store to credentials.
    new_creds = creds.MaybeAttachAccessTokenCacheStoreGoogleAuth(credentials)
    self.assertEqual(new_creds.token, 'token1')

  def testAccessTokenCacheReadonlyStore(self):
    access_token_cache = creds.AccessTokenCache(
        config.Paths().access_token_db_path)
    credentials = creds.FromJson(self.SERVICE_ACCOUNT_CREDENTIALS_JSON)
    credentials.token_response = json.loads("""{"id_token": "woweee"}""")
    self.assertIsNone(credentials.access_token)
    self.StartObjectPatch(
        access_token_cache,
        '_Execute',
        side_effect=sqlite3.OperationalError(
            'attempt to write to read-only database'))
    access_token_cache.Store(
        credentials.service_account_email,
        access_token='token1',
        token_expiry=datetime.datetime.utcnow() +
        datetime.timedelta(seconds=3600),
        rapt_token=None,
        id_token=None)
    self.AssertLogContains('Could not store access token in cache: '
                           'attempt to write to read-only database')

  def testAccessTokenCacheReadonlyRemove(self):
    access_token_cache = creds.AccessTokenCache(
        config.Paths().access_token_db_path)
    credentials = creds.FromJson(self.SERVICE_ACCOUNT_CREDENTIALS_JSON)
    self.StartObjectPatch(
        access_token_cache,
        '_Execute',
        side_effect=sqlite3.OperationalError(
            'attempt to write to read-only database'))
    access_token_cache.Remove(credentials.service_account_email)
    self.AssertLogContains('Could not delete access token from cache: '
                           'attempt to write to read-only database')


class ADCTestsOauth2client(cli_test_base.CliTestBase,
                           credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.adc_file_path = os.path.join(self.temp_path,
                                      'application_default_credentials.json')
    self.StartObjectPatch(
        config, 'ADCFilePath', return_value=self.adc_file_path)

    self.user_creds = creds.FromJson(self.USER_CREDENTIALS_JSON)
    self.service_creds = creds.FromJson(self.SERVICE_ACCOUNT_CREDENTIALS_JSON)
    self.p12_service_creds = self.MakeP12ServiceAccountCredentials()

  def testDumpADCToFile_UserCreds(self):
    adc = creds.ADC(self.user_creds)
    adc.DumpADCToFile()
    self.AssertFileEquals(self.USER_CREDENTIALS_JSON, self.adc_file_path)

  def testDumpADCToFile_ServiceCreds(self):
    adc = creds.ADC(self.service_creds)
    adc.DumpADCToFile()
    self.AssertFileEquals(self.SERVICE_ACCOUNT_CREDENTIALS_JSON,
                          self.adc_file_path)

  def testDumpExtendedADCToFile_UserCreds(self):
    adc = creds.ADC(self.user_creds)
    adc.DumpExtendedADCToFile(quota_project='my project')
    self.AssertFileEquals(self.EXTENDED_USER_CREDENTIALS_JSON,
                          self.adc_file_path)

  def testDumpExtendedADCToFile_ServiceCreds(self):
    adc = creds.ADC(self.service_creds)
    with self.AssertRaisesExceptionRegexp(creds.CredentialFileSaveError,
                                          'The credential is not .*'):
      adc.DumpExtendedADCToFile(quota_project='my project')

  def testDumpExtendedADCToFile_QuotaProjectNotFound(self):
    self.StartObjectPatch(creds, 'GetQuotaProject', return_value=None)
    adc = creds.ADC(self.user_creds)
    adc.DumpExtendedADCToFile()
    self.AssertFileEquals(self.USER_CREDENTIALS_JSON, self.adc_file_path)
    self.AssertErrContains('Cannot find a project')

  def testDumpADCToFile_P12ServiceAccount(self):
    with self.AssertRaisesExceptionMatches(creds.ADCError,
                                           'Cannot convert credentials'):
      adc = creds.ADC(self.p12_service_creds)
      adc.DumpADCToFile()


class ADCTestsGoogleAuth(cli_test_base.CliTestBase,
                         credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.adc_file_path = os.path.join(self.temp_path,
                                      'application_default_credentials.json')
    self.StartObjectPatch(
        config, 'ADCFilePath', return_value=self.adc_file_path)
    # Mocks the signer of service account credentials.
    self.rsa_mock = self.StartObjectPatch(google_auth_crypt.RSASigner,
                                          'from_service_account_info')

    self.user_creds = self.MakeUserAccountCredentialsGoogleAuth()
    self.service_creds = self.MakeServiceAccountCredentialsGoogleAuth()

  def testDumpADCToFile_UserCreds(self):
    adc = creds.ADC(self.user_creds)
    adc.DumpADCToFile()
    self.AssertFileEquals(self.USER_CREDENTIALS_JSON, self.adc_file_path)

  def testDumpADCToFile_ServiceCreds(self):
    adc = creds.ADC(self.service_creds)
    adc.DumpADCToFile()
    self.AssertFileEquals(self.SERVICE_ACCOUNT_CREDENTIALS_JSON,
                          self.adc_file_path)

  def testDumpExtendedADCToFile_UserCreds(self):
    adc = creds.ADC(self.user_creds)
    adc.DumpExtendedADCToFile(quota_project='my project')
    self.AssertFileEquals(self.EXTENDED_USER_CREDENTIALS_JSON,
                          self.adc_file_path)

  def testDumpExtendedADCToFile_ServiceCreds(self):
    adc = creds.ADC(self.service_creds)
    with self.AssertRaisesExceptionRegexp(creds.CredentialFileSaveError,
                                          'The credential is not .*'):
      adc.DumpExtendedADCToFile(quota_project='my project')

  def testDumpExtendedADCToFile_QuotaProjectNotFound(self):
    self.StartObjectPatch(creds, 'GetQuotaProject', return_value=None)
    adc = creds.ADC(self.user_creds)
    adc.DumpExtendedADCToFile()
    self.AssertFileEquals(self.USER_CREDENTIALS_JSON, self.adc_file_path)
    self.AssertErrContains('Cannot find a project')


class UnKnownCredentials(object):
  pass


class UtilsTests(sdk_test_base.SdkBase, parameterized.TestCase):

  @parameterized.parameters((True, {}, 'fake_token_host'), (True, {
      'token_uri': 'another_token_host'
  }, 'fake_token_host'), (False, {}, properties.VALUES.auth.DEFAULT_TOKEN_HOST),
                            (False, {
                                'token_uri': 'another_token_host'
                            }, 'another_token_host'))
  def testGetEffectiveTokenUri(self, explicitly_set, cred_json, expected_value):
    if explicitly_set:
      properties.VALUES.auth.token_host.Set('fake_token_host')
    self.assertEqual(expected_value, creds.GetEffectiveTokenUri(cred_json))

  @parameterized.parameters(
      (google_auth_credentials.UserCredWithReauth('access_token',
                                                  'refresh_token'), True, True),
      (google_auth_credentials.UserCredWithReauth(
          'access_token', 'refresh_token'), False, True),
      (google_auth_gce.Credentials(), True, True),
      (google_auth_gce.Credentials(), False, False),
      (UnKnownCredentials(), True, False),
      (UnKnownCredentials(), False, False),
  )
  def testIsUserAccountCredentialsGoogleAuth(self, credentials, is_devshell,
                                             expected_result):
    self.StartObjectPatch(
        devshell, 'IsDevshellEnvironment', return_value=is_devshell)
    self.assertEqual(
        creds.IsUserAccountCredentials(credentials), expected_result)

  @parameterized.parameters(
      (client.OAuth2Credentials('token', 'client_id', 'client_secret',
                                'refresh_token', None, None, None), True, True),
      (client.OAuth2Credentials('token', 'client_id', 'client_secret',
                                'refresh_token', None, None,
                                None), False, True),
      (gce.AppAssertionCredentials(), True, True),
      (gce.AppAssertionCredentials(), False, False),
      (UnKnownCredentials(), True, False),
      (UnKnownCredentials(), False, False),
  )
  def testIsUserAccountCredentialsOauth2client(self, credentials, is_devshell,
                                               expected_result):
    self.StartObjectPatch(
        devshell, 'IsDevshellEnvironment', return_value=is_devshell)
    self.assertEqual(
        creds.IsUserAccountCredentials(credentials), expected_result)


if __name__ == '__main__':
  test_case.main()
