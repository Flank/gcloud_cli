# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
            accessToken='access-token', expireTime='expire-time')
    )
    result = util.GenerateAccessToken('asdf@google.com', config.CLOUDSDK_SCOPES)
    self.assertEqual(result.accessToken, 'access-token')
    self.assertEqual(result.expireTime, 'expire-time')

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
            accessToken=fake_token, expireTime='expire-time')
    )

    request_mock = self.StartObjectPatch(
        httplib2.Http, 'request',
        return_value=(httplib2.Response({'status': 200}), ''))
    try:
      store.IMPERSONATION_TOKEN_PROVIDER = (
          util.ImpersonationAccessTokenProvider())
      http.Http().request('http://foo.com', 'GET', None, {})
      access_token = request_mock.call_args[0][3][b'Authorization']
      self.assertEqual(access_token, b'Bearer ' + fake_token.encode('utf8'))
    finally:
      store.IMPERSONATION_TOKEN_PROVIDER = None


if __name__ == '__main__':
  sdk_test_base.main()
