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
from googlecloudsdk.core.credentials import google_auth_credentials
from googlecloudsdk.core.credentials import http
from googlecloudsdk.core.credentials import store
from tests.lib import sdk_test_base
from tests.lib.core.credentials import credentials_test_base

import httplib2
from oauth2client import client

from google.auth import impersonated_credentials


class UtilTests(sdk_test_base.WithFakeAuth):

  def SetUp(self):
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

  def testGenerateAccessToken(self):
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
    self.mock_client.projects_serviceAccounts.GenerateIdToken.Expect(
        self.gen_id_msg(
            name='projects/-/serviceAccounts/asdf@google.com',
            generateIdTokenRequest=self.messages.GenerateIdTokenRequest(
                audience=audience, includeEmail=False)),
        self.messages.GenerateIdTokenResponse(token='id-token')
    )

    result = util.GenerateIdToken('asdf@google.com', audience)

    self.assertEqual(result, 'id-token')

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


class UtilTestsGoogleAuth(sdk_test_base.SdkBase,
                          credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    properties.VALUES.core.account.Set('fakeuser')
    fake_creds = self.MakeUserAccountCredentialsGoogleAuth()
    fake_creds.token = 'access-token'
    store.Store(fake_creds)
    properties.VALUES.auth.impersonate_service_account.Set('asdf@google.com')

    self.refresh_mock = self.StartObjectPatch(
        google_auth_credentials.UserCredWithReauth, 'refresh')
    self.StartObjectPatch(client.OAuth2Credentials, 'refresh')

    self.request_mock = self.StartObjectPatch(
        httplib2.Http,
        'request',
        autospec=True,
        return_value=(httplib2.Response({'status': 200}), b''))
    self.impersonation_token = 'impersonation-token'
    self.StartObjectPatch(
        impersonated_credentials,
        '_make_iam_token_request',
        return_value=(self.impersonation_token,
                      datetime.datetime(9999, 2, 3, 14, 15, 16)))

    store.IMPERSONATION_TOKEN_PROVIDER = (
        util.ImpersonationAccessTokenProvider())

  def TearDown(self):
    store.IMPERSONATION_TOKEN_PROVIDER = None

  def testServiceAccountImpersonation(self):

    http.Http().request('http://foo.com', 'GET', None, {})
    access_token = self.request_mock.call_args[1]['headers'][b'authorization']
    self.assertEqual(access_token,
                     b'Bearer ' + self.impersonation_token.encode('utf-8'))


if __name__ == '__main__':
  sdk_test_base.main()
