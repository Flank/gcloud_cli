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

"""Unit tests for http proxy properties setup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core import http_proxy
from googlecloudsdk.core import properties
from googlecloudsdk.core.diagnostics import http_proxy_setup
from tests.lib import cli_test_base
from tests.lib import test_case
import socks


SET_PROXY = http_proxy_setup.SetGcloudProxyProperties


class DisplayGcloudProxyInfoTests(cli_test_base.CliTestBase):

  def testAllPropertiesSetInGcloud(self):
    SET_PROXY(proxy_type='http', address='golden', port='80',
              username='username', password='password')
    proxy_info, from_gcloud = http_proxy_setup.EffectiveProxyInfo()
    self.assertIsNotNone(proxy_info)
    self.assertTrue(from_gcloud)
    http_proxy_setup._DisplayGcloudProxyInfo(proxy_info, from_gcloud)
    self.AssertErrEquals(textwrap.dedent("""\
        Current effective Cloud SDK network proxy settings:
            type = http
            host = golden
            port = 80
            username = username
            password = password
        """) + '\n')

  def testInvalidPropertiesSetInGcloud(self):
    SET_PROXY(proxy_type='http', port='80')
    with self.assertRaises(properties.InvalidValueError):
      http_proxy_setup.EffectiveProxyInfo()

  def testNoGcloudPropertiesProxyInEnvironmentVars(self):
    self.StartEnvPatch(
        {'http_proxy': 'https://baduser:badpassword@badproxy:8080',
         'https_proxy': 'https://baduser:badpassword@badproxy:8081'})
    proxy_info, from_gcloud = http_proxy_setup.EffectiveProxyInfo()
    self.assertIsNotNone(proxy_info)
    self.assertFalse(from_gcloud)
    http_proxy_setup._DisplayGcloudProxyInfo(proxy_info, from_gcloud)
    self.AssertErrEquals(textwrap.dedent("""\
        Current effective Cloud SDK network proxy settings:
        (These settings are from your machine's environment, not gcloud properties.)
            type = http
            host = badproxy
            port = 8081
            username = baduser
            password = badpassword
        """) + '\n')

  def testNoGcloudPropertiesNoProxyInEnvironmentVars(self):
    proxy_info, from_gcloud = http_proxy_setup.EffectiveProxyInfo()
    self.assertIsNone(proxy_info)
    self.assertFalse(from_gcloud)
    http_proxy_setup._DisplayGcloudProxyInfo(proxy_info, from_gcloud)
    self.AssertErrEquals('\n')


class ChangeGcloudProxySettingsTests(cli_test_base.CliTestBase):

  _CHANGE_EXISTING_MENU = (
      '{"ux": "PROMPT_CHOICE", "message": "What would you like to do?", '
      '"choices": ["Change Cloud SDK network proxy properties", '
      '"Clear all gcloud proxy properties", "Exit"]}')

  _ADD_NEW_PROXY_PROMPT = (
      'Do you have a network proxy you would like to set in gcloud')

  def ClearGcloudProxyProperties(self):
    SET_PROXY()
    self.AssertNoGloudProxyProperties()

  def AssertGoldenProxyProperties(self, with_auth=False):
    self.assertEqual('http', properties.VALUES.proxy.proxy_type.Get())
    self.assertEqual('golden', properties.VALUES.proxy.address.Get())
    self.assertEqual('80', properties.VALUES.proxy.port.Get())
    self.assertEqual('username' if with_auth else None,
                     properties.VALUES.proxy.username.Get())
    self.assertEqual('password' if with_auth else None,
                     properties.VALUES.proxy.password.Get())

  def AssertBadGloudProxyProperties(self):
    self.assertEqual('http', properties.VALUES.proxy.proxy_type.Get())
    self.assertEqual('badproxy', properties.VALUES.proxy.address.Get())
    self.assertEqual('8081', properties.VALUES.proxy.port.Get())
    self.assertEqual('baduser', properties.VALUES.proxy.username.Get())
    self.assertEqual('badpassword', properties.VALUES.proxy.password.Get())

  def AssertNoGloudProxyProperties(self):
    self.assertEqual(None, properties.VALUES.proxy.proxy_type.Get())
    self.assertEqual(None, properties.VALUES.proxy.address.Get())
    self.assertEqual(None, properties.VALUES.proxy.port.Get())
    self.assertEqual(None, properties.VALUES.proxy.username.Get())
    self.assertEqual(None, properties.VALUES.proxy.password.Get())

  def setAnswers(self, *answers):
    for answer in answers:
      self.WriteInput(answer)

  def testChangeExistingProxy(self):
    SET_PROXY(proxy_type='http', address='badproxy', port='8081',
              username='baduser', password='badpassword')
    self.AssertBadGloudProxyProperties()
    self.setAnswers('1', '1', 'golden', '80', 'Y', 'username', 'password')
    self.assertTrue(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrNotContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrContains('Cloud SDK proxy properties set.')
    self.AssertGoldenProxyProperties(with_auth=True)

  def testUserPromptsDisabled(self):
    SET_PROXY(proxy_type='http', address='badproxy', port='8081',
              username='baduser', password='badpassword')
    self.AssertBadGloudProxyProperties()
    self.StartObjectPatch(properties.VALUES.core.disable_prompts,
                          'GetBool').return_value = True
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrNotContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertBadGloudProxyProperties()

  def testChangeExistingProxyFromEnvVar(self):
    self.StartEnvPatch(
        {'http_proxy': 'https://baduser:badpassword@badproxy:8080',
         'https_proxy': 'https://baduser:badpassword@badproxy:8081'})
    pi = http_proxy.GetHttpProxyInfo()
    self.assertTrue(callable(pi))
    self.assertEqual(
        (socks.PROXY_TYPE_HTTP, 'badproxy', 8080, True, 'baduser',
         'badpassword', None),
        pi('http').astuple())
    self.assertEqual(
        (socks.PROXY_TYPE_HTTP, 'badproxy', 8081, True, 'baduser',
         'badpassword', None),
        pi('https').astuple())
    self.AssertNoGloudProxyProperties()
    self.setAnswers('Y', '1', 'golden', '80', 'Y', 'username', 'password')
    self.assertTrue(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrContains('Cloud SDK proxy properties set.')
    self.AssertGoldenProxyProperties(with_auth=True)

  def testClearExistingProxy(self):
    SET_PROXY(proxy_type='http', address='badproxy', port='8081',
              username='baduser', password='badpassword')
    self.AssertBadGloudProxyProperties()
    self.setAnswers('2')
    self.assertTrue(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrNotContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrContains('Cloud SDK proxy properties cleared.')
    self.AssertNoGloudProxyProperties()

  def testExistingProxyMakeNoChanges(self):
    SET_PROXY(proxy_type='http', address='badproxy', port='8081',
              username='baduser', password='badpassword')
    self.AssertBadGloudProxyProperties()
    self.setAnswers('3')
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrNotContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains('Cloud SDK proxy properties cleared.')
    self.AssertErrNotContains('Cloud SDK proxy properties set.')
    self.AssertBadGloudProxyProperties()

  def testInvalidPropertiesInGcloudMakeNoChanges(self):
    SET_PROXY(proxy_type='http', port='80')
    self.setAnswers('N')
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(
        'Cloud SDK network proxy settings appear to be invalid. Proxy type, '
        'address, and port must be specified. Run [gcloud info] for more '
        'details.')
    self.AssertErrContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrNotContains('Cloud SDK proxy properties set.')

  def testFromScratchMakeNoChanges(self):
    self.setAnswers('N')
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains('Cloud SDK proxy properties set.')
    self.AssertNoGloudProxyProperties()

  def testAddProxyFromScratchNoAuth(self):
    self.setAnswers('Y', '1', 'golden', '80', 'N')
    self.assertTrue(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrContains('Cloud SDK proxy properties set.')
    self.AssertGoldenProxyProperties(with_auth=False)

  def testAddProxyFromScratchWithAuth(self):
    self.setAnswers('Y', '1', 'golden', '80', 'Y', 'username', 'password')
    self.assertTrue(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrContains('Cloud SDK proxy properties set.')
    self.AssertGoldenProxyProperties(with_auth=True)

  def testAddProxyFromScratchNoTypeExit(self):
    self.setAnswers('Y', '')
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrContains('Select the proxy type:')
    self.AssertErrNotContains('Enter the proxy host address:')
    self.AssertErrNotContains('Enter the proxy port:')
    self.AssertErrNotContains('Is your proxy authenticated')
    self.AssertErrNotContains('Enter the proxy username:')
    self.AssertErrNotContains('Enter the proxy password:')
    self.AssertErrNotContains('Cloud SDK proxy properties set.')
    self.AssertNoGloudProxyProperties()

  def testAddProxyFromScratchNoHostExit(self):
    self.setAnswers('Y', '1', '')
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrContains('Select the proxy type:')
    self.AssertErrContains('Enter the proxy host address:')
    self.AssertErrNotContains('Enter the proxy port:')
    self.AssertErrNotContains('Is your proxy authenticated')
    self.AssertErrNotContains('Enter the proxy username:')
    self.AssertErrNotContains('Enter the proxy password:')
    self.AssertErrNotContains('Cloud SDK proxy properties set.')
    self.AssertNoGloudProxyProperties()

  def testAddProxyFromScratchNoPortExit(self):
    self.setAnswers('Y', '1', 'golden', '')
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrContains('Select the proxy type:')
    self.AssertErrContains('Enter the proxy host address:')
    self.AssertErrContains('Enter the proxy port:')
    self.AssertErrNotContains('Is your proxy authenticated')
    self.AssertErrNotContains('Enter the proxy username:')
    self.AssertErrNotContains('Enter the proxy password:')
    self.AssertErrNotContains('Cloud SDK proxy properties set.')
    self.AssertNoGloudProxyProperties()

  def testAddProxyFromScratchNoUsernameExit(self):
    self.setAnswers('Y', '1', 'golden', '80', 'Y', '')
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrContains('Select the proxy type:')
    self.AssertErrContains('Enter the proxy host address:')
    self.AssertErrContains('Enter the proxy port:')
    self.AssertErrContains('Is your proxy authenticated')
    self.AssertErrContains('Enter the proxy username:')
    self.AssertErrNotContains('Enter the proxy password:')
    self.AssertErrNotContains('Cloud SDK proxy properties set.')
    self.AssertNoGloudProxyProperties()

  def testAddProxyFromScratchNoPasswordExit(self):
    self.setAnswers('Y', '1', 'golden', '80', 'Y', 'username', '')
    self.assertFalse(http_proxy_setup.ChangeGcloudProxySettings())
    self.AssertErrContains(self._ADD_NEW_PROXY_PROMPT)
    self.AssertErrNotContains(self._CHANGE_EXISTING_MENU)
    self.AssertErrContains('Select the proxy type:')
    self.AssertErrContains('Enter the proxy host address:')
    self.AssertErrContains('Enter the proxy port:')
    self.AssertErrContains('Is your proxy authenticated')
    self.AssertErrContains('Enter the proxy username:')
    self.AssertErrContains('Enter the proxy password:')
    self.AssertErrNotContains('Cloud SDK proxy properties set.')
    self.AssertNoGloudProxyProperties()


if __name__ == '__main__':
  test_case.main()
