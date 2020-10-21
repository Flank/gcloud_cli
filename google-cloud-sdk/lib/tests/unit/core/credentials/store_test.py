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

"""Tests for googlecloudsdk.core.credentials.store."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import hashlib
import json
import dateutil
import google_auth_httplib2

from googlecloudsdk.api_lib.iamcredentials import util as iamcredentials_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import devshell as c_devshell
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import google_auth_credentials as c_google_auth
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base
from tests.lib.core.credentials import devshell_test_base

import httplib2
import mock
from oauth2client import client
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce
from oauth2client.contrib import reauth_errors
import six
from six.moves import http_client as httplib
from google.auth import compute_engine as google_auth_gce
from google.auth import exceptions as google_auth_exceptions
from google.auth import impersonated_credentials as google_auth_impersonated_creds
from google.oauth2 import _client
from google.oauth2 import credentials as google_auth_creds
from google.oauth2 import service_account as google_auth_service_account


def _MakeFakeCredentialsRefreshExpiry():
  """Returns an expiry for fake credentials refresh result."""
  return datetime.datetime.utcnow() + datetime.timedelta(seconds=3599)


def _MakeFakeEmptyIdTokenRefreshResponseGoogleAuth():
  """Returns a fake empty ID token refresh response for google-auth."""
  return mock.Mock(status=200, data='{}')


def _MakeFakeIdTokenRefreshFailureGoogleAuth():
  """Returns a fake ID token refresh failure for google-auth."""
  response_data = (
      '{"error": "invalid_scope", "error_description": '
      '"foo.apps.googleusercontent.com is not a valid audience string."}')
  return mock.Mock(status=400, data=response_data)


# The argument list needs to match that of the refresh of oauth2client
# credentials, so pylint: disable=unused-argument
def _FakeRefreshOauth2clientUserCredentials(self, http):
  """A fake refresh method for oauth2client user credentails."""
  self.access_token = 'REFRESHED-ACCESS-TOKEN'
  self.token_expiry = _MakeFakeCredentialsRefreshExpiry()
  self.id_tokenb64 = 'REFRESHED-ID-TOKEN'


# The argument list needs to match that of the refresh of google auth
# credentials.
def _FakeRefreshGoogleAuthCredentials(self, http):
  """A fake refresh method for google auth credentails."""
  del http
  self.token = 'REFRESHED-ACCESS-TOKEN'
  self.expiry = _MakeFakeCredentialsRefreshExpiry()
  self._id_token = 'REFRESHED-ID-TOKEN'


# The argument list needs to match that of the refresh of google auth ID token
# credentials.
def _FakeRefreshGoogleAuthIdTokenCredentials(self, http):
  """A fake refresh method for google auth ID token credentails."""
  del http
  self.token = 'REFRESHED-ID-TOKEN'
  self.expiry = _MakeFakeCredentialsRefreshExpiry()


def _MockImpersonatedGoogleAuthAccessTokenRefresh(
    self, requests):  # pylint=invalid-name
  del requests
  self.token = 'test-access-token'


def _MockImpersonatedGoogleAuthIdTokenRefresh(self,
                                              requests):  # pylint=invalid-name
  del requests
  self.token = 'test-id-token'


# pylint: enable=unused-argument


# The argument list needs to match that of the refresh of oauth2client
# credentials, so pylint: disable=unused-argument
def _FakeRefreshOauth2clientServiceAccountCredentials(self, http):
  """A fake refresh method for oauth2client service account credentails."""
  self.access_token = 'REFRESHED-ACCESS-TOKEN'
  self.token_expiry = _MakeFakeCredentialsRefreshExpiry()


# pylint: enable=unused-argument


def _MakeFakeOauth2clientServiceAccountIdTokenRefreshResponse():
  """Returns a fake response for service account ID token refresh.

  This returned response is used by oauth2client credentials.
  """
  response = httplib2.Response({'status': httplib.OK})
  content = b'{"id_token": "REFRESHED-ID-TOKEN"}'
  return response, content


class StoreTests(sdk_test_base.WithLogCapture,
                 credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.fake_project = 'fake-project'
    self.fake_account = 'fake-account'
    properties.VALUES.core.account.Set(self.fake_account)
    properties.VALUES.core.project.Set(self.fake_project)
    self.StartObjectPatch(
        config, '_GetGlobalConfigDir', return_value=self.temp_path)
    self.fake_cred = client.OAuth2Credentials(
        'access-token',
        'client_id',
        'client_secret',
        'fake-token',
        datetime.datetime(2017, 1, 8, 0, 0, 0),
        'token_uri',
        'user_agent',
        scopes=config.CLOUDSDK_SCOPES)
    self.refresh_mock = self.StartObjectPatch(
        client.OAuth2Credentials, 'refresh', autospec=True)
    self.refresh_mock_google_auth = self.StartObjectPatch(
        c_google_auth.UserCredWithReauth, 'refresh', autospec=True)
    self.request_mock = self.StartObjectPatch(httplib2.Http, 'request',
                                              autospec=True)
    self.accounts_mock = self.StartObjectPatch(c_gce.Metadata(), 'Accounts')
    self.StartObjectPatch(
        _client,
        'jwt_grant',
        return_value=('REFRESHED-ACCESS-TOKEN',
                      _MakeFakeCredentialsRefreshExpiry(), []))
    self.adc_file = self.Touch(self.root_path, contents="""\
{
  "client_id": "foo.apps.googleusercontent.com",
  "client_secret": "file-secret",
  "refresh_token": "file-token",
  "type": "authorized_user"
}""")
    self.json_file = self.Touch(
        self.root_path,
        contents="""\
{
    "private_key_id": "key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
    "client_email": "bar@developer.gserviceaccount.com",
    "client_id": "bar.apps.googleusercontent.com",
    "type": "service_account",
    "token_uri": "https://oauth2.googleapis.com/token"
  }""")

  def testLoadFreshCredential(self):
    self.fake_cred.token_expiry = (
        datetime.datetime.utcnow() - datetime.timedelta(hours=1))
    store.Store(self.fake_cred)
    loaded = store.LoadFreshCredential()
    self.assertEqual('fake-token', loaded.refresh_token)
    self.refresh_mock.assert_called()

  def testLoadFreshCredentialNoRefresh(self):
    self.fake_cred.token_expiry = (
        datetime.datetime.utcnow() + datetime.timedelta(hours=1))
    store.Store(self.fake_cred)
    store.LoadFreshCredential(min_expiry_duration='30m')
    self.refresh_mock.assert_not_called()

  def testLoadFreshCredentialDefaultDuration(self):
    self.fake_cred.token_expiry = (
        datetime.datetime.utcnow() + datetime.timedelta(hours=1))
    store.Store(self.fake_cred)
    store.LoadFreshCredential()
    self.refresh_mock.assert_called_once()

  def testLoadFreshCredentialDefaultDurationNoRefresh(self):
    self.fake_cred.token_expiry = (
        datetime.datetime.utcnow() + datetime.timedelta(hours=2))
    store.Store(self.fake_cred)
    store.LoadFreshCredential()
    self.refresh_mock.assert_not_called()

  def testLoadFreshCredentialBadDuration(self):
    self.fake_cred.token_expiry = (
        datetime.datetime.utcnow() - datetime.timedelta(1))
    store.Store(self.fake_cred)
    with self.assertRaises(ValueError):
      store.LoadFreshCredential(min_expiry_duration='2h')

    with self.assertRaises(ValueError):
      store.LoadFreshCredential(min_expiry_duration='Foo')

  def testStoreAndLoad(self):
    store.Store(self.fake_cred)
    loaded = store.Load()
    self.assertIsInstance(loaded, client.OAuth2Credentials)
    self.assertEqual(loaded.scopes, set(config.CLOUDSDK_SCOPES))
    self.assertEqual(loaded.refresh_token, 'fake-token')
    self.refresh_mock.assert_called_once()

    loaded = store.LoadIfEnabled()
    self.assertIsInstance(loaded, client.OAuth2Credentials)
    self.assertEqual(loaded.refresh_token, 'fake-token')
    properties.VALUES.auth.disable_credentials.Set(True)
    self.assertIsNone(store.LoadIfEnabled())
    properties.VALUES.auth.disable_credentials.Set(False)

    paths = config.Paths()

    self.AssertFileNotExists(
        paths.LegacyCredentialsBqPath(self.fake_account))

    with open(paths.LegacyCredentialsAdcPath(self.fake_account)) as f:
      adc_file = json.load(f)
    self.assertEqual(json.loads("""
       {
         "client_id": "client_id",
         "client_secret": "client_secret",
         "refresh_token": "fake-token",
         "type": "authorized_user"
       }"""), adc_file)

    self.AssertFileExistsWithContents(
        """
[OAuth2]
client_id = {cid}
client_secret = {secret}

[Credentials]
gs_oauth2_refresh_token = fake-token
""".strip().format(cid=config.CLOUDSDK_CLIENT_ID,
                   secret=config.CLOUDSDK_CLIENT_NOTSOSECRET),
        paths.LegacyCredentialsGSUtilPath(self.fake_account))

    # Not SignedJwtAssertionCredentials
    self.AssertFileNotExists(
        paths.LegacyCredentialsP12KeyPath(self.fake_account))

  def testStoreOauth2client_LoadOAuth2client_UserCreds(self):
    self.refresh_mock.side_effect = _FakeRefreshOauth2clientUserCredentials

    creds_stored = self.MakeUserCredentials()
    expected_creds_dict = {
        'access_token': 'access-token',
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'fake-token',
        'token_uri': 'token_uri',
        'rapt_token': 'rapt_token5',
        'user_agent': 'user_agent',
    }
    expected_expired = True
    self.AssertCredentials(creds_stored, c_creds.CredentialType.USER_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(
        config.Paths().LegacyCredentialsGSUtilPath(self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsAdcPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account)

    expected_creds_dict['access_token'] = 'REFRESHED-ACCESS-TOKEN'
    expected_creds_dict['id_tokenb64'] = 'REFRESHED-ID-TOKEN'
    expected_expired = False
    self.AssertCredentials(creds_loaded, c_creds.CredentialType.USER_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreOauth2client_LoadOAuth2client_ServiceAccountCreds(self):
    self.refresh_mock.side_effect = (
        _FakeRefreshOauth2clientServiceAccountCredentials)
    self.request_mock.return_value = (
        _MakeFakeOauth2clientServiceAccountIdTokenRefreshResponse())

    creds_stored = self.MakeServiceAccountCredentials()
    expected_creds_dict = {
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
    expected_expired = True
    self.AssertCredentials(creds_stored, c_creds.CredentialType.SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(
        config.Paths().LegacyCredentialsGSUtilPath(self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsAdcPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account)

    expected_creds_dict['access_token'] = 'REFRESHED-ACCESS-TOKEN'
    expected_creds_dict['id_tokenb64'] = 'REFRESHED-ID-TOKEN'
    expected_expired = False
    self.AssertCredentials(creds_loaded, c_creds.CredentialType.SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreOauth2client_LoadOAuth2client_P12ServiceAccountCreds(self):
    self.refresh_mock.side_effect = (
        _FakeRefreshOauth2clientServiceAccountCredentials)
    self.request_mock.return_value = (
        _MakeFakeOauth2clientServiceAccountIdTokenRefreshResponse())

    creds_stored = self.MakeP12ServiceAccountCredentials()
    expected_creds_dict = {
        'access_token': 'access_token',
        'service_account_email': 'p12owner@developer.gserviceaccount.com',
        '_private_key_pkcs12': b'BASE64ENCODED',
        '_private_key_password': 'key-password',
        'token_uri': 'https://oauth2.googleapis.com/token'
    }
    expected_expired = True
    self.AssertCredentials(creds_stored,
                           c_creds.CredentialType.P12_SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(
        config.Paths().LegacyCredentialsGSUtilPath(self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsP12KeyPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account)

    expected_creds_dict['access_token'] = 'REFRESHED-ACCESS-TOKEN'
    expected_creds_dict['id_tokenb64'] = 'REFRESHED-ID-TOKEN'
    expected_expired = False
    self.AssertCredentials(creds_loaded,
                           c_creds.CredentialType.P12_SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreOauth2client_LoadGoogleAuth_UserCreds(self):
    self.refresh_mock_google_auth.side_effect = _FakeRefreshGoogleAuthCredentials

    creds_stored = self.MakeUserCredentials()
    expected_creds_dict = {
        'access_token': 'access-token',
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'fake-token',
        'token_uri': 'token_uri',
        'rapt_token': 'rapt_token5',
        'user_agent': 'user_agent',
    }
    expected_expired = True
    self.AssertCredentials(creds_stored, c_creds.CredentialType.USER_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(
        config.Paths().LegacyCredentialsGSUtilPath(self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsAdcPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account, use_google_auth=True)

    expected_creds_dict = {
        'token': 'REFRESHED-ACCESS-TOKEN',
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'refresh_token': 'fake-token',
        'token_uri': 'token_uri',
    }
    expected_expired = False
    self.AssertCredentials(creds_loaded,
                           c_creds.CredentialTypeGoogleAuth.USER_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreGoogleAuth_LoadOauth2client_UserCreds(self):
    self.refresh_mock.side_effect = _FakeRefreshOauth2clientUserCredentials

    creds_stored = self.MakeUserAccountCredentialsGoogleAuth()
    creds_stored.token = 'access-token'
    creds_stored._rapt_token = 'rapt_token5'
    creds_stored._id_token = 'id-token'
    expected_creds_dict = {
        'token': 'access-token',
        'client_id': 'foo.apps.googleusercontent.com',
        'client_secret': 'file-secret',
        'refresh_token': 'file-token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'rapt_token': 'rapt_token5',
        'id_token': 'id-token'
    }
    expected_expired = True
    self.AssertCredentials(creds_stored,
                           c_creds.CredentialTypeGoogleAuth.USER_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(config.Paths().LegacyCredentialsGSUtilPath(
        self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsAdcPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account, use_google_auth=False)

    expected_creds_dict = {
        'access_token': 'REFRESHED-ACCESS-TOKEN',
        'client_id': 'foo.apps.googleusercontent.com',
        'client_secret': 'file-secret',
        'refresh_token': 'file-token',
        'id_tokenb64': 'REFRESHED-ID-TOKEN',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }
    expected_expired = False
    self.AssertCredentials(creds_loaded, c_creds.CredentialType.USER_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreGoogleAuth_LoadGoogleAuth_UserCreds(self):
    self.refresh_mock_google_auth.side_effect = _FakeRefreshGoogleAuthCredentials

    creds_stored = self.MakeUserAccountCredentialsGoogleAuth()
    creds_stored.token = 'access-token'
    creds_stored._rapt_token = 'rapt_token5'
    creds_stored._id_token = 'id-token'
    expected_creds_dict = {
        'token': 'access-token',
        'client_id': 'foo.apps.googleusercontent.com',
        'client_secret': 'file-secret',
        'refresh_token': 'file-token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'rapt_token': 'rapt_token5',
        'id_token': 'id-token'
    }
    expected_expired = True
    self.AssertCredentials(creds_stored,
                           c_creds.CredentialTypeGoogleAuth.USER_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(config.Paths().LegacyCredentialsGSUtilPath(
        self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsAdcPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account, use_google_auth=True)

    expected_creds_dict = {
        'token': 'REFRESHED-ACCESS-TOKEN',
        'client_id': 'foo.apps.googleusercontent.com',
        'client_secret': 'file-secret',
        'refresh_token': 'file-token',
        'id_token': 'REFRESHED-ID-TOKEN',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }
    expected_expired = False
    self.AssertCredentials(creds_loaded,
                           c_creds.CredentialTypeGoogleAuth.USER_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreOauth2client_LoadGoogleAuth_ServiceAccountCreds(self):
    self.StartObjectPatch(
        _client,
        'id_token_jwt_grant',
        return_value=('REFRESHED-ID-TOKEN', _MakeFakeCredentialsRefreshExpiry(),
                      []))

    creds_stored = self.MakeServiceAccountCredentials()
    expected_creds_dict = {
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
    expected_expired = True
    self.AssertCredentials(creds_stored, c_creds.CredentialType.SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(
        config.Paths().LegacyCredentialsGSUtilPath(self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsAdcPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account, use_google_auth=True)

    expected_creds_dict = {
        'token':
            'REFRESHED-ACCESS-TOKEN',
        'id_tokenb64':
            'REFRESHED-ID-TOKEN',
        '_id_token':
            'REFRESHED-ID-TOKEN',
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
    expected_expired = False
    self.AssertCredentials(creds_loaded,
                           c_creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreOauth2client_LoadGoogleAuth_P12ServiceAccountCreds(self):
    self.refresh_mock.side_effect = (
        _FakeRefreshOauth2clientServiceAccountCredentials)
    self.request_mock.return_value = (
        _MakeFakeOauth2clientServiceAccountIdTokenRefreshResponse())

    creds_stored = self.MakeP12ServiceAccountCredentials()
    expected_creds_dict = {
        'access_token': 'access_token',
        'service_account_email': 'p12owner@developer.gserviceaccount.com',
        '_private_key_pkcs12': b'BASE64ENCODED',
        '_private_key_password': 'key-password',
        'token_uri': 'https://oauth2.googleapis.com/token'
    }
    expected_expired = True
    self.AssertCredentials(creds_stored,
                           c_creds.CredentialType.P12_SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(
        config.Paths().LegacyCredentialsGSUtilPath(self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsP12KeyPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account, use_google_auth=True)

    expected_creds_dict.clear()
    expected_creds_dict['token'] = 'REFRESHED-ACCESS-TOKEN'
    expected_creds_dict['id_tokenb64'] = 'REFRESHED-ID-TOKEN'
    expected_expired = False
    self.assertIsInstance(creds_loaded, c_creds.P12CredentialsGoogleAuth)
    self.AssertCredentials(creds_loaded,
                           c_creds.CredentialTypeGoogleAuth.P12_SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreGoogleAuth_LoadGoogleAuth_ServiceAccountCreds(self):
    self.StartObjectPatch(
        _client,
        'id_token_jwt_grant',
        return_value=('REFRESHED-ID-TOKEN', _MakeFakeCredentialsRefreshExpiry(),
                      []))

    creds_stored = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_creds_dict = {
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
    expected_expired = True
    self.AssertCredentials(creds_stored,
                           c_creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(config.Paths().LegacyCredentialsGSUtilPath(
        self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsAdcPath(
        self.fake_account))

    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account, use_google_auth=True)

    expected_creds_dict['token'] = 'REFRESHED-ACCESS-TOKEN'
    expected_creds_dict['id_tokenb64'] = 'REFRESHED-ID-TOKEN'
    expected_creds_dict['_id_token'] = 'REFRESHED-ID-TOKEN'
    expected_expired = False
    self.AssertCredentials(creds_loaded,
                           c_creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreGoogleAuth_LoadOauth2client_ServiceAccountCreds(self):
    self.refresh_mock.side_effect = (
        _FakeRefreshOauth2clientServiceAccountCredentials)
    self.request_mock.return_value = (
        _MakeFakeOauth2clientServiceAccountIdTokenRefreshResponse())

    creds_stored = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_creds_dict = {
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
    expected_expired = True
    self.AssertCredentials(creds_stored,
                           c_creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

    store.Store(creds_stored, self.fake_account)
    self.AssertFileExists(config.Paths().LegacyCredentialsGSUtilPath(
        self.fake_account))
    self.AssertFileExists(config.Paths().LegacyCredentialsAdcPath(
        self.fake_account))
    # Load() refreshes expired tokens
    creds_loaded = store.Load(self.fake_account)

    expected_creds_dict = {
        'access_token':
            'REFRESHED-ACCESS-TOKEN',
        'id_tokenb64':
            'REFRESHED-ID-TOKEN',
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
    expected_expired = False
    self.AssertCredentials(creds_loaded, c_creds.CredentialType.SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreGceCredentials(self):
    self.StartObjectPatch(c_gce._GCEMetadata, 'Accounts', return_value=[])
    store.Store(client.OAuth2Credentials(
        'access-token', 'client_id', 'client_secret',
        'fake-token', None, 'token_uri', 'user_agent'), account='account1')
    store.Store(oauth2client_gce.AppAssertionCredentials(), account='from_gce')
    store.Store(google_auth_gce.Credentials(), account='from_google_auth_gce')
    self.assertEqual(['account1'], store.AvailableAccounts())

  def testNoRefreshOnLoadIfPrevented(self):
    store.Store(self.fake_cred)
    loaded = store.Load(prevent_refresh=True)
    self.assertEqual('fake-token', loaded.refresh_token)
    self.refresh_mock.assert_not_called()

  def testRefreshOnLoadIfStale(self):
    self.fake_cred.token_expiry = (
        datetime.datetime.utcnow() - datetime.timedelta(1))
    store.Store(self.fake_cred)
    loaded = store.Load()
    self.assertEqual('fake-token', loaded.refresh_token)
    self.refresh_mock.assert_called_once()

  def testNoRefreshOnLoadIfFresh(self):
    self.fake_cred.token_expiry = (
        datetime.datetime.utcnow() + datetime.timedelta(1))
    store.Store(self.fake_cred)
    loaded = store.Load()
    self.assertEqual('fake-token', loaded.refresh_token)
    self.refresh_mock.assert_not_called()

  def testAvailableAccounts(self):
    self.StartObjectPatch(c_gce._GCEMetadata, 'Accounts', return_value=[])
    store.Store(client.OAuth2Credentials(
        'access-token', 'client_id', 'client_secret',
        'fake-token', None, 'token_uri', 'user_agent'), account='account1')
    store.Store(client.OAuth2Credentials(
        'access-token', 'client_id', 'client_secret',
        'fake-token', None, 'token_uri', 'user_agent'), account='account2')
    store.Store(client.OAuth2Credentials(
        'access-token2', 'client_id2', 'client_secret2',
        'fake-token2', None, 'token_uri2', 'user_agent2'), account='account2')
    self.assertEqual(['account1', 'account2'], store.AvailableAccounts())

  def testStoreAndLoadFileOverride(self):
    response = httplib2.Response({'status': httplib.OK})
    content = '{"id_token": "id-token"}'.encode()
    self.request_mock.return_value = response, content
    store.Store(self.fake_cred)
    properties.VALUES.auth.credential_file_override.Set(self.adc_file)
    loaded = store.Load()
    self.assertEqual('file-token', loaded.refresh_token)
    self.assertIsNone(loaded.access_token)
    loaded.access_token = 'access-token-2'
    loaded.store.put(loaded)
    # Make sure access-token was cached.
    reloaded = store.Load()
    self.assertEqual('access-token-2', reloaded.access_token)

    properties.VALUES.auth.credential_file_override.Set(self.json_file)
    loaded = store.Load()
    self.assertIsInstance(
        loaded, service_account.ServiceAccountCredentials)
    self.assertEqual('bar.apps.googleusercontent.com', loaded.client_id)
    self.assertEqual(loaded._scopes, ' '.join(config.CLOUDSDK_SCOPES))
    self.assertNotEqual('token_uri', loaded.token_uri)

    properties.VALUES.auth.token_host.Set('token_uri')
    loaded = store.Load()
    self.assertEqual('token_uri', loaded.token_uri)

    properties.VALUES.auth.credential_file_override.Set(None)
    loaded = store.Load()
    self.assertEqual('fake-token', loaded.refresh_token)

  def testError(self):
    properties.VALUES.auth.credential_file_override.Set('non-existing-file')
    with self.assertRaisesRegex(
        store.InvalidCredentialFileException,
        r'Failed to load credential file: \[non-existing-file\]'):
      store.Load()

  def testStoreAndLoadFileOverrideGoogleAuth(self):
    self.StartObjectPatch(
        google_auth_service_account.Credentials,
        'refresh',
        new=_FakeRefreshGoogleAuthCredentials)
    self.StartObjectPatch(
        google_auth_creds.Credentials,
        'refresh',
        new=_FakeRefreshGoogleAuthCredentials)
    self.StartObjectPatch(
        google_auth_service_account.IDTokenCredentials,
        'refresh',
        new=_FakeRefreshGoogleAuthIdTokenCredentials)
    access_token_cache = c_creds.AccessTokenCache(
        config.Paths().access_token_db_path)

    # 1. Test user creds json file override. Creds will be auto refreshed by
    # store.Load. We will also check access token is stored in cache after the
    # refresh.
    properties.VALUES.auth.credential_file_override.Set(self.adc_file)
    loaded = store.Load(use_google_auth=True)
    self.assertIsInstance(loaded, google_auth_creds.Credentials)
    self.assertEqual('file-token', loaded.refresh_token)
    self.assertEqual('REFRESHED-ACCESS-TOKEN', loaded.token)
    self.assertEqual('REFRESHED-ID-TOKEN', loaded.id_tokenb64)
    access_token_in_cache, _, _, _ = access_token_cache.Load(
        hashlib.sha256(six.ensure_binary(loaded.refresh_token)).hexdigest())
    self.assertEqual('REFRESHED-ACCESS-TOKEN', access_token_in_cache)

    # 2. Test sevice account creds json file override and token uri override.
    # Creds will be auto refreshed by store.Load. We will also check access
    # token is stored in cache after the refresh.
    properties.VALUES.auth.credential_file_override.Set(self.json_file)
    properties.VALUES.auth.token_host.Set('token_uri')
    loaded = store.Load(use_google_auth=True)
    self.assertIsInstance(loaded, google_auth_service_account.Credentials)
    self.assertEqual(loaded._scopes, config.CLOUDSDK_SCOPES)
    self.assertEqual('token_uri', loaded._token_uri)
    self.assertEqual('REFRESHED-ACCESS-TOKEN', loaded.token)
    self.assertEqual('REFRESHED-ID-TOKEN', loaded.id_tokenb64)
    access_token_in_cache, _, _, _ = access_token_cache.Load(
        loaded._service_account_email)
    self.assertEqual('REFRESHED-ACCESS-TOKEN', access_token_in_cache)

  def testErrorGoogleAuth(self):
    properties.VALUES.auth.disable_load_google_auth.Set(False)
    properties.VALUES.auth.credential_file_override.Set('non-existing-file')
    with self.assertRaisesRegex(
        store.InvalidCredentialFileException,
        r'Failed to load credential file: \[non-existing-file\]'):
      store.Load(use_google_auth=True)

  def testLoadServiceAccountImpersonationNotConfiguredError(self):
    store.Store(self.fake_cred)
    properties.VALUES.auth.impersonate_service_account.Set('asdf@google.com')
    with mock.patch(
        'googlecloudsdk.core.credentials.store.IMPERSONATION_TOKEN_PROVIDER',
        None):
      with self.assertRaisesRegex(
          store.AccountImpersonationError,
          r'gcloud is configured to impersonate service account '
          r'\[asdf@google.com\] but impersonation support is not available.'):
        store.Load()

  def testRefreshServiceAccountImpersonationNotConfiguredError(self):
    self.StartObjectPatch(iamcredentials_util, 'GenerateAccessToken')
    credentials = iamcredentials_util.ImpersonationCredentials(
        'service-account-id', 'access-token', '2016-01-08T00:00:00Z',
        config.CLOUDSDK_SCOPES)
    store.IMPERSONATION_TOKEN_PROVIDER = None
    with self.assertRaisesRegex(
        store.AccountImpersonationError,
        'gcloud is configured to impersonate a service account '
        'but impersonation support is not available.'):
      store.Refresh(credentials, is_impersonated_credential=True)

  def testServiceAccountImpersonationGoogleAuthNotConfiguredError(self):
    fake_cred = self.MakeServiceAccountCredentialsGoogleAuth()
    store.Store(fake_cred)
    properties.VALUES.auth.impersonate_service_account.Set('asdf@google.com')
    with mock.patch(
        'googlecloudsdk.core.credentials.store.IMPERSONATION_TOKEN_PROVIDER',
        None):
      with self.assertRaisesRegex(
          store.AccountImpersonationError,
          r'gcloud is configured to impersonate service account '
          r'\[asdf@google.com\] but impersonation support is not available.'):
        store.Load(use_google_auth=True)

  def testRefreshServiceAccountImpersonationBadCredError(self):
    self.StartObjectPatch(iamcredentials_util, 'GenerateAccessToken')

    bad_credential = self.MakeUserAccountCredentialsGoogleAuth()

    try:
      store.IMPERSONATION_TOKEN_PROVIDER = (
          iamcredentials_util.ImpersonationAccessTokenProvider())
      with self.assertRaisesRegex(store.AccountImpersonationError,
                                  'Invalid impersonation account for refresh'):
        store.Refresh(bad_credential, is_impersonated_credential=True)
    finally:  # Clean-Up
      store.IMPERSONATION_TOKEN_PROVIDER = None

  def testNoAccountError(self):
    store.Store(self.fake_cred)
    properties.VALUES.core.account.Set(None)
    with self.assertRaises(store.NoActiveAccountException):
      store.Load()
    with self.assertRaises(store.NoActiveAccountException):
      store.LoadIfEnabled()

    properties.VALUES.auth.disable_credentials.Set(True)
    self.assertIsNone(store.LoadIfEnabled())
    with self.assertRaises(store.NoActiveAccountException):
      store.Load()

  def testNoActiveAccountExceptionWithPath(self):
    store.Store(self.fake_cred)
    properties.VALUES.core.account.Set(None)
    with self.assertRaises(store.NoActiveAccountException):
      store.Load()
    self.AssertLogContains(
        'Could not open the configuration file: [')

  def testRefreshServiceAccountId(self):
    """Test that store.Refresh refreshes a service account's id_token."""
    response = httplib2.Response({'status': httplib.OK})
    content = '{"id_token": "old-id-token"}'.encode()
    self.request_mock.return_value = response, content
    properties.VALUES.auth.credential_file_override.Set(self.json_file)
    loaded = store.Load()
    # token_response is initialized in the refresh method of oauth2client
    # credentials, which is mocked in the test. Manually initialize it here so
    # that the test can verify it will be updated later.
    loaded.token_response = {'id_token': 'old-id-token'}
    self.assertIsInstance(loaded, service_account.ServiceAccountCredentials)
    self.assertEqual(loaded.id_tokenb64, 'old-id-token')

    content = '{"id_token": "fresh-id-token"}'.encode()
    self.request_mock.return_value = response, content
    store.Refresh(loaded)
    self.assertEqual(loaded.id_tokenb64, 'fresh-id-token')
    self.assertEqual(loaded.token_response['id_token'], 'fresh-id-token')

  def testRefreshServiceAccountId_GoogleAuth(self):
    self.StartObjectPatch(
        _client,
        'id_token_jwt_grant',
        return_value=('REFRESHED-ID-TOKEN', _MakeFakeCredentialsRefreshExpiry(),
                      []))

    creds = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_creds_dict = {
        'token':
            'access_token',
        'id_tokenb64':
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
    }
    self.assertIsInstance(creds, google_auth_service_account.Credentials)
    self.AssertCredentialsEqual(creds, expected_creds_dict)

    store.Refresh(creds)
    expected_creds_dict['token'] = 'REFRESHED-ACCESS-TOKEN'
    expected_creds_dict['id_tokenb64'] = 'REFRESHED-ID-TOKEN'
    expected_creds_dict['_id_token'] = 'REFRESHED-ID-TOKEN'
    self.AssertCredentialsEqual(creds, expected_creds_dict)

  def testRefreshServiceAccountId_GoogleAuth_IdTokenRefreshFailure(self):
    """Verifies that ID token refresh failures will not throw the refresh."""
    self.StartObjectPatch(
        google_auth_httplib2.Request,
        '__call__',
        return_value=_MakeFakeIdTokenRefreshFailureGoogleAuth())

    creds = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_creds_dict = {
        'token':
            'access_token',
        'id_tokenb64':
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
    }
    self.assertIsInstance(creds, google_auth_service_account.Credentials)
    self.AssertCredentialsEqual(creds, expected_creds_dict)

    store.Refresh(creds)
    expected_creds_dict['token'] = 'REFRESHED-ACCESS-TOKEN'
    self.AssertCredentialsEqual(creds, expected_creds_dict)

  def testRefreshServiceAccountId_GoogleAuth_EmptyIdToken(self):
    """Verifies that an empty ID token will not throw the refresh.

    google-auth will throw a RefreshError if the refresh response does not
    contain a valid ID token even though the status code is 200
    (http://shortn/_JaUf79ElnU). The credentials store is expected to catch
    such an error and proceed the refresh without a new ID token.
    """
    self.StartObjectPatch(
        google_auth_httplib2.Request,
        '__call__',
        return_value=_MakeFakeEmptyIdTokenRefreshResponseGoogleAuth())

    creds = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_creds_dict = {
        'token':
            'access_token',
        'id_tokenb64':
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
    }
    self.assertIsInstance(creds, google_auth_service_account.Credentials)
    self.AssertCredentialsEqual(creds, expected_creds_dict)

    store.Refresh(creds)
    expected_creds_dict['token'] = 'REFRESHED-ACCESS-TOKEN'
    self.AssertCredentialsEqual(creds, expected_creds_dict)

  def testRefreshGceIdToken(self):
    """Test that store.Refresh refreshes a gce service account's id_token."""
    mock_GetIdToken = self.StartObjectPatch(  # pylint: disable=invalid-name
        c_gce._GCEMetadata, 'GetIdToken', return_value='test-id-token')
    test_cred = oauth2client_gce.AppAssertionCredentials()
    test_cred.token_response = {'id_token': 'old-id-token'}
    # Mock Refresh request
    http_mock = mock.Mock()
    store.Refresh(
        test_cred,
        http_client=http_mock,
        gce_token_format='full',
        gce_include_license=True)
    self.assertEqual(test_cred.id_tokenb64, 'test-id-token')
    self.assertEqual(test_cred.token_response['id_token'], 'test-id-token')
    mock_GetIdToken.assert_called_once_with(
        mock.ANY,
        include_license=True,
        token_format='full')

  def testRefreshGoogleAuthGceIdToken(self):
    """Test that store.Refresh refreshes a gce service account's id_token."""
    mock_GetIdToken = self.StartObjectPatch(  # pylint: disable=invalid-name
        c_gce._GCEMetadata,
        'GetIdToken',
        return_value='test-id-token')
    mock_gce_cred_refresh = self.StartObjectPatch(  # pylint: disable=invalid-name
        google_auth_gce.Credentials, 'refresh')
    test_cred = google_auth_gce.Credentials()
    test_cred._id_token = 'old-id-token'
    # Mock Refresh request
    http_mock = mock.Mock()
    http_mock.Request.return_value = mock.Mock()
    store.Refresh(
        test_cred,
        http_client=http_mock,
        gce_token_format='full',
        gce_include_license=True)
    self.assertEqual(test_cred.id_tokenb64, 'test-id-token')
    self.assertEqual(test_cred._id_token, 'test-id-token')
    mock_GetIdToken.assert_called_once_with(
        mock.ANY, include_license=True, token_format='full')
    mock_gce_cred_refresh.assert_called_once()

  def testRefreshImpersonateServiceAccountIdToken(self):
    test_cred = iamcredentials_util.ImpersonationCredentials(
        'service-account-id', 'access-token', '2016-01-08T00:00:00Z',
        config.CLOUDSDK_SCOPES)
    store.IMPERSONATION_TOKEN_PROVIDER = (
        iamcredentials_util.ImpersonationAccessTokenProvider())
    mock_GetElevationIdToken = mock.Mock(return_value='test-id-token')  # pylint: disable=invalid-name
    store.IMPERSONATION_TOKEN_PROVIDER.GetElevationIdToken = mock_GetElevationIdToken
    test_cred.token_response = {'id_token': 'old-id-token'}
    # Mock Refresh request
    http_mock = mock.Mock()
    store.Refresh(
        test_cred,
        http_client=http_mock,
        is_impersonated_credential=True,
        include_email=True)
    self.assertEqual(test_cred.id_tokenb64, 'test-id-token')
    mock_GetElevationIdToken.assert_called_once_with(
        'service-account-id', mock.ANY, True)

  def testRefreshImpersonateServiceAccountIdTokenGoogleAuth(self):
    store.IMPERSONATION_TOKEN_PROVIDER = (
        iamcredentials_util.ImpersonationAccessTokenProvider())
    source_cred = mock.Mock()

    self.StartObjectPatch(
        google_auth_impersonated_creds.Credentials,
        'refresh',
        new=_MockImpersonatedGoogleAuthAccessTokenRefresh)
    self.StartObjectPatch(
        google_auth_impersonated_creds.IDTokenCredentials,
        'refresh',
        new=_MockImpersonatedGoogleAuthIdTokenRefresh)

    access_token_cred = store.IMPERSONATION_TOKEN_PROVIDER.GetElevationAccessTokenGoogleAuth(
        source_cred, 'service_account_id', config.CLOUDSDK_SCOPES)

    store.Refresh(
        access_token_cred,
        http_client=mock.Mock(),
        is_impersonated_credential=True,
        include_email=True)

    self.assertEqual(access_token_cred.token, 'test-access-token')
    self.assertEqual(access_token_cred.id_tokenb64, 'test-id-token')

  def testGetElevationAccessTokenGoogleAuthRefreshError(self):
    store.IMPERSONATION_TOKEN_PROVIDER = (
        iamcredentials_util.ImpersonationAccessTokenProvider())
    source_cred = mock.Mock()

    self.StartObjectPatch(
        google_auth_impersonated_creds.Credentials,
        'refresh',
        side_effect=google_auth_exceptions.RefreshError)

    with self.assertRaises(
        iamcredentials_util.ImpersonatedCredGoogleAuthRefreshError):
      store.IMPERSONATION_TOKEN_PROVIDER.GetElevationAccessTokenGoogleAuth(
          source_cred, 'service_account_id', config.CLOUDSDK_SCOPES)

  def testRefreshError(self):
    self.refresh_mock.side_effect = client.AccessTokenRefreshError
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      store.Refresh(self.fake_cred)

  def testRefreshErrorCAA(self):
    self.refresh_mock.side_effect = client.AccessTokenRefreshError(
        'access_denied: Account restricted')
    with self.assertRaisesRegex(
        store.TokenRefreshDeniedByCAAError,
        'There was a problem refreshing your current auth tokens'):
      store.Refresh(self.fake_cred)

  def testRefreshError_GoogleAuth(self):
    self.refresh_mock_google_auth.side_effect = google_auth_exceptions.RefreshError
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      store.Refresh(self.MakeUserAccountCredentialsGoogleAuth())

  def testRefreshReauthError(self):
    self.refresh_mock.side_effect = reauth_errors.ReauthError
    with self.assertRaisesRegex(
        store.TokenRefreshReauthError,
        'There was a problem reauthenticating while refreshing your current '
        'auth tokens'):
      store.Refresh(self.fake_cred)

  def testRefreshReauthError_GoogleAuth(self):
    self.refresh_mock_google_auth.side_effect = reauth_errors.ReauthError
    with self.assertRaisesRegex(
        store.TokenRefreshReauthError,
        'There was a problem reauthenticating while refreshing your current '
        'auth tokens'):
      store.Refresh(self.MakeUserAccountCredentialsGoogleAuth())
    self.refresh_mock_google_auth.side_effect = c_google_auth.ReauthRequiredError
    with self.assertRaisesRegex(
        store.TokenRefreshReauthError,
        'There was a problem reauthenticating while refreshing your current '
        'auth tokens'):
      store.Refresh(self.MakeUserAccountCredentialsGoogleAuth())

  def testRefreshReauthError_WebLoginRequired(self):
    self.refresh_mock.side_effect = reauth_errors.ReauthSamlLoginRequiredError
    with self.assertRaisesRegex(store.WebLoginRequiredReauthError,
                                'Please run:'):
      store.Refresh(self.fake_cred)

  def testRefreshReauthError_WebLoginRequired_GoogleAuth(self):
    self.refresh_mock_google_auth.side_effect = reauth_errors.ReauthSamlLoginRequiredError
    with self.assertRaisesRegex(store.WebLoginRequiredReauthError,
                                'Please run:'):
      store.Refresh(self.MakeUserAccountCredentialsGoogleAuth())

  def testRefreshIfAlmostExpireTokenExceedExpiryWindow_oauth2client(self):
    now = datetime.datetime(2020, 3, 6, 14, 15, 16, tzinfo=dateutil.tz.tzutc())
    token_expiry = now + datetime.timedelta(seconds=200)
    self.StartObjectPatch(times, 'Now', return_value=now)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = client.OAuth2Credentials(None, None, None, None, token_expiry, None,
                                     None)

    store.RefreshIfAlmostExpire(creds)
    mock_refresh.assert_called_once()

  def testRefreshIfAlmostExpireTokenNoExpiry_oauth2client(self):
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = client.OAuth2Credentials(None, None, None, None, None, None, None)

    store.RefreshIfAlmostExpire(creds)
    mock_refresh.assert_called_once()

  def testRefreshIfAlmostExpireTokenNotExceedExpiryWindow_oauth2client(self):
    now = datetime.datetime(2020, 3, 6, 14, 15, 16, tzinfo=dateutil.tz.tzutc())
    token_expiry = now + datetime.timedelta(seconds=400)
    self.StartObjectPatch(times, 'Now', return_value=now)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = client.OAuth2Credentials(None, None, None, None, token_expiry, None,
                                     None)

    store.RefreshIfAlmostExpire(creds)
    mock_refresh.assert_not_called()

  def testRefreshIfAlmostExpireTokenExpired_google_auth(self):
    # RefreshIfAlmostExpires refreshes when token expires within 300 seconds.
    expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=20)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = google_auth_creds.Credentials('fake-access-token')
    creds.expiry = expiry

    store.RefreshIfAlmostExpire(creds)
    mock_refresh.assert_called_once()

  def testRefreshIfAlmostExpireNotExpired_google_auth(self):
    # RefreshIfAlmostExpires refreshes when token expires in 300 seconds.
    expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=350)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = google_auth_creds.Credentials('fake-access-token')
    creds.expiry = expiry

    store.RefreshIfAlmostExpire(creds)
    mock_refresh.assert_not_called()

  def testRefreshIfExpireWithinWindow_NotExpired_google_auth(self):
    expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=3350)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = google_auth_creds.Credentials('fake-access-token')
    creds.expiry = expiry

    store.RefreshIfExpireWithinWindow(creds, window=3300)
    mock_refresh.assert_not_called()

  def testRefreshIfExpireWithinWindow_Expired_google_auth(self):
    expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=3250)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = google_auth_creds.Credentials('fake-access-token')
    creds.expiry = expiry

    store.RefreshIfExpireWithinWindow(creds, window=3300)
    mock_refresh.assert_called_once()

  def testRefreshIfExpireWithinWindow_NotExpired_oauth2client(self):
    token_expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=3350)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = client.OAuth2Credentials(None, None, None, None, token_expiry, None,
                                     None)

    store.RefreshIfExpireWithinWindow(creds, window=3300)
    mock_refresh.assert_not_called()

  def testRefreshIfExpireWithinWindow_Expired_oauth2client(self):
    token_expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=3250)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = client.OAuth2Credentials(None, None, None, None, token_expiry, None,
                                     None)

    store.RefreshIfExpireWithinWindow(creds, window=3300)
    mock_refresh.assert_called_once()

  def testHandleGoogleAuthCredsRefreshError_TokenRefreshError(self):
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      with store.HandleGoogleAuthCredentialsRefreshError():
        raise google_auth_exceptions.RefreshError()

  def testHandleGoogleAuthCredsRefreshError_TokenRefreshErrorCAA(self):
    with self.assertRaisesRegex(
        store.TokenRefreshDeniedByCAAError,
        'There was a problem refreshing your current auth tokens'):
      with store.HandleGoogleAuthCredentialsRefreshError():
        raise google_auth_exceptions.RefreshError(
            'access_denied: Account restricted')

  def testHandleGoogleAuthCredsRefreshError_TokenRefreshReauthError(self):
    with self.assertRaisesRegex(
        store.TokenRefreshReauthError,
        'There was a problem reauthenticating while refreshing your current '
        'auth tokens'):
      with store.HandleGoogleAuthCredentialsRefreshError():
        raise reauth_errors.ReauthError()
    with self.assertRaisesRegex(
        store.TokenRefreshReauthError,
        'There was a problem reauthenticating while refreshing your current '
        'auth tokens'):
      with store.HandleGoogleAuthCredentialsRefreshError():
        raise c_google_auth.ReauthRequiredError()

  def testHandleGoogleAuthCredsRefreshError_WebLoginRequiredReauthError(self):
    with self.assertRaisesRegex(store.WebLoginRequiredReauthError,
                                'Please run:'):
      with store.HandleGoogleAuthCredentialsRefreshError():
        raise reauth_errors.ReauthSamlLoginRequiredError()

  def testUserCredsTokenHostOverride(self):
    user_creds = self.MakeUserAccountCredentialsGoogleAuth()
    store.Store(user_creds, self.fake_account)
    properties.VALUES.auth.token_host.Set('fake-token-host')
    loaded_oauth2client_creds = store.Load(
        self.fake_account, use_google_auth=False)
    self.assertEqual(loaded_oauth2client_creds.token_uri, 'fake-token-host')
    loaded_google_auth_creds = store.Load(
        self.fake_account, use_google_auth=True)
    self.assertEqual(loaded_google_auth_creds._token_uri, 'fake-token-host')

  def testLoadP12GoogleAuthCredentials_ForceRefresh(self):
    refresh_mock = self.StartObjectPatch(store, '_Refresh')

    creds_stored = self.MakeP12ServiceAccountCredentials()
    creds_stored.token_expiry = (
        datetime.datetime.utcnow() + datetime.timedelta(hours=1))
    store.Store(creds_stored, self.fake_account)
    store.Load(self.fake_account, use_google_auth=True)
    refresh_mock.assset_called()


@test_case.Filters.RunOnlyOnLinux
class DevshellTests(devshell_test_base.DevshellTestBase):

  def testThrowsExceptionInDevshell(self):
    with self.assertRaisesRegex(store.RevokeError, 'Cannot revoke'):
      store.Revoke('joe@example.com')


class LegacyGeneratorTests(cli_test_base.CliTestBase,
                           credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.account = 'fake-account'
    self.StartObjectPatch(
        config, '_GetGlobalConfigDir', return_value=self.temp_path)
    self.paths = config.Paths()

    self.oauth2client_user_creds = self.MakeUserCredentials()
    self.oauth2client_sv_creds = self.MakeServiceAccountCredentials()
    self.oauth2client_gce_creds = oauth2client_gce.AppAssertionCredentials()

    self.google_auth_user_creds = self.MakeUserAccountCredentialsGoogleAuth()
    self.google_auth_sv_creds = self.MakeServiceAccountCredentialsGoogleAuth()
    self.google_auth_gce_creds = google_auth_gce.Credentials()

    self.p12_creds = self.MakeP12ServiceAccountCredentials()

  def testOauth2client_UserAccount(self):
    store._LegacyGenerator(self.account,
                           self.oauth2client_user_creds).WriteTemplate()
    with open(self.paths.LegacyCredentialsAdcPath(self.account)) as f:
      adc_file = json.load(f)
    self.assertEqual(
        json.loads("""
       {
         "client_id": "client_id",
         "client_secret": "client_secret",
         "refresh_token": "fake-token",
         "type": "authorized_user"
       }"""), adc_file)

    self.AssertFileExistsWithContents(
        """
[OAuth2]
client_id = {cid}
client_secret = {secret}

[Credentials]
gs_oauth2_refresh_token = fake-token
""".strip().format(
    cid=config.CLOUDSDK_CLIENT_ID, secret=config.CLOUDSDK_CLIENT_NOTSOSECRET),
        self.paths.LegacyCredentialsGSUtilPath(self.account))

  def testOauth2client_ServiceAccount(self):
    store._LegacyGenerator(self.account,
                           self.oauth2client_sv_creds).WriteTemplate()
    with open(self.paths.LegacyCredentialsAdcPath(self.account)) as f:
      adc_file = json.load(f)
    self.assertEqual(
        json.loads("""
       {
         "client_email": "bar@developer.gserviceaccount.com",
         "client_id": "bar.apps.googleusercontent.com",
         "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
         "private_key_id": "key-id",
         "type": "service_account"
       }"""), adc_file)

    self.AssertFileExistsWithContents(
        """
[Credentials]
gs_service_key_file = {adc_path}
""".strip().format(adc_path=self.paths.LegacyCredentialsAdcPath(self.account)),
        self.paths.LegacyCredentialsGSUtilPath(self.account))

  def testGoogleAuth_UserAccount(self):
    store._LegacyGenerator(self.account,
                           self.google_auth_user_creds).WriteTemplate()
    with open(self.paths.LegacyCredentialsAdcPath(self.account)) as f:
      adc_file = json.load(f)
    self.assertEqual(
        json.loads("""
        {
          "client_id": "foo.apps.googleusercontent.com",
          "client_secret": "file-secret",
          "refresh_token": "file-token",
          "type": "authorized_user"
        }"""), adc_file)
    self.AssertFileExistsWithContents(
        """
[OAuth2]
client_id = {cid}
client_secret = {secret}

[Credentials]
gs_oauth2_refresh_token = file-token
""".strip().format(
    cid=config.CLOUDSDK_CLIENT_ID, secret=config.CLOUDSDK_CLIENT_NOTSOSECRET),
        self.paths.LegacyCredentialsGSUtilPath(self.account))

  def testGoogleAuth_ServiceAccount(self):
    store._LegacyGenerator(self.account,
                           self.google_auth_sv_creds).WriteTemplate()
    with open(self.paths.LegacyCredentialsAdcPath(self.account)) as f:
      adc_file = json.load(f)
    self.assertEqual(
        json.loads("""
       {
         "client_email": "bar@developer.gserviceaccount.com",
         "client_id": "bar.apps.googleusercontent.com",
         "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
         "private_key_id": "key-id",
         "type": "service_account"
       }"""), adc_file)

    self.AssertFileExistsWithContents(
        """
[Credentials]
gs_service_key_file = {adc_path}
""".strip().format(adc_path=self.paths.LegacyCredentialsAdcPath(self.account)),
        self.paths.LegacyCredentialsGSUtilPath(self.account))

  def testP12(self):
    store._LegacyGenerator(self.account, self.p12_creds).WriteTemplate()

    p12_creds = service_account.ServiceAccountCredentials.from_p12_keyfile(
        service_account_email='p12owner@developer.gserviceaccount.com',
        filename=self.paths.LegacyCredentialsP12KeyPath(self.account),
        private_key_password='key-password')
    self.assertEqual(p12_creds._private_key_pkcs12,
                     self.p12_creds._private_key_pkcs12)

    self.AssertFileExistsWithContents(
        """
[Credentials]
gs_service_client_id = {client_id}
gs_service_key_file = {key_file}
gs_service_key_file_password = {key_password}
""".strip().format(
    client_id='p12owner@developer.gserviceaccount.com',
    key_file=self.paths.LegacyCredentialsP12KeyPath(self.account),
    key_password='key-password'),
        self.paths.LegacyCredentialsGSUtilPath(self.account))

  def testUnSupportedOauth2ClientCreds(self):
    with self.AssertRaisesExceptionMatches(c_creds.CredentialFileSaveError,
                                           'Unsupported credentials'):
      store._LegacyGenerator(self.account,
                             self.oauth2client_gce_creds).WriteTemplate()

  def testUnSupportedGoogleAuthCreds(self):
    with self.AssertRaisesExceptionMatches(c_creds.CredentialFileSaveError,
                                           'Unsupported credentials'):
      store._LegacyGenerator(self.account,
                             self.google_auth_gce_creds).WriteTemplate()


class RevokeTest(cli_test_base.CliTestBase,
                 credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.fake_project = 'fake-project'
    self.fake_account = 'fake-account'
    properties.VALUES.core.account.Set(self.fake_account)
    properties.VALUES.core.project.Set(self.fake_project)
    self.oauth2client_creds = self.MakeUserCredentials()
    self.StartObjectPatch(
        config, '_GetGlobalConfigDir', return_value=self.temp_path)
    self.oauth2client_revoke_mock = self.StartObjectPatch(
        client.OAuth2Credentials, 'revoke')
    self.google_auth_revoke_mock = self.StartObjectPatch(
        c_google_auth.UserCredWithReauth, 'revoke')

  def _AssertLegacyCredsNotPresent(self, account):
    self.AssertDirectoryNotExists(config.Paths().LegacyCredentialsDir(account))

  def _AssertLegacyCredsPresent(self, account):
    self.AssertDirectoryExists(config.Paths().LegacyCredentialsDir(account))

  def _AssertCredsNotInStore(self, account):
    with self.AssertRaisesExceptionRegexp(
        store.NoCredentialsForAccountException, account):
      store.Load(account, prevent_refresh=True)

  def _AssertCredsInStore(self, account):
    loaded_creds = store.Load(account, prevent_refresh=True)
    self.assertIsNotNone(loaded_creds)

  def AssertCredsExistInLocal(self, account):
    self._AssertCredsInStore(account)
    self._AssertLegacyCredsPresent(account)

  def AssertCredsNotExistInLocal(self, account):
    self._AssertCredsNotInStore(account)
    self._AssertLegacyCredsNotPresent(account)

  def testRevokeCredentialsWhenNoAccount(self):
    properties.VALUES.core.account.Set(None)
    with self.assertRaises(store.NoActiveAccountException):
      store.Revoke()

  def testRevoke_Oauth2client(self):
    self.StartObjectPatch(
        store, 'GoogleAuthDisabledGlobally', return_value=True)
    store.Store(self.oauth2client_creds, self.fake_account)
    self.AssertCredsExistInLocal(self.fake_account)
    result = store.Revoke(account=self.fake_account)
    self.AssertCredsNotExistInLocal(self.fake_account)
    self.assertTrue(result)
    self.oauth2client_revoke_mock.assert_called()

  def testRevoke_Oauth2client_KnownError(self):
    self.StartObjectPatch(
        store, 'GoogleAuthDisabledGlobally', return_value=True)
    self.oauth2client_revoke_mock.side_effect = client.TokenRevokeError(
        'invalid_token')
    store.Store(self.oauth2client_creds, self.fake_account)
    self.AssertCredsExistInLocal(self.fake_account)
    result = store.Revoke(account=self.fake_account)
    self.AssertCredsNotExistInLocal(self.fake_account)
    self.assertFalse(result)
    self.oauth2client_revoke_mock.assert_called()

  def testRevoke_Oauth2client_UnknownError(self):
    self.StartObjectPatch(
        store, 'GoogleAuthDisabledGlobally', return_value=True)
    self.oauth2client_revoke_mock.side_effect = client.TokenRevokeError(
        'random_error')
    store.Store(self.oauth2client_creds, self.fake_account)
    self.AssertCredsExistInLocal(self.fake_account)
    with self.assertRaisesRegex(client.TokenRevokeError, 'random_error'):
      store.Revoke(account=self.fake_account)

  def testRevoke_GoogleAuth(self):
    store.Store(self.oauth2client_creds, self.fake_account)
    self.AssertCredsExistInLocal(self.fake_account)
    result = store.Revoke(account=self.fake_account)
    self.AssertCredsNotExistInLocal(self.fake_account)
    self.assertTrue(result)
    self.google_auth_revoke_mock.assert_called()

  def testRevoke_UserAccount_GoogleAuth_KnownError(self):
    self.google_auth_revoke_mock.side_effect = c_google_auth.TokenRevokeError(
        'invalid_token')
    store.Store(self.oauth2client_creds, self.fake_account)
    self.AssertCredsExistInLocal(self.fake_account)
    result = store.Revoke(account=self.fake_account)
    self.AssertCredsNotExistInLocal(self.fake_account)
    self.assertFalse(result)
    self.google_auth_revoke_mock.assert_called()

  def testRevoke_UserAccount_GoogleAuth_UnknownError(self):
    self.google_auth_revoke_mock.side_effect = c_google_auth.TokenRevokeError(
        'random_error')
    store.Store(self.oauth2client_creds, self.fake_account)
    self.AssertCredsExistInLocal(self.fake_account)
    with self.assertRaisesRegex(c_google_auth.TokenRevokeError, 'random_error'):
      store.Revoke(account=self.fake_account)

  def testRevoke_GCE(self):
    self.StartObjectPatch(
        c_gce._GCEMetadata, 'Accounts', return_value=[self.fake_account])
    with self.assertRaisesRegex(store.RevokeError,
                                'Cannot revoke GCE-provided credentials.'):
      store.Revoke(account=self.fake_account)

  def testRevoke_Devshell(self):
    self.StartObjectPatch(c_devshell.DevshellCredentials, '_refresh')
    self.StartObjectPatch(
        store, 'Load', return_value=c_devshell.DevshellCredentials())
    with self.assertRaisesRegex(store.RevokeError,
                                'Cannot revoke .* Cloud Shell .*'):
      store.Revoke(account=self.fake_account)

    self.StartObjectPatch(
        store,
        'Load',
        return_value=c_devshell.DevShellCredentialsGoogleAuth(None))
    with self.assertRaisesRegex(store.RevokeError,
                                'Cannot revoke .* Cloud Shell .*'):
      store.Revoke(account=self.fake_account)

  def testRevoke_NonExistingAccount(self):
    with self.assertRaisesRegex(store.NoCredentialsForAccountException,
                                'non-existing-account'):
      store.Revoke(account='non-existing-account')

  def testRevoke_ServiceAccount(self):
    revoke_credentials_mock = self.StartObjectPatch(store, 'RevokeCredentials')
    sv = self.MakeServiceAccountCredentials()
    store.Store(sv, sv.service_account_email)
    self.AssertCredsExistInLocal(sv.service_account_email)
    result = store.Revoke(sv.service_account_email)
    self.AssertCredsNotExistInLocal(sv.service_account_email)
    revoke_credentials_mock.assert_not_called()
    self.assertFalse(result)

  def testRevoke_ServiceAccount_GoogleAuth(self):
    revoke_credentials_mock = self.StartObjectPatch(store, 'RevokeCredentials')
    sv = self.MakeServiceAccountCredentialsGoogleAuth()
    store.Store(sv, sv.service_account_email)
    self.AssertCredsExistInLocal(sv.service_account_email)
    result = store.Revoke(sv.service_account_email)
    self.AssertCredsNotExistInLocal(sv.service_account_email)
    revoke_credentials_mock.assert_not_called()
    self.assertFalse(result)

  def testRevoke_MissingLegacyCredentials(self):
    store.Store(self.oauth2client_creds, self.fake_account)
    files.RmTree(config.Paths().LegacyCredentialsDir(self.fake_account))
    store.Revoke(account=self.fake_account)
    self.AssertCredsNotExistInLocal(self.fake_account)


if __name__ == '__main__':
  test_case.main()
