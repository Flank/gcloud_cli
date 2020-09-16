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
"""Tests for user credential reauth during refresh."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import json

from googlecloudsdk.core.credentials import google_auth_credentials as c_google_auth
from tests.lib import cli_test_base
from tests.lib import test_case

import mock
from oauth2client.contrib import reauth
from requests import models
import six
from six.moves import urllib

from google.auth.transport import requests

_AUTH_REQUEST_HEADER = {'content-type': 'application/x-www-form-urlencoded'}


def _MockResponse(status_code, content):
  requests_response = models.Response()
  requests_response.status_code = status_code
  requests_response._content = content
  return requests._Response(requests_response)


def _RefreshHttpResponseRequireReauth():
  error_json = {'error': 'invalid_grant', 'error_subtype': 'invalid_rapt'}
  content = six.ensure_binary(json.dumps(error_json))
  return _MockResponse(500, content)


def _ValidRefreshHttpResponse():
  response_json = {
      'access_token': 'new_access_token',
      'refresh_token': 'new_refresh_token',
      'expires_in': 3600,
      'id_token': 'new_id_token'
  }
  content = six.ensure_binary(json.dumps(response_json))
  return _MockResponse(200, content)


class ReauthUsingSecurityKeyTest(cli_test_base.CliTestBase):

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
    # mock the Http request for refresh
    self.http_request = mock.MagicMock(spec=requests.Request())
    self.http_request.side_effect = [
        _RefreshHttpResponseRequireReauth(),
        _ValidRefreshHttpResponse()
    ]

    # mock the Http for reauth.
    # reauth can only use Http from httplib2.
    self.mock_http_reauth = mock.MagicMock()
    self.StartPatch(
        'googlecloudsdk.core.http.Http',
        autospec=True,
        return_value=self.mock_http_reauth)
    self.mock_http_reauth_request = mock.MagicMock()
    self.mock_http_reauth.request = self.mock_http_reauth_request
    # Prepare the mock Http responses.
    reauth_access_token_response = '{"access_token": "access_token_reauth"}'
    challenge_response = ('{"status": "CHALLENGE_REQUIRED", "sessionId": '
                          '"fake_session_id", "challenges": [{"status": '
                          '"READY", "challengeType": "SECURITY_KEY", '
                          '"securityKey": {"challenges": ""}}]}')
    self.mock_http_reauth_request.side_effect = [(None,
                                                  reauth_access_token_response),
                                                 (None, challenge_response)]

    # mock the security key interface.
    self.mock_security_key = mock.MagicMock()
    self.StartObjectPatch(
        reauth,
        'SecurityKeyChallenge',
        autospec=True,
        return_value=self.mock_security_key)
    self.mock_security_key.GetName.return_value = 'SECURITY_KEY'
    self.mock_security_key.Execute.return_value = {
        'status': 'AUTHENTICATED',
        'encodedProofOfReauthToken': 'valid_rapt_token'
    }

    # mock interactive mode
    self.StartObjectPatch(reauth, 'InteractiveCheck', return_value=True)

  def testBasic(self):
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

    self.creds.refresh(self.http_request)
    self.http_request.assert_has_calls(calls)
    self.mock_security_key.Execute.assert_called()


if __name__ == '__main__':
  test_case.main()
