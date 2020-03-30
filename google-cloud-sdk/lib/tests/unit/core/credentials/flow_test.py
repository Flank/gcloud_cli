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

"""Tests for googlecloudsdk.core.credentials.flow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import socket
import wsgiref

from googlecloudsdk.core.credentials import flow
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock
import six


class FlowTest(test_case.WithInput, sdk_test_base.WithOutputCapture):

  _CREDENTIALS = 'some credentials'
  _AUTH_CODE = 'the_code'
  _AUTH_URL = 'https://some.url.com'

  def _mockWebflow(self):
    webflow_mock = mock.Mock()
    webflow_mock.step1_get_authorize_url.return_value = self._AUTH_URL
    webflow_mock.step2_exchange.return_value = self._CREDENTIALS
    return webflow_mock

  def testFlowNoBrowser(self):
    webflow_mock = self._mockWebflow()
    http_mock = mock.Mock()
    self.WriteInput(self._AUTH_CODE)

    cred = flow.Run(
        webflow_mock,
        launch_browser=False,
        http=http_mock)

    webflow_mock.step1_get_authorize_url.assert_called_with()
    self.AssertErrContains('Go to the following link in your browser:')
    self.AssertErrContains(self._AUTH_URL)
    webflow_mock.step2_exchange.assert_called_with(
        self._AUTH_CODE, http=http_mock)
    self.assertEqual(cred, self._CREDENTIALS)

  def testFlowResponseNotReady(self):
    webflow_mock = mock.Mock()
    webflow_mock.step1_get_authorize_url.return_value = self._AUTH_URL
    webflow_mock.step2_exchange.side_effect = (
        six.moves.http_client.ResponseNotReady())

    http_mock = mock.Mock()
    self.WriteInput(self._AUTH_CODE)

    with self.assertRaises(flow.AuthRequestFailedError):
      flow.Run(webflow_mock, launch_browser=False, http=http_mock)

  def testFlowWithBrowser(self):
    webflow_mock = self._mockWebflow()
    http_mock = mock.Mock()
    webbrowser_open_mock = self.StartPatch('webbrowser.open')
    http_server_mock = mock.Mock()
    http_server_mock.query_params = {'code': self._AUTH_CODE}

    # We want the ClientRedirectServer to first throw an exception and then
    # return an http_server_mock. This way we test the port increment.
    def server_side_effect(*unused_args):
      server_side_effect.attempt += 1
      if server_side_effect.attempt == 1:
        raise socket.error
      return http_server_mock
    server_side_effect.attempt = 0
    self.StartPatch('oauth2client.tools.ClientRedirectServer',
                    side_effect=server_side_effect)

    cred = flow.Run(
        webflow_mock,
        launch_browser=True,
        http=http_mock)

    self.assertEqual(server_side_effect.attempt, 2)
    webflow_mock.step1_get_authorize_url.assert_called_with()
    webbrowser_open_mock.assert_called_with(
        self._AUTH_URL, new=1, autoraise=True)
    self.AssertErrContains('Your browser has been opened to visit')
    self.AssertErrContains(self._AUTH_URL)
    webflow_mock.step2_exchange.assert_called_with(
        self._AUTH_CODE, http=http_mock)
    self.assertEqual(cred, self._CREDENTIALS)

  def testFlowBrowserIntoNoBrowser(self):
    webflow_mock = self._mockWebflow()
    http_mock = mock.Mock()
    self.WriteInput(self._AUTH_CODE)
    self.StartPatch('oauth2client.tools.ClientRedirectServer',
                    side_effect=socket.error)

    cred = flow.Run(
        webflow_mock,
        launch_browser=True,
        http=http_mock)

    self.AssertErrContains('Failed to start a local webserver '
                           'listening on any port')
    webflow_mock.step1_get_authorize_url.assert_called_with()
    self.AssertErrContains('Go to the following link in your browser:')
    self.AssertErrContains(self._AUTH_URL)
    webflow_mock.step2_exchange.assert_called_with(
        self._AUTH_CODE, http=http_mock)
    self.assertEqual(cred, self._CREDENTIALS)


class GoogleAuthFlowTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.scopes = ('openid', 'https://www.googleapis.com/auth/userinfo.email',
                   'https://www.googleapis.com/auth/accounts.reauth')
    client_id_file_content = {
        'installed': {
            'client_id': 'client_id',
            'client_secret': 'client_secret',
            'auth_uri': 'auth_uri',
            'token_uri': 'token_uri'
        }
    }

    self.client_id_file = self.Touch(
        self.temp_path, contents=json.dumps(client_id_file_content))
    self.StartPatch(
        'googlecloudsdk.core.properties.VALUES.auth.auth_host.Get',
        return_value='auth_uri_property')
    self.StartPatch(
        'googlecloudsdk.core.properties.VALUES.auth.token_host.Get',
        return_value='token_uri_property')
    self.StartPatch(
        'googlecloudsdk.core.properties.VALUES.auth.client_id.Get',
        return_value='client_id_property')
    self.StartPatch(
        'googlecloudsdk.core.properties.VALUES.auth.client_secret.Get',
        return_value='client_secret_property')

  def testCreateGoogleAuthFlow_FromProperties(self):
    google_auth_flow = flow.CreateGoogleAuthFlow(self.scopes)
    self.assertEqual(google_auth_flow.client_type, 'installed')
    client_config = google_auth_flow.client_config
    self.assertEqual(client_config['client_id'], 'client_id_property')
    self.assertEqual(client_config['client_secret'], 'client_secret_property')
    self.assertEqual(client_config['auth_uri'], 'auth_uri_property')
    self.assertEqual(client_config['token_uri'], 'token_uri_property')
    self.assertTrue(google_auth_flow.autogenerate_code_verifier)

  def testCreateGoogleAuthFlow_FromFile(self):
    google_auth_flow = flow.CreateGoogleAuthFlow(self.scopes,
                                                 self.client_id_file)
    self.assertEqual(google_auth_flow.client_type, 'installed')
    client_config = google_auth_flow.client_config
    self.assertEqual(client_config['client_id'], 'client_id')
    self.assertEqual(client_config['client_secret'], 'client_secret')
    self.assertEqual(client_config['auth_uri'], 'auth_uri')
    self.assertEqual(client_config['token_uri'], 'token_uri')
    self.assertTrue(google_auth_flow.autogenerate_code_verifier)

  def testRunGoogleAuthFlow_NoLaunchBrowser(self):
    run_local_server_mock = self.StartObjectPatch(flow.InstalledAppFlow,
                                                  'run_local_server')
    run_console_mock = self.StartObjectPatch(flow.InstalledAppFlow,
                                             'run_console')
    google_auth_flow = flow.CreateGoogleAuthFlow(self.scopes,
                                                 self.client_id_file)
    flow.RunGoogleAuthFlow(google_auth_flow, launch_browser=False)
    run_console_mock.assert_called()
    run_local_server_mock.assert_not_called()

  def testRunGoogleAuthFlow_LaunchBrowser(self):
    run_local_server_mock = self.StartObjectPatch(flow.InstalledAppFlow,
                                                  'run_local_server')
    run_console_mock = self.StartObjectPatch(flow.InstalledAppFlow,
                                             'run_console')
    google_auth_flow = flow.CreateGoogleAuthFlow(self.scopes,
                                                 self.client_id_file)
    flow.RunGoogleAuthFlow(google_auth_flow, launch_browser=True)
    run_console_mock.assert_not_called()
    run_local_server_mock.assert_called()

  def testRunGoogleAuthFlow_LaunchBrowser_LocalServerError(self):
    run_local_server_mock = self.StartObjectPatch(flow.InstalledAppFlow,
                                                  'run_local_server')
    run_local_server_mock.side_effect = flow.LocalServerCreationError
    run_console_mock = self.StartObjectPatch(flow.InstalledAppFlow,
                                             'run_console')
    google_auth_flow = flow.CreateGoogleAuthFlow(self.scopes,
                                                 self.client_id_file)
    flow.RunGoogleAuthFlow(google_auth_flow, launch_browser=True)
    run_console_mock.assert_called()
    run_local_server_mock.assert_called()
    self.AssertErrContains('Defaulting to URL copy/paste mode.')


class LocalSeverCreationTest(cli_test_base.CliTestBase):

  def testCreateLocalServer_CannotFindPort(self):
    mock_make_server = self.StartObjectPatch(wsgiref.simple_server,
                                             'make_server')
    mock_make_server.side_effect = OSError
    with self.AssertRaisesExceptionRegexp(
        flow.LocalServerCreationError,
        'Failed to start a local webserver listening on any port '
        'between 8085 and 8184.*'):
      flow.CreateLocalServer(None, 8085, 8185)
    self.assertEqual(mock_make_server.call_count, 100)

  def testCreateLocalServer(self):
    mock_make_server = self.StartObjectPatch(wsgiref.simple_server,
                                             'make_server')
    mock_make_server.side_effect = [OSError, socket.error, 'server']
    server = flow.CreateLocalServer(None, 8085, 8185)
    self.assertEqual(server, 'server')
    self.assertEqual(mock_make_server.call_count, 3)


if __name__ == '__main__':
  test_case.main()
