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

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.resource import resource_projector
from tests.lib import cli_test_base
from tests.lib import test_case


class ListTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_accounts = self.StartObjectPatch(store, 'AvailableAccounts',
                                               autospec=True)

  def Project(self):
    return 'junkproj'

  def AssertSerializedResultEquals(self, expected, actual):
    self.assertEqual(expected, resource_projector.MakeSerializable(actual))

  def testList(self):
    properties.VALUES.core.account.Set(None)
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    expected = [
        {'account': 'acct1', 'status': ''},
        {'account': 'acct2', 'status': ''},
        {'account': 'acct3', 'status': ''},
    ]
    actual = self.Run('auth list --format=disable')
    self.AssertSerializedResultEquals(expected, actual)

  def testListOutput(self):
    properties.VALUES.core.account.Set(None)
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    self.Run('auth list')
    self.AssertOutputContains("""\
Credentialed Accounts
ACTIVE ACCOUNT
acct1
acct2
acct3
""", normalize_space=True)

  def testActive(self):
    properties.VALUES.core.account.Set('acct2')
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    expected = [
        {'account': 'acct1', 'status': ''},
        {'account': 'acct2', 'status': 'ACTIVE'},
        {'account': 'acct3', 'status': ''},
    ]
    actual = self.Run('auth list --format=disable')
    self.AssertSerializedResultEquals(expected, actual)

  def testActiveOutput(self):
    properties.VALUES.core.account.Set('acct2')
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    self.Run('auth list')
    self.AssertOutputContains("""\
Credentialed Accounts
ACTIVE ACCOUNT
acct1
* acct2
acct3
""", normalize_space=True)

  def testAccount(self):
    properties.VALUES.core.account.Set('acct2')
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    expected = [
        {'account': 'acct2', 'status': 'ACTIVE'},
    ]
    actual = self.Run(
        'auth list --filter-account=acct2 --format=disable')
    self.AssertSerializedResultEquals(expected, actual)

  def testAccountOutput(self):
    properties.VALUES.core.account.Set('acct2')
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    self.Run('auth list --filter-account acct2')
    self.AssertOutputEquals("""\
Credentialed Accounts
ACTIVE ACCOUNT
* acct2
""", normalize_space=True)

    self.ClearOutput()
    self.Run('auth list --format=json')
    self.AssertOutputContains("""\
[
  {
    "account": "acct1",
    "status": ""
  },
  {
    "account": "acct2",
    "status": "ACTIVE"
  },
  {
    "account": "acct3",
    "status": ""
  }
]
""")

    self.ClearOutput()
    self.Run('auth list --filter=account:acct2')
    self.AssertOutputContains("""\
Credentialed Accounts
ACTIVE ACCOUNT
* acct2
""", normalize_space=True)

  def testNonExistingAccount(self):
    properties.VALUES.core.account.Set('acct2')
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    expected = []
    actual = list(self.Run('auth list --filter-account=junk --format=disable'))
    self.AssertSerializedResultEquals(expected, actual)

  def testNonExistingAccountOutput(self):
    properties.VALUES.core.account.Set('acct2')
    accts = ['acct1', 'acct2', 'acct3']
    self.mock_accounts.return_value = accts

    self.Run('auth list --filter-account junk')
    self.AssertOutputEquals('')
    self.AssertErrEquals("""
No credentialed accounts.

To login, run:
  $ gcloud auth login `ACCOUNT`

""")

  def testNone(self):
    properties.VALUES.core.account.Set(None)
    accts = []
    self.mock_accounts.return_value = accts

    expected = []
    actual = list(self.Run('auth list --format=disable'))
    self.AssertSerializedResultEquals(expected, actual)

  def testNoneOutput(self):
    properties.VALUES.core.account.Set(None)
    accts = []
    self.mock_accounts.return_value = accts

    self.Run('auth list')
    self.AssertErrContains('No credentialed accounts.')


if __name__ == '__main__':
  test_case.main()
