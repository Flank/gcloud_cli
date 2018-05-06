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
from __future__ import unicode_literals

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case

import mock
from oauth2client import client


class PrintAccessTokenTest(cli_test_base.CliTestBase):

  def GetGoogleCredentials(self, token, scoped_required=False):
    cred_mock = mock.MagicMock(autospec=True)
    cred_mock.create_scoped_required.return_value = scoped_required

    if token:
      cred_mock.get_access_token.return_value = client.AccessTokenInfo(
          access_token=token, expires_in=0)
    else:
      cred_mock.get_access_token.return_value = None

    return cred_mock

  def testPrint(self):
    # It would be best to use autospec here, but mock doesn't support it for
    # static methods yet.
    mock_get_adc = self.StartPatch(
        'oauth2client.client.GoogleCredentials.get_application_default')
    mock_get_adc.return_value = self.GetGoogleCredentials(
        token='foo_access_token')

    self.Run('beta auth application-default print-access-token')
    self.AssertOutputContains('foo_access_token')

  def testBadCred(self):
    # It would be best to use autospec here, but mock doesn't support it for
    # static methods yet.
    mock_get_adc = self.StartPatch(
        'oauth2client.client.GoogleCredentials.get_application_default')
    mock_get_adc.return_value = self.GetGoogleCredentials(token=None)

    with self.assertRaisesRegex(exceptions.ToolException,
                                'No access token could be obtained'):
      self.Run('beta auth application-default print-access-token')

  def testNoCred(self):
    mock_get_adc = self.StartPatch(
        'oauth2client.client.GoogleCredentials.get_application_default')
    mock_get_adc.side_effect = client.ApplicationDefaultCredentialsError(
        'no file')

    with self.assertRaisesRegex(exceptions.ToolException,
                                'no file'):
      self.Run('beta auth application-default print-access-token')

  def testScopedDefault(self):
    # It would be best to use autospec here, but mock doesn't support it for
    # static methods yet.
    mock_get_adc = self.StartPatch(
        'oauth2client.client.GoogleCredentials.get_application_default')
    mock_creds = self.GetGoogleCredentials(
        token='foo_access_token', scoped_required=True)
    mock_get_adc.return_value = mock_creds

    mock_creds.create_scoped.return_value = mock_creds

    self.Run('beta auth application-default print-access-token')
    self.AssertOutputContains('foo_access_token')

    mock_creds.create_scoped.assert_called_once_with(
        [auth_util.CLOUD_PLATFORM_SCOPE])

  def testServiceAccountTokenURIOverride(self):
    # It would be best to use autospec here, but mock doesn't support it for
    # static methods yet.
    mock_get_adc = self.StartPatch(
        'oauth2client.client.GoogleCredentials.get_application_default')
    mock_creds = self.GetGoogleCredentials(
        token='foo_access_token', scoped_required=True)

    mock_creds.serialization_data = {'type': client.SERVICE_ACCOUNT}
    properties.VALUES.auth.token_host.Set('token_uri_override')

    mock_get_adc.return_value = mock_creds
    mock_creds.create_scoped.return_value = mock_creds

    self.Run('beta auth application-default print-access-token')
    self.AssertOutputContains('foo_access_token')

    mock_creds.create_scoped.assert_called_once_with(
        [auth_util.CLOUD_PLATFORM_SCOPE], token_uri='token_uri_override')


if __name__ == '__main__':
  test_case.main()
