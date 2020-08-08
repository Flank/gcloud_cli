# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import filecmp
import json
import os

from googlecloudsdk.api_lib.auth import service_account as auth_service_account
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

from mock import patch
from oauth2client import client
from oauth2client import service_account
from google.oauth2 import service_account as google_auth_service_account

_ACCESS_TOKEN = 'test-access-token-25'
_CLIENT_ID = '999999999999999999999'
_PRIVATE_KEY = (
    '-----BEGIN PRIVATE KEY-----\nMIIEwAIBADANBgkqhkiG9w0BAQEFAASCBKowggSmAgEAA'
    'oIBAQDUPbMTOYxjab1E\niLxq8wQ3gYFTWAo5EvHBbRcn/bj8tgsXf0+XMwCjj328vg9TFj3Hi'
    '4aHeo4MbxXF\nw1vt0URqu0y18cmRXF6ntY3vyGThXFQyUvQPWjEdpvXY0GYgRo3+XvlaupEX/'
    'Ftj\ngR6sV3lDmQPoiMaDAB/nFP8L3NyddZpJDb90eV2gvQXSlN2oXP+a0ReNVJ8xfPvC\nY8p'
    'z9mzxrmo7u9ci/Xb8S6W+zglNn5Ur63cttotLrAQejaqdwxbREfvV7fGwJGjD\nXuXhBXaKvDq'
    '7BWrQE6PBJxlhKEEO5euYuM44enNBnps1Zzx5XzqJXtF3yfhnZSLn\nEJy/6UoZAgMBAAECggE'
    'BAIhIPg6gK1dCdHfnXSVHenOxwrsjkxzm3zmWtQHG19vd\ngO3Ln+20oDpmTxS87dYqN+1D2FR'
    'yC3hMdCySrxrb/xSRxEYoRYgDSfxihgtsH+rd\ngGr3/SNGhLdHmCFqX8llxJOLpI3vsm82afB'
    'Q3sNHP+R6App0CRPhJpsZTlPts/Oe\nfaBnQz/5scxIxna33T2S8SIG45dUcDri+6JMCsWgn7l'
    'Mf80E94rc2ZQosjbcv5Uw\nT1GSo8k4OKIW8lF0x08MTtgallDAbPETyyUOwj8K8eIVDgMCg4M'
    '7zrjLQTkw1DrN\nchjXnHtz5KgLegi/P+TcO3P90g72DV2zCwwm7bhZD+kCgYEA/4EENBTSung'
    '4LZlz\nhaZ/aqMr+wqVzKNWGmezudMjmhcFJHPr6YqElWbJt88U99db3X31gFxMv+NcCwf1\n0'
    'P46/BPwt6LtyQnJVoIFVrjpeHOjbzb2nP0OrUFUNuyp9Hz/0flOrIbjrofzy/0n\nn/xS4a8BB'
    'mRwcfxPpKUkvDVKQL8CgYEA1KcuhW3CMkNtoD9FvzJZTQ5fTREYiuW7\nlCxGD90dAhLbotjBe'
    '5gthJAzgB9NFfnou05Rhco/PHusFbOyBBxEaNKCpXOspfU6\nZv3GxZ2630QCvHP7fgMbPYyfk'
    'LRCQoW/ChiiJryGSCmpPU2ITbVRjKtxmbLB5sGD\njH9Z8CTE0ycCgYEAlUA9P1smmcyeLGzmI'
    'Z1X8ufsShIt3UNQic4oG5Wtx1ZJJ7kb\nhunmdwt7LAconXpM7H6myVuhbboXS05UFshblmLji'
    '7H+KyCvXvxGuBj+MOGEB/RY\nbO4aA7UUx5zJzsqx+WsjvP5yw8Ig9Pkli3wuwiyjcaN8V+lmc'
    'KwTYGnUvSsCgYEA\np68E0hYQkc31vezmtLOhE1AH+h9G+Q/acCbRQGUdIKt6IdlGCI2hJu0Gj'
    'zsfb/rW\neAxz4Enwv2LN+XbvIqqfjwCgIJMsStkqqlfmy6Fq3+8jMTNL1rvgWRJwKIzbytTo'
    '\nJa/y/RSf1ntzhnGCz7PwkDoIpCf/GlTxxHIPm3uC8PUCgYEAkUDRxj3i8mPXMje9\nJjVxQ9'
    'w4EVBqsjLiOdMYp5TFwK7ScDOVSpmJraaQbRE9C2roFwpUJkXpyJW6P/fy\nWHueM8fHJqzYuW'
    'N2zpRvHdjS93xn7Z9ADiLV4UV43XVXZAcV8obQaPbDzANFhNUe\nR59I27S9QkZQMX7Dojkpa6'
    'lz5/Q=\n-----END PRIVATE KEY-----\n')
_PRIVATE_KEY_ID = '294b4cce6389e0491d1c055585764d5631a3b0b4'
_SERVICE_ACCOUNT_EMAIL = 'inactive@developer.gserviceaccount.com'


def TestOauth2clientAndGoogleAuth(test_func):
  """Decorates the input test to cover both oauth2client and google-auth."""

  def Decorator(test_class_instance):
    """Decorator for the input test function.

    Args:
       test_class_instance: cli_test_base.CliTestBase, the instance of the test
         class the input test function belongs to.
    """
    # Runs the input test against oauth2client.
    test_class_instance.StartObjectPatch(
        properties.VALUES.auth.disable_activate_service_account_google_auth,
        'GetBool',
        return_value=True)
    test_func(test_class_instance)

    # Clears the stdin and stderr which could potentially be verified in the
    # next execution.
    test_class_instance.ClearOutput()
    test_class_instance.ClearErr()

    # Runs the input test against google-auth.
    test_class_instance.StartObjectPatch(
        properties.VALUES.auth.disable_activate_service_account_google_auth,
        'GetBool',
        return_value=False)
    test_func(test_class_instance)

  return Decorator


class ServiceAuthTestJSON(cli_test_base.CliTestBase,
                          credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    def _Refresh(cred):
      if c_creds.IsOauth2ClientCredentials(cred):
        cred.access_token = _ACCESS_TOKEN
      else:
        cred.token = _ACCESS_TOKEN

    self.refresh_mock = self.StartObjectPatch(
        store, 'Refresh', side_effect=_Refresh)

    # TODO(b/157745076): Activating service account via google-auth is enabled
    # only for Googlers at the moment. We need to mock IsHostGoogleDomain() to
    # to return True so that google-auth will invoked in the tests.
    # Remove this mock once it is enabled for everyone.
    self.StartObjectPatch(auth_util, 'IsHostGoogleDomain', return_value=True)

  def _GetTestDataPathFor(self, filename):
    return self.Resource(
        'tests', 'unit', 'surface', 'auth', 'test_data', filename)

  def RemoveServiceAccount(self):
    c_store = c_creds.GetCredentialStore()
    c_store.Remove(_SERVICE_ACCOUNT_EMAIL)

  @patch.object(client, 'HAS_CRYPTO', False)
  @TestOauth2clientAndGoogleAuth
  def testJSONCryptoNotRequired(self):
    self.RemoveServiceAccount()

    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run('auth activate-service-account {0} --key-file={1}'.format(
        _SERVICE_ACCOUNT_EMAIL, json_key_file))

    self.AssertErrEquals(
        'Activated service account credentials for: [{0}]\n'.format(
            _SERVICE_ACCOUNT_EMAIL))

    # Loads oauth2client credentials and verifies.
    creds_oauth2client = store.Load()
    self.assertIsInstance(creds_oauth2client,
                          service_account.ServiceAccountCredentials)
    self.AssertCredentialsEqual(
        creds_oauth2client, {
            'access_token': _ACCESS_TOKEN,
            'client_id': _CLIENT_ID,
            'service_account_email': _SERVICE_ACCOUNT_EMAIL,
            '_private_key_id': _PRIVATE_KEY_ID,
            '_private_key_pkcs8_pem': _PRIVATE_KEY,
        })
    # Activate via oauth2client or google-auth will have loaded credentials
    # carry different URLs. Both are valid.
    self.assertIn(creds_oauth2client.token_uri,
                  ('https://www.googleapis.com/oauth2/v4/token',
                   'https://oauth2.googleapis.com/token'))

    # Loads google-auth credentials and verifies.
    creds_google_auth = store.Load(use_google_auth=True)
    self.assertIsInstance(creds_google_auth,
                          google_auth_service_account.Credentials)
    self.AssertCredentialsEqual(
        creds_google_auth, {
            'token': _ACCESS_TOKEN,
            'client_id': _CLIENT_ID,
            'service_account_email': _SERVICE_ACCOUNT_EMAIL,
            'private_key_id': _PRIVATE_KEY_ID,
            'private_key': _PRIVATE_KEY,
            '_token_uri': 'https://oauth2.googleapis.com/token',
        })

  @patch.object(client, 'HAS_CRYPTO', False)
  @TestOauth2clientAndGoogleAuth
  def testJSONTokenUriNotProvided(self):
    self.RemoveServiceAccount()

    json_key_file = self._GetTestDataPathFor('no_token_uri_key_file.json')
    self.Run('auth activate-service-account {0} --key-file={1}'.format(
        _SERVICE_ACCOUNT_EMAIL, json_key_file))

    self.AssertErrEquals(
        'Activated service account credentials for: [{0}]\n'.format(
            _SERVICE_ACCOUNT_EMAIL))

    # Loads oauth2client credentials and verifies.
    creds_oauth2client = store.Load()
    self.assertIsInstance(creds_oauth2client,
                          service_account.ServiceAccountCredentials)
    self.AssertCredentialsEqual(
        creds_oauth2client, {
            'access_token': _ACCESS_TOKEN,
            'client_id': _CLIENT_ID,
            'service_account_email': _SERVICE_ACCOUNT_EMAIL,
            '_private_key_id': _PRIVATE_KEY_ID,
            '_private_key_pkcs8_pem': _PRIVATE_KEY,
        })
    # Activate via oauth2client or google-auth will have loaded credentials
    # carry different URLs. Both are valid.
    self.assertIn(creds_oauth2client.token_uri,
                  ('https://www.googleapis.com/oauth2/v4/token',
                   'https://oauth2.googleapis.com/token'))

    # Loads google-auth credentials and verifies.
    creds_google_auth = store.Load(use_google_auth=True)
    self.assertIsInstance(creds_google_auth,
                          google_auth_service_account.Credentials)
    self.AssertCredentialsEqual(
        creds_google_auth, {
            'token': _ACCESS_TOKEN,
            'client_id': _CLIENT_ID,
            'service_account_email': _SERVICE_ACCOUNT_EMAIL,
            'private_key_id': _PRIVATE_KEY_ID,
            'private_key': _PRIVATE_KEY,
            '_token_uri': 'https://oauth2.googleapis.com/token',
        })

  @TestOauth2clientAndGoogleAuth
  def testJSONFromStdin(self):
    self.RemoveServiceAccount()

    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    contents = files.ReadFileContents(json_key_file)
    self.WriteInput(contents)
    self.Run('auth activate-service-account {0} --key-file=-'.format(
        _SERVICE_ACCOUNT_EMAIL))

    self.AssertErrEquals(
        'Activated service account credentials for: [{0}]\n'.format(
            _SERVICE_ACCOUNT_EMAIL))

    # Loads oauth2client credentials and verifies.
    creds_oauth2client = store.Load()
    self.assertIsInstance(creds_oauth2client,
                          service_account.ServiceAccountCredentials)
    self.AssertCredentialsEqual(
        creds_oauth2client, {
            'access_token': _ACCESS_TOKEN,
            'client_id': _CLIENT_ID,
            'service_account_email': _SERVICE_ACCOUNT_EMAIL,
            '_private_key_id': _PRIVATE_KEY_ID,
            '_private_key_pkcs8_pem': _PRIVATE_KEY,
        })
    # Activate via oauth2client or google-auth will have loaded credentials
    # carry different URLs. Both are valid.
    self.assertIn(creds_oauth2client.token_uri,
                  ('https://www.googleapis.com/oauth2/v4/token',
                   'https://oauth2.googleapis.com/token'))

    # Loads google-auth credentials and verifies.
    creds_google_auth = store.Load(use_google_auth=True)
    self.assertIsInstance(creds_google_auth,
                          google_auth_service_account.Credentials)
    self.AssertCredentialsEqual(
        creds_google_auth, {
            'token': _ACCESS_TOKEN,
            'client_id': _CLIENT_ID,
            'service_account_email': _SERVICE_ACCOUNT_EMAIL,
            'private_key_id': _PRIVATE_KEY_ID,
            'private_key': _PRIVATE_KEY,
            '_token_uri': 'https://oauth2.googleapis.com/token',
        })

  @TestOauth2clientAndGoogleAuth
  def testP12CryptoRequired(self):
    try:
      import OpenSSL  # pylint: disable=g-import-not-at-top,unused-variable
    except ImportError:
      raise self.SkipTest('Needs PyOpenSSL installed.')

    p12_key_file = self._GetTestDataPathFor('service_account_key.p12')
    self.Run('auth activate-service-account {0} --key-file={1}'.format(
        _SERVICE_ACCOUNT_EMAIL, p12_key_file))

    # Check that internally scopes and user agent is set.
    creds_dict = json.loads(store.Load().to_json())
    self.assertEqual('google-cloud-sdk', creds_dict['_user_agent'])
    self.assertEqual('google-cloud-sdk', creds_dict['user_agent'])
    scopes = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/appengine.admin',
        'https://www.googleapis.com/auth/compute'

    ]
    self.assertEqual(' '.join(scopes), creds_dict['_scopes'])

    paths = config.Paths()
    expected_legacy_file = paths.LegacyCredentialsP12KeyPath(
        _SERVICE_ACCOUNT_EMAIL)

    self.AssertFileExists(expected_legacy_file)
    self.assertTrue(filecmp.cmp(p12_key_file, expected_legacy_file),
                    'original and saved P12 keys are different in {0} and {1}'
                    .format(p12_key_file, expected_legacy_file))

    self.AssertFileNotExists(
        paths.LegacyCredentialsAdcPath(_SERVICE_ACCOUNT_EMAIL))
    self.AssertFileNotExists(
        paths.LegacyCredentialsBqPath(_SERVICE_ACCOUNT_EMAIL))

  @TestOauth2clientAndGoogleAuth
  def testP12NoCrypto_NoSitePackages(self):
    with patch.object(service_account.ServiceAccountCredentials,
                      'from_p12_keyfile_buffer',
                      side_effect=NotImplementedError):
      p12_key_file = self._GetTestDataPathFor('service_account_key.p12')
      with self.assertRaisesRegex(
          auth_service_account.UnsupportedCredentialsType,
          r'PyOpenSSL is not available. If you have already installed '
          r'PyOpenSSL, you will need to enable site packages by setting the '
          r'environment variable CLOUDSDK_PYTHON_SITEPACKAGES to 1. If that '
          r'does not work, see https://developers.google.com/cloud/sdk/crypto '
          r'for details or consider using .json private key instead.'):
        self.Run('auth activate-service-account {0} --key-file={1}'.format(
            _SERVICE_ACCOUNT_EMAIL, p12_key_file))

  @TestOauth2clientAndGoogleAuth
  def testP12NoCrypto_WithSitePackages(self):
    with patch.dict(os.environ, {'CLOUDSDK_PYTHON_SITEPACKAGES': '1'}):
      with patch.object(service_account.ServiceAccountCredentials,
                        'from_p12_keyfile_buffer',
                        side_effect=NotImplementedError):
        p12_key_file = self._GetTestDataPathFor('service_account_key.p12')
        with self.assertRaisesRegex(
            auth_service_account.UnsupportedCredentialsType,
            r'PyOpenSSL is not available. See '
            r'https://developers.google.com/cloud/sdk/crypto for details or '
            r'consider using .json private key instead.'):
          self.Run('auth activate-service-account {0} --key-file={1}'.format(
              _SERVICE_ACCOUNT_EMAIL, p12_key_file))

  @TestOauth2clientAndGoogleAuth
  def testJSONPassword(self):
    """Make sure we can't specify a password when using a JSON key."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    with self.assertRaises(c_exc.InvalidArgumentException):
      self.Run(('auth activate-service-account {0} --key-file={1} '
                '--prompt-for-password').format(_SERVICE_ACCOUNT_EMAIL,
                                                json_key_file))

  @TestOauth2clientAndGoogleAuth
  def testJSONBadAccount(self):
    """Make sure we can't specify the wrong account for json keys."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    with self.assertRaises(c_exc.InvalidArgumentException):
      self.Run(
          'auth activate-service-account foo --key-file={0} '
          .format(json_key_file))

  @TestOauth2clientAndGoogleAuth
  def testJSONNoAccount(self):
    """Test service account auth with a JSON key not specifying an account."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run(
        'auth activate-service-account --key-file={0}'.format(json_key_file))
    self.AssertErrEquals(
        'Activated service account credentials for: [{0}]\n'.format(
            _SERVICE_ACCOUNT_EMAIL))
    self.AssertOutputEquals('')
    self.Run(
        'auth print-access-token --account={0}'.format(_SERVICE_ACCOUNT_EMAIL))

    self.AssertOutputEquals('test-access-token-25\n')

    # Check that internally scopes and user agent is set.
    creds_dict = json.loads(store.Load().to_json())
    self.assertEqual('google-cloud-sdk', creds_dict['user_agent'])
    self.assertEqual('google-cloud-sdk', creds_dict['_user_agent'])
    scopes = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/appengine.admin',
        'https://www.googleapis.com/auth/compute'

    ]
    self.assertEqual(' '.join(scopes), creds_dict['_scopes'])

  @TestOauth2clientAndGoogleAuth
  def testJSONWithRefreshError(self):
    self.refresh_mock.side_effect = store.TokenRefreshError('Can not refresh')
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    # Make sure refresh error propogates out of the command.
    with self.assertRaises(store.TokenRefreshError):
      self.Run(
          'auth activate-service-account --key-file={0}'.format(json_key_file))

  @TestOauth2clientAndGoogleAuth
  def testJSONBadKey(self):
    """Test that we validate the key file."""
    key_file = self.Touch(directory=self.temp_path, contents='{"foo": "bar"}')
    with self.assertRaisesRegex(
        auth_service_account.BadCredentialJsonFileException,
        r'The \.json key file is not in a valid format'):
      self.Run('auth activate-service-account --key-file={0}'.format(key_file))

  @TestOauth2clientAndGoogleAuth
  def testJSONPasswordFile(self):
    """Make sure we can't specify a password file when using a JSON key."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    with self.assertRaises(c_exc.InvalidArgumentException):
      self.Run(('auth activate-service-account {0} --key-file={1} '
                '--password-file=passwordfile').format(_SERVICE_ACCOUNT_EMAIL,
                                                       json_key_file))

  @TestOauth2clientAndGoogleAuth
  def testProject(self):
    """Make sure the project gets set."""
    project_prop = properties.VALUES.core.project
    account_prop = properties.VALUES.core.account
    properties.PersistProperty(project_prop, None)
    properties.PersistProperty(account_prop, None)

    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run('--project=junkproj auth activate-service-account {account} '
             '--key-file={key_file} '.format(
                 account=_SERVICE_ACCOUNT_EMAIL, key_file=json_key_file))
    self.assertEqual('junkproj', project_prop.Get())
    self.assertEqual(_SERVICE_ACCOUNT_EMAIL, account_prop.Get())

  @TestOauth2clientAndGoogleAuth
  def testLegacyFiles(self):
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run(
        'auth activate-service-account --key-file={0}'
        .format(json_key_file))

    paths = config.Paths()
    adc_path = paths.LegacyCredentialsAdcPath(_SERVICE_ACCOUNT_EMAIL)

    with open(adc_path) as f:
      json_key_file = json.load(f)

    self.assertEqual(
        json.loads("""
        {{
          "private_key_id": "{0}",
          "type": "service_account",
          "private_key": "{1}",
          "client_id": "{2}",
          "client_email": "{3}"}}
        """.format(_PRIVATE_KEY_ID, _PRIVATE_KEY.replace('\n', '\\n'),
                   _CLIENT_ID, _SERVICE_ACCOUNT_EMAIL)), json_key_file)

    self.AssertFileExistsWithContents(
        """
[Credentials]
gs_service_key_file = {0}
""".strip().format(paths.LegacyCredentialsAdcPath(_SERVICE_ACCOUNT_EMAIL)),
        paths.LegacyCredentialsGSUtilPath(_SERVICE_ACCOUNT_EMAIL))

    # Not SignedJwtAssertionCredentials
    self.AssertFileNotExists(
        paths.LegacyCredentialsP12KeyPath(_SERVICE_ACCOUNT_EMAIL))

    # Removes the generated file to ensure the second execution of this test
    # agsinst google-auth generates the file correctly.
    os.remove(adc_path)


class BadServiceAccountTest(cli_test_base.CliTestBase):

  def SetUp(self):
    # TODO(b/157745076): Activating service account via google-auth is enabled
    # only for Googlers at the moment. We need to mock IsHostGoogleDomain() to
    # to return True so that google-auth will invoked in the tests.
    # Remove this mock once it is enabled for everyone.
    self.StartObjectPatch(auth_util, 'IsHostGoogleDomain', return_value=True)

  @TestOauth2clientAndGoogleAuth
  def testNonExistentFile(self):
    with self.assertRaises(files.Error):
      key_file = self.Resource('tests', 'unit', 'surface', 'auth', 'test_data',
                               'does-not-exist-privatekey.json')
      self.Run(
          'auth activate-service-account {account} --key-file={key_file}'
          .format(
              account=('462803083913-lak0k1ette3muh3o3kb3pp2im3urj3e9'
                       '@developer.gserviceaccount.com'),
              key_file=key_file))

  @TestOauth2clientAndGoogleAuth
  def testBadJsonFile(self):
    with self.assertRaises(auth_service_account.BadCredentialFileException):
      key_file = self.Resource('tests', 'unit', 'surface', 'auth', 'test_data',
                               'bad_key_file.json')
      self.Run('auth activate-service-account --key-file={key_file}'
               .format(key_file=key_file))


# TODO(b/157745076): Removes this test class once activating service account
# via google-auth is enabled for everyone.
class GoogleAuthServiceAccountActivationEnableTest(cli_test_base.CliTestBase,
                                                   parameterized.TestCase):
  """Tests of enabling google-auth for service account activation."""

  def _GetTestDataPathFor(self, filename):
    return self.Resource('tests', 'unit', 'surface', 'auth', 'test_data',
                         filename)

  def SetUp(self):
    self.activate_creds_mock = self.StartObjectPatch(store,
                                                     'ActivateCredentials')

  @parameterized.parameters((False, True, True), (False, False, False),
                            (True, True, False), (True, False, False))
  def testEnableGoogleAuth(self, google_auth_disabled, is_host_google_domain,
                           expect_use_google_auth):
    """Test google-auth enabling logic.

    Args:
      google_auth_disabled: bool, True if google-auth is disabled for service
        account activation.
      is_host_google_domain: bool, whether the host on which gcloud runs is on
        Google domain.
      expect_use_google_auth: bool, True to expect google-auth is used to
        activate service account.
    """
    self.StartObjectPatch(
        properties.VALUES.auth.disable_activate_service_account_google_auth,
        'GetBool',
        return_value=google_auth_disabled)
    self.StartObjectPatch(
        auth_util, 'IsHostGoogleDomain', return_value=is_host_google_domain)

    # pylint:disable=unused-argument
    # This function must match the signature of store.ActivateCredentials.
    def _AssertCredentialsType(account, cred):
      if expect_use_google_auth:
        self.assertIsInstance(cred, google_auth_service_account.Credentials)
      else:
        self.assertIsInstance(cred, service_account.ServiceAccountCredentials)

    # pylint:enable=unused-argument

    # This is the core of verifying whether google-auth is enabled for
    # activating service account. If it is enabled, the credentials
    # passed to the credentials store (http://shortn/_yLO2MBbOEb) should be
    # google-auth. Otherwise, it will be oauth2client.
    self.activate_creds_mock.side_effect = _AssertCredentialsType

    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run('auth activate-service-account {0} --key-file={1}'.format(
        _SERVICE_ACCOUNT_EMAIL, json_key_file))

    self.activate_creds_mock.assert_called_once()


if __name__ == '__main__':
  test_case.main()
