# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

import datetime

from googlecloudsdk.api_lib.iamcredentials import util
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import google_auth_credentials
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

import httplib2
from oauth2client import client

from google.auth import impersonated_credentials


class ImpersonationTest(cli_test_base.CliTestBase,
                        credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    properties.VALUES.core.account.Set('fakeuser')
    fake_creds = self.MakeUserAccountCredentialsGoogleAuth()
    fake_creds.token = 'access-token'
    store.Store(fake_creds)
    self.refresh_mock = self.StartObjectPatch(
        google_auth_credentials.UserCredWithReauth, 'refresh')
    self.StartObjectPatch(client.OAuth2Credentials, 'refresh')

    self.request_mock = self.StartObjectPatch(
        httplib2.Http, 'request', autospec=True)
    self.StartObjectPatch(
        impersonated_credentials,
        '_make_iam_token_request',
        return_value=('impersonation-token',
                      datetime.datetime(9999, 2, 3, 14, 15, 16)))

  def testImpersonation(self):

    self.request_mock.return_value = (httplib2.Response({'status': 200}),
                                      b'{"projects": []}')

    try:
      store.IMPERSONATION_TOKEN_PROVIDER = (
          util.ImpersonationAccessTokenProvider())
      self.Run('--impersonate-service-account asdf@google.com projects list')
      access_token = self.request_mock.call_args[1]['headers'][b'authorization']
      # Make sure the request was made with the service account token.
      self.assertEqual(access_token, b'Bearer impersonation-token')
    finally:
      store.IMPERSONATION_TOKEN_PROVIDER = None


if __name__ == '__main__':
  test_case.main()
