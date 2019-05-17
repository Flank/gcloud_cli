# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

import contextlib
import datetime
import json

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import store
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.credentials import devshell_test_base
import httplib2
import mock

from oauth2client import client
from oauth2client import crypt
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce


class StoreTests(sdk_test_base.WithLogCapture):

  def SetUp(self):
    self.fake_project = 'fake-project'
    self.fake_account = 'fake-account'
    properties.VALUES.core.account.Set(self.fake_account)
    properties.VALUES.core.project.Set(self.fake_project)
    self.fake_cred = client.OAuth2Credentials(
        'access-token', 'client_id', 'client_secret',
        'fake-token', None, 'token_uri', 'user_agent',
        scopes=config.CLOUDSDK_SCOPES)
    self.crypt_mock = self.StartObjectPatch(crypt, 'make_signed_jwt')
    self.refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                              'refresh')
    self.request_mock = self.StartObjectPatch(httplib2.Http, 'request',
                                              autospec=True)
    self.response_mock = self.StartObjectPatch(httplib2, 'Response',
                                               autospec=True)
    self.accounts_mock = self.StartObjectPatch(c_gce.Metadata(), 'Accounts')
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.adc_file = self.Touch(self.root_path, contents="""\
{
  "client_id": "foo.apps.googleusercontent.com",
  "client_secret": "file-secret",
  "refresh_token": "file-token",
  "type": "authorized_user"
}""")
    self.json_file = self.Touch(self.root_path, contents="""\
{
    "private_key_id": "key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
    "client_email": "bar@developer.gserviceaccount.com",
    "client_id": "bar.apps.googleusercontent.com",
    "type": "service_account"
  }""")

  def testStoreAndLoad(self):
    store.Store(self.fake_cred)
    loaded = store.Load()
    self.assertEqual(loaded.scopes, set(config.CLOUDSDK_SCOPES))
    self.assertEqual('fake-token', loaded.refresh_token)
    self.refresh_mock.assert_called_once()

    self.assertEqual('fake-token', store.LoadIfEnabled().refresh_token)
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

  def testStoreGceCredentials(self):
    self.StartObjectPatch(c_gce._GCEMetadata, 'Accounts', return_value=[])
    store.Store(client.OAuth2Credentials(
        'access-token', 'client_id', 'client_secret',
        'fake-token', None, 'token_uri', 'user_agent'), account='account1')
    store.Store(oauth2client_gce.AppAssertionCredentials(), account='from_gce')
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
    self.assertTrue(
        isinstance(loaded, service_account.ServiceAccountCredentials))
    self.assertEqual('bar.apps.googleusercontent.com', loaded.client_id)
    self.assertEqual(loaded._scopes, ' '.join(config.CLOUDSDK_SCOPES))
    self.assertNotEquals('token_uri', loaded.token_uri)

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

  @test_case.Filters.skip('Flaky', 'b/119435008')
  def testServiceAccountImpersonationNotConfiguredError(self):
    store.Store(self.fake_cred)
    properties.VALUES.auth.impersonate_service_account.Set('asdf@google.com')
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
    credentials = store.AcquireFromToken(loaded.refresh_token)
    store.Refresh(credentials)
    store.Store(credentials, self.fake_account)
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
    credentials = store.AcquireFromToken(self.fake_cred.refresh_token)
    store.Store(credentials, self.fake_account)
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
    credentials = store.AcquireFromToken(self.fake_cred.refresh_token)
    store.Store(credentials, self.fake_account)
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
    credentials = store.AcquireFromToken(self.fake_cred.refresh_token)
    store.Store(credentials, self.fake_account)
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
    properties.VALUES.auth.credential_file_override.Set(self.json_file)
    loaded = store.Load()
    loaded.token_response = {'id_token': 'old-id-token'}
    self.assertIsInstance(loaded, service_account.ServiceAccountCredentials)
    http_mock = mock.Mock()
    http_mock.request.return_value = (
        mock.Mock(status=200),
        json.dumps({'id_token': 'fresh-id-token'}))
    store.Refresh(loaded, http_client=http_mock)
    self.assertEqual(loaded.id_tokenb64, 'fresh-id-token')
    self.assertEqual(loaded.token_response['id_token'], 'fresh-id-token')

  def testRefreshError(self):
    self.refresh_mock.side_effect = client.AccessTokenRefreshError
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      store.Refresh(self.fake_cred)


@test_case.Filters.RunOnlyOnLinux
@test_case.Filters.SkipInDebPackage(
    'Socket conflict in docker container in test environment', 'b/37959415')
@test_case.Filters.SkipInRpmPackage(
    'Socket conflict in docker container in test environment', 'b/37959415')
class DevshellTests(sdk_test_base.SdkBase):

  def _UnregisterDevshellProvider(self, provider):
    try:
      provider.UnRegister()
    except:  # pylint: disable=bare-except
      # Provider may have all already been unregistered.
      pass

  @contextlib.contextmanager
  def _DevshellProvider(self):
    devshell_provider = store.DevShellCredentialProvider()
    try:
      devshell_provider.Register()
      yield devshell_provider
    finally:
      self._UnregisterDevshellProvider(devshell_provider)

  @contextlib.contextmanager
  def _DevshellProxy(self):
    devshell_proxy = devshell_test_base.AuthReferenceServer(self.GetPort())
    try:
      devshell_proxy.Start()
      yield devshell_proxy
    finally:
      devshell_proxy.Stop()

  @sdk_test_base.Retry(
      why=('The test server is very rarely flaky.'),
      max_retrials=3,
      sleep_ms=300)
  def _testRevokeRaisesError(self):
    with self._DevshellProvider() as devshell_provider:
      self.assertIsNone(properties.VALUES.core.project.Get())
      with self._DevshellProxy():
        self.assertEqual('fooproj', properties.VALUES.core.project.Get())
        with self.assertRaisesRegex(store.RevokeError, 'Cannot revoke'):
          store.Revoke('joe@example.com')

        # Need to do this check while the dev shell proxy is still active.
        devshell_provider.UnRegister()
        self.assertIsNone(properties.VALUES.core.project.Get())

  def testThrowsExceptionInDevshell(self):
    self._testRevokeRaisesError()

if __name__ == '__main__':
  test_case.main()
