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
"""Unit tests for the transport module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport

from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock

import six
from six.moves import http_client as httplib


class Request(transport.Request):
  """"Implements a simple http object for testing.

  http.request has the following signature:
    request(self, uri, method, body=None, headers=None)
  """

  @classmethod
  def FromRequestArgs(cls, *args, **kwargs):
    return cls(args[0], args[1], kwargs.get('headers', {}), kwargs.get('body'))

  def ToRequestArgs(self):
    args = [self.uri, self.method]
    kwargs = {}
    if self.headers:
      kwargs['headers'] = self.headers
    if self.body:
      kwargs['body'] = self.body
    return args, kwargs


class Response(transport.Response):
  """Encapsulates responses from making a general HTTP request."""

  @classmethod
  def FromResponse(cls, response):
    return cls(
        response.get('status'), response.get('headers'),
        response.get('content'))


class RequestWrapper(transport.RequestWrapper):

  request_class = Request
  response_class = Response

  def DecodeResponse(self, response, response_encoding):
    return response


class HttpClient(object):

  def request(self, *args, **kwargs):
    pass


class RequestWrapperTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def testExceptionHandling(self):
    http_client = HttpClient()
    orig_request = self.StartObjectPatch(http_client, 'request')

    exception_handler = mock.Mock()
    RequestWrapper().WrapRequest(
        http_client, [], exc_handler=exception_handler, exc_type=ValueError)

    orig_request.return_value = {
        'status': httplib.OK,
    }
    http_client.request('uri', 'method')
    exception_handler.assert_not_called()

    orig_request.side_effect = TypeError
    with self.assertRaises(TypeError):
      http_client.request('uri', 'method')
    exception_handler.assert_not_called()

    orig_request.side_effect = ValueError
    http_client.request('uri', 'method')
    exception_handler.assert_called_once()
    self.assertIsInstance(exception_handler.call_args[0][0], ValueError)

  def testResponseEncoding(self):
    http_client = HttpClient()
    self.StartObjectPatch(http_client, 'request', return_value='response')
    request_wrapper = RequestWrapper()
    self.StartObjectPatch(request_wrapper, 'DecodeResponse')

    request_wrapper.WrapRequest(http_client, [], response_encoding='utf-8')
    http_client.request('uri', 'method')

    request_wrapper.DecodeResponse.assert_called_once_with('response', 'utf-8')

  def testHeaderEncoding(self):
    http_client = HttpClient()
    orig_request = self.StartObjectPatch(
        http_client, 'request', return_value={})

    RequestWrapper().WrapRequest(http_client, [], response_encoding='utf-8')
    http_client.request('uri', 'method', headers={'a': 'b'})

    orig_request.assert_called_once_with('uri', 'method', headers={b'a': b'b'})

  @parameterized.parameters(
      {'with_trace': True, 'with_reason': False, 'with_logging': False},
      {'with_trace': False, 'with_reason': True, 'with_logging': False},
      {'with_trace': False, 'with_reason': False, 'with_logging': True})
  def testWrapWithDefaults(self, with_trace, with_reason, with_logging):
    self.StartObjectPatch(
        transport,
        'MakeUserAgentString',
        return_value='user-agent-body',
        autospec=True)

    log_mock = self.StartObjectPatch(log.status, 'Print', autospec=True)

    if with_trace:
      self.StartObjectPatch(transport, 'GetTraceValue',
                            return_value='test-trace', autospec=True)

    if with_reason:
      properties.VALUES.core.request_reason.Set('test-reason')

    time_mock = self.StartPatch('time.time', autospec=True)
    if with_logging:
      properties.VALUES.core.log_http.Set(True)
      # Time is called twice by RPC duration reporting and twice by logging.
      time_mock.side_effect = [1.0, 1.1, 3.0, 5.1]
    else:
      # Time is called twice by RPC duration reporting.
      time_mock.side_effect = [1.0, 3.0]

    metrics_mock = self.StartObjectPatch(metrics, 'RPCDuration', autospec=True)

    http_client = HttpClient()
    orig_request = self.StartObjectPatch(
        http_client, 'request', return_value={
            'status': httplib.OK,
            'headers': {},
        })

    RequestWrapper().WrapWithDefaults(http_client, response_encoding='utf-8')
    http_client.request('uri', 'method', headers={'a': 'b'})

    expected_uri = 'uri'
    if with_trace:
      expected_uri += '?trace=test-trace'

    expected_headers = {
        b'a': b'b',
        b'user-agent': b'google-cloud-sdk user-agent-body'
    }
    if with_reason:
      expected_headers[b'X-Goog-Request-Reason'] = b'test-reason'

    orig_request.assert_called_once_with(expected_uri, 'method',
                                         headers=expected_headers)

    # Ensure duration reporting
    metrics_mock.assert_called_once_with(2.0)

    if with_logging:
      log_mock.assert_has_calls([
          mock.call('==== request start ===='),
          mock.call('---- response start ----'),
          mock.call('total round trip time (request+response): 4.000 secs'),
      ], any_order=True)
    else:
      log_mock.assert_not_called()


class HandlerTest(sdk_test_base.SdkBase, parameterized.TestCase,
                  test_case.WithOutputCapture):

  def SetUp(self):
    self.http_client = HttpClient()
    self.orig_request = self.StartObjectPatch(
        self.http_client, 'request', return_value={})

  def testHandlers(self):
    mock_request = Request('uri', 'method', {'a': 'b'}, None)
    self.StartObjectPatch(Request, 'FromRequestArgs', return_value=mock_request)
    mock_response = Response(httplib.OK, {}, None)
    self.StartObjectPatch(Response, 'FromResponse', return_value=mock_response)

    request_handler = mock.Mock(return_value='data')
    response_handler = mock.Mock()
    handlers = [transport.Handler(request_handler, response_handler)]
    RequestWrapper().WrapRequest(self.http_client, handlers)

    self.http_client.request('uri', 'method', headers={'a': 'A'})
    request_handler.assert_called_once_with(mock_request)
    response_handler.assert_called_once_with(mock_response, 'data')

  @parameterized.parameters(
      ({
          b'a': b'A'
      }, 'a', {
          b'a': b'prepended A'
      }),
      ({
          b'a': b'prepended A'
      }, 'a', {
          b'a': b'prepended A'
      }),
      ({
          b'a': b'A'
      }, 'A', {
          b'A': b'prepended A'
      }),
      ({
          b'A': b'A'
      }, 'a', {
          b'a': b'prepended A'
      }),
  )
  def testMaybePrependToHeader(self, current_headers, header, expected_headers):
    handlers = [
        transport.Handler(transport.MaybePrependToHeader(header, 'prepended'))
    ]
    RequestWrapper().WrapRequest(self.http_client, handlers)

    self.http_client.request('uri', 'method', headers=current_headers)
    self.orig_request.assert_called_once_with(
        'uri', 'method', headers=expected_headers)

  @parameterized.parameters(
      ({b'a': b'A'}, 'a', {b'a': b'A appended'}),
      ({b'a': b'A'}, 'A', {b'A': b'A appended'}),
      ({b'A': b'A'}, 'a', {b'a': b'A appended'}),
  )
  def testAppendToHeader(self, current_headers, header, expected_headers):
    handlers = [transport.Handler(transport.AppendToHeader(header, 'appended'))]
    RequestWrapper().WrapRequest(self.http_client, handlers)

    self.http_client.request('uri', 'method', headers=current_headers)
    self.orig_request.assert_called_once_with(
        'uri', 'method', headers=expected_headers)

  @parameterized.parameters(
      ({b'a': b'A'}, 'b', {b'a': b'A', b'b': b'B'}),
      ({b'b': b'orig_B'}, 'b', {b'b': b'B'}),
      ({b'b': b'orig_B'}, 'B', {b'B': b'B'}),
      ({b'B': b'orig_B'}, 'b', {b'b': b'B'}),
  )
  def testSetHeader(self, current_headers, header, expected_headers):
    handlers = [transport.Handler(transport.SetHeader(header, 'B'))]
    RequestWrapper().WrapRequest(self.http_client, handlers)

    self.http_client.request('uri', 'method', headers=current_headers)
    self.orig_request.assert_called_once_with(
        'uri', 'method', headers=expected_headers)

  def testAddQueryParam(self):
    handlers = [transport.Handler(transport.AddQueryParam('a', 'A'))]
    RequestWrapper().WrapRequest(self.http_client, handlers)

    self.http_client.request('uri.com', 'method')
    self.orig_request.assert_called_once_with('uri.com?a=A', 'method')

  def _FormatHeaderOutput(self, headers):
    return '\n'.join(
        ['{0}: {1}'.format(k, v) for k, v in sorted(six.iteritems(headers))])

  def testLogRequestResponse(self):
    url = 'http://foo.com'
    request_headers = {b'header1': b'value1', b'header2': b'value2'}
    response_headers = {b'header3': b'value3', b'header4': b'value4'}

    self.orig_request.return_value = {
        'status': httplib.OK,
        'headers': response_headers,
        'content': 'response content',
    }

    time_mock = self.StartPatch('time.time', autospec=True)
    # Time is called twice by logging.
    time_mock.side_effect = [1.0, 3.0]

    log_mock = self.StartObjectPatch(log.status, 'Print')

    handlers = [
        transport.Handler(transport.LogRequest(True), transport.LogResponse())
    ]
    RequestWrapper().WrapRequest(self.http_client, handlers)

    self.http_client.request(
        url, 'GET', headers=request_headers, body='Request Body')
    self.orig_request.assert_called_once_with(
        url, 'GET', headers=request_headers, body='Request Body')
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
status: 200
-- headers start --
{1}
-- headers end --
-- body start --
response content
-- body end --
total round trip time (request+response): 2.000 secs
---- response end ----
----------------------""".format(
    self._FormatHeaderOutput(request_headers),
    self._FormatHeaderOutput(response_headers))

    log_mock.assert_has_calls(
        [mock.call(line) for line in expected_output.split('\n')])

  def testLogHttpOauthRedaction(self):
    handlers = [
        transport.Handler(transport.LogRequest(True), transport.LogResponse())
    ]
    RequestWrapper().WrapRequest(self.http_client, handlers)

    def run(url, extra_headers):
      self.orig_request.return_value = {
          'status': httplib.OK,
          'headers': {
              'header1': 'value1',
              'header2': 'value2'
          },
          'content': 'response content',
      }
      self.http_client.request(
          url, 'GET', body='request content', headers=extra_headers)
      self.orig_request.assert_called_once()
      self.assertEqual(self.orig_request.call_args[0], (url, 'GET'))
      self.assertEqual(self.orig_request.call_args[1].get('body'),
                       'request content')
      self.orig_request.reset_mock()

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

  def testReportDuration(self):
    url = 'http://foo.com'
    request_headers = {b'header1': b'value1', b'header2': b'value2'}
    response_headers = {b'header3': b'value3', b'header4': b'value4'}

    self.orig_request.return_value = {
        'status': httplib.OK,
        'headers': response_headers,
        'content': 'response content',
    }

    time_mock = self.StartPatch('time.time', autospec=True)
    # Time is called twice by RPC duration reporting.
    time_mock.side_effect = [1.0, 3.0]

    metrics_mock = self.StartObjectPatch(metrics, 'RPCDuration')

    handlers = [
        transport.Handler(transport.RecordStartTime(),
                          transport.ReportDuration())
    ]
    RequestWrapper().WrapRequest(self.http_client, handlers)

    self.http_client.request(
        url, 'GET', headers=request_headers, body='Request Body')

    metrics_mock.assert_called_once_with(2.0)


if __name__ == '__main__':
  test_case.main()
