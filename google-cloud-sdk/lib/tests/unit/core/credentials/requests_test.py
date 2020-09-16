# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Tests for the requests module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import textwrap
import uuid

from apitools.base.py import batch
from apitools.base.py import http_wrapper

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import requests as creds_requests
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import platforms
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import httplib2
import mock
import requests
import six
from six.moves import http_client as httplib
from google.auth import credentials
from google.auth import exceptions as google_auth_exceptions
from google.oauth2 import credentials as google_auth_creds


def MakeRequestsResponse(status_code, headers, body):
  http_resp = requests.Response()
  http_resp.status_code = status_code
  http_resp.raw = io.BytesIO(six.ensure_binary(body))
  http_resp.headers = headers
  return http_resp


class CredentialsTest(sdk_test_base.WithFakeAuth):

  def PreSetUp(self):
    self.use_google_auth = True

  def FakeAuthAccessToken(self):
    return None

  def testTokenRefreshError(self):
    refresh_mock = self.StartObjectPatch(credentials.Credentials,
                                         'before_request')
    refresh_mock.side_effect = google_auth_exceptions.RefreshError
    http_client = creds_requests.GetSession()
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      http_client.request('GET', 'http://foo.com')

  def testTokenRefreshDeniedByCAAError(self):
    refresh_mock = self.StartObjectPatch(credentials.Credentials,
                                         'before_request')
    refresh_mock.side_effect = google_auth_exceptions.RefreshError(
        'access_denied: Account restricted')
    http_client = creds_requests.GetSession()
    with self.assertRaisesRegex(
        store.TokenRefreshDeniedByCAAError,
        'Access was blocked due to an organization policy'):
      http_client.request('GET', 'http://foo.com')

  def testBatchTokenRefreshError(self):
    refresh_mock = self.StartObjectPatch(credentials.Credentials,
                                         'before_request')
    refresh_mock.side_effect = google_auth_exceptions.RefreshError
    http_client = creds_requests.GetApitoolsRequests(
        creds_requests.GetSession())
    batch_http_request = batch.BatchHttpRequest(
        'https://www.googleapis.com/batch/compute')
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      batch_http_request.Execute(http_client)

  def testBatchTokenRefreshDeniedByCAAError(self):
    refresh_mock = self.StartObjectPatch(credentials.Credentials,
                                         'before_request')
    refresh_mock.side_effect = google_auth_exceptions.RefreshError(
        'access_denied: Account restricted')
    http_client = creds_requests.GetApitoolsRequests(
        creds_requests.GetSession())
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


class BatchTokenRefreshTest(sdk_test_base.WithFakeAuth):

  def PreSetUp(self):
    self.use_google_auth = True

  def __ConfigureMock(self, mock_request, expected_request, response):
    if isinstance(response, list):
      response = list(response)

    def CheckRequest(_, request, **kwargs):
      del request, kwargs  # unused

      if isinstance(response, list):
        return response.pop(0)
      return response

    mock_request.side_effect = CheckRequest

  def testBatchTokenRefresh(self):
    refresh_mock = self.StartObjectPatch(google_auth_creds.Credentials,
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

    http_client = creds_requests.GetApitoolsRequests(
        creds_requests.GetSession())
    batch_api_request.Execute(http_client)
    refresh_mock.assert_called_once()


class HttpTestBase(sdk_test_base.SdkBase):

  def FakeAuthUserAgent(self):
    return ''

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
        requests.Session,
        'request',
        return_value=MakeRequestsResponse(httplib.OK, {}, ''))
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


class HttpTestUserCreds(HttpTestBase, sdk_test_base.WithFakeAuth):

  def PreSetUp(self):
    self.use_google_auth = True

  def _EncodeHeaders(self, headers):
    return {
        k.encode('ascii'): v.encode('ascii')
        for k, v in six.iteritems(headers)}

  def testIAMAuthoritySelectorHeader(self):
    url = 'http://foo.com'
    authority_selector = 'superuser@google.com'
    properties.VALUES.auth.authority_selector.Set(authority_selector)

    expected_headers = {'x-goog-iam-authority-selector': authority_selector}
    expected_headers = self._EncodeHeaders(expected_headers)

    creds_requests.GetSession().request('GET', url)
    self.assertDictContainsSubset(expected_headers,
                                  self.request_mock.call_args[1]['headers'])

  def testIAMAuthorizationTokenHeader(self):
    url = 'http://foo.com'
    authorization_token = 'A very interesting authorization token'
    authorization_token_file = self.Touch(
        self.temp_path, 'auth_token_file', contents=authorization_token)
    properties.VALUES.auth.authorization_token_file.Set(
        authorization_token_file)

    expected_headers = {'x-goog-iam-authorization-token': authorization_token}
    expected_headers = self._EncodeHeaders(expected_headers)
    creds_requests.GetSession().request('GET', url)
    self.assertDictContainsSubset(expected_headers,
                                  self.request_mock.call_args[1]['headers'])

  def testDisabledAuth(self):
    properties.VALUES.auth.disable_credentials.Set(True)
    url = 'http://foo.com'
    expected_headers = {'user-agent': self.expected_user_agent}
    expected_headers = self._EncodeHeaders(expected_headers)
    http_client = creds_requests.GetSession()
    http_client.request('GET', url)
    self.request_mock.assert_called_once_with(
        'GET', url, headers=expected_headers, timeout=mock.ANY)

  def testResourceProjectOverride(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.CURRENT_PROJECT)
    properties.VALUES.core.project.Set('foo')
    creds_requests.GetSession(
        enable_resource_quota=True).request('GET', 'http://foo.com')
    expected_headers = self._EncodeHeaders({'X-Goog-User-Project': 'foo'})
    self.assertDictContainsSubset(expected_headers,
                                  self.request_mock.call_args[1]['headers'])

  def testResourceProjectOverrideLegacyProject(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.LEGACY)
    for enable_resource_quota in [False, True]:
      creds_requests.GetSession(
          enable_resource_quota=enable_resource_quota
          ).request('GET', 'http://foo.com')
      self.assertNotIn('X-Goog-User-Project',
                       self.request_mock.call_args[1]['headers'])
      self.assertNotIn(b'X-Goog-User-Project',
                       self.request_mock.call_args[1]['headers'])

  def testResourceProjectOverrideUnsetDefault(self):
    properties.VALUES.billing.quota_project.Set(None)
    creds_requests.GetSession(
        enable_resource_quota=False).request('GET', 'http://foo.com')
    self.assertNotIn('X-Goog-User-Project',
                     self.request_mock.call_args[1]['headers'])
    self.assertNotIn(b'X-Goog-User-Project',
                     self.request_mock.call_args[1]['headers'])

  def testResourceProjectOverrideCustomProject(self):
    properties.VALUES.billing.quota_project.Set('bar')
    creds_requests.GetSession(
        enable_resource_quota=True).request('GET', 'http://foo.com')
    expected_headers = self._EncodeHeaders({'X-Goog-User-Project': 'bar'})
    self.assertDictContainsSubset(expected_headers,
                                  self.request_mock.call_args[1]['headers'])

  def testResourceProjectOverrideForceResourceQuota(self):
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.LEGACY)
    properties.VALUES.core.project.Set('foo')
    creds_requests.GetSession(
        enable_resource_quota=True,
        force_resource_quota=True).request('GET', 'http://foo.com')
    expected_headers = self._EncodeHeaders({'X-Goog-User-Project': 'foo'})
    self.assertDictContainsSubset(expected_headers,
                                  self.request_mock.call_args[1]['headers'])


class HttpTestGCECreds(HttpTestBase, sdk_test_base.WithFakeComputeAuth):

  def PreSetUp(self):
    self.use_google_auth = True

  def testComputeServiceAccount(self):
    # Don't do it for service accounts.
    properties.VALUES.billing.quota_project.Set('bar')
    creds_requests.GetSession(
        enable_resource_quota=True).request('GET', 'http://foo.com')
    self.assertNotIn('X-Goog-User-Project',
                     self.request_mock.call_args[1]['headers'])
    self.assertNotIn(b'X-Goog-User-Project',
                     self.request_mock.call_args[1]['headers'])


class ApitoolsRequestsTest(sdk_test_base.WithFakeAuth, parameterized.TestCase):

  def PreSetUp(self):
    self.use_google_auth = True

  @parameterized.parameters(
      (None, b'data'),
      ('utf-8', 'data'),
  )
  def testResponseEncoding(self, encoding, expected_response):
    self.request_mock = self.StartObjectPatch(
        requests.Session,
        'request',
        return_value=MakeRequestsResponse(httplib.OK, {
            'header': 'value',
        }, b'data'))
    session = creds_requests.GetSession(response_encoding=encoding)
    apitools_requests = creds_requests.GetApitoolsRequests(session)
    response = apitools_requests.request('url')
    self.assertEqual(response[0], httplib2.Response({
        'status': httplib.OK,
        'header': 'value',
    }))
    self.assertEqual(response[1], expected_response)


if __name__ == '__main__':
  test_case.main()
