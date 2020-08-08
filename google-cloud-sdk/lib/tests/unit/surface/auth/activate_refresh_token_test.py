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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.auth import refresh_token
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import test_case

from oauth2client import client


class ActivateRefreshTokenTest(cli_test_base.CliTestBase):

  def SetUp(self):
    properties.PersistProperty(properties.VALUES.core.account, 'junk')

  def Project(self):
    return 'junkproj'

  def testActivate(self):
    self.StartObjectPatch(store, 'Refresh', autospec=True)
    account = 'foo@google.com'
    token = 'asdf'

    self.Run(
        'auth activate-refresh-token {account} {token}'.format(
            account=account, token=token))

    self.assertEqual(token, refresh_token.GetForAccount(account))
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Activated refresh token credentials: [foo@google.com]\n')

  def testActivateStdin(self):
    self.StartObjectPatch(store, 'Refresh', autospec=True)
    account = 'foo@google.com'
    token = 'asdf'

    self.WriteInput(token)
    self.Run(
        '--project=myproj auth activate-refresh-token {account}'.format(
            account=account))

    self.assertEqual(token, refresh_token.GetForAccount(account))
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('myproj', properties.VALUES.core.project.Get())
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "Refresh token: "}'
        'Activated refresh token credentials: [foo@google.com]\n')

  def testActivate_RefreshException(self):
    self.StartObjectPatch(store, 'Refresh',
                          side_effect=client.AccessTokenRefreshError)
    account = 'foo@google.com'
    token = 'asdf'

    with self.assertRaises(store.TokenRefreshError):
      self.Run(
          'auth activate-refresh-token {account} {token}'.format(
              account=account, token=token))

    self.AssertOutputEquals('')
    self.AssertErrContains(
        'There was a problem refreshing your current auth tokens')

  def testNoToken(self):
    refresh_mock = self.StartObjectPatch(store, 'Refresh')
    account = 'foo@google.com'
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[token\]: No value provided.'):
      self.Run(
          'auth activate-refresh-token account={account}'
          .format(account=account))
    self.assertFalse(refresh_mock.called)


class ActivateRefreshTokenOauth2ClientTest(ActivateRefreshTokenTest):

  def SetUp(self):
    properties.VALUES.auth.disable_load_google_auth.Set(True)


if __name__ == '__main__':
  test_case.main()
