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

import socket
import uuid

from googlecloudsdk.core import config
from googlecloudsdk.core import http
from googlecloudsdk.core import http_proxy
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import platforms
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
import httplib2
import mock

import six
from six.moves import http_client as httplib
import socks


class _UncopyableObject(object):
  """Dummy object used for testing."""

  def __copy__(self):
    raise ValueError()

  def __deepcopy__(self, memo):
    del memo  # Unused in __deepcopy__
    return self.__copy__()


class HttpTest(sdk_test_base.WithFakeAuth, test_case.WithOutputCapture,
               parameterized.TestCase):

  def SetUp(self):
    self.old_version = config.CLOUD_SDK_VERSION
    config.CLOUD_SDK_VERSION = '10.0.0'
    self.StartObjectPatch(
        console_io, 'IsRunFromShellScript', return_value=False)
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermIdentifier', return_value='xterm')

    self.default_response = ({}, b'response content')

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
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    headers = {}
    http_client = http.Http()
    url = 'http://foo.com'
    request_mock.return_value = self.default_response
    http_client.request(url, headers=headers, uncopyable=_UncopyableObject())
    expect_user_agent = self.UserAgent('10.0.0', 'None',
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    request_mock.assert_called_once_with(
        url, headers={b'user-agent': expect_user_agent}, uncopyable=mock.ANY)
    request_mock.reset_mock()
    # Make sure our wrapping did not actually affect args we pass into request.
    # If it does, we could accidentally be modifying global state.
    self.assertEqual(headers, {})

    cmd_path = 'a.b.c.d'
    properties.VALUES.metrics.command_name.Set(cmd_path)
    http_client = http.Http()
    request_mock.return_value = self.default_response
    http_client.request(url)
    expect_user_agent = self.UserAgent('10.0.0', cmd_path,
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    request_mock.assert_called_once_with(
        url, headers={b'user-agent': expect_user_agent})
    request_mock.reset_mock()

    cmd_path = 'a.b.e.d'
    properties.VALUES.metrics.command_name.Set(cmd_path)
    http_client = http.Http()
    expect_headers = {b'user-agent': b'hello'}
    request_mock.return_value = self.default_response
    http_client.request(url, headers=expect_headers)
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
        url, headers={b'user-agent': expect_user_agent})
    request_mock.reset_mock()

    cmd_path = 'a.b.e.d'
    properties.VALUES.metrics.command_name.Set(cmd_path)
    http_client = http.Http()
    expect_headers = {b'user-agent': b'google-cloud-sdk'}
    request_mock.return_value = self.default_response
    http_client.request(url, headers=expect_headers)
    expect_user_agent = self.UserAgent('10.0.0', cmd_path,
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    request_mock.assert_called_once_with(
        url, headers={b'user-agent': expect_user_agent})

  @parameterized.parameters(('USER-AGENT', b'my.user.agent'),
                            ('user-agent', b'my.user.agent'),
                            ('User-Agent', b'my.user.agent'))
  def testUserAgent_AllSpellings(self, ua_header, ua_value):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    headers = {}
    http_client = http.Http()
    url = 'http://foo.com'
    request_mock.return_value = self.default_response
    headers[ua_header] = ua_value
    http_client.request(url, headers=headers, uncopyable=_UncopyableObject())
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
        url, headers={b'user-agent': expect_user_agent}, uncopyable=mock.ANY)
    request_mock.reset_mock()

  def testUserAgent_SpacesInVersion(self):
    # This is similar to what the versions look like for some internal builds
    config.CLOUD_SDK_VERSION = 'Mon Sep 12 08:35:01 2016'
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    http_client = http.Http()
    url = 'http://foo.com'
    request_mock.return_value = self.default_response
    http_client.request(url)
    expect_user_agent = self.UserAgent('Mon_Sep_12_08:35:01_2016', 'None',
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    request_mock.assert_called_once_with(
        url, headers={b'user-agent': expect_user_agent})
    request_mock.reset_mock()

  def testTraces(self):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    expect_user_agent = self.UserAgent('10.0.0', 'None',
                                       uuid_mock.return_value.hex,
                                       python_version, False)
    http_client = http.Http()
    url = 'http://foo.com'
    request_mock.return_value = self.default_response
    http_client.request(url)
    request_mock.assert_called_once_with(
        url, headers={b'user-agent': expect_user_agent})
    request_mock.reset_mock()

    trace_token = 'hello'
    properties.VALUES.core.trace_token.Set(trace_token)
    http_client = http.Http()
    request_mock.return_value = self.default_response
    http_client.request(url)
    expect_url = '{0}?trace=token%3A{1}'.format(url, trace_token)
    request_mock.assert_called_once_with(
        expect_url, headers={b'user-agent': expect_user_agent})
    request_mock.reset_mock()
    properties.VALUES.core.trace_token.Set(None)

    trace_email = 'hello'
    properties.VALUES.core.trace_email.Set(trace_email)
    http_client = http.Http()
    request_mock.return_value = self.default_response
    http_client.request(url)
    expect_url = '{0}?trace=email%3A{1}'.format(url, trace_email)
    request_mock.assert_called_once_with(
        expect_url, headers={b'user-agent': expect_user_agent})
    request_mock.reset_mock()
    properties.VALUES.core.trace_email.Set(None)

    properties.VALUES.core.trace_log.Set(True)
    http_client = http.Http()
    request_mock.return_value = self.default_response
    http_client.request(url)
    expect_url = '{0}?trace=log'.format(url)
    request_mock.assert_called_once_with(
        expect_url, headers={b'user-agent': expect_user_agent})
    properties.VALUES.core.trace_log.Set(None)

  def _FormatHeaderOutput(self, headers):
    return '\n'.join(
        ['{0}: {1}'.format(k, v) for k, v in sorted(six.iteritems(headers))])

  def testRequestResponseDump(self):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    response_headers = {b'header1': b'value1', b'header2': b'value2'}
    request_mock.return_value = (response_headers, 'response content')
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
    http_client = http.Http()
    url = 'http://foo.com'
    time_mock = self.StartPatch('time.time', autospec=True)
    # Time is called twice by RPC duration reporting and twice by logging
    time_mock.side_effect = [1.0, 1.1, 3.0, 3.1]
    http_client.request(url, method='GET', body='Request Body')
    request_mock.assert_called_once_with(
        url,
        method='GET',
        headers=user_agent_header,
        body='Request Body',
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
    self._FormatHeaderOutput({'status': None}),
    self._FormatHeaderOutput(response_headers))

    log_mock.assert_has_calls(
        [mock.call(line) for line in expected_output.split('\n')])
    log_mock.reset_mock()
    time_mock.reset_mock()
    # Time is called twice by RPC duration reporting and twice by logging
    time_mock.side_effect = [1.0, 1.1, 5.0, 5.1]

    # Test with positional argument list.
    request_headers = {b'req_header1': b'val1'}
    http_client.request(url, 'GET', 'Request Body', request_headers)
    request_headers.update(user_agent_header)

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
total round trip time (request+response): 4.000 secs
---- response end ----
----------------------""".format(
    self._FormatHeaderOutput(request_headers),
    self._FormatHeaderOutput({'status': None}),
    self._FormatHeaderOutput(response_headers))

    log_mock.assert_has_calls(
        [mock.call(line) for line in expected_output.split('\n')])
    log_mock.reset_mock()

  def testLogHttpOauthRedaction(self):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')

    def run(url, extra_headers):
      request_mock.return_value = (httplib2.Response({
          'header1': 'value1',
          'header2': 'value2'
      }), b'response content')
      properties.VALUES.core.log_http.Set(True)
      http_client = http.Http()
      http_client.request(
          url, method='GET', body='request content', headers=extra_headers)
      request_mock.assert_called_once_with(
          url,
          method='GET',
          headers=mock.ANY,
          body='request content',
      )
      request_mock.reset_mock()

    # Test authorization header is redacted.
    run(
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
    run('https://accounts.google.com/o/oauth2/token', {})
    self.AssertErrNotContains('request content')
    self.AssertErrNotContains('response content')
    self.ClearErr()

    # Test body is redacted from response. Body of request doesn't matter.
    run(
        'http://metadata.google.internal/computeMetadata/v1/instance/'
        'service-accounts/something@developer.gserviceaccount.com/token', {})
    self.AssertErrNotContains('response content')
    self.ClearErr()

  def testRequestReason(self):
    properties.VALUES.core.request_reason.Set('my request justification')
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    request_mock.return_value = ({
        'header1': 'value1',
        'header2': 'value2'
    }, b'response content')
    http_client = http.Http()

    http_client.request(
        'http://www.example.com/foo',
        method='GET',
        body='request content',
        headers={})

    expected_headers = {
        b'user-agent': mock.ANY,
        b'X-Goog-Request-Reason': b'my request justification'
    }
    request_mock.assert_called_once_with(
        'http://www.example.com/foo',
        method='GET',
        body='request content',
        headers=expected_headers)

  def testDefaultTimeout(self):
    timeout_mock = self.StartObjectPatch(transport, 'GetDefaultTimeout')
    timeout_mock.return_value = 0.001
    self.socket_connect_mock.side_effect = socket.timeout
    http_client = http.Http()
    with self.assertRaises(socket.timeout):
      http_client.request('http://localhost/')

  def testProxyHttpProxyInfo(self):
    properties.VALUES.proxy.proxy_type.Set('socks4')
    properties.VALUES.proxy.address.Set('123.123.123.123')
    properties.VALUES.proxy.port.Set('4321')
    pi = http_proxy.GetHttpProxyInfo()
    self.assertEqual((socks.PROXY_TYPE_SOCKS4, '123.123.123.123', 4321, True,
                      None, None, None), pi.astuple())
    self.assertTrue(pi.isgood())

  def testProxyHttpProxyInfo_NoRdns(self):
    properties.VALUES.proxy.proxy_type.Set('socks4')
    properties.VALUES.proxy.address.Set('123.123.123.123')
    properties.VALUES.proxy.port.Set('4321')
    properties.VALUES.proxy.rdns.Set(False)
    pi = http_proxy.GetHttpProxyInfo()
    self.assertEqual((socks.PROXY_TYPE_SOCKS4, '123.123.123.123', 4321, False,
                      None, None, None), pi.astuple())
    self.assertTrue(pi.isgood())

  def testProxyHttpProxyInfoNoType(self):
    properties.VALUES.proxy.proxy_type.Set(None)
    properties.VALUES.proxy.address.Set('123.123.123.123')
    properties.VALUES.proxy.port.Set('4321')
    with self.assertRaisesRegex(
        properties.InvalidValueError,
        'Please set all or none of the following properties: '
        'proxy/type, proxy/address and proxy/port'):
      unused_pi = http_proxy.GetHttpProxyInfo()

  def testProxyHttpProxyInfoNoProperties(self):
    pi = http_proxy.GetHttpProxyInfo()
    self.assertTrue(callable(pi))
    self.assertEqual(None, pi('http'))

  def testProxyHttpProxyInfoEnvVar(self):
    self.StartEnvPatch({
        'HTTP_PROXY': 'http://user:pass@awesome_proxy:8080',
        'HTTPS_PROXY': 'http://suser:spass@secure_proxy:8081',
        'NO_PROXY': 'someaddress.com,otheraddress.com'
    })
    pi = http_proxy.GetHttpProxyInfo()
    self.assertTrue(callable(pi))
    self.assertEqual((socks.PROXY_TYPE_HTTP, 'awesome_proxy', 8080, True,
                      b'user', b'pass', None),
                     pi('http').astuple())
    self.assertEqual((socks.PROXY_TYPE_HTTP, 'secure_proxy', 8081, True,
                      b'suser', b'spass', None),
                     pi('https').astuple())
    self.assertTrue(pi('http').isgood())
    self.assertTrue(pi('https').isgood())
    self.assertTrue(pi('http').bypass_host('someaddress.com'))
    self.assertTrue(pi('https').bypass_host('someaddress.com'))
    self.assertTrue(pi('http').bypass_host('otheraddress.com'))
    self.assertTrue(pi('https').bypass_host('otheraddress.com'))
    self.assertFalse(pi('http').bypass_host('google.com'))
    self.assertFalse(pi('https').bypass_host('google.com'))

  def testRPCDurationReporting(self):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    request_mock.return_value = self.default_response

    time_mock = self.StartPatch('time.time', autospec=True)
    time_mock.side_effect = [1.0, 4.0]

    duration_mock = self.StartObjectPatch(metrics, 'RPCDuration')

    http_client = http.Http()
    http_client.request('http://foo.com', method='GET', body='Request Body')
    duration_mock.assert_called_once_with(3.0)

  def testResponseEncoding(self):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    request_mock.return_value = ({},
                                 b'\xe1\x95\x95( \xe1\x90\x9b )\xe1\x95\x97')

    http_client = http.Http(response_encoding='utf-8')
    _, content = http_client.request(
        'http://foo.com', method='GET', body='Request Body')
    self.assertEqual('ᕕ( ᐛ )ᕗ', content)


class RequestTest(parameterized.TestCase):

  @parameterized.parameters(
      (
          ['url', 'method', 'body', {'hdr': '1'}],
          {},
          ['e_url', 'e_method', 'e_body', {'e_hdr': '2'}],
          {},
      ),
      (
          ['url', 'method', 'body'],
          {'headers': {'hdr': '1'}},
          ['e_url', 'e_method', 'e_body'],
          {'headers': {'e_hdr': '2'}},
      ),
      (
          ['url', 'method'],
          {'headers': {'hdr': '1'}, 'body': 'body'},
          ['e_url', 'e_method'],
          {'headers': {'e_hdr': '2'}, 'body': 'e_body'},
      ),
      (
          ['url'],
          {'headers': {'hdr': '1'}, 'body': 'body', 'method': 'method'},
          ['e_url'],
          {'headers': {'e_hdr': '2'}, 'body': 'e_body', 'method': 'e_method'},
      ),
  )
  def testRequest(self, args, kwargs, expected_args, expected_kwargs):
    request = http.Request.FromRequestArgs(*args, **kwargs)
    request.uri = 'e_url'
    request.method = 'e_method'
    request.headers = {'e_hdr': '2'}
    request.body = 'e_body'

    actual_args, actual_kwargs = request.ToRequestArgs()

    self.assertEqual(actual_args, expected_args)
    self.assertEqual(actual_kwargs, expected_kwargs)


class ResponseTest(test_case.TestCase):

  def testResponse(self):
    http_resp = httplib2.Response({'status': httplib.OK, 'hdr': '1'}), 'body'
    response = http.Response.FromResponse(http_resp)
    self.assertEqual(response.status_code, httplib.OK)
    self.assertEqual(response.headers, {'hdr': '1'})
    self.assertEqual(response.body, 'body')


if __name__ == '__main__':
  test_case.main()
