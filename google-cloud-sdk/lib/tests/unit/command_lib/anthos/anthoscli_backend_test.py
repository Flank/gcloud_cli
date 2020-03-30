# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for anthoscli_backend module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime


from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store
from tests.lib import sdk_test_base
from tests.lib import test_case
from oauth2client import client


class AnthoscliBackendTest(sdk_test_base.SdkBase):
  """Unit tests for anthoscli_backend module."""

  def SetUp(self):
    self.fake_account = 'fake-account'
    properties.VALUES.core.account.Set(self.fake_account)
    self.fake_cred = client.OAuth2Credentials(
        'access-token',
        'client_id',
        'client_secret',
        'fake-token',
        datetime.datetime(2017, 1, 8, 0, 0, 0),
        'token_uri',
        'user_agent',
        scopes=config.CLOUDSDK_SCOPES)

  def testGetAuthTokens(self):
    self.mock_load = self.StartObjectPatch(c_store,
                                           'LoadFreshCredential',
                                           return_value=self.fake_cred)
    expected = ('{"auth_token": "access-token"}')
    actual = anthoscli_backend.GetAuthToken('fake-account', 'fake-operation')
    self.mock_load.assert_called_with('fake-account',
                                      allow_account_impersonation=False)
    self.assertEqual(expected, actual)

  def testGetAuthTokensWithError(self):
    self.mock_load = self.StartObjectPatch(
        c_store, 'LoadFreshCredential',
        side_effect=c_store.ReauthenticationException('Foo'))
    with self.assertRaisesRegex(anthoscli_backend.AnthosAuthException, 'Foo'):
      anthoscli_backend.GetAuthToken('fake-account', 'fake-operation')


if __name__ == '__main__':
  test_case.main()
