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

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.credentials import google_auth_credentials as c_google_auth
from googlecloudsdk.core.credentials import store as c_store
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

from oauth2client.contrib import reauth

from google.auth import _default as google_auth_default
from google.auth import exceptions as google_auth_exceptions


def _MockRefreshGrant(request,
                      token_uri,
                      refresh_token,
                      client_id,
                      client_secret,
                      scopes=None,
                      rapt_token=None):
  del request, token_uri, refresh_token, client_id, client_secret, scopes
  del rapt_token
  return 'new_access_token', 'new_refresh_token', None, {'id_token': 'id_token'}


class PrintAccessTokenTest(cli_test_base.CliTestBase,
                           credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    self.mock_default_creds = self.StartObjectPatch(google_auth_default,
                                                    'default')
    self.mock_default_creds.return_value = (
        self.MakeUserAccountCredentialsGoogleAuth(), 'project')
    self.mock_refresh_grant = self.StartObjectPatch(c_google_auth,
                                                    '_RefreshGrant')
    self.mock_refresh_grant.side_effect = _MockRefreshGrant

  def testPrint(self):
    self.Run('auth application-default print-access-token')
    self.mock_default_creds.assert_called_with(
        scopes=[auth_util.CLOUD_PLATFORM_SCOPE])
    self.AssertOutputContains('new_access_token')

  def testNoCred(self):
    self.mock_default_creds.side_effect = google_auth_exceptions.DefaultCredentialsError(
        'no file')

    with self.assertRaisesRegex(calliope_exceptions.ToolException, 'no file'):
      self.Run('auth application-default print-access-token')

  def testImpersonateServiceAccount(self):
    self.Run('auth application-default print-access-token '
             '--impersonate-service-account '
             'serviceaccount@project.iam.gserviceaccount.com')
    self.AssertErrContains(
        'Impersonate service account '
        "'serviceaccount@project.iam.gserviceaccount.com' is detected.")

  def testRaiseTokenRefreshError(self):
    self.mock_refresh_grant.side_effect = google_auth_exceptions.RefreshError(
        'API error')
    with self.AssertRaisesExceptionMatches(
        c_store.TokenRefreshError, '$ gcloud auth application-default login'):
      self.Run('auth application-default print-access-token')

  def testRaiseTokenRefreshReauthError(self):
    self.mock_refresh_grant.side_effect = c_google_auth.ReauthRequiredError(
        'API error')
    self.StartObjectPatch(reauth, 'GetRaptToken')
    with self.AssertRaisesExceptionMatches(
        c_store.TokenRefreshReauthError,
        '$ gcloud auth application-default login'):
      self.Run('auth application-default print-access-token')


if __name__ == '__main__':
  test_case.main()
