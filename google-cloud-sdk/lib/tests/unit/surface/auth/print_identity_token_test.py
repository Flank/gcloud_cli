# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce
import google.auth.compute_engine.credentials as google_auth_gce_creds
import google.oauth2.service_account as google_auth_service_account


def GetFakeRefresh(fake_id_token):

  def FakeRefresh(cred,
                  http=None,
                  is_impersonated_credential=False,
                  include_email=False,
                  gce_token_format='standard',
                  gce_include_license=False):
    del http
    del is_impersonated_credential
    del include_email
    del gce_token_format
    del gce_include_license

    if cred:
      if c_creds.IsOauth2ClientCredentials(cred):
        cred.token_response = {'id_token': fake_id_token}
      else:
        cred.id_tokenb64 = fake_id_token

  return FakeRefresh


class PrintIdentityTokenTest(sdk_test_base.WithFakeAuth,
                             cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.use_google_auth = False

  def TearDown(self):
    # 'gcloud auth print-identity-token' can change the global state
    # 'config.CLOUDSDK_CLIENT_ID'. Reset it after running each test.
    config.CLOUDSDK_CLIENT_ID = '32555940559.apps.googleusercontent.com'

  def testIsGceAccountCredentials(self):
    oauth2client_cred = oauth2client_gce.AppAssertionCredentials()
    google_auth_cred = google_auth_gce_creds.Credentials()
    self.assertTrue(auth_util.IsGceAccountCredentials(oauth2client_cred))
    self.assertTrue(auth_util.IsGceAccountCredentials(google_auth_cred))

  def testIsServiceAccountCredential(self):
    oauth2client_cred = service_account.ServiceAccountCredentials(None, 'email')
    google_auth_cred = google_auth_service_account.Credentials(
        None, 'email', 'token_uri')
    self.assertTrue(auth_util.IsServiceAccountCredential(oauth2client_cred))
    self.assertTrue(auth_util.IsServiceAccountCredential(google_auth_cred))

  def testPrintServiceAccount(self):

    self.StartObjectPatch(auth_util,
                          'IsServiceAccountCredential',
                          return_value=True)
    self.StartObjectPatch(
        store, 'Refresh', side_effect=GetFakeRefresh('FakeIdToken'))
    self.Run('auth print-identity-token')
    self.AssertOutputEquals('FakeIdToken\n')

  def testPrintImpersonatedAccount(self):

    self.StartObjectPatch(auth_util,
                          'IsServiceAccountCredential',
                          return_value=False)
    self.StartObjectPatch(auth_util,
                          'IsImpersonationCredential',
                          return_value=True)
    self.StartObjectPatch(
        store, 'Refresh', side_effect=GetFakeRefresh('FakeIdToken'))
    self.Run('auth print-identity-token '
             '--impersonate-service-account foo@google.com')
    self.AssertOutputEquals('FakeIdToken\n')

  def testPrintUserAccount(self):

    self.StartObjectPatch(auth_util,
                          'IsServiceAccountCredential',
                          return_value=False)
    self.StartObjectPatch(auth_util,
                          'IsImpersonationCredential',
                          return_value=False)
    self.StartObjectPatch(
        store, 'Refresh', side_effect=GetFakeRefresh('FakeIdToken'))
    self.Run('auth print-identity-token')
    self.AssertOutputEquals('FakeIdToken\n')

  def testBadCred(self):

    self.StartObjectPatch(auth_util,
                          'IsServiceAccountCredential',
                          return_value=True)
    self.StartObjectPatch(store, 'Refresh', side_effect=GetFakeRefresh(None))
    with self.assertRaisesRegex(auth_exceptions.InvalidIdentityTokenError,
                                'No identity token can be obtained '):
      self.Run('auth print-identity-token')

  def testPrintWithServiceAccountAndAudience(self):

    self.StartObjectPatch(auth_util,
                          'IsServiceAccountCredential',
                          return_value=True)
    self.StartObjectPatch(
        store, 'Refresh', side_effect=GetFakeRefresh('FakeIdToken'))
    self.Run('auth print-identity-token --audiences='
             '"FakeAudienceHttpString"')
    self.assertEqual(config.CLOUDSDK_CLIENT_ID, 'FakeAudienceHttpString')
    self.AssertOutputEquals('FakeIdToken\n')

  def testPrintWithImpersonatedAccountAndAudience(self):

    self.StartObjectPatch(auth_util,
                          'IsServiceAccountCredential',
                          return_value=False)
    self.StartObjectPatch(auth_util,
                          'IsImpersonationCredential',
                          return_value=True)
    self.StartObjectPatch(
        store, 'Refresh', side_effect=GetFakeRefresh('FakeIdToken'))
    self.Run('auth print-identity-token --audiences='
             '"FakeAudienceHttpString"')
    self.assertEqual(config.CLOUDSDK_CLIENT_ID, 'FakeAudienceHttpString')
    self.AssertOutputEquals('FakeIdToken\n')

  def testPrintWithGCEAccountAndAudience(self):

    self.StartObjectPatch(auth_util,
                          'IsServiceAccountCredential',
                          return_value=False)
    self.StartObjectPatch(auth_util,
                          'IsImpersonationCredential',
                          return_value=False)
    self.StartObjectPatch(auth_util,
                          'IsGceAccountCredentials',
                          return_value=True)
    self.StartObjectPatch(
        store, 'Refresh', side_effect=GetFakeRefresh('FakeIdToken'))
    self.Run('auth print-identity-token --audiences='
             '"FakeAudienceHttpString"')
    self.assertEqual(config.CLOUDSDK_CLIENT_ID, 'FakeAudienceHttpString')
    self.AssertOutputEquals('FakeIdToken\n')

  def testPrintWithAudienceWrongAccountType(self):

    self.StartObjectPatch(auth_util,
                          'ValidIdTokenCredential',
                          return_value=False)
    with self.assertRaisesRegex(auth_exceptions.WrongAccountTypeError,
                                'Invalid account Type for `--audiences`. '
                                'Requires valid service account'):
      self.Run('auth print-identity-token --audiences='
               '"FakeAudienceHttpString"')

  def testSpecifyTokenFormatForNonGCECredentials(self):
    self.StartObjectPatch(
        auth_util, 'IsGceAccountCredentials', return_value=False)
    with self.AssertRaisesExceptionMatches(
        auth_exceptions.WrongAccountTypeError,
        'Invalid account type for `--token-format` or `--include-license`. '
        'Requires a valid GCE service account.'):
      self.Run(
          'auth print-identity-token --token-format=full --include-license')

  def testSpecifyStandardTokenFormat_IncludeLicense(self):
    self.StartObjectPatch(
        auth_util, 'IsGceAccountCredentials', return_value=True)
    with self.AssertRaisesExceptionMatches(
        auth_exceptions.GCEIdentityTokenError,
        '`--include-license` can only be specified when `--token-format=full`.'
    ):
      self.Run('auth print-identity-token --include-license')

  def testSpecifyIncludeEmailForNonImpersonateServiceAccount(self):
    self.StartObjectPatch(
        auth_util, 'IsImpersonationCredential', return_value=False)
    with self.AssertRaisesExceptionMatches(
        auth_exceptions.WrongAccountTypeError,
        'Invalid account type for `--include-email`. '
        'Requires an impersonate service account.'):
      self.Run('auth print-identity-token --include-email')

  def testRefreshGceAccountIdToken_Full_IncludeLicense(self):

    self.StartObjectPatch(
        auth_util, 'IsGceAccountCredentials', return_value=True)

    mock_refresh = self.StartObjectPatch(
        store, 'Refresh', side_effect=GetFakeRefresh('FakeIdToken'))

    self.Run('auth print-identity-token --include-license --token-format=full')
    mock_refresh.assert_called_once_with(
        mock.ANY,
        is_impersonated_credential=False,
        include_email=False,
        gce_token_format='full',
        gce_include_license=True)
    self.AssertOutputEquals('FakeIdToken\n')

  def testRefreshImpersonateSAIdToken_IncludeEmail(self):

    self.StartObjectPatch(
        auth_util, 'IsImpersonationCredential', return_value=True)

    mock_refresh = self.StartObjectPatch(
        store, 'Refresh', side_effect=GetFakeRefresh('FakeIdToken'))

    self.Run('auth print-identity-token --include-email')
    mock_refresh.assert_called_once_with(
        mock.ANY,
        is_impersonated_credential=True,
        include_email=True,
        gce_token_format='standard',
        gce_include_license=False)
    self.AssertOutputEquals('FakeIdToken\n')


class PrintIdentityTokenGoogleAuthTest(PrintIdentityTokenTest):

  def PreSetUp(self):
    properties.VALUES.auth.disable_load_google_auth.Set(False)
    self.use_google_auth = True


if __name__ == '__main__':
  test_case.main()
