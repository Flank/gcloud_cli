# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

import os

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import gce
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import test_case

import mock
from mock import patch
from oauth2client import client


class LoginTest(cli_test_base.CliTestBase, test_case.WithInput):

  def SetUp(self):
    self.mock_run_webflow = self.StartObjectPatch(
        store, 'RunWebFlow', autospec=True)
    self.mock_webflow = self.StartObjectPatch(
        store, 'AcquireFromWebFlow', autospec=True)
    self.fake_webflow = mock.MagicMock()
    self.mock_create_webflow = self.StartObjectPatch(
        client, 'flow_from_clientsecrets', autospec=True)
    self.mock_create_webflow.return_value = self.fake_webflow

    self.mock_browser = self.StartPatch('webbrowser.get', autospec=True)
    self.mock_browser.return_value.name = 'Chrome'

    self.mock_adc_file_path = self.StartObjectPatch(auth_util, 'ADCFilePath')
    self.mock_adc_file_path.return_value = os.path.join(
        self.temp_path, 'ADC')

    self.mock_metadata = self.StartObjectPatch(gce, 'Metadata', autospec=True)
    self.mock_metadata.return_value.connected = False
    self.mock_metadata.return_value.Project = lambda: 'metadata-project'
    self.StartDictPatch('os.environ', {'DISPLAY': ':1'})

  def GetFakeCred(self, account):
    cred_mock = mock.MagicMock()
    cred_mock.id_token = {'email': account}
    cred_mock.access_token = ''
    cred_mock.client_id = ''
    cred_mock.client_secret = ''
    cred_mock.refresh_token = ''
    cred_mock.token_expiry = ''
    cred_mock.token_uri = ''
    cred_mock.user_agent = ''
    cred_mock.revoke_uri = ''
    return cred_mock

  def Login(self, more_args=''):
    return self.Run('beta auth application-default login {more_args}'.format(
        more_args=more_args))

  def testBasicLogin(self):
    """Basic login with default client id and default scopes."""
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_webflow.return_value = fake_cred
    result = self.Login()
    self.assertEqual(fake_cred, result)

    self.mock_webflow.assert_called_once_with(
        launch_browser=True,
        scopes=auth_util.DEFAULT_SCOPES,
        client_id=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID,
        client_secret=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET)

    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'ADC')

  def testLoginWithScopes(self):
    """Login with scopes provided."""
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_webflow.return_value = fake_cred
    result = self.Login(more_args='--scopes scope1,scope2')
    self.assertEqual(fake_cred, result)

    self.mock_webflow.assert_called_once_with(
        launch_browser=True,
        scopes=['scope1', 'scope2'],
        client_id=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID,
        client_secret=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET)

    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'ADC')

  def testLoginWithClientIdFile(self):
    """Login with client id file provided."""
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_run_webflow.return_value = fake_cred
    client_id_file = self.Resource(
        'tests', 'unit', 'surface', 'auth', 'test_data', 'client_id_file.json')
    result = self.Login(
        more_args='--client-id-file {file}'.format(file=client_id_file))
    self.assertEqual(fake_cred, result)

    self.mock_create_webflow.assert_called_once_with(
        filename=client_id_file,
        scope=auth_util.DEFAULT_SCOPES)
    self.mock_run_webflow.assert_called_once_with(
        self.fake_webflow,
        launch_browser=True)

    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'ADC')

  def testLoginWithClientIdFileAndScopes(self):
    """Login with both client id file and scopes provided."""
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_run_webflow.return_value = fake_cred
    client_id_file = self.Resource(
        'tests', 'unit', 'surface', 'auth', 'test_data', 'client_id_file.json')

    result = self.Login(
        more_args=' --scopes scope1,scope2 '
                  '--client-id-file {file}'.format(file=client_id_file))
    self.assertEqual(fake_cred, result)

    self.mock_create_webflow.assert_called_once_with(
        filename=client_id_file,
        scope=['scope1', 'scope2'])
    self.mock_run_webflow.assert_called_once_with(
        self.fake_webflow,
        launch_browser=True)

    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'ADC')

  def testSaveWithError(self):
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_webflow.return_value = fake_cred
    self.StartObjectPatch(
        files, 'PrivatizeFile').side_effect = files.Error('Error')
    with self.assertRaisesRegex(
        store.CredentialFileSaveError, 'Error saving Application'):
      self.Login()

  def testBrowserBlacklist(self):
    """Call it with launch_browser=True, but have it get switched to False."""
    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_webflow.return_value = fake_cred
    self.mock_browser.return_value.name = 'www-browser'

    result = self.Login()
    self.assertEqual(fake_cred, result)

    self.mock_webflow.assert_called_once_with(
        launch_browser=False,
        scopes=auth_util.DEFAULT_SCOPES,
        client_id=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID,
        client_secret=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET)

  def testNoDisplaySet(self):
    """Call it with launch_browser=True, but have it get switched to False."""
    # DISPLAY is only checked for on Linux
    current_os = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    current_os.return_value = platforms.OperatingSystem.LINUX

    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_webflow.return_value = fake_cred

    self.StartDictPatch('os.environ')
    del os.environ['DISPLAY']
    result = self.Login()
    self.assertEqual(fake_cred, result)

    self.mock_webflow.assert_called_once_with(
        launch_browser=False,
        scopes=auth_util.DEFAULT_SCOPES,
        client_id=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID,
        client_secret=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET)

  def testNoDisplaySetAlternateDisplaySet(self):
    """Call it with launch_browser=True."""
    # DISPLAY is only checked for on Linux
    current_os = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    current_os.return_value = platforms.OperatingSystem.LINUX

    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_webflow.return_value = fake_cred

    self.StartDictPatch('os.environ')
    del os.environ['DISPLAY']
    os.environ['MIR_SOCKET'] = '/var/run/mir_socket'

    result = self.Login()
    self.assertEqual(fake_cred, result)

    self.mock_webflow.assert_called_once_with(
        launch_browser=True,
        scopes=auth_util.DEFAULT_SCOPES,
        client_id=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID,
        client_secret=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET)

  def testWebFlowError(self):
    """When an error occurs in the web flow."""
    self.mock_webflow.side_effect = store.FlowError('flowerror')

    with self.assertRaisesRegex(store.FlowError, 'flowerror'):
      self.Login()
    self.AssertErrContains('There was a problem with web authentication.')

    self.mock_webflow.assert_called_once_with(
        launch_browser=True,
        scopes=auth_util.DEFAULT_SCOPES,
        client_id=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID,
        client_secret=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET)

  def testWarnUserAuthGceVmAnswerYes(self):
    """Warn the user when authenticating on a GCE VM.

    When authenticating on a GCE VM, the user's credentials might
    become vulnerable. Test the case where the user wishes to continue
    authentication.
    """
    self.mock_metadata.return_value.connected = True

    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_webflow.return_value = fake_cred

    self.WriteInput('y')
    result = self.Login()
    self.assertEqual(fake_cred, result)

    self.mock_webflow.assert_called_once_with(
        launch_browser=False,
        scopes=auth_util.DEFAULT_SCOPES,
        client_id=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID,
        client_secret=auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET)

  def testWarnUserAuthGceVmAnswerNo(self):
    """Warn the user when authenticating on a GCE VM.

    When authenticating on a GCE VM, the user's credentials might
    become vulnerable. Test the case where the user wishes to abort
    authentication.
    """
    self.mock_metadata.return_value.connected = True

    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_webflow.return_value = fake_cred

    self.WriteInput('n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Login()

    self.assertEqual(False, self.mock_webflow.called)

  def testWarnUserADCEnvVarAnswerNo(self):
    """Warn the user when the ADC environment variable is set."""
    env_var_dict = {client.GOOGLE_APPLICATION_CREDENTIALS: 'foo'}
    with patch.dict('os.environ', env_var_dict):
      fake_cred = self.GetFakeCred('foo@google.com')
      self.mock_webflow.return_value = fake_cred

      self.WriteInput('n')
      with self.assertRaises(console_io.OperationCancelledError):
        self.Login()

      self.assertEqual(False, self.mock_webflow.called)

  def testLoginMissingDirectory(self):
    """Test login when the .gcloud directory is missing."""
    self.mock_adc_file_path.return_value = os.path.join(
        self.temp_path, 'junk', 'ADC')

    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_webflow.return_value = fake_cred

    self.Login()
    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'junk', 'ADC')


if __name__ == '__main__':
  test_case.main()
