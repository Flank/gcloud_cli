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

import os
import socket
import uuid

from googlecloudsdk.core import config
from googlecloudsdk.core import http
from googlecloudsdk.core import http_proxy
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import session_capturer
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case
import httplib2
import mock
import socks


class _UncopyableObject(object):
  """Dummy object used for testing."""

  def __copy__(self):
    raise ValueError()

  def __deepcopy__(self, memo):
    del memo  # Unused in __deepcopy__
    return self.__copy__()


class HttpTest(sdk_test_base.WithFakeAuth, test_case.WithOutputCapture):

  def SetUp(self):
    self.old_version = config.CLOUD_SDK_VERSION
    config.CLOUD_SDK_VERSION = '10.0.0'
    self.StartObjectPatch(console_io, 'IsRunFromShellScript',
                          return_value=False)

  def TearDown(self):
    config.CLOUD_SDK_VERSION = self.old_version

  def UserAgent(self, version, cmd_path, invocation_id, python_version,
                interactive, fromscript=False):
    template = ('gcloud/{0} command/{1} invocation-id/{2} environment/{3} '
                'environment-version/{4} interactive/{5} from-script/{8} '
                'python/{6} {7}')
    # Mocking the platform fragment doesn't seem to work all the time.
    # Use the real platform we are on.
    platform = platforms.Platform.Current().UserAgentFragment()
    environment = properties.GetMetricsEnvironment()
    environment_version = properties.VALUES.metrics.environment_version.Get()
    user_agent = template.format(version,
                                 cmd_path,
                                 invocation_id,
                                 environment,
                                 environment_version,
                                 interactive,
                                 python_version,
                                 platform,
                                 fromscript)
    return user_agent

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
    http_client.request(url, headers=headers, uncopyable=_UncopyableObject())
    expect_user_agent = self.UserAgent('10.0.0',
                                       'None',
                                       uuid_mock.return_value.hex,
                                       python_version,
                                       False)
    request_mock.assert_called_once_with(
        url, headers={'user-agent': expect_user_agent}, uncopyable=mock.ANY)
    request_mock.reset_mock()
    # Make sure our wrapping did not actually affect args we pass into request.
    # If it does, we could accidentally be modifying global state.
    self.assertEqual(headers, {})

    cmd_path = 'a.b.c.d'
    properties.VALUES.metrics.command_name.Set(cmd_path)
    http_client = http.Http()
    http_client.request(url)
    expect_user_agent = self.UserAgent('10.0.0',
                                       cmd_path,
                                       uuid_mock.return_value.hex,
                                       python_version,
                                       False)
    request_mock.assert_called_once_with(
        url, headers={'user-agent': expect_user_agent})
    request_mock.reset_mock()

    cmd_path = 'a.b.e.d'
    properties.VALUES.metrics.command_name.Set(cmd_path)
    http_client = http.Http()
    http_client.request(url, headers={'user-agent': 'hello'})
    expect_user_agent = 'hello ' + self.UserAgent('10.0.0',
                                                  cmd_path,
                                                  uuid_mock.return_value.hex,
                                                  python_version,
                                                  False)
    request_mock.assert_called_once_with(
        url, headers={'user-agent': expect_user_agent})

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
    http_client.request(url)
    expect_user_agent = self.UserAgent('Mon_Sep_12_08:35:01_2016',
                                       'None',
                                       uuid_mock.return_value.hex,
                                       python_version,
                                       False)
    request_mock.assert_called_once_with(
        url, headers={'user-agent': expect_user_agent})
    request_mock.reset_mock()

  def testTraces(self):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    expect_user_agent = self.UserAgent('10.0.0',
                                       'None',
                                       uuid_mock.return_value.hex,
                                       python_version,
                                       False)
    expect_headers = {'user-agent': expect_user_agent}
    http_client = http.Http()
    url = 'http://foo.com'
    http_client.request(url)
    request_mock.assert_called_once_with(url, headers=expect_headers)
    request_mock.reset_mock()

    trace_token = 'hello'
    properties.VALUES.core.trace_token.Set(trace_token)
    http_client = http.Http()
    http_client.request(url)
    expect_url = '{0}?trace=token%3A{1}'.format(url, trace_token)
    request_mock.assert_called_once_with(expect_url, headers=expect_headers)
    request_mock.reset_mock()
    properties.VALUES.core.trace_token.Set(None)

    trace_email = 'hello'
    properties.VALUES.core.trace_email.Set(trace_email)
    http_client = http.Http()
    http_client.request(url)
    expect_url = '{0}?trace=email%3A{1}'.format(url, trace_email)
    request_mock.assert_called_once_with(expect_url, headers=expect_headers)
    request_mock.reset_mock()
    properties.VALUES.core.trace_email.Set(None)

    properties.VALUES.core.trace_log.Set(True)
    http_client = http.Http()
    http_client.request(url)
    expect_url = '{0}?trace=log'.format(url)
    request_mock.assert_called_once_with(expect_url, headers=expect_headers)
    properties.VALUES.core.trace_log.Set(None)

  def testRequestResponseDump(self):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    request_mock.return_value = (
        {'header1': 'value1', 'header2': 'value2'}, 'response content')
    uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')
    is_interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    is_interactive_mock.return_value = False
    python_version = '2.7.6'
    self.StartPatch('platform.python_version').return_value = python_version

    expect_user_agent = self.UserAgent('10.0.0',
                                       'None',
                                       uuid_mock.return_value.hex,
                                       python_version,
                                       False)
    expect_headers = {'user-agent': expect_user_agent}
    log_mock = self.StartObjectPatch(log.status, 'Print')
    properties.VALUES.core.log_http.Set(True)
    capture_session_file = os.path.join(self.CreateTempDir(), 'session.yaml')
    capturer = session_capturer.SessionCapturer(capture_streams=False)
    session_capturer.SessionCapturer.capturer = capturer
    http_client = http.Http()
    url = 'http://foo.com'
    time_mock = self.StartPatch('time.time', autospec=True)
    # Time is called twice by RPC duration reporting and twice by logging
    time_mock.side_effect = [1.0, 1.1, 3.0, 3.1]
    http_client.request(url, method='GET', body='Request Body')
    request_mock.assert_called_once_with(
        url, method='GET', headers=expect_headers, body='Request Body',)
    request_mock.reset_mock()

    expected_output = """\
=======================
==== request start ====
uri: http://foo.com
method: GET
== headers start ==
user-agent: {0}
== headers end ==
== body start ==
Request Body
== body end ==
==== request end ====
---- response start ----
-- headers start --
header1: value1
header2: value2
-- headers end --
-- body start --
response content
-- body end --
total round trip time (request+response): 2.000 secs
---- response end ----
----------------------""".format(expect_user_agent)

    log_mock.assert_has_calls(
        [mock.call(line) for line in expected_output.split('\n')])
    log_mock.reset_mock()
    time_mock.reset_mock()
    # Time is called twice by RPC duration reporting and twice by logging
    time_mock.side_effect = [1.0, 1.1, 5.0, 5.1]

    # Test with positional argument list.
    http_client.request(url, 'GET', 'Request Body', {'req_header1': 'val1'})

    expected_output = """\
=======================
==== request start ====
uri: http://foo.com
method: GET
== headers start ==
req_header1: val1
user-agent: {0}
== headers end ==
== body start ==
Request Body
== body end ==
==== request end ====
---- response start ----
-- headers start --
header1: value1
header2: value2
-- headers end --
-- body start --
response content
-- body end --
total round trip time (request+response): 4.000 secs
---- response end ----
----------------------""".format(expect_user_agent)

    with open(capture_session_file, 'w') as fp:
      session_capturer.SessionCapturer.capturer.Print(fp)
    self.AssertFileExists(capture_session_file)
    self.AssertFileContains('uri: http://foo.com', capture_session_file)
    self.AssertFileContains('header1: value1', capture_session_file)
    self.AssertFileContains('header2: value2', capture_session_file)
    self.AssertFileContains('req_header1: val1', capture_session_file)
    self.AssertFileContains('Request Body', capture_session_file)
    self.AssertFileContains('response content', capture_session_file)

    session_capturer.SessionCapturer.capturer = None

    log_mock.assert_has_calls(
        [mock.call(line) for line in expected_output.split('\n')])
    log_mock.reset_mock()

  def testLogHttpOauthRedaction(self):
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    def run(url, extra_headers):
      request_mock.return_value = (
          {'header1': 'value1', 'header2': 'value2'}, 'response content')
      properties.VALUES.core.log_http.Set(True)
      http_client = http.Http()
      http_client.request(url, method='GET', body='request content',
                          headers=extra_headers)
      request_mock.assert_called_once_with(
          url, method='GET', headers=mock.ANY, body='request content',)
      request_mock.reset_mock()

    # Test authorization header is redacted.
    run('https://fake.googleapis.com/foo', {'Authorization': 'Bearer mytoken'})
    self.AssertErrNotContains('mytoken')
    self.AssertErrContains('request content')
    self.AssertErrContains('response content')
    self.ClearErr()

    # Test body is redacted from both request and response.
    run('https://accounts.google.com/o/oauth2/token', {})
    self.AssertErrNotContains('request content')
    self.AssertErrNotContains('response content')
    self.ClearErr()

    # Test body is redacted from response. Body of request doesn't matter.
    run('http://metadata.google.internal/computeMetadata/v1/instance/'
        'service-accounts/something@developer.gserviceaccount.com/token',
        {})
    self.AssertErrNotContains('response content')
    self.ClearErr()

  def testDefaultTimeout(self):
    timeout_mock = self.StartObjectPatch(http, 'GetDefaultTimeout')
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
    self.assertEquals(
        (socks.PROXY_TYPE_SOCKS4, '123.123.123.123', 4321, True, None, None,
         None),
        pi.astuple())
    self.assertTrue(pi.isgood())

  def testProxyHttpProxyInfo_NoRdns(self):
    properties.VALUES.proxy.proxy_type.Set('socks4')
    properties.VALUES.proxy.address.Set('123.123.123.123')
    properties.VALUES.proxy.port.Set('4321')
    properties.VALUES.proxy.rdns.Set(False)
    pi = http_proxy.GetHttpProxyInfo()
    self.assertEqual(
        (socks.PROXY_TYPE_SOCKS4, '123.123.123.123', 4321, False, None, None,
         None),
        pi.astuple())
    self.assertTrue(pi.isgood())

  def testProxyHttpProxyInfoNoType(self):
    properties.VALUES.proxy.proxy_type.Set(None)
    properties.VALUES.proxy.address.Set('123.123.123.123')
    properties.VALUES.proxy.port.Set('4321')
    with self.assertRaisesRegexp(
        properties.InvalidValueError,
        'Please set all or none of the following properties: '
        'proxy/type, proxy/address and proxy/port'):
      unused_pi = http_proxy.GetHttpProxyInfo()

  def testProxyHttpProxyInfoNoProperties(self):
    pi = http_proxy.GetHttpProxyInfo()
    self.assertTrue(callable(pi))
    self.assertEquals(None, pi('http'))

  def testProxyHttpProxyInfoEnvVar(self):
    self.StartEnvPatch(
        {'HTTP_PROXY': 'http://user:pass@awesome_proxy:8080',
         'HTTPS_PROXY': 'http://suser:spass@secure_proxy:8081',
         'NO_PROXY': 'someaddress.com,otheraddress.com'})
    pi = http_proxy.GetHttpProxyInfo()
    self.assertTrue(callable(pi))
    self.assertEquals(
        (socks.PROXY_TYPE_HTTP, 'awesome_proxy', 8080, True, 'user', 'pass',
         None),
        pi('http').astuple())
    self.assertEquals(
        (socks.PROXY_TYPE_HTTP, 'secure_proxy', 8081, True, 'suser', 'spass',
         None),
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
    self.StartObjectPatch(httplib2.Http, 'request')

    time_mock = self.StartPatch('time.time', autospec=True)
    time_mock.side_effect = [1.0, 4.0]

    duration_mock = self.StartObjectPatch(metrics, 'RPCDuration')

    http_client = http.Http()
    http_client.request('http://foo.com', method='GET', body='Request Body')
    duration_mock.assert_called_once_with(3.0)


if __name__ == '__main__':
  test_case.main()
