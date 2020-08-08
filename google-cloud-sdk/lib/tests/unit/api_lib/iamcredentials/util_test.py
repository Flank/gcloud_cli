# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Unit tests for the genomics filter expression rewrite module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.iamcredentials import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import http
from googlecloudsdk.core.credentials import store
from tests.lib import sdk_test_base

import httplib2
from oauth2client import client


class UtilTests(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.account.Set('fakeuser')
    self.fake_cred = client.OAuth2Credentials(
        'access-token', 'client_id', 'client_secret',
        'fake-token', None, 'token_uri', 'user_agent',
        scopes=config.CLOUDSDK_SCOPES)
    self.mock_client = mock.Client(apis.GetClientClass('iamcredentials', 'v1'))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = self.mock_client.MESSAGES_MODULE
    self.gen_request_msg = (
        self.messages
        .IamcredentialsProjectsServiceAccountsGenerateAccessTokenRequest)
    self.gen_id_msg = (
        self.messages
        .IamcredentialsProjectsServiceAccountsGenerateIdTokenRequest)
    self.refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                              'refresh')

  def testGenerateAccessToken(self):
    store.Store(self.fake_cred)
    self.mock_client.projects_serviceAccounts.GenerateAccessToken.Expect(
        self.gen_request_msg(
            name='projects/-/serviceAccounts/asdf@google.com',
            generateAccessTokenRequest=self.messages.GenerateAccessTokenRequest(
                scope=config.CLOUDSDK_SCOPES)),
        self.messages.GenerateAccessTokenResponse(
            accessToken='access-token', expireTime='2016-01-08T00:00:00Z')
    )
    result = util.GenerateAccessToken('asdf@google.com', config.CLOUDSDK_SCOPES)
    self.assertEqual(result.accessToken, 'access-token')
    self.assertEqual(result.expireTime, '2016-01-08T00:00:00Z')

  def testGenerateIdToken(self):
    audience = 'https://service-hash-uc.a.run.app'
    store.Store(self.fake_cred)
    self.mock_client.projects_serviceAccounts.GenerateIdToken.Expect(
        self.gen_id_msg(
            name='projects/-/serviceAccounts/asdf@google.com',
            generateIdTokenRequest=self.messages.GenerateIdTokenRequest(
                audience=audience, includeEmail=False)),
        self.messages.GenerateIdTokenResponse(token='id-token')
    )

    result = util.GenerateIdToken('asdf@google.com', audience)

    self.assertEqual(result, 'id-token')

  def testServiceAccountImpersonation(self):
    # This is the logged in credential, but it will not be used to make the call
    # because of the impersonation.
    store.Store(self.fake_cred)
    properties.VALUES.auth.impersonate_service_account.Set('asdf@google.com')

    # Expect a call to get a temp access token for impersonation.
    fake_token = 'impersonation-token'
    self.mock_client.projects_serviceAccounts.GenerateAccessToken.Expect(
        self.gen_request_msg(
            name='projects/-/serviceAccounts/asdf@google.com',
            generateAccessTokenRequest=self.messages.GenerateAccessTokenRequest(
                scope=config.CLOUDSDK_SCOPES)),
        self.messages.GenerateAccessTokenResponse(
            accessToken=fake_token, expireTime='2016-01-08T00:00:00Z')
    )

    request_mock = self.StartObjectPatch(
        httplib2.Http, 'request',
        return_value=(httplib2.Response({'status': 200}), b''))
    try:
      store.IMPERSONATION_TOKEN_PROVIDER = (
          util.ImpersonationAccessTokenProvider())
      http.Http().request('http://foo.com', 'GET', None, {})
      access_token = request_mock.call_args[0][3][b'Authorization']
      self.assertEqual(access_token, b'Bearer ' + fake_token.encode('utf-8'))
    finally:
      store.IMPERSONATION_TOKEN_PROVIDER = None

  def testImpersonationCredentials(self):
    self.StartObjectPatch(
        util, 'GenerateAccessToken',
        return_value=self.messages.GenerateAccessTokenResponse(
            accessToken='new-access-token', expireTime='2017-01-08T00:00:00Z'))
    credentials = util.ImpersonationCredentials('service-account-id',
                                                'access-token',
                                                '2016-01-08T00:00:00Z',
                                                config.CLOUDSDK_SCOPES)

    credentials._refresh(None)
    util.GenerateAccessToken.assert_called_once()
    self.assertEqual(len(util.GenerateAccessToken.call_args[0]), 2)
    service_account_arg = util.GenerateAccessToken.call_args[0][0]
    scopes_arg = util.GenerateAccessToken.call_args[0][1]
    self.assertEqual(service_account_arg, 'service-account-id')
    self.assertIsInstance(scopes_arg, list)
    self.assertEqual(set(scopes_arg), set(config.CLOUDSDK_SCOPES))
    self.assertEqual(credentials.access_token, 'new-access-token')
    self.assertEqual(credentials.token_expiry,
                     datetime.datetime(2017, 1, 8, 0, 0, 0))

  def testRefreshImpersonationAccountId(self):
    # Store test credential
    store.Store(self.fake_cred)
    properties.VALUES.auth.impersonate_service_account.Set('asdf@google.com')
    try:
      # Set Token Provider
      store.IMPERSONATION_TOKEN_PROVIDER = (
          util.ImpersonationAccessTokenProvider())
      # Mock response from util.GenerateAccessToken
      self.mock_client.projects_serviceAccounts.GenerateAccessToken.Expect(
          self.gen_request_msg(
              name='projects/-/serviceAccounts/asdf@google.com',
              generateAccessTokenRequest=(
                  self.messages.GenerateAccessTokenRequest(
                      scope=config.CLOUDSDK_SCOPES))),
          self.messages.GenerateAccessTokenResponse(
              accessToken='impersonation-token',
              expireTime='2016-01-08T00:00:00Z'))

      # Load test impersonation token
      loaded = store.Load(allow_account_impersonation=True)
      loaded.token_response = {'id_token': 'old-id-token'}
      audience = 'https://service-hash-uc.a.run.app'
      config.CLOUDSDK_CLIENT_ID = audience

      # Refresh the credential
      # Mock response from util.GenerateAccessToken (2nd call from Refresh)
      self.mock_client.projects_serviceAccounts.GenerateAccessToken.Expect(
          self.gen_request_msg(
              name='projects/-/serviceAccounts/asdf@google.com',
              generateAccessTokenRequest=(
                  self.messages.GenerateAccessTokenRequest(
                      scope=config.CLOUDSDK_SCOPES))),
          self.messages.GenerateAccessTokenResponse(
              accessToken='impersonation-token',
              expireTime='2016-01-08T00:00:00Z'))

      # Mock response from util.GenerateIdToken
      new_token_id = 'new-id-token'
      self.mock_client.projects_serviceAccounts.GenerateIdToken.Expect(
          self.gen_id_msg(
              name='projects/-/serviceAccounts/asdf@google.com',
              generateIdTokenRequest=self.messages.GenerateIdTokenRequest(
                  audience=audience, includeEmail=False)),
          self.messages.GenerateIdTokenResponse(token=new_token_id)
      )
      # Load test impersonation token
      loaded = store.Load(allow_account_impersonation=True)
      loaded.token_response = {'id_token': 'old-id-token'}
      audience = 'https://service-hash-uc.a.run.app'
      config.CLOUDSDK_CLIENT_ID = audience
      store.Refresh(loaded, is_impersonated_credential=True)
      self.assertEqual(loaded.token_response['id_token'], new_token_id)
    finally:  # Clean-Up
      store.IMPERSONATION_TOKEN_PROVIDER = None

  def testRefreshImpersonationAccountImpersonationNotConfigured(self):
    self.StartObjectPatch(util, 'GenerateAccessToken')
    credentials = util.ImpersonationCredentials('service-account-id',
                                                'access-token',
                                                '2016-01-08T00:00:00Z',
                                                config.CLOUDSDK_SCOPES)
    store.IMPERSONATION_TOKEN_PROVIDER = None
    with self.assertRaisesRegex(
        store.AccountImpersonationError,
        'gcloud is configured to impersonate a service account '
        'but impersonation support is not available.'):
      store.Refresh(credentials, is_impersonated_credential=True)

  def testRefreshImpersonationAccountImpersonationBadCred(self):
    self.StartObjectPatch(util, 'GenerateAccessToken')

    def refresh(fake_client):
      del fake_client

    bad_credential = client.OAuth2Credentials(None, None, None, None, None,
                                              None, None)
    bad_credential.refresh = refresh

    try:
      store.IMPERSONATION_TOKEN_PROVIDER = (
          util.ImpersonationAccessTokenProvider())
      with self.assertRaisesRegex(store.AccountImpersonationError,
                                  'Invalid impersonation account for refresh'):
        store.Refresh(bad_credential, is_impersonated_credential=True)
    finally:  # Clean-Up
      store.IMPERSONATION_TOKEN_PROVIDER = None


if __name__ == '__main__':
  sdk_test_base.main()
