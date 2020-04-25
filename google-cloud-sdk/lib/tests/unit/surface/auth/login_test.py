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

import abc
import os
import textwrap

from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import devshell
from googlecloudsdk.core.credentials import gce
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

import mock
import six
from google.auth import crypt as google_auth_crypt
from google.auth import jwt


class LoginTestMixin(six.with_metaclass(abc.ABCMeta, object)):

  def LoginTestSetUp(self):
    properties.PersistProperty(properties.VALUES.core.account, 'junk')
    self.StartObjectPatch(store, 'Store', autospec=True)

    self.mock_load = self.StartObjectPatch(store, 'Load', autospec=True)
    self.mock_browser = self.StartPatch('webbrowser.get', autospec=True)
    self.mock_browser.return_value.name = 'Chrome'

    self.mock_metadata = self.StartObjectPatch(gce, 'Metadata', autospec=True)
    self.mock_metadata.return_value.connected = False
    self.mock_metadata.return_value.Project = lambda: 'metadata-project'
    self.StartDictPatch('os.environ', {'DISPLAY': ':1'})

    self.expected_scopes = (
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/appengine.admin',
        'https://www.googleapis.com/auth/compute',
        'https://www.googleapis.com/auth/accounts.reauth',
    )

  def Project(self):
    return 'junkproj'

  @abc.abstractmethod
  def GetFakeCred(self, account):
    pass

  @abc.abstractmethod
  def Login(self, account='', more_args=''):
    pass

  @abc.abstractmethod
  def assert_mock_flow_called_with(self, launch_browser, scopes):
    pass

  def testGoogleDriveEnabled(self):
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    result = self.Login(account='foo@google.com',
                        more_args=' --enable-gdrive-access')
    self.assertEqual(fake_cred, result)

    expected_scopes = self.expected_scopes + (
        'https://www.googleapis.com/auth/drive',
    )

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testNoAccount(self):
    """Always do the web flow if no account is given."""
    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    result = self.Login()
    self.assertEqual(fake_cred, result)

    self.assertEqual(self.mock_load.call_count, 0)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=self.expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testLoginNoCreds(self):
    """The normal case, use the web flow to get new credentials."""
    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    result = self.Login(account='foo@google.com')
    self.assertEqual(fake_cred, result)

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=self.expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testLoginNoCredsMismatchedCase(self):
    """The normal case, use the web flow to get new credentials.

    Should handle mismatched case seamlessly.
    """
    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    result = self.Login(account='FOO@google.com')
    self.assertEqual(fake_cred, result)

    self.mock_load.assert_called_once_with(
        account='FOO@google.com', scopes=self.expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=self.expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testLoginWrongAccount(self):
    """Runs the web flow, but you logged in as the wrong user."""
    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    with self.assertRaisesRegex(
        auth_exceptions.WrongAccountError,
        r'You attempted to log in as account \[bar@google.com\] but the '
        r'received credentials were for account \[foo@google.com\]\.'):
      self.Login(account='bar@google.com')

    self.mock_load.assert_called_once_with(
        account='bar@google.com', scopes=self.expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=self.expected_scopes)
    self.assertEqual('junk', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testLoginWithValidCreds(self):
    """Account has valid creds but force flow anyway."""
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_load.return_value = fake_cred  # Valid cred to start.

    result = self.Login(account='foo@google.com')
    self.assertEqual(fake_cred, result)

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    # Web flow is not run.
    self.assertEqual(False, self.mock_flow.called)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testLoginWithValidCredsForce(self):
    """When the account already has valid credentials, don't run the flow."""
    fake_cred1 = self.GetFakeCred('foo@google.com')
    fake_cred2 = self.GetFakeCred('foo@google.com')
    self.mock_load.return_value = fake_cred1  # Valid cred to start.
    self.mock_flow.return_value = fake_cred2  # Valid cred after flow.

    result = self.Login(account='foo@google.com', more_args=' --force')
    self.assertEqual(fake_cred2, result)

    self.assertEqual(False, self.mock_load.called)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=self.expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testBrowserBlacklist(self):
    """Call it with launch_browser=True, but have it get switched to False."""
    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.
    self.mock_browser.return_value.name = 'www-browser'

    result = self.Login(account='foo@google.com')
    self.assertEqual(fake_cred, result)

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=False, scopes=self.expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testNoDisplaySet(self):
    """Call it with launch_browser=True, but have it get switched to False."""
    # DISPLAY is only checked for on Linux
    current_os = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    current_os.return_value = platforms.OperatingSystem.LINUX

    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    self.StartDictPatch('os.environ')
    del os.environ['DISPLAY']
    result = self.Login(account='foo@google.com')
    self.assertEqual(fake_cred, result)

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=False, scopes=self.expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testNoDisplaySetAlternateDisplaySet(self):
    """Call it with launch_browser=True."""
    # DISPLAY is only checked for on Linux
    current_os = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    current_os.return_value = platforms.OperatingSystem.LINUX

    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    self.StartDictPatch('os.environ')
    del os.environ['DISPLAY']
    os.environ['MIR_SOCKET'] = '/var/run/mir_socket'

    result = self.Login(account='foo@google.com')
    self.assertEqual(fake_cred, result)

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=self.expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testSetProject(self):
    """Make sure the project gets set."""
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_load.return_value = fake_cred  # Valid cred to start.

    result = self.Login(account='foo@google.com',
                        more_args=' --project=newproj')
    self.assertEqual(fake_cred, result)

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    # Web flow is not run.
    self.assertEqual(False, self.mock_flow.called)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('newproj', properties.VALUES.core.project.Get())

  def testDoNotActivate(self):
    """Make sure the active account and project do not get set."""
    fake_cred = self.GetFakeCred('foo@google.com')

    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    result = self.Login(account='foo@google.com',
                        more_args=' --project=newproj --do-not-activate')
    self.assertEqual(fake_cred, result)

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=self.expected_scopes)
    self.assertEqual('junk', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testWarnUserAuthGceVmAnswerYes(self):
    """Warn the user when authenticating on a GCE VM.

    When authenticating on a GCE VM, the user's credentials might
    become vulnerable. Test the case where the user wishes to continue
    authentication.
    """
    self.mock_metadata.return_value.connected = True

    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    self.WriteInput('y')
    result = self.Login(account='foo@google.com')
    self.assertEqual(fake_cred, result)

    self.assert_mock_flow_called_with(
        launch_browser=False, scopes=self.expected_scopes)
    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    self.assertEqual('foo@google.com', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testWarnUserAuthGceVmAnswerNo(self):
    """Warn the user when authenticating on a GCE VM.

    When authenticating on a GCE VM, the user's credentials might
    become vulnerable. Test the case where the user wishes to abort
    authentication.
    """
    self.mock_metadata.return_value.connected = True

    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    self.WriteInput('n')
    result = self.Login(account='foo@google.com')
    self.assertEqual(None, result)

    self.assertEqual(False, self.mock_flow.called)
    self.assertEqual('junk', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testWarnUserLocalCredentials(self):
    """Warn the user when re-using locally stored credentials.

    Useful when the user might expect a fresh set of credentials that
    authorize additional scopes, such as the one provided by the
    `--enable-gdrive-access`. Test that the appropriate message is displayed.

    """
    self.mock_metadata.return_value.connected = False
    fake_account = 'foo@google.com'
    fake_cred = self.GetFakeCred(fake_account)
    self.mock_load.return_value = fake_cred  # Simulating existing creds.

    result = self.Login(account=fake_account)
    self.assertEqual(fake_cred, result)
    self.mock_load.assert_called_once_with(
        account=fake_account, scopes=self.expected_scopes)
    self.AssertErrContains(
        'Re-using locally stored credentials for [{}]. '
        'To fetch new credentials, re-run the command with the '
        '`--force` flag.'.format(fake_account))
    self.assertEqual(fake_account, properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())

  def testAlertUserOfDevshellLogin(self):
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    self.StartDictPatch('os.environ', {
        devshell.DEVSHELL_ENV: 'true',
        devshell.DEVSHELL_CLIENT_PORT: '1000',
    })

    self.WriteInput('n')
    result = self.Login(account='foo@google.com')
    self.assertEqual(None, result)

    self.WriteInput('y')
    result = self.Login(account='foo@google.com')
    self.assertEqual(fake_cred, result)

  def testNoAlertWhenNoDevshellClient(self):
    fake_cred = self.GetFakeCred('foo@google.com')
    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.return_value = fake_cred  # Valid cred after flow.

    self.StartDictPatch('os.environ', {
        devshell.DEVSHELL_ENV: 'true',
    })

    result = self.Login(account='foo@google.com')
    self.assertEqual(fake_cred, result)


class LoginTestOauth2client(LoginTestMixin, cli_test_base.CliTestBase,
                            test_case.WithInput):

  def SetUp(self):
    self.LoginTestSetUp()
    self.mock_flow = self.StartObjectPatch(
        store, 'AcquireFromWebFlow', autospec=True)

  def Login(self, account='', more_args=''):
    return self.Run('auth login {account}{more_args} --use-oauth2client'.format(
        account=account, more_args=more_args))

  def assert_mock_flow_called_with(self, launch_browser, scopes):
    self.mock_flow.assert_called_once_with(
        launch_browser=launch_browser,
        scopes=scopes,
        client_id=None,
        client_secret=None)

  def GetFakeCred(self, account):
    cred_mock = mock.MagicMock()
    cred_mock.id_token = {'email': account}
    return cred_mock

  def testWebFlowError(self):
    """When an error occurs in the web flow."""
    self.mock_load.return_value = None  # No creds to start.
    self.mock_flow.side_effect = store.FlowError('flowerror')

    with self.assertRaisesRegex(store.FlowError, 'flowerror'):
      self.Login(account='foo@google.com')
    self.AssertErrContains('There was a problem with web authentication.')

    self.mock_load.assert_called_once_with(
        account='foo@google.com', scopes=self.expected_scopes)
    self.assert_mock_flow_called_with(
        launch_browser=True, scopes=self.expected_scopes)
    self.assertEqual('junk', properties.VALUES.core.account.Get())
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())


class LoginTestGoogleAuth(LoginTestMixin, cli_test_base.CliTestBase,
                          test_case.WithInput):

  def SetUp(self):
    self.LoginTestSetUp()
    self.mock_flow = self.StartObjectPatch(
        auth_util, 'DoInstalledAppBrowserFlowGoogleAuth', autospec=True)
    self.mock_jwt_decode = self.StartObjectPatch(jwt, 'decode', autospec=True)

  def Login(self, account='', more_args=''):
    return self.Run('auth login {account}{more_args}'.format(
        account=account, more_args=more_args))

  def assert_mock_flow_called_with(self, launch_browser, scopes):
    self.mock_flow.assert_called_once_with(launch_browser, scopes)

  def GetFakeCred(self, account):
    cred_mock = mock.MagicMock()
    cred_mock.id_token = 'id_token'
    self.mock_jwt_decode.return_value = {'email': account}
    return cred_mock


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


def _GetJsonServiceADC():
  return textwrap.dedent("""\
      {
        "client_email": "bar@developer.gserviceaccount.com",
        "client_id": "bar.apps.googleusercontent.com",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
        "private_key_id": "key-id",
        "type": "service_account"
      }""")


class TestWriteToADC(cli_test_base.CliTestBase, test_case.WithInput,
                     credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    properties.PersistProperty(properties.VALUES.core.account, 'junk')
    self.StartObjectPatch(store, 'Store', autospec=True)

    self.mock_load = self.StartObjectPatch(store, 'Load', autospec=True)
    self.adc_file_path = os.path.join(self.temp_path,
                                      'application_default_credentials.json')
    self.StartObjectPatch(
        config, 'ADCFilePath', return_value=self.adc_file_path)
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)

    # Mocks the signer of google-auth credentials.
    self.StartObjectPatch(google_auth_crypt.RSASigner,
                          'from_service_account_info')

    self.mock_metadata = self.StartObjectPatch(gce, 'Metadata', autospec=True)
    self.mock_metadata.return_value.connected = False

    self.StartObjectPatch(creds, 'GetQuotaProject', return_value='my project')

  def testLoginWithWriteToADC_UserCreds(self):
    self.mock_load.return_value = creds.FromJson(_GetJsonUserADC())
    self.Run('auth login foo@gmail.com --update-adc')
    self.AssertFileEquals(_GetJsonUserADC(), self.adc_file_path)
    self.AssertErrNotContains(
        "'my project' is added to ADC as the quota project")

  def testLoginWithWriteToADC_GoogleAuthUserCreds(self):
    self.mock_load.return_value = self.MakeUserAccountCredentialsGoogleAuth()
    self.Run('auth login foo@gmail.com --update-adc')
    self.AssertFileEquals(self.USER_CREDENTIALS_JSON, self.adc_file_path)
    self.AssertErrNotContains(
        "'my project' is added to ADC as the quota project")

  def testLoginWithWriteToADC_UserCredsWithQuotaProject(self):
    self.mock_load.return_value = creds.FromJson(_GetJsonUserADC())
    self.Run('auth login foo@gmail.com --update-adc --add-quota-project-to-adc')
    self.AssertFileEquals(self.EXTENDED_USER_CREDENTIALS_JSON,
                          self.adc_file_path)
    self.AssertErrContains("'my project' is added to ADC as the quota project")

  def testLoginWithWriteToADC_GoogleAuthUserCredsWithQuotaProject(self):
    self.mock_load.return_value = self.MakeUserAccountCredentialsGoogleAuth()
    self.Run('auth login foo@gmail.com --update-adc --add-quota-project-to-adc')
    self.AssertFileEquals(self.EXTENDED_USER_CREDENTIALS_JSON,
                          self.adc_file_path)
    self.AssertErrContains("'my project' is added to ADC as the quota project")

  def testLoginWithWriteToADC_UserCreds_CannotFindQuotaProject(self):
    self.StartObjectPatch(creds, 'GetQuotaProject', return_value=None)
    self.mock_load.return_value = creds.FromJson(_GetJsonUserADC())
    self.Run('auth login foo@gmail.com --update-adc --add-quota-project-to-adc')
    self.AssertFileEquals(_GetJsonUserADC(), self.adc_file_path)
    self.AssertErrContains('Cannot find a project to insert into application '
                           'default credentials (ADC) as a quota project')

  def testLoginWithWriteToADC_GoogleAuthUserCreds_CannotFindQuotaProject(self):
    self.StartObjectPatch(creds, 'GetQuotaProject', return_value=None)
    self.mock_load.return_value = self.MakeUserAccountCredentialsGoogleAuth()
    self.Run('auth login foo@gmail.com --update-adc --add-quota-project-to-adc')
    self.AssertFileEquals(self.USER_CREDENTIALS_JSON, self.adc_file_path)
    self.AssertErrContains('Cannot find a project to insert into application '
                           'default credentials (ADC) as a quota project')

  def testLoginWithWriteToADC_ServiceCreds(self):
    self.mock_load.return_value = creds.FromJson(_GetJsonServiceADC())
    self.Run('auth login bar@developer.gserviceaccount.com --update-adc')
    self.AssertFileNotExists(self.adc_file_path)
    self.AssertErrContains('Credentials cannot be written')
    self.AssertErrNotContains('Application default credentials (ADC) were '
                              'updated.')

  def testLoginWithWriteToADC_GoogleAuthServiceCreds(self):
    self.mock_load.return_value = self.MakeServiceAccountCredentialsGoogleAuth()
    self.Run('auth login bar@developer.gserviceaccount.com --update-adc')
    self.AssertFileNotExists(self.adc_file_path)
    self.AssertErrContains('Credentials cannot be written')
    self.AssertErrNotContains('Application default credentials (ADC) were '
                              'updated.')

  def testLoginAddQuotaProjectWithoutUpdateADC(self):
    self.mock_load.return_value = creds.FromJson(_GetJsonUserADC())
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        '--add-quota-project-to-adc cannot be specified without specifying '
        '--update-adc'):
      self.Run('auth login foo@gmail.com --add-quota-project-to-adc')


if __name__ == '__main__':
  test_case.main()
