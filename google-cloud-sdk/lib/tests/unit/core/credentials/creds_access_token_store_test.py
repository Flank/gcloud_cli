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
"""Tests for AccessTokenStore and AccessTokenStoreGoogleAuth."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import os

from googlecloudsdk.core.credentials import creds as c_creds
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

from oauth2client import client
from oauth2client import crypt
from oauth2client import service_account
from google.auth import crypt as google_auth_crypt
from google.oauth2 import credentials
from google.oauth2 import service_account as google_auth_aservice_account


def _MakeEmptyUserCredentialsOauth2client():
  return client.OAuth2Credentials(None, None, None, None, None, None, None)


def _MakeEmptyUserCredentialsGoogleAuth():
  return credentials.Credentials(None)


def _MakeEmptyServiceAccountCredentialsOauth2client():
  return service_account.ServiceAccountCredentials(None, None)


def _MakeEmptyServiceAccountCredentialsGoogleAuth():
  return google_auth_aservice_account.Credentials(None, None, None)


def _GetCredsFromStore(store):
  """Calls the right method to get credentials based on the store type."""
  if isinstance(store, c_creds.AccessTokenStore):
    return store.get()
  else:
    return store.Get()


def _PutCredsToStore(store):
  """Calls the right method to put credentials based on the store type."""
  if isinstance(store, c_creds.AccessTokenStore):
    # The credentials to put is kept inside the store class. The credentials
    # of the input argument of the put() method is just a place holder for
    # matching the signature of the function to that of the interface of
    # oauth2client. Passes None here to stuff the place holder.
    store.put(None)
  else:
    store.Put()


def _DeleteCredsFromStore(store):
  """Calls the right method to delete credentials based on the store type."""
  if isinstance(store, c_creds.AccessTokenStore):
    store.delete()
  else:
    store.Delete()


class AccessTokenStoreTests(sdk_test_base.SdkBase,
                            credentials_test_base.CredentialsTestBase):
  """Tests for AccessTokenStore and AccessTokenStoreGoogleAuth.

  This class tests the interoperations between the AccessTokenStore and the
  AccessTokenStoreGoogleAuth and covers the following 4 cases,
  1. Puts via AccessTokenStore and gets via AccessTokenStore: an example of
     this case is, the cache is first populated by the refresh of oauth2client
     credentials and later read by oauth2client credentials.
  2. Puts via AccessTokenStore and gets via AccessTokenStoreGoogleAuth: an
     example of this case is, the cache is first populated by the refresh of
     oauth2client credentials and later read by google-auth credentials.
  3. Puts via AccessTokenStoreGoogleAuth and gets via
     AccessTokenStoreGoogleAuth: an example of this case is, the cache is first
     populated by the refresh of google-auth credentials and later read by
     google-auth credentials.
  4. Puts via AccessTokenStoreGoogleAuth and gets via AccessTokenStore: an
     example of this case is, the cache is first populated by the refresh of
     google-auth credentials and later read by oauth2client credentials.
  """

  def SetUp(self):
    signer = self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(crypt, 'OpenSSLSigner', new=signer)
    self.StartObjectPatch(google_auth_crypt.RSASigner,
                          'from_service_account_info')
    access_token_file = os.path.join(self.temp_path, 'access_token.db')
    self.access_token_cache = c_creds.AccessTokenCache(access_token_file)
    self.fake_account = 'fake-account'

  def AssertCredentialsEmpty(self, creds):
    if isinstance(creds, client.OAuth2Credentials):
      self.AssertCredentialsEqual(
          creds, {
              'access_token': None,
              'token_expiry': None,
              'rapt_token': None,
              'id_tokenb64': None,
          })
    else:
      self.AssertCredentialsEqual(creds, {
          'token': None,
          'expiry': None,
          'rapt_token': None,
          'id_tokenb64': None,
      })

  def TestStoreOperations(self, store_put_builder, store_get_builder, creds_put,
                          expected_creds_got_dict, empty_creds_builder):
    """Tests interoperations of AccessTokenStore and AccessTokenStoreGoogleAuth.

    This test run through the following steps:
    1. Creates store_get for getting credentials. Gets credentials from the
       empty cache and verifies the returned credentials are empty.
    2. Creates store_put for putting credentials. Puts creds_put into the cache.
    3. Gets credetnails from the cache which is populated in step 2 and verifies
       the returned credentials matches the expected values.
    4. Deletes the credentials from the cache. Gets credentials from the empty
       cache and verifies the returned credentials are empty.

    Args:
      store_put_builder: function, A function that builds creds.AccessTokenCache
        or creds.AccessTokenCacheGoogleAuth, for putting credentials into the
        cache.
      store_get_builder: function, A function that builds creds.AccessTokenCache
        or creds.AccessTokenCacheGoogleAuth, for getting credentials from the
        cache.
      creds_put: google.auth.credentials.Credentials or
        client.OAuth2Credentials，The credentials to be put into the cache.
      expected_creds_got_dict: dict, The expected values of the credentials got
        from the cache, in the form of dict.
      empty_creds_builder: function, A function that builds empty oauth2client
        or google-auth credentials. The empty credentials are used for getting
        tokens from the cache.
    """
    # Creates a store for getting credentials from the cache, calls the get
    # method on the store and verifies the returned credentials are empty.
    store_get = store_get_builder(self.access_token_cache, self.fake_account,
                                  empty_creds_builder())
    creds_got = _GetCredsFromStore(store_get)
    self.AssertCredentialsEmpty(creds_got)

    # Creates a store for putting credentials to the cache and puts creds_put.
    store_put = store_put_builder(self.access_token_cache, self.fake_account,
                                  creds_put)
    _PutCredsToStore(store_put)

    # Get credentials from store_get again and verifies the returned credentials
    # match the expected values.
    creds_got = _GetCredsFromStore(store_get)
    self.AssertCredentialsEqual(creds_got, expected_creds_got_dict)

    # Calls delete on store_put. Creates a new store_get instance and calls
    # the get method on the store. Verifies the returned credentials are empty.
    _DeleteCredsFromStore(store_put)
    store_get = store_get_builder(self.access_token_cache, self.fake_account,
                                  empty_creds_builder())
    creds_got = _GetCredsFromStore(store_get)
    self.AssertCredentialsEmpty(creds_got)

  def testStoreViaAccessTokenStore_LoadViaAccessTokenStore_UserCreds(self):
    store_put_builder = c_creds.AccessTokenStore
    store_get_builder = c_creds.AccessTokenStore
    creds_put = self.MakeUserCredentials()
    expected_creds_got_dict = {
        'access_token': 'access-token',
        'token_expiry': datetime.datetime(2001, 2, 3, 14, 15, 16),
        'rapt_token': 'rapt_token5',
        'id_tokenb64': 'id-token',
    }
    empty_creds_builder = _MakeEmptyUserCredentialsOauth2client

    self.TestStoreOperations(store_put_builder, store_get_builder, creds_put,
                             expected_creds_got_dict, empty_creds_builder)

  def testStoreViaAccessTokenStore_LoadViaAccessTokenStore_ServiceAccountCreds(
      self):
    store_put_builder = c_creds.AccessTokenStore
    store_get_builder = c_creds.AccessTokenStore
    creds_put = self.MakeServiceAccountCredentials()
    expected_creds_got_dict = {
        'access_token': 'access_token',
        'token_expiry': datetime.datetime(2001, 2, 3, 14, 15, 16),
        'rapt_token': None,
        'id_tokenb64': 'id-token',
    }
    empty_creds_builder = _MakeEmptyServiceAccountCredentialsOauth2client

    self.TestStoreOperations(store_put_builder, store_get_builder, creds_put,
                             expected_creds_got_dict, empty_creds_builder)

  def testStoreViaAccessTokenStore_LoadViaAccessTokenStore_P12ServiceAccountCreds(  # pylint: disable=line-too-long
      self):
    store_put_builder = c_creds.AccessTokenStore
    store_get_builder = c_creds.AccessTokenStore
    creds_put = self.MakeP12ServiceAccountCredentials()
    expected_creds_got_dict = {
        'access_token': 'access_token',
        'token_expiry': datetime.datetime(2001, 2, 3, 14, 15, 16),
        'rapt_token': None,
        'id_tokenb64': 'id-token',
    }
    empty_creds_builder = _MakeEmptyServiceAccountCredentialsOauth2client

    self.TestStoreOperations(store_put_builder, store_get_builder, creds_put,
                             expected_creds_got_dict, empty_creds_builder)

  def testStoreViaAccessTokenStore_LoadViaAccessTokenStoreGoogleAuth_UserCreds(
      self):
    store_put_builder = c_creds.AccessTokenStore
    store_get_builder = c_creds.AccessTokenStoreGoogleAuth
    creds_put = self.MakeUserCredentials()
    expected_creds_got_dict = {
        'token': 'access-token',
        'expiry': datetime.datetime(2001, 2, 3, 14, 15, 16),
        'rapt_token': 'rapt_token5',
        'id_tokenb64': 'id-token',
    }
    empty_creds_builder = _MakeEmptyUserCredentialsGoogleAuth

    self.TestStoreOperations(store_put_builder, store_get_builder, creds_put,
                             expected_creds_got_dict, empty_creds_builder)

  def testStoreViaAccessTokenStore_LoadViaAccessTokenStoreGoogleAuth_ServiceAccountCreds(  # pylint: disable=line-too-long
      self):
    store_put_builder = c_creds.AccessTokenStore
    store_get_builder = c_creds.AccessTokenStoreGoogleAuth
    creds_put = self.MakeServiceAccountCredentials()
    expected_creds_got_dict = {
        'token': 'access_token',
        'expiry': datetime.datetime(2001, 2, 3, 14, 15, 16),
        'rapt_token': None,
        'id_tokenb64': 'id-token',
    }
    empty_creds_builder = _MakeEmptyServiceAccountCredentialsGoogleAuth

    self.TestStoreOperations(store_put_builder, store_get_builder, creds_put,
                             expected_creds_got_dict, empty_creds_builder)

  def testStoreViaAccessTokenStore_LoadViaAccessTokenStoreGoogleAuth_ServiceAccountCreds_NoIdToken(  # pylint: disable=line-too-long
      self):
    store_put_builder = c_creds.AccessTokenStore
    store_get_builder = c_creds.AccessTokenStoreGoogleAuth
    creds_put = self.MakeServiceAccountCredentials()
    # id_token is stored inside token_response.
    creds_put.token_response = None
    expected_creds_got_dict = {
        'token': 'access_token',
        'expiry': datetime.datetime(2001, 2, 3, 14, 15, 16),
        'rapt_token': None,
        'id_tokenb64': None,
    }
    empty_creds_builder = _MakeEmptyServiceAccountCredentialsGoogleAuth

    self.TestStoreOperations(store_put_builder, store_get_builder, creds_put,
                             expected_creds_got_dict, empty_creds_builder)

  def testStoreViaAccessTokenStoreGoogleAuth_LoadViaAccessTokenStoreGoogleAuth_ServiceAccountCreds(  # pylint: disable=line-too-long
      self):
    store_put_builder = c_creds.AccessTokenStoreGoogleAuth
    store_get_builder = c_creds.AccessTokenStoreGoogleAuth
    creds_put = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_creds_got_dict = {
        'token': 'access_token',
        'expiry': datetime.datetime(2001, 2, 3, 14, 15, 16),
        'rapt_token': None,
        'id_tokenb64': 'id-token',
    }
    empty_creds_builder = _MakeEmptyServiceAccountCredentialsGoogleAuth

    self.TestStoreOperations(store_put_builder, store_get_builder, creds_put,
                             expected_creds_got_dict, empty_creds_builder)

  def testStoreViaAccessTokenStoreGoogleAuth_LoadViaAccessTokenStore_ServiceAccountCreds(  # pylint: disable=line-too-long
      self):
    store_put_builder = c_creds.AccessTokenStoreGoogleAuth
    store_get_builder = c_creds.AccessTokenStore
    creds_put = self.MakeServiceAccountCredentialsGoogleAuth()
    expected_creds_got_dict = {
        'access_token': 'access_token',
        'token_expiry': datetime.datetime(2001, 2, 3, 14, 15, 16),
        'rapt_token': None,
        'id_tokenb64': 'id-token',
    }
    empty_creds_builder = _MakeEmptyServiceAccountCredentialsGoogleAuth

    self.TestStoreOperations(store_put_builder, store_get_builder, creds_put,
                             expected_creds_got_dict, empty_creds_builder)


if __name__ == '__main__':
  test_case.main()
