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
"""Base class used for testing credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import textwrap

from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import reauth
from tests.lib import test_case

from oauth2client import client
import six


class CredentialsTestBase(test_case.Base):
  """A base class for tests of credentials."""

  # JSON representation for user credentials.
  USER_CREDENTIALS_JSON = textwrap.dedent("""\
        {
          "client_id": "foo.apps.googleusercontent.com",
          "client_secret": "file-secret",
          "refresh_token": "file-token",
          "type": "authorized_user"
        }""")

  # JSON representation for extened user credentials.
  EXTENDED_USER_CREDENTIALS_JSON = textwrap.dedent("""\
        {
          "client_id": "foo.apps.googleusercontent.com",
          "client_secret": "file-secret",
          "quota_project_id": "my project",
          "refresh_token": "file-token",
          "type": "authorized_user"
        }""")

  # JSON representation for serivce account credentials.
  SERVICE_ACCOUNT_CREDENTIALS_JSON = textwrap.dedent("""\
        {
          "client_email": "bar@developer.gserviceaccount.com",
          "client_id": "bar.apps.googleusercontent.com",
          "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
          "private_key_id": "key-id",
          "type": "service_account"
        }""")

  # JSON representation for exteneded serivce account credentials.
  # For testing google-auth credentials serialiaztion and deserialiaztion.
  # Unlike oauth2client credentials, google-auth serialiaztion and
  # deserialiaztion includes token URI and project ID.
  EXTENDED_SERVICE_ACCOUNT_CREDENTIALS_JSON = textwrap.dedent("""\
        {
          "client_email": "bar@developer.gserviceaccount.com",
          "client_id": "bar.apps.googleusercontent.com",
          "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
          "private_key_id": "key-id",
          "project_id": "bar-test",
          "token_uri": "https://oauth2.googleapis.com/token",
          "type": "service_account"
        }""")

  # Returns a JSON representation for P12 serivce account credentials.
  P12_SERVICE_ACCOUNT_CREDENTIALS_JSON = textwrap.dedent("""\
        {
          "client_email": "p12owner@developer.gserviceaccount.com",
          "password": "key-password",
          "private_key": "QkFTRTY0RU5DT0RFRA==",
          "type": "service_account_p12"
        }""")

  GOOGLE_AUTH_USER_ACCOUNT_INFO = {
      'refresh_token': 'file-token',
      'client_id': 'foo.apps.googleusercontent.com',
      'client_secret': 'file-secret',
      'quota_project_id': 'quota-project-id'
  }

  def MakeUserCredentials(self):
    """Returns a user credentials."""
    expiry = datetime.datetime(2001, 2, 3, 14, 15, 16)
    token_response = {'id_token': 'id-token'}
    # client.GoogleCredentials cannot serialize token-expiry.
    # use OAuth2Credentials. We generaly do not store GoogleCredentials.
    # credentials = creds.FromJson(GetJsonUser())
    return client.OAuth2Credentials(
        'access-token',
        'client_id',
        'client_secret',
        'fake-token',
        expiry,
        'token_uri',
        'user_agent',
        rapt_token='rapt_token5',
        token_response=token_response)

  def MakeServiceAccountCredentials(self):
    """Returns a service account credentials."""
    expiry = datetime.datetime(2001, 2, 3, 14, 15, 16)
    token_response = {'id_token': 'id-token'}
    credentials = creds.FromJson(self.SERVICE_ACCOUNT_CREDENTIALS_JSON)
    credentials.access_token = 'access_token'
    credentials.token_expiry = expiry
    credentials.token_response = token_response
    return credentials

  def MakeServiceAccountCredentialsGoogleAuth(self):
    expiry = datetime.datetime(2001, 2, 3, 14, 15, 16)
    credentials = creds.FromJsonGoogleAuth(
        self.EXTENDED_SERVICE_ACCOUNT_CREDENTIALS_JSON)
    credentials.token = 'access_token'
    credentials.expiry = expiry
    credentials.id_tokenb64 = 'id-token'
    return credentials

  def MakeUserAccountCredentialsGoogleAuth(self):
    return reauth.UserCredWithReauth.from_authorized_user_info(
        self.GOOGLE_AUTH_USER_ACCOUNT_INFO, scopes=['scope1'])

  def MakeP12ServiceAccountCredentials(self):
    """Returns P12 service account credentials."""
    expiry = datetime.datetime(2001, 2, 3, 14, 15, 16)
    token_response = {'id_token': 'id-token'}
    credentials = creds.FromJson(self.P12_SERVICE_ACCOUNT_CREDENTIALS_JSON)
    credentials.access_token = 'access_token'
    credentials.token_expiry = expiry
    credentials.token_response = token_response
    return credentials

  def AssertCredentialsEqual(self, actual_cred, expected_cred_dict):
    """Checks if the actual and expected credentials are equal.

    Please note that fields of tuple will be checked using assertCountEqual
    which compares all the elements in the tuple. Everything else of the
    credentials are not collection and will be checked via assertEqual.

    Args:
      actual_cred: google.auth.credentials.Credentials or
        client.OAuth2Credentials, The actual credentials to check.
      expected_cred_dict: dict, The expected credentials values, in the form of
        a dict.
    """
    for key, expected in six.iteritems(expected_cred_dict):
      actual = getattr(actual_cred, key, None)

      if isinstance(expected, tuple):
        self.assertCountEqual(actual, expected)
      else:
        self.assertEqual(actual, expected)

  def AssertCredentials(self, actual_creds, expected_type, expected_creds_dict,
                        expected_expired):
    """Asserts credentials with the a few aspects of expectations.

    Different logic will be executed for oauth2client and google-auth
    credentials.

    Args:
      actual_creds: google.auth.credentials.Credentials or
        client.OAuth2Credentials, the credentials to assert.
      expected_type: creds.CredentialTypeGoogleAuth or creds.CredentialType, the
        expected type of the credentials.
      expected_creds_dict: dict, the expected values of the credentials, in the
        form of a dict.
      expected_expired: bool, whether the credentials are expected to be
        expired.
    """
    if isinstance(actual_creds, client.OAuth2Credentials):
      actual_type = creds.CredentialType.FromCredentials(actual_creds)
      self.assertEqual(actual_type, expected_type)
      self.AssertCredentialsEqual(actual_creds, expected_creds_dict)
      self.assertEqual(actual_creds.access_token_expired, expected_expired)
    else:
      actual_type = creds.CredentialTypeGoogleAuth.FromCredentials(actual_creds)
      self.assertEqual(actual_type, expected_type)
      self.AssertCredentialsEqual(actual_creds, expected_creds_dict)
      self.assertEqual(actual_creds.expired, expected_expired)
