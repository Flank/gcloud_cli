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

"""Tests for googlecloudsdk.core.credentials.flow."""

from __future__ import absolute_import
from __future__ import unicode_literals

import socket
import sys
import webbrowser
from googlecloudsdk.core.credentials import flow
from googlecloudsdk.core.util import platforms
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

    with self.assertRaises(flow.AuthRequestFailedException):
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

  def testFlowWithMacChromeBrowser(self):
    self.StartObjectPatch(sys, 'platform', 'darwin')
    six.moves.reload_module(webbrowser)
    webflow_mock = self._mockWebflow()
    http_mock = mock.Mock()
    http_server_mock = mock.Mock()
    http_server_mock.query_params = {'code': self._AUTH_CODE}

    self.StartPatch('webbrowser.open')
    self.StartObjectPatch(platforms.OperatingSystem, 'Current',
                          return_value=platforms.OperatingSystem.MACOSX)

    self.StartPatch('oauth2client.tools.ClientRedirectServer',
                    side_effect=lambda x, y: http_server_mock)

    flow.Run(
        webflow_mock,
        launch_browser=True,
        http=http_mock)

    self.assertIsNotNone(webbrowser.get('Google Chrome'))
    self.AssertErrContains('Your browser has been opened to visit')

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


if __name__ == '__main__':
  test_case.main()
