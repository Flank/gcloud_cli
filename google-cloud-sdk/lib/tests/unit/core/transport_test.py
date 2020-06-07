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

from googlecloudsdk.core import transport

from tests.lib import sdk_test_base
from tests.lib import test_case

import mock

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

  def AttachCredentials(self, http_client, orig_request):
    pass


class HttpClient(object):

  def request(self, *args, **kwargs):
    pass


class RequestWrapperTest(sdk_test_base.SdkBase):

  def testAttachCredentials(self):
    http_client = HttpClient()
    orig_request = self.StartObjectPatch(
        http_client, 'request', return_value={
            'status': httplib.OK,
        })
    request_wrapper = RequestWrapper()
    self.StartObjectPatch(request_wrapper, 'AttachCredentials')

    request_wrapper.WrapRequest(http_client, [])
    http_client.request('uri', 'method')

    request_wrapper.AttachCredentials.assert_called_once_with(
        http_client, orig_request)

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


class HandlerTest(sdk_test_base.SdkBase):

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


if __name__ == '__main__':
  test_case.main()
