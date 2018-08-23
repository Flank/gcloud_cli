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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import test_case


class RevokeTest(cli_test_base.CliTestBase):

  def SetUp(self):
    properties.PersistProperty(properties.VALUES.core.account, 'junk')
    self.mock_accounts = self.StartObjectPatch(store, 'AvailableAccounts',
                                               autospec=True)
    self.mock_revoke = self.StartObjectPatch(store, 'Revoke', autospec=True)

  def testRevoke(self):
    self.mock_accounts.side_effect = [
        ['acct1', 'acct2', 'acct3'],
        ['acct2', 'acct3']
    ]

    result = self.Run('auth revoke acct1')
    self.assertEqual(['acct1'], result)
    self.mock_revoke.assert_called_once_with('acct1')
    self.assertEqual('junk', properties.VALUES.core.account.Get())
    self.AssertOutputEquals('Revoked credentials:\n - acct1\n')
    self.AssertErrEquals("""\
Credentialed Accounts
ACTIVE ACCOUNT
acct2
acct3
""", normalize_space=True)

  def testAll(self):
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    result = self.Run('auth revoke acct1 --all')
    self.assertEqual(accts, result)
    for acct in accts:
      self.mock_revoke.assert_any_call(acct)
    self.assertEqual('junk', properties.VALUES.core.account.Get())

  def testActive(self):
    properties.PersistProperty(properties.VALUES.core.account, 'acct1')
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    result = self.Run('auth revoke')
    self.assertEqual(['acct1'], result)
    self.mock_revoke.assert_called_once_with('acct1')
    self.assertEqual(None, properties.VALUES.core.account.Get())

  def testNone(self):
    properties.PersistProperty(properties.VALUES.core.account, None)
    self.mock_accounts.return_value = []

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[accounts\]: No credentials available to revoke.'):
      self.Run('auth revoke')

  def testUnknown(self):
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    with self.assertRaisesRegex(
        exceptions.UnknownArgumentException,
        r'Unknown value for \[accounts\]: foo'):
      self.Run('auth revoke foo')


if __name__ == '__main__':
  test_case.main()
