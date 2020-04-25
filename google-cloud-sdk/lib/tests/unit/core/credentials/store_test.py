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
import json
import dateutil

from googlecloudsdk.api_lib.iamcredentials import util as iamcredentials_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import reauth
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base
from tests.lib.core.credentials import devshell_test_base

import httplib2
import mock
from oauth2client import client
from oauth2client import crypt
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce
from oauth2client.contrib import reauth_errors
from google.auth import _helpers
from google.auth import compute_engine as google_auth_gce
from google.auth import crypt as google_auth_crypt
from google.auth import exceptions as google_auth_exceptions
from google.auth import jwt
from google.oauth2 import _client
from google.oauth2 import credentials
from google.oauth2 import service_account as google_auth_service_account


def _MakeFakeCredentialsRefreshExpiry():
  """Returns an expiry for fake credentials refresh result."""
  return datetime.datetime.utcnow() + datetime.timedelta(seconds=3599)


# The argument list needs to match that of the refresh of oauth2client
# credentials, so pylint: disable=unused-argument
def _FakeRefreshOauth2clientUserCredentials(self, http):
  """A fake refresh method for oauth2client user credentails."""
  self.access_token = 'REFRESHED-ACCESS-TOKEN'
  self.token_expiry = _MakeFakeCredentialsRefreshExpiry()
  self.id_tokenb64 = 'REFRESHED-ID-TOKEN'


# The argument list needs to match that of the refresh of oauth2client
# credentials, so pylint: disable=unused-argument
def _FakeRefreshGoogleAuthUserCredentials(self, http):
  """A fake refresh method for google auth user credentails."""
  self.token = 'REFRESHED-ACCESS-TOKEN'
  self.expiry = _MakeFakeCredentialsRefreshExpiry()
  self._id_token = 'REFRESHED-ID-TOKEN'


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
  response = mock.Mock(status=200)
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
    self.crypt_mock = self.StartObjectPatch(crypt, 'make_signed_jwt')
    self.refresh_mock = self.StartObjectPatch(
        client.OAuth2Credentials, 'refresh', autospec=True)
    self.refresh_mock_google_auth = self.StartObjectPatch(
        reauth.UserCredWithReauth, 'refresh', autospec=True)
    self.request_mock = self.StartObjectPatch(httplib2.Http, 'request',
                                              autospec=True)
    self.response_mock = self.StartObjectPatch(httplib2, 'Response',
                                               autospec=True)
    self.accounts_mock = self.StartObjectPatch(c_gce.Metadata(), 'Accounts')
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)
    self.StartObjectPatch(google_auth_crypt.RSASigner,
                          'from_service_account_info')
    self.StartObjectPatch(jwt, 'encode', return_value=b'fake_assertion')
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
            'https://www.googleapis.com/oauth2/v4/token'
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
        'token_uri': 'https://www.googleapis.com/oauth2/v4/token'
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

    expected_creds_dict['access_token'] = 'REFRESHED-ACCESS-TOKEN'
    expected_creds_dict['id_tokenb64'] = 'REFRESHED-ID-TOKEN'
    expected_expired = False
    self.AssertCredentials(creds_loaded,
                           c_creds.CredentialType.P12_SERVICE_ACCOUNT,
                           expected_creds_dict, expected_expired)

  def testStoreOauth2client_LoadGoogleAuth_UserCreds(self):
    self.refresh_mock_google_auth.side_effect = _FakeRefreshGoogleAuthUserCredentials

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
        'token_uri': 'https://oauth2.googleapis.com/token',
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
    self.refresh_mock_google_auth.side_effect = _FakeRefreshGoogleAuthUserCredentials

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
            'https://www.googleapis.com/oauth2/v4/token'
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
        'token_uri': 'https://www.googleapis.com/oauth2/v4/token'
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

    expected_creds_dict['access_token'] = 'REFRESHED-ACCESS-TOKEN'
    expected_creds_dict['id_tokenb64'] = 'REFRESHED-ID-TOKEN'
    expected_expired = False
    self.AssertCredentials(creds_loaded,
                           c_creds.CredentialType.P12_SERVICE_ACCOUNT,
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
    response = mock.Mock(status=200)
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

  def testServiceAccountImpersonationNotConfiguredError(self):
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

  def testRevokeCredentialsWhenNoAccount(self):
    with self.assertRaises(store.NoActiveAccountException):
      properties.VALUES.core.account.Set(None)
      store.Revoke()

  def testRevokeCredentialsAfterRefresh(self):
    self.accounts_mock = ''
    self.response_mock.status = 200
    fake_content = 'fake-content'
    self.request_mock.return_value = self.response_mock, fake_content
    store.Store(self.fake_cred)
    loaded = store.Load()
    creds = store.AcquireFromToken(loaded.refresh_token)
    store.Refresh(creds)
    store.Store(creds, self.fake_account)
    result = store.Revoke()
    self.assertTrue(result)
    # check that we made an HTTP request to the correct revoke URL
    self.assertIsNotNone(self.request_mock.call_args)
    call_args, unused_kwargs = self.request_mock.call_args
    call_url = call_args[1]
    self.assertIn(store.GOOGLE_OAUTH2_PROVIDER_REVOKE_URI, call_url)
    with self.assertRaises(store.NoCredentialsForAccountException):
      loaded = store.Load()

  def testRevokeNoRefresh(self):
    self.accounts_mock = ''
    self.response_mock.status = 200
    fake_content = 'fake-content'
    self.request_mock.return_value = self.response_mock, fake_content
    creds = store.AcquireFromToken(self.fake_cred.refresh_token)
    store.Store(creds, self.fake_account)
    result = store.Revoke()
    self.assertTrue(result)
    self.refresh_mock.assert_not_called()
    # check that we made an HTTP request to the correct revoke URL
    self.assertIsNotNone(self.request_mock.call_args)
    call_args, unused_kwargs = self.request_mock.call_args
    call_url = call_args[1]
    self.assertIn(store.GOOGLE_OAUTH2_PROVIDER_REVOKE_URI, call_url)
    with self.assertRaises(store.NoCredentialsForAccountException):
      store.Load()

  def testRevokeAlreadyRevoked(self):
    self.accounts_mock = ''
    self.response_mock.status = 400
    fake_content = '{"error":"invalid_token"}'
    self.request_mock.return_value = self.response_mock, fake_content
    creds = store.AcquireFromToken(self.fake_cred.refresh_token)
    store.Store(creds, self.fake_account)
    result = store.Revoke()
    self.assertFalse(result)
    self.refresh_mock.assert_not_called()
    # check that we made an HTTP request to the correct revoke URL
    self.assertIsNotNone(self.request_mock.call_args)
    call_args, unused_kwargs = self.request_mock.call_args
    call_url = call_args[1]
    self.assertIn(store.GOOGLE_OAUTH2_PROVIDER_REVOKE_URI, call_url)
    with self.assertRaises(store.NoCredentialsForAccountException):
      store.Load()

  def testRevokeServiceAccountToken(self):
    self.accounts_mock = ''
    self.response_mock.status = 400
    fake_content = '{"error":"invalid_request"}'
    self.request_mock.return_value = self.response_mock, fake_content
    creds = store.AcquireFromToken(self.fake_cred.refresh_token)
    store.Store(creds, self.fake_account)
    result = store.Revoke()
    self.assertFalse(result)
    self.refresh_mock.assert_not_called()
    # check that we made an HTTP request to the correct revoke URL
    self.assertIsNotNone(self.request_mock.call_args)
    call_args, unused_kwargs = self.request_mock.call_args
    call_url = call_args[1]
    self.assertIn(store.GOOGLE_OAUTH2_PROVIDER_REVOKE_URI, call_url)
    with self.assertRaises(store.NoCredentialsForAccountException):
      store.Load()

  def testRefreshServiceAccountId(self):
    """Test that store.Refresh refreshes a service account's id_token."""
    response = mock.Mock(status=200)
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

  def testRefreshError(self):
    self.refresh_mock.side_effect = client.AccessTokenRefreshError
    with self.assertRaisesRegex(
        store.TokenRefreshError,
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
    self.refresh_mock_google_auth.side_effect = reauth.ReauthRequiredError
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

    store._RefreshIfAlmostExpire(creds)
    mock_refresh.assert_called_once()

  def testRefreshIfAlmostExpireTokenNoExpiry_oauth2client(self):
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = client.OAuth2Credentials(None, None, None, None, None, None, None)

    store._RefreshIfAlmostExpire(creds)
    mock_refresh.assert_called_once()

  def testRefreshIfAlmostExpireTokenNotExceedExpiryWindow_oauth2client(self):
    now = datetime.datetime(2020, 3, 6, 14, 15, 16, tzinfo=dateutil.tz.tzutc())
    token_expiry = now + datetime.timedelta(seconds=400)
    self.StartObjectPatch(times, 'Now', return_value=now)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = client.OAuth2Credentials(None, None, None, None, token_expiry, None,
                                     None)

    store._RefreshIfAlmostExpire(creds)
    mock_refresh.assert_not_called()

  def testRefreshIfAlmostExpireTokenExpired_google_auth(self):
    now = datetime.datetime(2020, 3, 6, 14, 15, 16)
    expiry = now - datetime.timedelta(seconds=20)
    self.StartObjectPatch(_helpers, 'utcnow', return_value=now)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = credentials.Credentials('fake-access-token')
    creds.expiry = expiry

    store._RefreshIfAlmostExpire(creds)
    mock_refresh.assert_called_once()

  def testRefreshIfAlmostExpireNotExpired_google_auth(self):
    now = datetime.datetime(2020, 3, 6, 14, 15, 16)
    # expiry needs to be at least 300s ahead of now for the credentials to be
    # vallid. This interval accounts for the clock skew
    # (http://shortn/_nXtCxPblUS) considered by google-auth when calculating the
    # the validity of the credentials.
    expiry = now + datetime.timedelta(seconds=320)
    self.StartObjectPatch(_helpers, 'utcnow', return_value=now)
    mock_refresh = self.StartObjectPatch(store, 'Refresh', autospec=True)
    creds = credentials.Credentials('fake-access-token')
    creds.expiry = expiry

    store._RefreshIfAlmostExpire(creds)
    mock_refresh.assert_not_called()


@test_case.Filters.RunOnlyOnLinux
@test_case.Filters.SkipInDebPackage(
    'Socket conflict in docker container in test environment', 'b/37959415')
@test_case.Filters.SkipInRpmPackage(
    'Socket conflict in docker container in test environment', 'b/37959415')
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

    # Mocks the signer of service account credentials.
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)
    self.rsa_mock = self.StartObjectPatch(google_auth_crypt.RSASigner,
                                          'from_service_account_info')

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


if __name__ == '__main__':
  test_case.main()
