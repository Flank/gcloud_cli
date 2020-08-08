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

from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.credentials import transport as creds_transport
from googlecloudsdk.core.util import files

from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock

from oauth2client import client

from six.moves import http_client as httplib
from google.auth import exceptions as google_auth_exceptions


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


class RequestWrapper(creds_transport.CredentialWrappingMixin,
                     transport.RequestWrapper):

  request_class = Request
  response_class = Response

  def DecodeResponse(self, response, response_encoding):
    return response

  def AttachCredentials(self, http_client, orig_request):
    pass

  def AuthorizeClient(self, http_client, credentials):
    return http_client


class HttpClient(object):

  def request(self, *args, **kwargs):
    pass


class RequestWrapperTest(sdk_test_base.SdkBase, parameterized.TestCase):

  @parameterized.parameters(
      (True, True),
      (True, False),
      (False, True),
      (False, False),
  )
  def testLoadCredentials(self, allow_account_impersonation, use_google_auth):
    http_client = HttpClient()
    self.StartObjectPatch(
        http_client, 'request', return_value={
            'status': httplib.OK,
        })
    fake_creds = mock.Mock()
    self.StartObjectPatch(store, 'LoadIfEnabled', return_value=fake_creds)

    RequestWrapper().WrapCredentials(
        http_client,
        allow_account_impersonation=allow_account_impersonation,
        use_google_auth=use_google_auth)
    http_client.request('uri', 'method')

    store.LoadIfEnabled.assert_called_once_with(allow_account_impersonation,
                                                use_google_auth)

  def testAuthorizeClient(self):
    http_client = HttpClient()
    self.StartObjectPatch(
        http_client, 'request', return_value={
            'status': httplib.OK,
        })
    fake_creds = mock.Mock()
    self.StartObjectPatch(store, 'LoadIfEnabled', return_value=fake_creds)
    request_wrapper = RequestWrapper()
    self.StartObjectPatch(request_wrapper, 'AuthorizeClient')

    request_wrapper.WrapCredentials(http_client)
    http_client.request('uri', 'method')

    request_wrapper.AuthorizeClient.assert_called_once_with(
        http_client, fake_creds)

  def testIamAuthoritySelector(self):
    authority_selector = 'superuser@google.com'
    properties.VALUES.auth.authority_selector.Set(authority_selector)

    http_client = HttpClient()
    orig_request = self.StartObjectPatch(
        http_client, 'request', return_value={
            'status': httplib.OK,
        })
    fake_creds = mock.Mock()
    self.StartObjectPatch(store, 'LoadIfEnabled', return_value=fake_creds)

    RequestWrapper().WrapCredentials(http_client)
    http_client.request('uri', 'method')

    orig_request.assert_called_once_with(
        'uri',
        'method',
        headers={b'x-goog-iam-authority-selector': b'superuser@google.com'})

  def testIamAuthorizationToken(self):
    token_file = 'token_file.x'
    properties.VALUES.auth.authorization_token_file.Set(token_file)

    http_client = HttpClient()
    orig_request = self.StartObjectPatch(
        http_client, 'request', return_value={
            'status': httplib.OK,
        })
    fake_creds = mock.Mock()
    self.StartObjectPatch(store, 'LoadIfEnabled', return_value=fake_creds)
    self.StartObjectPatch(files, 'ReadFileContents', return_value='token')

    RequestWrapper().WrapCredentials(http_client)
    http_client.request('uri', 'method')

    files.ReadFileContents.assert_called_once_with(token_file)
    orig_request.assert_called_once_with(
        'uri', 'method', headers={b'x-goog-iam-authorization-token': b'token'})

  @parameterized.parameters(
      (True, True, True, True),
      (True, True, False, False),
      (True, False, True, True),
      (True, False, False, False),
      (False, True, True, True),
      (False, True, False, False),
      (False, False, True, False),
      (False, False, False, False),
  )
  def testResourceQuota(self, enable_resource_quota, force_resource_quota,
                        quota_project_returned, header_expected):
    http_client = HttpClient()
    orig_request = self.StartObjectPatch(
        http_client, 'request', return_value={
            'status': httplib.OK,
        })
    fake_creds = mock.Mock()
    self.StartObjectPatch(store, 'LoadIfEnabled', return_value=fake_creds)
    self.StartObjectPatch(creds, 'GetQuotaProject')
    if quota_project_returned:
      creds.GetQuotaProject.return_value = 'quota project'
    else:
      creds.GetQuotaProject.return_value = None

    RequestWrapper().WrapCredentials(
        http_client,
        enable_resource_quota=enable_resource_quota,
        force_resource_quota=force_resource_quota)
    http_client.request('uri', 'method')

    if header_expected:
      orig_request.assert_called_once_with(
          'uri', 'method', headers={b'X-Goog-User-Project': b'quota project'})
    else:
      orig_request.assert_called_once_with('uri', 'method')

  def testExceptionHandling(self):
    http_client = HttpClient()
    orig_request = self.StartObjectPatch(
        http_client, 'request', return_value={
            'status': httplib.OK,
        })
    fake_creds = mock.Mock()
    self.StartObjectPatch(store, 'LoadIfEnabled', return_value=fake_creds)
    RequestWrapper().WrapCredentials(http_client)
    http_client.request('uri', 'method')

    orig_request.side_effect = TypeError
    with self.assertRaises(TypeError):
      http_client.request('uri', 'method')

    orig_request.side_effect = client.AccessTokenRefreshError
    with self.assertRaises(store.TokenRefreshError):
      http_client.request('uri', 'method')

    orig_request.side_effect = google_auth_exceptions.RefreshError
    with self.assertRaises(store.TokenRefreshError):
      http_client.request('uri', 'method')

    orig_request.side_effect = google_auth_exceptions.RefreshError(
        'access_denied: Account restricted')
    with self.assertRaises(store.TokenRefreshDeniedByCAAError):
      http_client.request('uri', 'method')


if __name__ == '__main__':
  test_case.main()
