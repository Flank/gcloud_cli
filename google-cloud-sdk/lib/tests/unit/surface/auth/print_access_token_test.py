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

from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

from oauth2client import client
from google.auth import exceptions as google_auth_exceptions


class PrintAccessTokenTestUsingGoogleAuth(sdk_test_base.WithFakeAuth,
                                          cli_test_base.CliTestBase):

  def testPrint(self):
    def FakeRefresh(cred, http=None):
      del http
      if cred:
        cred.token = 'NewFakeAccessToken'

    self.StartObjectPatch(store, 'Refresh', side_effect=FakeRefresh)
    self.Run('auth print-access-token')
    self.AssertOutputEquals('NewFakeAccessToken\n')

  def testRefreshWithException(self):
    self.StartObjectPatch(
        store, 'Refresh', side_effect=google_auth_exceptions.RefreshError())
    with self.assertRaises(auth_exceptions.AuthenticationError):
      self.Run('auth print-access-token')

  def testBadCred(self):
    def FakeRefresh(cred, http=None):
      del http
      if cred:
        cred.token = None

    self.StartObjectPatch(store, 'Refresh', side_effect=FakeRefresh)
    with self.assertRaisesRegex(auth_exceptions.InvalidCredentialsError,
                                'No access token could be obtained'):
      self.Run('auth print-access-token')


class PrintAccessTokenTestUsingOauth2client(sdk_test_base.WithFakeAuth,
                                            cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartObjectPatch(
        properties.VALUES.auth.disable_google_auth,
        'GetBool',
        return_value=True)

  def testPrint(self):
    def FakeRefresh(cred, http=None):
      del http
      if cred:
        cred.access_token = 'NewFakeAccessToken'

    self.StartObjectPatch(store, 'Refresh', side_effect=FakeRefresh)
    self.Run('auth print-access-token')
    self.AssertOutputEquals('NewFakeAccessToken\n')

  def testRefreshWithException(self):
    self.StartObjectPatch(store, 'Refresh', side_effect=client.Error())
    with self.assertRaises(auth_exceptions.AuthenticationError):
      self.Run('auth print-access-token')

  def testBadCred(self):
    def FakeRefresh(cred, http=None):
      del http
      if cred:
        cred.access_token = None

    self.StartObjectPatch(store, 'Refresh', side_effect=FakeRefresh)
    with self.assertRaisesRegex(auth_exceptions.InvalidCredentialsError,
                                'No access token could be obtained'):
      self.Run('auth print-access-token')


if __name__ == '__main__':
  test_case.main()
