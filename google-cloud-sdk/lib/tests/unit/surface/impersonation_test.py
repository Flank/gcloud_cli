# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Test the top level service account impersonation flag."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.iamcredentials import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import test_case

import httplib2
from oauth2client import client


class ImpersonationTest(cli_test_base.CliTestBase):

  def SetUp(self):
    properties.VALUES.core.account.Set('fakeuser')
    self.fake_cred = client.OAuth2Credentials(
        'access-token', 'client_id', 'client_secret',
        'fake-token', None, 'token_uri', 'user_agent',
        scopes=config.CLOUDSDK_SCOPES)
    store.Store(self.fake_cred)
    self.refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                              'refresh')

    self.mock_client = mock.Client(apis.GetClientClass('iamcredentials', 'v1'))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = self.mock_client.MESSAGES_MODULE
    self.gen_request_msg = (
        self.messages
        .IamcredentialsProjectsServiceAccountsGenerateAccessTokenRequest)

    self.request_mock = self.StartObjectPatch(
        httplib2.Http, 'request', autospec=True)

  def testImpersonation(self):
    self.mock_client.projects_serviceAccounts.GenerateAccessToken.Expect(
        self.gen_request_msg(
            name='projects/-/serviceAccounts/asdf@google.com',
            generateAccessTokenRequest=self.messages.GenerateAccessTokenRequest(
                scope=config.CLOUDSDK_SCOPES)),
        self.messages.GenerateAccessTokenResponse(
            accessToken='impersonation-token', expireTime='expire-time')
    )

    self.request_mock.return_value = (httplib2.Response({'status': 200}),
                                      b'{"projects": []}')

    try:
      store.IMPERSONATION_TOKEN_PROVIDER = (
          util.ImpersonationAccessTokenProvider())
      self.Run(
          'alpha --impersonate-service-account asdf@google.com projects list')
      access_token = self.request_mock.call_args[0][4][b'Authorization']
      # Make sure the request was made with the service account token.
      self.assertEqual(access_token, b'Bearer impersonation-token')
    finally:
      store.IMPERSONATION_TOKEN_PROVIDER = None


if __name__ == '__main__':
  test_case.main()
