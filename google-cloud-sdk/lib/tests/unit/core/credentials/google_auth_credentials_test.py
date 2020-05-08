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
"""Tests for the google_auth_credentials module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import datetime
import json

from googlecloudsdk.core.credentials import google_auth_credentials as c_google_auth
from tests.lib import cli_test_base
from tests.lib import test_case
import mock

from oauth2client.contrib import reauth as oauth2client_reauth
from requests import models

import six
from six.moves import urllib

from google.auth import _helpers
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport import requests


def _MockResponse(status_code, content):
  requests_response = models.Response()
  requests_response.status_code = status_code
  requests_response._content = content
  return requests._Response(requests_response)


def _ValidRefreshHttpResponse():
  response_json = {
      'access_token': 'new_access_token',
      'refresh_token': 'new_refresh_token',
      'expires_in': 3600,
      'id_token': 'new_id_token'
  }
  content = six.ensure_binary(json.dumps(response_json))
  return _MockResponse(200, content)


def _RefreshHttpResponseMissingScopes():
  response_json = {
      'access_token': 'new_access_token',
      'refresh_token': 'new_refresh_token',
      'expires_in': 3600,
      'id_token': 'new_id_token',
      'scope': 'scope1'
  }
  content = six.ensure_binary(json.dumps(response_json))
  return _MockResponse(200, content)


def _RefreshHttpResponseMissingAccessToken():
  response_json = {
      'refresh_token': 'new_refresh_token',
      'expires_in': 3600,
      'id_token': 'new_id_token',
  }
  content = six.ensure_binary(json.dumps(response_json))
  return _MockResponse(200, content)


def _RefreshHttpResponseWithInternalError():
  error_json = {'error': 'internal_error'}
  content = six.ensure_binary(json.dumps(error_json))
  return _MockResponse(500, content)


def _RefreshHttpResponseRequireReauth():
  error_json = {'error': 'invalid_grant', 'error_subtype': 'invalid_rapt'}
  content = six.ensure_binary(json.dumps(error_json))
  return _MockResponse(500, content)


def _ValidRevokeHttpResponse():
  response_json = {}
  content = six.ensure_binary(json.dumps(response_json))
  return _MockResponse(200, content)


def _RevokeHttpResponseFailed():
  error_json = {'error': 'invalid_token'}
  content = six.ensure_binary(json.dumps(error_json))
  return _MockResponse(500, content)


_AUTH_REQUEST_HEADER = {'content-type': 'application/x-www-form-urlencoded'}


class GoogleAuthUserCredsRefreshTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.creds = c_google_auth.UserCredWithReauth(
        token='token',
        refresh_token='refresh_token',
        id_token='id_token',
        token_uri='token_uri',
        client_id='client_id',
        client_secret='client_secret',
        scopes=['scope1', 'scope2'],
        quota_project_id='quota_project_id')
    self.http_request = mock.MagicMock(spec=requests.Request())
    self.now = datetime.datetime(2020, 1, 1)
    self.StartObjectPatch(_helpers, 'utcnow').return_value = self.now
    self.expected_expiry = datetime.datetime(2020, 1, 1, 1)

  def _AssertTokenRefreshed(self):
    self.assertEqual(self.creds.token, 'new_access_token')
    self.assertEqual(self.creds.refresh_token, 'new_refresh_token')
    self.assertEqual(self.creds.expiry, self.expected_expiry)
    self.assertEqual(self.creds._id_token, 'new_id_token')

  def _AssertRaptTokenRefreshed(self):
    self.assertEqual(self.creds._rapt_token, 'valid_rapt_token')

  def testMissingRefreshToken(self):
    self.creds._refresh_token = None
    with self.AssertRaisesExceptionRegexp(
        google_auth_exceptions.RefreshError,
        'The credentials do not contain the necessary fields'):
      self.creds.refresh(self.http_request)

  def testNoRaptToken(self):
    self.http_request.return_value = _ValidRefreshHttpResponse()
    self.creds.refresh(self.http_request)
    body = [
        ('grant_type', 'refresh_token'),
        ('client_id', 'client_id'),
        ('client_secret', 'client_secret'),
        ('refresh_token', 'refresh_token'),
        ('scope', 'scope1 scope2'),
    ]
    self.http_request.assert_called_with(
        method='POST',
        url='token_uri',
        headers=_AUTH_REQUEST_HEADER,
        body=urllib.parse.urlencode(body))
    self._AssertTokenRefreshed()

  def testScopesMismatch(self):
    self.http_request.return_value = _RefreshHttpResponseMissingScopes()
    with self.AssertRaisesExceptionMatches(
        google_auth_exceptions.RefreshError,
        'Not all requested scopes were granted by the authorization server, '
        'missing scopes scope2.'):
      self.creds.refresh(self.http_request)

  def testValidRaptToken(self):
    self.creds._rapt_token = 'valid_rapt_token'
    self.http_request.return_value = _ValidRefreshHttpResponse()
    self.creds.refresh(self.http_request)
    body = [
        ('grant_type', 'refresh_token'),
        ('client_id', 'client_id'),
        ('client_secret', 'client_secret'),
        ('refresh_token', 'refresh_token'),
        ('scope', 'scope1 scope2'),
        ('rapt', 'valid_rapt_token'),
    ]
    self.http_request.assert_called_with(
        method='POST',
        url='token_uri',
        headers=_AUTH_REQUEST_HEADER,
        body=urllib.parse.urlencode(body))
    self._AssertTokenRefreshed()

  def testMissingAccessToken(self):
    self.http_request.return_value = _RefreshHttpResponseMissingAccessToken()
    with self.AssertRaisesExceptionMatches(google_auth_exceptions.RefreshError,
                                           'No access token'):
      self.creds.refresh(self.http_request)


class GoogleAuthUserCredsRefreshWithReauthTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.creds = c_google_auth.UserCredWithReauth(
        token='token',
        refresh_token='refresh_token',
        id_token='id_token',
        token_uri='token_uri',
        client_id='client_id',
        client_secret='client_secret',
        scopes=['scope1', 'scope2'],
        quota_project_id='quota_project_id')
    self.http_request = mock.MagicMock(spec=requests.Request())
    self.get_rapt_token_mock = self.StartObjectPatch(oauth2client_reauth,
                                                     'GetRaptToken')
    self.now = datetime.datetime(2020, 1, 1)
    self.StartObjectPatch(_helpers, 'utcnow').return_value = self.now
    self.expected_expiry = datetime.datetime(2020, 1, 1, 1)

  def _AssertTokenRefreshed(self):
    self.assertEqual(self.creds.token, 'new_access_token')
    self.assertEqual(self.creds.refresh_token, 'new_refresh_token')
    self.assertEqual(self.creds.expiry, self.expected_expiry)
    self.assertEqual(self.creds._id_token, 'new_id_token')

  def _AssertRaptTokenRefreshed(self):
    self.assertEqual(self.creds._rapt_token, 'valid_rapt_token')

  def testRetryWhenServerInternalErrors_Fail(self):
    self.http_request.return_value = _RefreshHttpResponseWithInternalError()
    with self.AssertRaisesExceptionMatches(google_auth_exceptions.RefreshError,
                                           'internal_error'):
      self.creds.refresh(self.http_request)
    self.assertEqual(self.http_request.call_count, 2)

  def testRetryWhenServerInternalErrors_Success(self):
    self.http_request.side_effect = [
        _RefreshHttpResponseWithInternalError(),
        _ValidRefreshHttpResponse()
    ]
    self.creds.refresh(self.http_request)
    self.assertEqual(self.http_request.call_count, 2)
    self._AssertTokenRefreshed()

  def testReauthRequired(self):
    self.http_request.side_effect = [
        _RefreshHttpResponseRequireReauth(),
        _ValidRefreshHttpResponse()
    ]
    self.get_rapt_token_mock.return_value = 'valid_rapt_token'
    self.creds.refresh(self.http_request)
    self.assertEqual(self.get_rapt_token_mock.call_count, 1)
    body1 = [
        ('grant_type', 'refresh_token'),
        ('client_id', 'client_id'),
        ('client_secret', 'client_secret'),
        ('refresh_token', 'refresh_token'),
        ('scope', 'scope1 scope2'),
    ]
    body2 = copy.deepcopy(body1)
    body2.append(('rapt', 'valid_rapt_token'))
    calls = [
        mock.call(
            method='POST',
            url='token_uri',
            headers=_AUTH_REQUEST_HEADER,
            body=urllib.parse.urlencode(body1)),
        mock.call(
            method='POST',
            url='token_uri',
            headers=_AUTH_REQUEST_HEADER,
            body=urllib.parse.urlencode(body2))
    ]

    self.http_request.assert_has_calls(calls)
    self._AssertTokenRefreshed()
    self._AssertRaptTokenRefreshed()

  def testReauthRequired_Failed(self):
    self.http_request.return_value = _RefreshHttpResponseRequireReauth()
    self.get_rapt_token_mock.return_value = 'valid_rapt_token'

    with self.AssertRaisesExceptionMatches(c_google_auth.ReauthRequiredError,
                                           'reauth is required'):
      self.creds.refresh(self.http_request)
    self.assertEqual(self.get_rapt_token_mock.call_count, 1)

    body1 = [
        ('grant_type', 'refresh_token'),
        ('client_id', 'client_id'),
        ('client_secret', 'client_secret'),
        ('refresh_token', 'refresh_token'),
        ('scope', 'scope1 scope2'),
    ]
    body2 = copy.deepcopy(body1)
    body2.append(('rapt', 'valid_rapt_token'))
    calls = [
        mock.call(
            method='POST',
            url='token_uri',
            headers=_AUTH_REQUEST_HEADER,
            body=urllib.parse.urlencode(body1)),
        mock.call(
            method='POST',
            url='token_uri',
            headers=_AUTH_REQUEST_HEADER,
            body=urllib.parse.urlencode(body2))
    ]

    self.http_request.assert_has_calls(calls)

  def testServerInternalErrorAndReauth(self):
    self.http_request.side_effect = [
        _RefreshHttpResponseRequireReauth(),
        _RefreshHttpResponseWithInternalError(),
        _ValidRefreshHttpResponse()
    ]

    self.get_rapt_token_mock.return_value = 'valid_rapt_token'

    body1 = [
        ('grant_type', 'refresh_token'),
        ('client_id', 'client_id'),
        ('client_secret', 'client_secret'),
        ('refresh_token', 'refresh_token'),
        ('scope', 'scope1 scope2'),
    ]
    body2 = copy.deepcopy(body1)
    body2.append(('rapt', 'valid_rapt_token'))
    calls = [
        mock.call(
            method='POST',
            url='token_uri',
            headers=_AUTH_REQUEST_HEADER,
            body=urllib.parse.urlencode(body1)),
        mock.call(
            method='POST',
            url='token_uri',
            headers=_AUTH_REQUEST_HEADER,
            body=urllib.parse.urlencode(body2)),
        mock.call(
            method='POST',
            url='token_uri',
            headers=_AUTH_REQUEST_HEADER,
            body=urllib.parse.urlencode(body2))
    ]
    self.creds.refresh(self.http_request)
    self.http_request.assert_has_calls(calls)
    self.assertEqual(self.get_rapt_token_mock.call_count, 1)

    self._AssertTokenRefreshed()
    self._AssertRaptTokenRefreshed()


class GoogleAuthUserCredsRevoke(cli_test_base.CliTestBase):

  def SetUp(self):
    self.creds = c_google_auth.UserCredWithReauth(
        token='token',
        refresh_token='refresh_token',
        id_token='id_token',
        token_uri='token_uri',
        client_id='client_id',
        client_secret='client_secret',
        scopes=['scope1', 'scope2'],
        quota_project_id='quota_project_id')
    self.http_request = mock.MagicMock(spec=requests.Request())
    self.expected_header = {'content-type': 'application/x-www-form-urlencoded'}

  def testRevoke_UsingRefreshToken(self):
    self.http_request.return_value = _ValidRevokeHttpResponse()
    self.creds.revoke(self.http_request)
    expected_revoke_uri = 'https://accounts.google.com/o/oauth2/revoke?token=refresh_token'
    self.http_request.assert_called_with(
        expected_revoke_uri, headers=self.expected_header)

  def testRevoke_UsingAccessToken(self):
    self.creds._refresh_token = None
    self.http_request.return_value = _ValidRevokeHttpResponse()
    self.creds.revoke(self.http_request)
    expected_revoke_uri = 'https://accounts.google.com/o/oauth2/revoke?token=token'
    self.http_request.assert_called_with(
        expected_revoke_uri, headers=self.expected_header)

  def testRevoke_Failed(self):
    self.http_request.return_value = _RevokeHttpResponseFailed()
    expected_revoke_uri = 'https://accounts.google.com/o/oauth2/revoke?token=refresh_token'
    with self.AssertRaisesExceptionMatches(c_google_auth.TokenRevokeError,
                                           'invalid_token'):
      self.creds.revoke(self.http_request)
    self.http_request.assert_called_with(
        expected_revoke_uri, headers=self.expected_header)


if __name__ == '__main__':
  test_case.main()
