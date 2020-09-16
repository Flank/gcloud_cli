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

import collections
import io
import socket
import uuid

from googlecloudsdk.core import config
from googlecloudsdk.core import context_aware
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests as core_requests
from googlecloudsdk.core import transport
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import platforms
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock
import requests
import six
from six.moves import http_client as httplib


class _UncopyableObject(object):
  """Dummy object used for testing."""

  def __copy__(self):
    raise ValueError()

  def __deepcopy__(self, memo):
    del memo  # Unused in __deepcopy__
    return self.__copy__()


def MakeRequestsResponse(status_code, headers, body):
  http_resp = requests.Response()
  http_resp.status_code = status_code
  http_resp.raw = io.BytesIO(six.ensure_binary(body))
  http_resp.headers = headers
  return http_resp

ProxySettings = collections.namedtuple(
    'ProxySettings',
    ['proxy_type', 'address', 'port', 'rdns', 'username', 'password'])


class RequestsTest(sdk_test_base.WithFakeAuth, test_case.WithOutputCapture,
                   parameterized.TestCase):

  def SetUp(self):
    self.old_version = config.CLOUD_SDK_VERSION
    config.CLOUD_SDK_VERSION = '10.0.0'
    self.StartObjectPatch(
        console_io, 'IsRunFromShellScript', return_value=False)
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermIdentifier', return_value='xterm')

    self.default_response = MakeRequestsResponse(
        httplib.OK, {}, b'response content')

  def TearDown(self):
    config.CLOUD_SDK_VERSION = self.old_version

  def UserAgent(self,
                version,
                cmd_path,
                invocation_id,
                python_version,
                interactive,
                fromscript=False,
                include_cloudsdk_prefix=True):
    template = ('gcloud/{0} command/{1} invocation-id/{2} environment/{3} '
                'environment-version/{4} interactive/{5} from-script/{8} '
                'python/{6} term/xterm {7}')
    # Mocking the platform fragment doesn't seem to work all the time.
    # Use the real platform we are on.
    platform = platforms.Platform.Current().UserAgentFragment()
    environment = properties.GetMetricsEnvironment()
    environment_version = properties.VALUES.metrics.environment_version.Get()
    user_agent = template.format(
        version, cmd_path, invocation_id, environment, environment_version,
        interactive, python_version, platform, fromscript)
    if include_cloudsdk_prefix:
      user_agent = config.CLOUDSDK_USER_AGENT + ' ' + user_agent
    return user_agent.encode('utf-8')

  def testUserAgent(self):
    request_mock = self.StartObjectPatch(requests.Session, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    headers = {}
    http_client = core_requests.GetSession()
    url = 'http://foo.com'
    request_mock.return_value = self.default_response
    http_client.request('GET', url, headers=headers,
                        uncopyable=_UncopyableObject())
    expect_user_agent = self.UserAgent('10.0.0', 'None',
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    request_mock.assert_called_once_with(
        'GET', url, headers={b'user-agent': expect_user_agent},
        uncopyable=mock.ANY, timeout=mock.ANY)
    request_mock.reset_mock()
    # Make sure our wrapping did not actually affect args we pass into request.
    # If it does, we could accidentally be modifying global state.
    self.assertEqual(headers, {})

    cmd_path = 'a.b.c.d'
    properties.VALUES.metrics.command_name.Set(cmd_path)
    http_client = core_requests.GetSession()
    request_mock.return_value = self.default_response
    http_client.request('GET', url)
    expect_user_agent = self.UserAgent('10.0.0', cmd_path,
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    request_mock.assert_called_once_with(
        'GET', url, headers={b'user-agent': expect_user_agent},
        timeout=mock.ANY)
    request_mock.reset_mock()

    cmd_path = 'a.b.e.d'
    properties.VALUES.metrics.command_name.Set(cmd_path)
    http_client = core_requests.GetSession()
    expect_headers = {b'user-agent': b'hello'}
    request_mock.return_value = self.default_response
    http_client.request('GET', url, headers=expect_headers)
    expect_user_agent = (b'%s hello %s' %
                         (config.CLOUDSDK_USER_AGENT.encode('utf-8'),
                          self.UserAgent(
                              '10.0.0',
                              cmd_path,
                              uuid_mock.return_value.hex,
                              python_version,
                              False,
                              include_cloudsdk_prefix=False)))
    request_mock.assert_called_once_with(
        'GET', url, headers={b'user-agent': expect_user_agent},
        timeout=mock.ANY)
    request_mock.reset_mock()

    cmd_path = 'a.b.e.d'
    properties.VALUES.metrics.command_name.Set(cmd_path)
    http_client = core_requests.GetSession()
    expect_headers = {b'user-agent': b'google-cloud-sdk'}
    request_mock.return_value = self.default_response
    http_client.request('GET', url, headers=expect_headers)
    expect_user_agent = self.UserAgent('10.0.0', cmd_path,
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    request_mock.assert_called_once_with(
        'GET', url, headers={b'user-agent': expect_user_agent},
        timeout=mock.ANY)

  @parameterized.parameters(('USER-AGENT', b'my.user.agent'),
                            ('user-agent', b'my.user.agent'),
                            ('User-Agent', b'my.user.agent'))
  def testUserAgent_AllSpellings(self, ua_header, ua_value):
    request_mock = self.StartObjectPatch(requests.Session, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    headers = {}
    http_client = core_requests.GetSession()
    url = 'http://foo.com'
    request_mock.return_value = self.default_response
    headers[ua_header] = ua_value
    http_client.request('GET', url, headers=headers,
                        uncopyable=_UncopyableObject())
    expect_user_agent = (b'%s %s %s' %
                         (config.CLOUDSDK_USER_AGENT.encode('utf-8'), ua_value,
                          self.UserAgent(
                              '10.0.0',
                              'None',
                              uuid_mock.return_value.hex,
                              python_version,
                              False,
                              include_cloudsdk_prefix=False)))

    request_mock.assert_called_once_with(
        'GET', url, headers={b'user-agent': expect_user_agent},
        uncopyable=mock.ANY, timeout=mock.ANY)
    request_mock.reset_mock()

  def testUserAgent_SpacesInVersion(self):
    # This is similar to what the versions look like for some internal builds
    config.CLOUD_SDK_VERSION = 'Mon Sep 12 08:35:01 2016'
    request_mock = self.StartObjectPatch(requests.Session, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    http_client = core_requests.GetSession()
    url = 'http://foo.com'
    request_mock.return_value = self.default_response
    http_client.request('GET', url)
    expect_user_agent = self.UserAgent('Mon_Sep_12_08:35:01_2016', 'None',
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    request_mock.assert_called_once_with(
        'GET', url, headers={b'user-agent': expect_user_agent},
        timeout=mock.ANY)
    request_mock.reset_mock()

  def testTraces(self):
    request_mock = self.StartObjectPatch(requests.Session, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    expect_user_agent = self.UserAgent('10.0.0', 'None',
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    http_client = core_requests.GetSession()
    url = 'http://foo.com'
    request_mock.return_value = self.default_response
    http_client.request('GET', url)
    request_mock.assert_called_once_with(
        'GET', url, headers={b'user-agent': expect_user_agent},
        timeout=mock.ANY)
    request_mock.reset_mock()

    trace_token = 'hello'
    properties.VALUES.core.trace_token.Set(trace_token)
    http_client = core_requests.GetSession()
    request_mock.return_value = self.default_response
    http_client.request('GET', url)
    expect_url = '{0}?trace=token%3A{1}'.format(url, trace_token)
    request_mock.assert_called_once_with(
        'GET', expect_url, headers={b'user-agent': expect_user_agent},
        timeout=mock.ANY)
    request_mock.reset_mock()
    properties.VALUES.core.trace_token.Set(None)

    trace_email = 'hello'
    properties.VALUES.core.trace_email.Set(trace_email)
    http_client = core_requests.GetSession()
    request_mock.return_value = self.default_response
    http_client.request('GET', url)
    expect_url = '{0}?trace=email%3A{1}'.format(url, trace_email)
    request_mock.assert_called_once_with(
        'GET', expect_url, headers={b'user-agent': expect_user_agent},
        timeout=mock.ANY)
    request_mock.reset_mock()
    properties.VALUES.core.trace_email.Set(None)

    properties.VALUES.core.trace_log.Set(True)
    http_client = core_requests.GetSession()
    request_mock.return_value = self.default_response
    http_client.request('GET', url)
    expect_url = '{0}?trace=log'.format(url)
    request_mock.assert_called_once_with(
        'GET', expect_url, headers={b'user-agent': expect_user_agent},
        timeout=mock.ANY)
    properties.VALUES.core.trace_log.Set(None)

  def _FormatHeaderOutput(self, headers):
    return '\n'.join(
        ['{0}: {1}'.format(k, v) for k, v in sorted(six.iteritems(headers))])

  def testRequestResponseDump(self):
    request_mock = self.StartObjectPatch(requests.Session, 'request')
    response_headers = {b'header1': b'value1', b'header2': b'value2'}
    request_mock.return_value = MakeRequestsResponse(
        httplib.OK, response_headers, 'response content')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    expect_user_agent = self.UserAgent('10.0.0', 'None',
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    user_agent_header = {b'user-agent': expect_user_agent}
    log_mock = self.StartObjectPatch(log.status, 'Print')
    properties.VALUES.core.log_http.Set(True)
    http_client = core_requests.GetSession()
    url = 'http://foo.com'
    time_mock = self.StartPatch('time.time', autospec=True)
    # Time is called twice by RPC duration reporting and twice by logging
    time_mock.side_effect = [1.0, 1.1, 3.0, 3.1]
    http_client.request('GET', url, data='Request Body')
    request_mock.assert_called_once_with(
        'GET',
        url,
        headers=user_agent_header,
        data='Request Body',
        timeout=mock.ANY,
    )
    request_mock.reset_mock()

    expected_output = """\
=======================
==== request start ====
uri: http://foo.com
method: GET
== headers start ==
{0}
== headers end ==
== body start ==
Request Body
== body end ==
==== request end ====
---- response start ----
{1}
-- headers start --
{2}
-- headers end --
-- body start --
response content
-- body end --
total round trip time (request+response): 2.000 secs
---- response end ----
----------------------""".format(
    self._FormatHeaderOutput(user_agent_header),
    self._FormatHeaderOutput({'status': httplib.OK}),
    self._FormatHeaderOutput(response_headers))

    calls = []
    for line in expected_output.split('\n'):
      if line == 'response content':
        line = b'response content'
      calls.append(mock.call(line))

    log_mock.assert_has_calls(calls)

  def testLogHttpOauthRedaction(self):
    request_mock = self.StartObjectPatch(requests.Session, 'request')

    def Run(url, extra_headers):
      request_mock.return_value = MakeRequestsResponse(
          httplib.OK, {
              'header1': 'value1',
              'header2': 'value2'},
          b'response content')
      properties.VALUES.core.log_http.Set(True)
      http_client = core_requests.GetSession()
      http_client.request(
          'GET', url, data='request content', headers=extra_headers)
      request_mock.assert_called_once_with(
          'GET',
          url,
          headers=mock.ANY,
          data='request content',
          timeout=mock.ANY,
      )
      request_mock.reset_mock()

    # Test authorization header is redacted.
    Run(
        'https://fake.googleapis.com/foo', {
            'Authorization': 'Bearer oauth2token',
            'x-goog-iam-authorization-token': 'iamtoken',
        })
    self.AssertErrNotContains('oauth2token')
    self.AssertErrNotContains('iamtoken')
    self.AssertErrContains('request content')
    self.AssertErrContains('response content')
    self.ClearErr()

    # Test body is redacted from both request and response.
    Run('https://accounts.google.com/o/oauth2/token', {})
    self.AssertErrNotContains('request content')
    self.AssertErrNotContains('response content')
    self.ClearErr()

    # Test body is redacted from response. Body of request doesn't matter.
    Run(
        'http://metadata.google.internal/computeMetadata/v1/instance/'
        'service-accounts/something@developer.gserviceaccount.com/token', {})
    self.AssertErrNotContains('response content')
    self.ClearErr()

  def testRequestReason(self):
    properties.VALUES.core.request_reason.Set('my request justification')
    request_mock = self.StartObjectPatch(requests.Session, 'request')
    request_mock.return_value = MakeRequestsResponse(
        httplib.OK, {
            'header1': 'value1',
            'header2': 'value2'},
        b'response content')
    http_client = core_requests.GetSession()

    http_client.request(
        'GET',
        'http://www.example.com/foo',
        data='request content',
        headers={})

    expected_headers = {
        b'user-agent': mock.ANY,
        b'X-Goog-Request-Reason': b'my request justification'
    }
    request_mock.assert_called_once_with(
        'GET',
        'http://www.example.com/foo',
        data='request content',
        headers=expected_headers,
        timeout=mock.ANY)

  def testDefaultTimeout(self):
    timeout_mock = self.StartObjectPatch(transport, 'GetDefaultTimeout')
    timeout_mock.return_value = 0.001
    self.socket_connect_mock.side_effect = socket.timeout
    http_client = core_requests.GetSession()
    with self.assertRaises(requests.ConnectTimeout):
      http_client.request('GET', 'http://localhost/')

  @parameterized.parameters(
      (ProxySettings(None, None, None, None, None, None),
       None, None),
      (ProxySettings('http', '123.123.123.123', '4321', None, None, None),
       'https://123.123.123.123:4321', None),
      (ProxySettings('http', '123.123.123.123', '4321', False,
                     'user', 'pass'),
       'https://user:pass@123.123.123.123:4321', None),
      (ProxySettings('http', '123.123.123.123', '4321', False,
                     'user', ''),
       'https://user:@123.123.123.123:4321', None),
      (ProxySettings('socks4', '123.123.123.123', '4321', False,
                     None, None),
       'socks4://123.123.123.123:4321', None),
      (ProxySettings('socks4', '123.123.123.123', '4321', True,
                     None, None),
       'socks4a://123.123.123.123:4321', None),
      (ProxySettings('socks5', '123.123.123.123', '4321', True,
                     None, None),
       'socks5h://123.123.123.123:4321', None),
      (ProxySettings(None, '123.123.123.123', '4321', None, None, None),
       None, (properties.InvalidValueError,
              'Please set all or none of the following properties: '
              'proxy/type, proxy/address and proxy/port')
       ),
  )
  def testGetProxyInfo(self, proxy_settings, expected_proxy,
                       expected_exception):
    properties.VALUES.proxy.proxy_type.Set(proxy_settings.proxy_type)
    properties.VALUES.proxy.address.Set(proxy_settings.address)
    properties.VALUES.proxy.port.Set(proxy_settings.port)
    properties.VALUES.proxy.rdns.Set(proxy_settings.rdns)
    properties.VALUES.proxy.username.Set(proxy_settings.username)
    properties.VALUES.proxy.password.Set(proxy_settings.password)

    if expected_exception:
      exception_type, exception_regex = expected_exception
      with self.assertRaisesRegex(exception_type, exception_regex):
        core_requests.GetProxyInfo()
    else:
      proxy = core_requests.GetProxyInfo()
      self.assertEqual(expected_proxy, proxy)

  def testRPCDurationReporting(self):
    request_mock = self.StartObjectPatch(requests.Session, 'request')
    request_mock.return_value = self.default_response

    time_mock = self.StartPatch('time.time', autospec=True)
    time_mock.side_effect = [1.0, 4.0]

    duration_mock = self.StartObjectPatch(metrics, 'RPCDuration')

    http_client = core_requests.GetSession()
    http_client.request('GET', 'http://foo.com', data='Request Body')
    duration_mock.assert_called_once_with(3.0)

  def testResponseEncoding(self):
    request_mock = self.StartObjectPatch(requests.Session, 'request')
    request_mock.return_value = MakeRequestsResponse(
        httplib.OK, {}, b'\xe1\x95\x95( \xe1\x90\x9b )\xe1\x95\x97')

    http_client = core_requests.GetSession(response_encoding='utf-8')
    response = http_client.request(
        'GET', 'http://foo.com', data='Request Body')
    self.assertEqual('ᕕ( ᐛ )ᕗ', response.text)


class RequestTest(parameterized.TestCase):

  def testRequest(self):
    request = core_requests.Request.FromRequestArgs(
        'method', 'url', data='body', headers={'hdr': '1'})
    self.assertEqual(request.uri, 'url')
    self.assertEqual(request.method, 'method')
    self.assertEqual(request.headers, {'hdr': '1'})
    self.assertEqual(request.body, 'body')

    actual_args, actual_kwargs = request.ToRequestArgs()
    self.assertEqual(actual_args, ['method', 'url'])
    self.assertEqual(actual_kwargs, {
        'data': 'body', 'headers': {'hdr': '1'},
    })


class ResponseTest(test_case.TestCase):

  def testResponse(self):
    http_resp = MakeRequestsResponse(httplib.OK, {'hdr': '1'}, 'body')
    response = core_requests.Response.FromResponse(http_resp)
    self.assertEqual(response.status_code, httplib.OK)
    self.assertEqual(response.headers, {'hdr': '1'})
    self.assertEqual(response.body, b'body')


class ContextAwareTest(test_case.TestCase):

  def testWithContextAwareConfig(self):
    properties.VALUES.context_aware.use_client_certificate.Set(True)
    context_mock = mock.Mock()
    self.StartObjectPatch(
        core_requests, 'CreateSSLContext', return_value=context_mock)

    context_aware_config = self.StartObjectPatch(context_aware, 'Config')
    context_aware_config.return_value = mock.Mock(
        client_cert_path='mock_path', client_cert_password='mock_pass')

    http_adapter_mock = self.StartObjectPatch(
        core_requests.HTTPAdapter, 'send')
    http_adapter_mock.return_value = MakeRequestsResponse(
        httplib.OK, {}, b'response content')
    http_client = core_requests.GetSession()
    http_client.request('GET', 'https://www.foo.com', data='Request Body')

    context_mock.load_cert_chain.assert_called_once_with(
        'mock_path',
        **{
            'keyfile': 'mock_path',
            'password': 'mock_pass',
        })


if __name__ == '__main__':
  test_case.main()
