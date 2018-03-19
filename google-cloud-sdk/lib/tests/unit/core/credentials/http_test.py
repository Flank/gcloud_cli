# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Tests for the http module."""

import uuid

from apitools.base.py import batch

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import http
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case

import httplib2
from oauth2client import client


class CredentialsTest(sdk_test_base.WithFakeAuth):

  def FakeAuthAccessToken(self):
    return None

  def testTokenRefreshError(self):
    refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                         '_do_refresh_request')
    refresh_mock.side_effect = client.AccessTokenRefreshError
    http_client = http.Http()
    with self.assertRaisesRegexp(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      http_client.request('http://foo.com')
    # Make sure it also extends the original exception.
    with self.assertRaisesRegexp(
        client.AccessTokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      http_client.request('http://foo.com')

  def testBatchTokenRefreshError(self):
    refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                         '_do_refresh_request')
    refresh_mock.side_effect = client.AccessTokenRefreshError
    http_client = http.Http()
    batch_http_request = batch.BatchHttpRequest(
        batch_url='https://www.googleapis.com/batch/compute')
    with self.assertRaisesRegexp(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      batch_http_request.Execute(http_client)


class HttpTestBase(sdk_test_base.SdkBase):

  def FakeAuthUserAgent(self):
    return ''

  def UserAgent(self, cmd_path, invocation_id, python_version, interactive,
                fromscript=False):
    template = ('gcloud/{0} command/{1} invocation-id/{2} environment/{3} '
                'environment-version/{4} interactive/{5} from-script/{8} '
                'python/{6} {7}')
    # Mocking the platform fragment doesn't seem to work all the time.
    # Use the real platform we are on.
    platform = platforms.Platform.Current().UserAgentFragment()
    environment = properties.GetMetricsEnvironment()
    environment_version = properties.VALUES.metrics.environment_version.Get()
    user_agent = template.format(config.CLOUD_SDK_VERSION,
                                 cmd_path,
                                 invocation_id,
                                 environment,
                                 environment_version,
                                 interactive,
                                 python_version,
                                 platform,
                                 fromscript)
    return user_agent

  def SetUp(self):
    self.request_mock = self.StartObjectPatch(
        httplib2.Http, 'request',
        return_value=(httplib2.Response({'status': 400}), ''))
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version
    self.StartObjectPatch(console_io, 'IsRunFromShellScript',
                          return_value=False)
    self.expected_user_agent = self.UserAgent(
        'None', uuid_mock.return_value.hex, python_version, False)


class HttpTestUserCreds(HttpTestBase, sdk_test_base.WithFakeAuth):

  def testIAMAuthoritySelectorHeader(self):
    url = 'http://foo.com'
    authority_selector = 'superuser@google.com'
    properties.VALUES.auth.authority_selector.Set(authority_selector)

    expect_headers = {
        'user-agent': self.expected_user_agent,
        'x-goog-iam-authority-selector': authority_selector,
        'Authorization': 'Bearer ' + self.FakeAuthAccessToken()}
    http.Http().request(url, 'GET', None, {}, 0, None)
    self.request_mock.assert_called_once_with(
        url, 'GET', None, expect_headers, 0, None)

  def testIAMAuthorizationTokenHeader(self):
    url = 'http://foo.com'
    authorization_token = 'A very interesting authorization token'
    authorization_token_file = self.Touch(
        self.temp_path, 'auth_token_file', contents=authorization_token)
    properties.VALUES.auth.authorization_token_file.Set(
        authorization_token_file)

    expect_headers = {
        'user-agent': self.expected_user_agent,
        'x-goog-iam-authorization-token': authorization_token,
        'Authorization': 'Bearer ' + self.FakeAuthAccessToken()}
    http.Http().request(url, 'GET', None, {}, 0, None)
    self.request_mock.assert_called_once_with(
        url, 'GET', None, expect_headers, 0, None)

  def testDisabledAuth(self):
    properties.VALUES.auth.disable_credentials.Set(True)
    url = 'http://foo.com'
    expect_headers = {'user-agent': self.expected_user_agent}
    http_client = http.Http()
    http_client.request(url, 'GET', None, None, 0, None)
    self.request_mock.assert_called_once_with(
        url, 'GET', None, expect_headers, 0, None)

  def testResourceProjectOverride(self):
    # If this property is set to legacy, never use the header.
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.LEGACY)
    for x in [False, True]:
      http.Http(enable_resource_quota=x).request(
          'http://foo.com', 'GET', None, {})
      self.assertNotIn('X-Goog-User-Project', self.request_mock.call_args[0][3])

    # Legacy is the default, so if unset, don't use the header.
    properties.VALUES.billing.quota_project.Set(None)
    http.Http(enable_resource_quota=False).request(
        'http://foo.com', 'GET', None, {})
    self.assertNotIn('X-Goog-User-Project', self.request_mock.call_args[0][3])

    # Use the header.
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT)
    properties.VALUES.core.project.Set('foo')
    http.Http(enable_resource_quota=True).request(
        'http://foo.com', 'GET', None, {})
    self.assertDictContainsSubset({'X-Goog-User-Project': 'foo'},
                                  self.request_mock.call_args[0][3])
    # Custom project.
    properties.VALUES.billing.quota_project.Set('bar')
    http.Http(enable_resource_quota=True).request(
        'http://foo.com', 'GET', None, {})
    self.assertDictContainsSubset({'X-Goog-User-Project': 'bar'},
                                  self.request_mock.call_args[0][3])


class HttpTestGCECreds(HttpTestBase, sdk_test_base.WithFakeComputeAuth):

  def testComputeServiceAccount(self):
    # Don't do it for service accounts.
    properties.VALUES.billing.quota_project.Set('bar')
    http.Http(enable_resource_quota=True).request(
        'http://foo.com', 'GET', None, {})
    self.assertNotIn('X-Goog-User-Project', self.request_mock.call_args[0][3])


if __name__ == '__main__':
  test_case.main()
