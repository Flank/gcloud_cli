# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
import uuid

from apitools.base.py import batch
from apitools.base.py import http_wrapper

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import http
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import platforms
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import httplib2
import mock
from oauth2client import client
import six
from google.auth import credentials
from google.auth import exceptions as google_auth_exceptions
from google.oauth2 import credentials as google_auth_creds


class CredentialsTestGoogleAuth(sdk_test_base.WithFakeAuth):

  def PreSetUp(self):
    self.use_google_auth = True

  def FakeAuthAccessToken(self):
    return None

  def testTokenRefreshErrorGoogleAuth(self):
    refresh_mock = self.StartObjectPatch(credentials.Credentials,
                                         'before_request')
    refresh_mock.side_effect = google_auth_exceptions.RefreshError
    http_client = http.Http(use_google_auth=True)
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      http_client.request('http://foo.com')

  def testTokenRefreshDeniedByCAAErrorGoogleAuth(self):
    refresh_mock = self.StartObjectPatch(credentials.Credentials,
                                         'before_request')
    refresh_mock.side_effect = google_auth_exceptions.RefreshError(
        'access_denied: Account restricted')
    http_client = http.Http(use_google_auth=True)
    with self.assertRaisesRegex(
        store.TokenRefreshDeniedByCAAError,
        'Access was blocked due to an organization policy'):
      http_client.request('http://foo.com')

  def testBatchTokenRefreshErrorGoogleAuth(self):
    refresh_mock = self.StartObjectPatch(credentials.Credentials,
                                         'before_request')
    refresh_mock.side_effect = google_auth_exceptions.RefreshError
    http_client = http.Http(use_google_auth=True)
    batch_http_request = batch.BatchHttpRequest(
        'https://www.googleapis.com/batch/compute')
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      batch_http_request.Execute(http_client)

  def testBatchTokenRefreshDeniedByCAAErrorGoogleAuth(self):
    refresh_mock = self.StartObjectPatch(credentials.Credentials,
                                         'before_request')
    refresh_mock.side_effect = google_auth_exceptions.RefreshError(
        'access_denied: Account restricted')
    http_client = http.Http(use_google_auth=True)
    batch_http_request = batch.BatchHttpRequest(
        'https://www.googleapis.com/batch/compute')
    with self.assertRaisesRegex(
        store.TokenRefreshDeniedByCAAError,
        'Access was blocked due to an organization policy'):
      batch_http_request.Execute(http_client)


class CredentialsTest(sdk_test_base.WithFakeAuth):

  def FakeAuthAccessToken(self):
    return None

  def testTokenRefreshError(self):
    refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                         '_do_refresh_request')
    refresh_mock.side_effect = client.AccessTokenRefreshError
    http_client = http.Http()
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      http_client.request('http://foo.com')

  def testTokenRefreshDeniedByCAAError(self):
    refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                         '_do_refresh_request')
    refresh_mock.side_effect = client.AccessTokenRefreshError(
        'access_deniedAccount restricted')
    http_client = http.Http()
    with self.assertRaisesRegex(
        store.TokenRefreshDeniedByCAAError,
        'Access was blocked due to an organization policy'):
      http_client.request('http://foo.com')

  def testBatchTokenRefreshError(self):
    refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                         '_do_refresh_request')
    refresh_mock.side_effect = client.AccessTokenRefreshError
    http_client = http.Http()
    batch_http_request = batch.BatchHttpRequest(
        'https://www.googleapis.com/batch/compute')
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      batch_http_request.Execute(http_client)

  def testBatchTokenRefreshDeniedByCAAError(self):
    refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                         '_do_refresh_request')
    refresh_mock.side_effect = client.AccessTokenRefreshError(
        'access_deniedAccount restricted')
    http_client = http.Http()
    batch_http_request = batch.BatchHttpRequest(
        'https://www.googleapis.com/batch/compute')
    with self.assertRaisesRegex(
        store.TokenRefreshDeniedByCAAError,
        'Access was blocked due to an organization policy'):
      batch_http_request.Execute(http_client)


class FakeService(object):
  """A service for testing."""

  def GetMethodConfig(self, _):
    return {}

  def GetUploadConfig(self, _):
    return {}

  # pylint: disable=unused-argument
  def PrepareHttpRequest(
      self, method_config, request, global_params, upload_config):
    return global_params['desired_request']

  def ProcessHttpResponse(self, _, http_response):
    return http_response


class BatchTokenRefreshTest(sdk_test_base.WithFakeAuth, parameterized.TestCase):

  def __ConfigureMock(self, mock_request, expected_request, response):
    if isinstance(response, list):
      response = list(response)

    def CheckRequest(_, request, **kwargs):
      del request, kwargs  # unused

      if isinstance(response, list):
        return response.pop(0)
      return response

    mock_request.side_effect = CheckRequest

  @parameterized.parameters(
      (True,),
      (False,),
  )
  def testBatchTokenRefresh(self, use_google_auth):
    self.use_google_auth = use_google_auth
    if use_google_auth:
      refresh_mock = self.StartObjectPatch(google_auth_creds.Credentials,
                                           'refresh')
    else:
      refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                           'refresh')
    mock_service = FakeService()

    desired_url = 'https://www.example.com'
    batch_api_request = batch.BatchApiRequest(batch_url=desired_url)
    # The request to be added. The actual request sent will be somewhat
    # larger, as this is added to a batch.
    desired_request = http_wrapper.Request(desired_url, 'POST', {
        'content-type': 'multipart/mixed; boundary="None"',
        'content-length': 80,
    }, 'x' * 80)

    mock_request = self.StartObjectPatch(http_wrapper, 'MakeRequest',
                                         autospec=True)
    self.__ConfigureMock(
        mock_request,
        http_wrapper.Request(
            desired_url, 'POST', {
                'content-type': 'multipart/mixed; boundary="None"',
                'content-length': 419,
            }, 'x' * 419), [
                http_wrapper.Response(
                    {
                        'status': '200',
                        'content-type': 'multipart/mixed; boundary="boundary"',
                    },
                    textwrap.dedent("""\
            --boundary
            content-type: text/plain
            content-id: <id+0>

            HTTP/1.1 401 UNAUTHORIZED
            Invalid grant

            --boundary--"""), None),
                http_wrapper.Response(
                    {
                        'status': '200',
                        'content-type': 'multipart/mixed; boundary="boundary"',
                    },
                    textwrap.dedent("""\
            --boundary
            content-type: text/plain
            content-id: <id+0>

            HTTP/1.1 200 OK
            content
            --boundary--"""), None)
            ])

    batch_api_request.Add(mock_service, 'unused', None, {
        'desired_request': desired_request,
    })

    batch_api_request.Execute(http.Http(use_google_auth=use_google_auth))
    refresh_mock.assert_called_once()


class HttpTestBase(sdk_test_base.SdkBase):

  def FakeAuthUserAgent(self):
    return ''

  def EncodeHeaders(self, headers):
    return {
        k.encode('ascii'): v.encode('ascii') for k, v in six.iteritems(headers)
    }

  def UserAgent(self, cmd_path, invocation_id, python_version, interactive,
                fromscript=False):
    template = ('{0} gcloud/{1} command/{2} invocation-id/{3} environment/{4} '
                'environment-version/{5} interactive/{6} from-script/{9} '
                'python/{7} term/xterm {8}')
    # Mocking the platform fragment doesn't seem to work all the time.
    # Use the real platform we are on.
    platform = platforms.Platform.Current().UserAgentFragment()
    environment = properties.GetMetricsEnvironment()
    environment_version = properties.VALUES.metrics.environment_version.Get()
    user_agent = template.format(config.CLOUDSDK_USER_AGENT,
                                 config.CLOUD_SDK_VERSION, cmd_path,
                                 invocation_id, environment,
                                 environment_version, interactive,
                                 python_version, platform, fromscript)
    return user_agent

  def SetUp(self):
    self.request_mock = self.StartObjectPatch(
        httplib2.Http,
        'request',
        return_value=(httplib2.Response({'status': 200}), b''))
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version
    self.StartObjectPatch(console_io, 'IsRunFromShellScript',
                          return_value=False)
    self.StartObjectPatch(console_attr.ConsoleAttr, 'GetTermIdentifier',
                          return_value='xterm')
    self.expected_user_agent = self.UserAgent(
        'None', uuid_mock.return_value.hex, python_version, False)
    self.url = 'http://foo.com'

  def AssertHeaderContains(self, header, call_args):
    args, kwargs = call_args
    if len(args) >= 3:
      self.assertDictContainsSubset(header, args[3])
    else:
      self.assertDictContainsSubset(header, kwargs['headers'])

  def AssertHeaderNotContains(self, header_key, call_args):
    args, kwargs = call_args
    if len(args) >= 3:
      self.assertNotIn(header_key, args[3])
    else:
      self.assertNotIn(header_key, kwargs['headers'])


class HttpTestUserCredsGoogleAuth(HttpTestBase, sdk_test_base.WithFakeAuth):

  def PreSetUp(self):
    self.use_google_auth = True

  def testIAMAuthoritySelectorHeaderGoogleAuth(self):
    authority_selector = 'superuser@google.com'
    properties.VALUES.auth.authority_selector.Set(authority_selector)

    expect_headers = {
        'user-agent': self.expected_user_agent,
        'x-goog-iam-authority-selector': authority_selector,
        'authorization': 'Bearer ' + self.FakeAuthAccessToken()
    }
    expect_headers = self.EncodeHeaders(expect_headers)

    http.Http(use_google_auth=True).request(
        self.url, 'GET', None, {}, redirections=0, connection_type=None)
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=expect_headers,
        redirections=0,
        connection_type=None)

  def testIAMAuthorizationTokenHeaderGoogleAuth(self):
    authorization_token = 'A very interesting authorization token'
    authorization_token_file = self.Touch(
        self.temp_path, 'auth_token_file', contents=authorization_token)
    properties.VALUES.auth.authorization_token_file.Set(
        authorization_token_file)

    expect_headers = {
        'user-agent': self.expected_user_agent,
        'x-goog-iam-authorization-token': authorization_token,
        'authorization': 'Bearer ' + self.FakeAuthAccessToken()
    }
    expect_headers = self.EncodeHeaders(expect_headers)
    http.Http(use_google_auth=True).request(
        self.url, 'GET', None, {}, redirections=0, connection_type=None)
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=expect_headers,
        redirections=0,
        connection_type=None)

  def testDisabledAuthGoogleAuth(self):
    properties.VALUES.auth.disable_credentials.Set(True)
    expect_headers = {'user-agent': self.expected_user_agent}
    expect_headers = self.EncodeHeaders(expect_headers)
    http.Http(use_google_auth=True).request(self.url, 'GET', None, None, 0,
                                            None)
    self.request_mock.assert_called_once_with(self.url, 'GET', None,
                                              expect_headers, 0, None)


class HttpTestUserCreds(HttpTestBase, sdk_test_base.WithFakeAuth):

  def testIAMAuthoritySelectorHeader(self):
    authority_selector = 'superuser@google.com'
    properties.VALUES.auth.authority_selector.Set(authority_selector)

    expect_headers = {
        'user-agent': self.expected_user_agent,
        'x-goog-iam-authority-selector': authority_selector,
        'Authorization': 'Bearer ' + self.FakeAuthAccessToken()}
    expect_headers = self.EncodeHeaders(expect_headers)
    http.Http().request(self.url, 'GET', None, {}, 0, None)
    self.request_mock.assert_called_once_with(self.url, 'GET', None,
                                              expect_headers, 0, None)

  def testIAMAuthorizationTokenHeader(self):
    authorization_token = 'A very interesting authorization token'
    authorization_token_file = self.Touch(
        self.temp_path, 'auth_token_file', contents=authorization_token)
    properties.VALUES.auth.authorization_token_file.Set(
        authorization_token_file)

    expect_headers = {
        'user-agent': self.expected_user_agent,
        'x-goog-iam-authorization-token': authorization_token,
        'Authorization': 'Bearer ' + self.FakeAuthAccessToken()}
    expect_headers = self.EncodeHeaders(expect_headers)
    http.Http().request(self.url, 'GET', None, {}, 0, None)
    self.request_mock.assert_called_once_with(self.url, 'GET', None,
                                              expect_headers, 0, None)

  def testDisabledAuth(self):
    properties.VALUES.auth.disable_credentials.Set(True)
    expect_headers = {'user-agent': self.expected_user_agent}
    expect_headers = self.EncodeHeaders(expect_headers)
    http_client = http.Http()
    http_client.request(self.url, 'GET', None, None, 0, None)
    self.request_mock.assert_called_once_with(self.url, 'GET', None,
                                              expect_headers, 0, None)

  def testResourceProjectOverride(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT)
    properties.VALUES.core.project.Set('foo')
    http.Http(enable_resource_quota=True).request(self.url, 'GET', None, {})
    expect_headers = self.EncodeHeaders({'X-Goog-User-Project': 'foo'})
    self.AssertHeaderContains(expect_headers, self.request_mock.call_args)

  def testResourceProjectOverrideLegacyProject(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.LEGACY)
    for x in [False, True]:
      http.Http(enable_resource_quota=x).request(self.url, 'GET', None, {})
      self.AssertHeaderNotContains('X-Goog-User-Project',
                                   self.request_mock.call_args)
      self.AssertHeaderNotContains(b'X-Goog-User-Project',
                                   self.request_mock.call_args)

  def testResourceProjectOverrideUnsetDefault(self):
    properties.VALUES.billing.quota_project.Set(None)
    http.Http(enable_resource_quota=False).request(self.url, 'GET', None, {})
    self.AssertHeaderNotContains('X-Goog-User-Project',
                                 self.request_mock.call_args)
    self.AssertHeaderNotContains(b'X-Goog-User-Project',
                                 self.request_mock.call_args)

  def testResourceProjectOverrideCustomProject(self):
    properties.VALUES.billing.quota_project.Set('bar')
    http.Http(enable_resource_quota=True).request(self.url, 'GET', None, {})
    expect_headers = self.EncodeHeaders({'X-Goog-User-Project': 'bar'})
    self.AssertHeaderContains(expect_headers, self.request_mock.call_args)

  def testResourceProjectOverrideForceResourceQuota(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.LEGACY)
    properties.VALUES.core.project.Set('foo')
    http.Http(
        enable_resource_quota=True,
        force_resource_quota=True).request(self.url, 'GET', None, {})
    expect_headers = self.EncodeHeaders({'X-Goog-User-Project': 'foo'})
    self.AssertHeaderContains(expect_headers, self.request_mock.call_args)


class HttpTestGCECreds(HttpTestBase, sdk_test_base.WithFakeComputeAuth):

  def testComputeServiceAccount(self):
    # Don't do it for service accounts.
    properties.VALUES.billing.quota_project.Set('bar')
    http.Http(enable_resource_quota=True).request(self.url, 'GET', None, {})
    self.AssertHeaderNotContains('X-Goog-User-Project',
                                 self.request_mock.call_args)
    self.AssertHeaderNotContains(b'X-Goog-User-Project',
                                 self.request_mock.call_args)


class HttpTestGCECredsGoogleAuth(HttpTestBase,
                                 sdk_test_base.WithFakeComputeAuth):

  def PreSetUp(self):
    self.use_google_auth = True

  def testComputeServiceAccountGoogleAuth(self):
    # Don't do it for service accounts.
    properties.VALUES.billing.quota_project.Set('bar')
    http.Http(
        enable_resource_quota=True,
        use_google_auth=True).request(self.url, 'GET', None, {})
    self.AssertHeaderNotContains('X-Goog-User-Project',
                                 self.request_mock.call_args)
    self.AssertHeaderNotContains(b'X-Goog-User-Project',
                                 self.request_mock.call_args)


class HttpTestUserProjectQuota(HttpTestBase, sdk_test_base.WithFakeAuth):

  def PreSetUp(self):
    self.use_google_auth = True

  def SetUp(self):
    common_headers = {
        'user-agent': self.expected_user_agent,
        'authorization': 'Bearer ' + self.FakeAuthAccessToken()
    }
    self.common_headers = self.EncodeHeaders(common_headers)

    self.permission_denied_response = (
        httplib2.Response({'status': 403}),
        b'{"error": {"message": "Grant the caller the Owner or Editor role, '
        b'or a custom role with the serviceusage.services.use permission"}}')

  def testForceUserProjectQuota(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.LEGACY)
    properties.VALUES.core.project.Set('foo')
    http.Http(
        enable_resource_quota=True,
        force_resource_quota=True,
        use_google_auth=True).request(self.url, 'GET', None, {})
    self.common_headers[b'X-Goog-User-Project'] = b'foo'
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testLegacyMode(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.LEGACY)
    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testCurrentProjectMode_WithPermission(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT)
    properties.VALUES.core.project.Set('foo')
    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    self.common_headers[b'X-Goog-User-Project'] = b'foo'
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testCurrentProjectMode_WithoutPermission(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT)
    properties.VALUES.core.project.Set('foo')
    self.request_mock.return_value = self.permission_denied_response
    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    self.common_headers[b'X-Goog-User-Project'] = b'foo'
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testCurrentProjectMode_EmptyProject(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT)
    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testCurrentProjectWithFallbackMode_WithPermission(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT_WITH_FALLBACK)
    properties.VALUES.core.project.Set('foo')

    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    self.common_headers[b'X-Goog-User-Project'] = b'foo'
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testCurrentProjectWithFallbackMode_WithoutPermission(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT_WITH_FALLBACK)
    properties.VALUES.core.project.Set('foo')
    self.request_mock.side_effect = (self.permission_denied_response,
                                     mock.DEFAULT)

    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    headers_with_quota = self.common_headers.copy()
    headers_with_quota[b'X-Goog-User-Project'] = b'foo'

    self.assertEqual(self.request_mock.call_count, 2)
    calls = [
        mock.call(
            self.url,
            'GET',
            body=None,
            headers=headers_with_quota,
            redirections=5,
            connection_type=None),
        mock.call(
            self.url,
            'GET',
            body=None,
            headers=self.common_headers,
            redirections=5,
            connection_type=None),
    ]
    self.request_mock.assert_has_calls(calls)

  def testCurrentProjectWithFallbackMode_EmptyProject(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT_WITH_FALLBACK)
    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testQuotaProjectManuallySet_WithPermission(self):
    properties.VALUES.billing.quota_project.Set('bar')
    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    self.common_headers[b'X-Goog-User-Project'] = b'bar'
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testQuotaProjectManuallySet_WithoutPermission(self):
    properties.VALUES.billing.quota_project.Set('bar')
    self.request_mock.return_value = self.permission_denied_response
    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    self.common_headers[b'X-Goog-User-Project'] = b'bar'
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testQuotaProjectDisabled(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT)
    properties.VALUES.core.project.Set('foo')
    http.Http(
        enable_resource_quota=False,
        use_google_auth=True).request(self.url, 'GET', None, {})
    self.request_mock.assert_called_once_with(
        self.url,
        'GET',
        body=None,
        headers=self.common_headers,
        redirections=5,
        connection_type=None)

  def testNoCredentialsMode(self):
    properties.VALUES.billing.quota_project.Set('bar')
    properties.VALUES.auth.disable_credentials.Set(True)
    http.Http(use_google_auth=True).request(self.url, 'GET', None, {})
    del self.common_headers[b'authorization']
    self.request_mock.assert_called_once_with(self.url, 'GET', None,
                                              self.common_headers)


if __name__ == '__main__':
  test_case.main()
