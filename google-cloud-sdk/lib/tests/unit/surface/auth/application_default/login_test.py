# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

import json
import os
import textwrap

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import flow
from googlecloudsdk.core.credentials import gce
from googlecloudsdk.core.credentials import google_auth_credentials as c_google_auth
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import test_case

import mock
from mock import patch
from oauth2client import client

from google.oauth2 import credentials as google_auth_creds


def _GetJsonUserADC():
  return textwrap.dedent("""\
      {
        "client_id": "foo.apps.googleusercontent.com",
        "client_secret": "file-secret",
        "refresh_token": "file-token",
        "type": "authorized_user"
      }""")


def _GetJsonUserExtendedADC():
  return textwrap.dedent("""\
      {
        "client_id": "foo.apps.googleusercontent.com",
        "client_secret": "file-secret",
        "quota_project_id": "fake-project",
        "refresh_token": "file-token",
        "type": "authorized_user"
      }""")


class LoginTestOauth2client(cli_test_base.CliTestBase, test_case.WithInput):

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

    self.mock_adc_file_path = self.StartObjectPatch(config, 'ADCFilePath')
    self.mock_adc_file_path.return_value = os.path.join(
        self.temp_path, 'ADC')

    self.mock_metadata = self.StartObjectPatch(gce, 'Metadata', autospec=True)
    self.mock_metadata.return_value.connected = False
    self.mock_metadata.return_value.Project = lambda: 'metadata-project'
    self.StartDictPatch('os.environ', {'DISPLAY': ':1'})
    self.scopes = auth_util.DEFAULT_SCOPES + [config.REAUTH_SCOPE]

  def GetFakeCred(self, account):
    return client.OAuth2Credentials(
        id_token={'email': account},
        access_token='',
        client_id='',
        client_secret='',
        refresh_token='',
        token_expiry='',
        token_uri='',
        user_agent=''
    )

  def Login(self, more_args=''):
    return self.Run('beta auth application-default login --use-oauth2client '
                    '{more_args}'.format(more_args=more_args))

  def testBasicLogin(self):
    """Basic login with default client id and default scopes."""
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_webflow.return_value = fake_cred
    result = self.Login()
    self.assertEqual(fake_cred, result)

    self.mock_webflow.assert_called_once_with(
        launch_browser=True,
        scopes=self.scopes,
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
        scopes=['scope1', 'scope2', config.REAUTH_SCOPE],
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
        filename=client_id_file, scope=self.scopes)
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
        scope=['scope1', 'scope2', config.REAUTH_SCOPE])
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
    with self.assertRaisesRegex(creds.CredentialFileSaveError,
                                'Error saving Application'):
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
        scopes=self.scopes,
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
        scopes=self.scopes,
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
        scopes=self.scopes,
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
        scopes=self.scopes,
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
        scopes=self.scopes,
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

  def testLoginWithQuotaProject(self):
    self.mock_webflow.return_value = creds.FromJson(_GetJsonUserADC())
    self.Login('--add-quota-project')
    self.AssertFileEquals(_GetJsonUserExtendedADC(),
                          os.path.join(self.temp_path, 'ADC'))
    self.AssertErrContains("Quota project 'fake-project' was added to ADC")

  def testLoginWithoutQuotaProject(self):
    self.mock_webflow.return_value = creds.FromJson(_GetJsonUserADC())
    self.Login()
    self.AssertFileEquals(_GetJsonUserADC(),
                          os.path.join(self.temp_path, 'ADC'))

  def testLoginWithQuotaProject_WithClientID(self):
    client_id_file = self.Resource('tests', 'unit', 'surface', 'auth',
                                   'test_data', 'client_id_file.json')
    self.mock_run_webflow.return_value = creds.FromJson(_GetJsonUserADC())
    self.Login(more_args='--client-id-file {file}'.format(file=client_id_file))
    self.AssertFileEquals(_GetJsonUserADC(),
                          os.path.join(self.temp_path, 'ADC'))


def GetFakeCredGoogleAuth():
  return google_auth_creds.Credentials(
      token='fake-token',
      refresh_token='file-token',
      id_token='fake-id-token',
      token_uri='fake-token-uri',
      client_id='foo.apps.googleusercontent.com',
      client_secret='file-secret',
      scopes=['scope1', 'scope2'],
  )


def GetDefaultClientConfig():
  return {
      'installed': {
          'client_id': auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_ID,
          'client_secret': auth_util.DEFAULT_CREDENTIALS_DEFAULT_CLIENT_SECRET,
          'auth_uri': properties.VALUES.auth.auth_host.Get(required=True),
          'token_uri': properties.VALUES.auth.token_host.Get(required=True),
      }
  }


class LoginTestGoogleAuth(cli_test_base.CliTestBase, test_case.WithInput):

  def SetUp(self):
    self.flow = self.StartObjectPatch(flow, 'InstalledAppFlow', autospec=True)
    self.flow_creator = mock.MagicMock()
    self.flow.from_client_config = self.flow_creator
    self.flow_runner = self.StartObjectPatch(
        flow,
        'RunGoogleAuthFlow',
        autospec=True,
        return_value=GetFakeCredGoogleAuth())

    self.mock_browser = self.StartPatch('webbrowser.get', autospec=True)
    self.mock_browser.return_value.name = 'Chrome'

    self.mock_adc_file_path = self.StartObjectPatch(config, 'ADCFilePath')
    self.mock_adc_file_path.return_value = os.path.join(self.temp_path, 'ADC')

    self.mock_metadata = self.StartObjectPatch(gce, 'Metadata', autospec=True)
    self.mock_metadata.return_value.connected = False
    self.mock_metadata.return_value.Project = lambda: 'metadata-project'
    self.StartDictPatch('os.environ', {'DISPLAY': ':1'})
    self.scopes = auth_util.DEFAULT_SCOPES + [config.REAUTH_SCOPE]

  def Login(self, more_args=''):
    return self.Run('beta auth application-default login {more_args}'.format(
        more_args=more_args))

  def testBasicLogin(self):
    """Basic login with default client id and default scopes."""
    result = self.Login()
    self.assertIsInstance(result, c_google_auth.UserCredWithReauth)

    self.flow_creator.assert_called_once_with(
        GetDefaultClientConfig(), self.scopes, autogenerate_code_verifier=True)
    self.flow_runner.assert_called_once_with(mock.ANY, launch_browser=True)

    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'ADC')

  def testLoginWithScopes(self):
    """Login with scopes provided."""
    result = self.Login(more_args='--scopes scope1,scope2')
    self.assertIsInstance(result, c_google_auth.UserCredWithReauth)

    self.flow_creator.assert_called_once_with(
        GetDefaultClientConfig(), ['scope1', 'scope2', config.REAUTH_SCOPE],
        autogenerate_code_verifier=True)
    self.flow_runner.assert_called_once_with(mock.ANY, launch_browser=True)

    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'ADC')

  def testLoginWithClientIdFile(self):
    """Login with client id file provided."""
    client_id_file = self.Resource('tests', 'unit', 'surface', 'auth',
                                   'test_data', 'client_id_file.json')
    with files.FileReader(client_id_file) as f:
      client_id_file_content = json.load(f)
    result = self.Login(more_args='--client-id-file {file}'.format(
        file=client_id_file))
    self.assertIsInstance(result, c_google_auth.UserCredWithReauth)

    self.flow_creator.assert_called_once_with(
        client_id_file_content, self.scopes, autogenerate_code_verifier=True)
    self.flow_runner.assert_called_once_with(mock.ANY, launch_browser=True)

    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'ADC')

  def testLoginWithClientIdFileAndScopes(self):
    """Login with both client id file and scopes provided."""
    client_id_file = self.Resource('tests', 'unit', 'surface', 'auth',
                                   'test_data', 'client_id_file.json')

    result = self.Login(more_args=' --scopes scope1,scope2 '
                        '--client-id-file {file}'.format(file=client_id_file))
    self.assertIsInstance(result, c_google_auth.UserCredWithReauth)

    with files.FileReader(client_id_file) as f:
      client_id_file_content = json.load(f)
    self.flow_creator.assert_called_once_with(
        client_id_file_content, ['scope1', 'scope2', config.REAUTH_SCOPE],
        autogenerate_code_verifier=True)
    self.flow_runner.assert_called_once_with(mock.ANY, launch_browser=True)

    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'ADC')

  def testSaveWithError(self):
    self.StartObjectPatch(files,
                          'PrivatizeFile').side_effect = files.Error('Error')
    with self.assertRaisesRegex(creds.CredentialFileSaveError,
                                'Error saving Application'):
      self.Login()

  def testBrowserBlacklist(self):
    """Call it with launch_browser=True, but have it get switched to False."""
    self.mock_browser.return_value.name = 'www-browser'

    result = self.Login()
    self.assertIsInstance(result, c_google_auth.UserCredWithReauth)

    self.flow_creator.assert_called_once_with(
        GetDefaultClientConfig(), self.scopes, autogenerate_code_verifier=True)
    self.flow_runner.assert_called_once_with(mock.ANY, launch_browser=False)

  def testNoDisplaySet(self):
    """Call it with launch_browser=True, but have it get switched to False."""
    # DISPLAY is only checked for on Linux
    current_os = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    current_os.return_value = platforms.OperatingSystem.LINUX

    self.StartDictPatch('os.environ')
    del os.environ['DISPLAY']
    result = self.Login()
    self.assertIsInstance(result, c_google_auth.UserCredWithReauth)

    self.flow_creator.assert_called_once_with(
        GetDefaultClientConfig(), self.scopes, autogenerate_code_verifier=True)
    self.flow_runner.assert_called_once_with(mock.ANY, launch_browser=False)

  def testNoDisplaySetAlternateDisplaySet(self):
    """Call it with launch_browser=True."""
    # DISPLAY is only checked for on Linux
    current_os = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    current_os.return_value = platforms.OperatingSystem.LINUX

    self.StartDictPatch('os.environ')
    del os.environ['DISPLAY']
    os.environ['MIR_SOCKET'] = '/var/run/mir_socket'

    result = self.Login()
    self.assertIsInstance(result, c_google_auth.UserCredWithReauth)

    self.flow_creator.assert_called_once_with(
        GetDefaultClientConfig(), self.scopes, autogenerate_code_verifier=True)
    self.flow_runner.assert_called_once_with(mock.ANY, launch_browser=True)

  def testWarnUserAuthGceVmAnswerYes(self):
    """Warn the user when authenticating on a GCE VM.

    When authenticating on a GCE VM, the user's credentials might
    become vulnerable. Test the case where the user wishes to continue
    authentication.
    """
    self.mock_metadata.return_value.connected = True

    self.WriteInput('y')
    result = self.Login()
    self.assertIsInstance(result, c_google_auth.UserCredWithReauth)

    self.flow_creator.assert_called_once_with(
        GetDefaultClientConfig(), self.scopes, autogenerate_code_verifier=True)
    self.flow_runner.assert_called_once_with(mock.ANY, launch_browser=False)

  def testWarnUserAuthGceVmAnswerNo(self):
    """Warn the user when authenticating on a GCE VM.

    When authenticating on a GCE VM, the user's credentials might
    become vulnerable. Test the case where the user wishes to abort
    authentication.
    """
    self.mock_metadata.return_value.connected = True

    self.WriteInput('n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Login()

    self.flow_creator.assert_not_called()
    self.flow_runner.assert_not_called()

  def testWarnUserADCEnvVarAnswerNo(self):
    """Warn the user when the ADC environment variable is set."""
    env_var_dict = {client.GOOGLE_APPLICATION_CREDENTIALS: 'foo'}
    with patch.dict('os.environ', env_var_dict):

      self.WriteInput('n')
      with self.assertRaises(console_io.OperationCancelledError):
        self.Login()
    self.flow_creator.assert_not_called()
    self.flow_runner.assert_not_called()

  def testLoginMissingDirectory(self):
    """Test login when the .gcloud directory is missing."""
    self.mock_adc_file_path.return_value = os.path.join(self.temp_path, 'junk',
                                                        'ADC')

    self.Login()
    self.AssertErrContains('Credentials saved to file')
    self.AssertFileExists(self.temp_path, 'junk', 'ADC')

  def testLoginWithQuotaProject(self):
    self.Login('--add-quota-project')
    self.AssertFileEquals(_GetJsonUserExtendedADC(),
                          os.path.join(self.temp_path, 'ADC'))
    self.AssertErrContains("Quota project 'fake-project' was added to ADC")

  def testLoginWithoutQuotaProject(self):
    self.Login()
    self.AssertFileEquals(_GetJsonUserADC(),
                          os.path.join(self.temp_path, 'ADC'))

  def testLoginWithQuotaProject_WithClientID(self):
    client_id_file = self.Resource('tests', 'unit', 'surface', 'auth',
                                   'test_data', 'client_id_file.json')
    self.Login(more_args='--client-id-file {file}'.format(file=client_id_file))
    self.AssertFileEquals(_GetJsonUserADC(),
                          os.path.join(self.temp_path, 'ADC'))


if __name__ == '__main__':
  test_case.main()
