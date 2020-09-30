# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Some helper classes for testing gcloud commands.

Extending any of these classes will give you a gcloud entry point with the core
modules installed (auth, components, config).  If you want to test just your
own module and you do not need these, use the gcloud_test_base module instead.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import cgi
import datetime
import json
import os
import sys
import tempfile

from googlecloudsdk.api_lib.auth import service_account as auth_service_account
from googlecloudsdk.api_lib.iamcredentials import util as iamcred_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import http as cred_http
from googlecloudsdk.core.credentials import requests as c_requests
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import retry
from tests.lib import cli_test_base
from tests.lib import test_case

import httplib2
import mock
from oauth2client.contrib import gce as oauth2client_gce
import requests
import six


def main():
  return test_case.main()


class WithCoreModules(cli_test_base.CliTestBase):
  """A base class for gcloud tests that need the core module directories."""
  pass


IGNORE = object()


class WithMockHttp(cli_test_base.CliTestBase):
  """A base class that mocks out all HTTP communication.

  If you extend this class, any URL that is hit must have a registered handler
  which determines what canned response is sent back to your application.

  It is an error if a URL is requested by your application that has no
  registered handler.  It is also an error if you register a handler for an
  expected URL, but that URL is never requested by your application.  To turn
  off this latter behavior, you can put:

  self.strict = False

  in your SetUp method.
  """

  def SetUp(self):
    self.http_mock = self.StartObjectPatch(cred_http, 'Http', autospec=True)
    self.http_mock.return_value.request.side_effect = self._httplib2Request

    self.requests_mock = self.StartObjectPatch(c_requests, 'GetSession',
                                               autospec=True)
    self.requests_mock.return_value.request.side_effect = self._requestsRequest

    self.strict = True
    self._responses = {}
    self._requests = []
    self._next_exception = None

  def TearDown(self):
    if sys.exc_info()[0]:
      # The tests ended with an exception. Don't hide the original error with
      # this failure as the requests almost certainly did not get made as we
      # expected if there was another failure.
      return

    if self.strict:
      msg_lines = ['The following URLs were expected to be called:']
      responses_iter = six.iteritems(self._responses)
      for ((url, request_headers_tuple), responses) in responses_iter:
        if responses:
          headers_dict = {}
          for i in request_headers_tuple:
            headers_dict[i[0]] = i[1]
          msg_lines.append('\turl: {url} headers: {headers_dict}'.format(
              url=url, headers_dict=headers_dict))
      if len(msg_lines) > 1:
        self.fail('\n'.join(msg_lines))

  def _httplib2Request(self, uri, method='GET', body=None, headers=None,
                       **kwargs):
    status, response_headers, response_body = self._request(uri, method, body,
                                                            headers)
    headers = {'status': status}
    headers.update(response_headers or {})
    return (httplib2.Response(headers), response_body)

  def _requestsRequest(self, method, uri, data=None, headers=None, **kwargs):
    status, response_headers, response_body = self._request(uri, method, data,
                                                            headers)
    response = requests.Response()
    response.status_code = status
    response.headers = response_headers
    response._content = response_body  # pylint: disable=protected-access
    return response

  def _request(self, uri, method, body, headers):
    if self._next_exception:
      e = self._next_exception
      self._next_exception = None
      # pylint: disable=raising-bad-type, This will be an actual exception.
      raise e
    if '?' in uri:
      parts = uri.split('?', 1)
      base_uri = parts[0]
      params = cgi.parse_qs(parts[1])
    else:
      base_uri = uri
      params = {}

    # Match request headers, removing common header keys for brevity
    request_headers = (headers or {}).copy()
    request_headers.pop('content-type', None)
    request_headers.pop('content-length', None)
    request_headers_tuple = tuple(request_headers.items())

    self._requests.append((base_uri, params, method, request_headers_tuple,
                           body))

    responses = self._responses.get((base_uri, request_headers_tuple))
    if responses is None:
      self.fail('No responses were registered for URL {base_uri} and headers '
                '{headers}'.format(base_uri=base_uri, headers=headers))
    if not responses:
      self.fail('Responses already consumed for URL {base_uri} and headers '
                '{headers}'.format(base_uri=base_uri, headers=headers))
    # Pop responses off in the order they were registered.
    response = responses.pop(0)

    (expected_params, expected_body, status, response_headers,
     response_body) = response

    if expected_params != IGNORE:
      self.assertEqual(
          expected_params, params,
          msg='Expected parameters do not match for URL: ' + base_uri)

    if expected_body != IGNORE:
      self.assertEqual(
          expected_body, body,
          msg='Expected body does not match for URL: ' + base_uri)

    return status, response_headers, response_body

  def SetNextException(self, e):
    self._next_exception = e

  def AddHTTPResponse(self, url, request_headers=None,
                      expected_params=None, expected_body=None,
                      status=200, headers=None, body=None):
    """Adds a mock HTTP response for the given URL.

    Args:
      url: str, The URL excluding any parameters.
      request_headers: dict, Headers in the request to match.
      expected_params: str, The query parameters that were expected for the URL.
        If any of the values for the params are a string, it will be converted
        to a single element list to match the parsing of query strings.
        gcloud_core_test_base.IGNORE can be passed in to disable request query
        parameter verification.
      expected_body: str, The expected body of the request.
        gcloud_core_test_base.IGNORE can be passed in to disable request body
        verification.
      status: int, The status code to return with the response.
      headers: dict, Headers to return with the response. By default,
        {'status': 200} is returned. This default can be updated with this arg.
      body: str, The body to return with the response.
    """
    if expected_params is None:
      expected_params = {}
    elif expected_params != IGNORE:
      for param, value in six.iteritems(expected_params):
        if isinstance(value, six.string_types):
          expected_params[param] = [value]
    request_headers = request_headers or {}
    request_headers_tuple = tuple(request_headers.items())
    responses = self._responses.setdefault((url, request_headers_tuple), [])
    responses.append((expected_params, expected_body, status, headers or {},
                      body))


def _LoadTestConfig():
  """Loads test config based on environment variable setting."""
  env_config_file = encoding.GetEncodedValue(os.environ,
                                             'CLOUD_SDK_TEST_CONFIG')
  if not env_config_file:
    env_config_file = cli_test_base.CliTestBase.Resource(
        'tests', 'lib', 'e2e', 'integration_test_config.yaml')
    if not os.path.isfile(env_config_file):
      return None
  elif not os.path.isfile(env_config_file):
    if os.path.isabs(env_config_file):
      resource_config_file = None
    else:
      # Relative path and does not exists wrt to current dir.
      # Check wrt to project root.
      resource_config_file = cli_test_base.CliTestBase.Resource(env_config_file)
      if os.path.isfile(resource_config_file):
        env_config_file = resource_config_file
      else:
        resource_config_file = None
    if resource_config_file is None:
      raise ValueError('CLOUD_SDK_TEST_CONFIG env var set to non-existent '
                       'file {}'.format(env_config_file))

  return yaml.load_path(env_config_file)


_TEST_CONFIG = _LoadTestConfig()


class WithServiceAccountFile(WithCoreModules):
  """A base class which only provides service account file."""

  def SetUp(self):
    with tempfile.NamedTemporaryFile(
        mode='w+t', dir=self.temp_path, delete=False) as key_file:
      json.dump(_TEST_CONFIG['auth_data']['service_account'], key_file)
    self.json_key_file = key_file.name

  def Account(self):
    return _TEST_CONFIG['auth_data']['service_account']['client_email']

  def Project(self):
    return _TEST_CONFIG['property_overrides']['project']


class WithServiceAuth(WithServiceAccountFile):
  """A base class for tests that have an authed service account.

     This will use a refresh token instead for the legacy tools which don't
     support service account auth.
  """

  def PreSetUp(self):
    self.requires_refresh_token = False
    self.disable_activate_service_account_google_auth = False

  def SetUp(self):
    """Runs the auth command."""
    if _TEST_CONFIG is None:
      raise RuntimeError('Credentials are not configured. Use '
                         'CLOUD_SDK_TEST_CONFIG env variable to point '
                         'to integration test config.')

    # Configures whether to execute the service account activation against
    # google-auth or oauth2client.
    self.Run('--no-user-output-enabled '
             'config set auth/disable_activate_service_account_google_auth ' +
             str(self.disable_activate_service_account_google_auth))

    if self.requires_refresh_token:
      self.Run(
          '--no-user-output-enabled '
          'auth activate-refresh-token {account} {token}'.format(
              account='no_accountability ',
              token=_TEST_CONFIG['auth_data']['user_account']['refresh_token']))
      self.Run('--no-user-output-enabled '
               'config set account no_accountability')
    else:
      self.Run(
          '--no-user-output-enabled '
          'auth activate-service-account {account} --key-file={key}'.format(
              account=self.Account(),
              key=self.json_key_file))
      self.Run('--no-user-output-enabled '
               'config set account ' + self.Account())

    orig_refresh = c_store.Refresh

    def RefreshWithRetry(
        creds, http=None, is_impersonated_credential=False, include_email=False,
        gce_token_format='standard', gce_include_license=False
    ):
      retryer = retry.Retryer(max_retrials=4, exponential_sleep_multiplier=2)
      retryer.RetryOnException(orig_refresh,
                               [
                                   creds, http, is_impersonated_credential,
                                   include_email,
                                   gce_token_format, gce_include_license
                               ],
                               sleep_ms=2000)

    self.StartObjectPatch(c_store, 'Refresh').side_effect = RefreshWithRetry

    if 'property_overrides' in _TEST_CONFIG:
      for prop, value in six.iteritems(_TEST_CONFIG['property_overrides']):
        self.Run(['--no-user-output-enabled', 'config', 'set', prop, value])

  def BillingId(self):
    return _TEST_CONFIG['auth_data']['user_account']['billing_id']


class WithExpiredUserAuthMixin(object):

  def Project(self):
    return _TEST_CONFIG['property_overrides']['project']

  def Account(self):
    return _TEST_CONFIG['auth_data']['user_account']['account']

  def _ActivateRefreshToken(self):
    self.Run('auth activate-refresh-token {account} {token}'.format(
        account=self.Account(),
        token=_TEST_CONFIG['auth_data']['user_account']['refresh_token']))


class WithExpiredUserAuthEnforcedRetry(WithExpiredUserAuthMixin,
                                       WithCoreModules):
  """A base class to test credentials refresh after the first request failed."""

  def SetUp(self):
    self.StartPatch('googlecloudsdk.core.credentials.store.Refresh')
    self._ActivateRefreshToken()
    creds = c_store.Load(use_google_auth=True)
    # Make sure an invalid token is sent to services.
    creds.token = 'invalid_access_token'
    creds.expiry = creds.expiry + datetime.timedelta(hours=1)
    c_store.Store(creds)


class WithExpiredUserAuth(WithExpiredUserAuthMixin, WithCoreModules):
  """A base class to test when the cached user credentials are invalid."""

  def SetUp(self):
    with mock.patch('googlecloudsdk.core.credentials.store.Refresh') as ref:
      ref.return_value = None
      self._ActivateRefreshToken()
      creds = c_store.Load(use_google_auth=True)
    creds.token = 'invalid_access_token'
    c_store.Store(creds)


class RefreshTokenAuth(object):
  """Context manager for test credentials based on refresh token."""

  def __init__(self, refresh_token=None):
    self._refresh_token = refresh_token or (
        _TEST_CONFIG['auth_data']['user_account']['refresh_token'])
    self._account = _TEST_CONFIG['auth_data']['user_account']['account']
    self._orig_account = None
    self._project = _TEST_CONFIG['property_overrides'].get('project', None)
    self._credentials = c_store.AcquireFromToken(self._refresh_token)

  def Account(self):
    return self._account

  def Project(self):
    return self._project

  @property
  def credentials(self):
    return self._credentials

  def __enter__(self):
    self._orig_account = properties.VALUES.core.account.Get()
    c_store.ActivateCredentials(self.Account(), self.credentials)
    return self

  def __exit__(self, ex_type, unused_value, unused_traceback):
    properties.VALUES.core.account.Set(self._orig_account)


class ImpersonationAccountAuth(object):
  """Context manager for tests with impersonation credentials."""

  def __init__(self):
    self._account = _TEST_CONFIG['auth_data']['user_account']['account']
    self._refresh_token = _TEST_CONFIG['auth_data']['user_account'][
        'refresh_token']
    self._service_account_email = _TEST_CONFIG['auth_data']['service_account'][
        'client_email']
    self._project_override = _TEST_CONFIG['property_overrides'].get(
        'project', None)

    self._orig_account = None
    self._orig_impersonate_service_account = None
    self._orig_project = None
    self._orig_impersonate_provider = None

  def Account(self):
    return self._account

  def ImpersonationServiceAccount(self):
    return self._service_account_email

  def __enter__(self):
    self._orig_account = properties.VALUES.core.account.Get()
    self._orig_project = properties.VALUES.core.project.Get()
    self._orig_impersonate_service_account = (
        properties.VALUES.auth.impersonate_service_account.Get())

    user_creds = c_store.AcquireFromToken(self._refresh_token)
    c_store.ActivateCredentials(self._account, user_creds)
    if self._project_override:
      properties.VALUES.core.project.Set(self._project_override)
    properties.VALUES.auth.impersonate_service_account.Set(
        self._service_account_email)

    self._orig_impersonate_provider = c_store.IMPERSONATION_TOKEN_PROVIDER
    c_store.IMPERSONATION_TOKEN_PROVIDER = (
        iamcred_util.ImpersonationAccessTokenProvider())
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    properties.VALUES.core.account.Set(self._orig_account)
    properties.VALUES.core.project.Set(self._orig_project)
    properties.VALUES.auth.impersonate_service_account.Set(
        self._orig_impersonate_service_account)
    c_store.IMPERSONATION_TOKEN_PROVIDER = self._orig_impersonate_provider


class ServiceAccountAuth(object):
  """Context manager for test credentials based on json service account."""

  def __init__(self):
    self._service_account_data = _TEST_CONFIG['auth_data']['service_account']
    self._project = _TEST_CONFIG['property_overrides'].get('project', None)
    self._orig_account = None
    self._credentials = auth_service_account.CredentialsFromAdcDict(
        self._service_account_data)

  def Account(self):
    return self.credentials.service_account_email

  def Project(self):
    return self._project

  @property
  def credentials(self):
    return self._credentials

  def __enter__(self):
    self._orig_account = properties.VALUES.core.account.Get()
    c_store.ActivateCredentials(self.Account(), self.credentials)
    return self

  def __exit__(self, ex_type, unused_value, unused_traceback):
    properties.VALUES.core.account.Set(self._orig_account)


class P12ServiceAccountAuth(object):
  """Context manager for test credentials based on p12 service account."""

  def __init__(self):
    self._private_key = base64.b64decode(
        _TEST_CONFIG['auth_data']['p12_service_account']['private_key'])
    self._account = _TEST_CONFIG['auth_data']['p12_service_account']['account']
    self._project = _TEST_CONFIG['property_overrides'].get('project', None)
    self._orig_account = None
    self._credentials = auth_service_account.CredentialsFromP12Key(
        self._private_key, self._account)

  def Account(self):
    return self._account

  def Project(self):
    return self._project

  @property
  def credentials(self):
    return self._credentials

  def __enter__(self):
    self._orig_account = properties.VALUES.core.account.Get()
    c_store.ActivateCredentials(self._account, self.credentials)
    return self

  def __exit__(self, ex_type, unused_value, unused_traceback):
    properties.VALUES.core.account.Set(self._orig_account)


class GceNotConnectedError(Exception):
  pass


class GceServiceAccount(object):
  """Context manager for test credentials based on gce service account."""

  def __init__(self):
    if not c_gce.Metadata().connected:
      raise GceNotConnectedError('Not connected')
    self._check_gce_metadata = None
    self._project = _TEST_CONFIG['property_overrides'].get('project', None)

  def Account(self):
    return c_gce.Metadata().DefaultAccount()

  def Project(self):
    return c_gce.Metadata().Project()

  def OverridingProject(self):
    return self._project

  @property
  def credentials(self):
    return oauth2client_gce.AppAssertionCredentials()

  def __enter__(self):
    self._check_gce_metadata = properties.VALUES.core.check_gce_metadata.Get()
    properties.VALUES.core.check_gce_metadata.Set(True)

    self._gce_provider = c_store.GceCredentialProvider()
    self._gce_provider.Register()
    return self

  def __exit__(self, ex_type, unused_value, unused_traceback):
    properties.VALUES.core.check_gce_metadata.Set(self._check_gce_metadata)
    self._gce_provider.UnRegister()
