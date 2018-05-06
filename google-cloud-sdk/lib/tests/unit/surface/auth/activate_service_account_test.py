# Copyright 2015 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals

import filecmp
import json
import os

from googlecloudsdk.api_lib.auth import service_account as auth_service_account
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import test_case

from mock import patch
from oauth2client import client
from oauth2client import service_account


class ServiceAuthTestJSON(cli_test_base.CliTestBase):

  def SetUp(self):
    def _Refresh(cred):
      cred.access_token = 'test-access-token-25'
    self.refresh_mock = self.StartObjectPatch(
        store, 'Refresh', side_effect=_Refresh)

  def _GetTestDataPathFor(self, filename):
    return self.Resource(
        'tests', 'unit', 'surface', 'auth', 'test_data', filename)

  def Account(self):
    return 'inactive@developer.gserviceaccount.com'

  @patch.object(client, 'HAS_CRYPTO', False)
  def testJSONCryptoNotRequired(self):
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run(
        'auth activate-service-account {0} --key-file={1}'
        .format(self.Account(), json_key_file))

  def testJSONFromStdin(self):
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    contents = files.GetFileContents(json_key_file)
    self.WriteInput(contents)
    self.Run('auth activate-service-account {0} --key-file=-'
             .format(self.Account()))

    self.AssertErrEquals('Activated service account credentials for: [{0}]\n'
                         .format(self.Account()))

  def testP12CryptoRequired(self):
    try:
      import OpenSSL  # pylint: disable=g-import-not-at-top,unused-variable
    except ImportError:
      raise self.SkipTest('Needs PyOpenSSL installed.')

    p12_key_file = self._GetTestDataPathFor('service_account_key.p12')
    self.Run(
        'auth activate-service-account {0} --key-file={1}'
        .format(self.Account(), p12_key_file))

    # Check that internally scopes and user agent is set.
    creds_dict = json.loads(store.Load().to_json())
    self.assertEqual('google-cloud-sdk', creds_dict['_user_agent'])
    self.assertEqual('google-cloud-sdk', creds_dict['user_agent'])
    scopes = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/appengine.admin',
        'https://www.googleapis.com/auth/compute'

    ]
    self.assertEqual(' '.join(scopes), creds_dict['_scopes'])

    paths = config.Paths()
    expected_legacy_file = paths.LegacyCredentialsP12KeyPath(self.Account())

    self.AssertFileExists(expected_legacy_file)
    self.assertTrue(filecmp.cmp(p12_key_file, expected_legacy_file),
                    'original and saved P12 keys are different in {0} and {1}'
                    .format(p12_key_file, expected_legacy_file))

    self.AssertFileNotExists(paths.LegacyCredentialsAdcPath(self.Account()))
    self.AssertFileNotExists(
        paths.LegacyCredentialsBqPath(self.Account()))

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
        self.Run(
            'auth activate-service-account {0} --key-file={1}'
            .format(self.Account(), p12_key_file))

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
          self.Run(
              'auth activate-service-account {0} --key-file={1}'
              .format(self.Account(), p12_key_file))

  def testJSONPassword(self):
    """Make sure we can't specify a password when using a JSON key."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    with self.assertRaises(c_exc.InvalidArgumentException):
      self.Run(
          ('auth activate-service-account {0} --key-file={1} '
           '--prompt-for-password').format(self.Account(), json_key_file))

  def testJSONBadAccount(self):
    """Make sure we can't specify the wrong account for json keys."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    with self.assertRaises(c_exc.InvalidArgumentException):
      self.Run(
          'auth activate-service-account foo --key-file={0} '
          .format(json_key_file))

  def testJSONNoAccount(self):
    """Test service account auth with a JSON key not specifying an account."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run(
        'auth activate-service-account --key-file={0}'.format(json_key_file))
    self.AssertErrEquals('Activated service account credentials for: [{0}]\n'
                         .format(self.Account()))
    self.AssertOutputEquals('')
    self.Run('auth print-access-token --account={0}'.format(self.Account()))

    self.AssertOutputEquals('test-access-token-25\n')

    # Check that internally scopes and user agent is set.
    creds_dict = json.loads(store.Load().to_json())
    self.assertEqual('google-cloud-sdk', creds_dict['user_agent'])
    self.assertEqual('google-cloud-sdk', creds_dict['_user_agent'])
    scopes = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/appengine.admin',
        'https://www.googleapis.com/auth/compute'

    ]
    self.assertEqual(' '.join(scopes), creds_dict['_scopes'])

  def testJSONWithRefreshError(self):
    self.refresh_mock.side_effect = store.TokenRefreshError('Can not refresh')
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    # Make sure refresh error propogates out of the command.
    with self.assertRaises(store.TokenRefreshError):
      self.Run(
          'auth activate-service-account --key-file={0}'.format(json_key_file))

  def testJSONBadKey(self):
    """Test that we validate the key file."""
    key_file = self.Touch(directory=self.temp_path, contents='{"foo": "bar"}')
    with self.assertRaisesRegex(
        auth_service_account.BadCredentialJsonFileException,
        r'The \.json key file is not in a valid format\.'):
      self.Run('auth activate-service-account --key-file={0}'.format(key_file))

  def testJSONPasswordFile(self):
    """Make sure we can't specify a password file when using a JSON key."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    with self.assertRaises(c_exc.InvalidArgumentException):
      self.Run(
          ('auth activate-service-account {0} --key-file={1} '
           '--password-file=passwordfile').format(self.Account(),
                                                  json_key_file))

  def testProject(self):
    """Make sure the project gets set."""
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run(
        '--project=junkproj auth activate-service-account {account} '
        '--key-file={key_file} '.format(account=self.Account(),
                                        key_file=json_key_file))
    self.assertEqual('junkproj', properties.VALUES.core.project.Get())
    self.assertEqual(self.Account(), properties.VALUES.core.account.Get())

  def testLegacyFiles(self):
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run(
        'auth activate-service-account --key-file={0}'
        .format(json_key_file))

    paths = config.Paths()

    with open(paths.LegacyCredentialsAdcPath(self.Account())) as f:
      json_key_file = json.load(f)

    self.assertEqual(json.loads(r"""
        {
          "private_key_id": "294b4cce6389e0491d1c055585764d5631a3b0b4",
          "type": "service_account",
          "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEwAIBADANBgkqhkiG9w0BAQEFAASCBKowggSmAgEAAoIBAQDUPbMTOYxjab1E\niLxq8wQ3gYFTWAo5EvHBbRcn/bj8tgsXf0+XMwCjj328vg9TFj3Hi4aHeo4MbxXF\nw1vt0URqu0y18cmRXF6ntY3vyGThXFQyUvQPWjEdpvXY0GYgRo3+XvlaupEX/Ftj\ngR6sV3lDmQPoiMaDAB/nFP8L3NyddZpJDb90eV2gvQXSlN2oXP+a0ReNVJ8xfPvC\nY8pz9mzxrmo7u9ci/Xb8S6W+zglNn5Ur63cttotLrAQejaqdwxbREfvV7fGwJGjD\nXuXhBXaKvDq7BWrQE6PBJxlhKEEO5euYuM44enNBnps1Zzx5XzqJXtF3yfhnZSLn\nEJy/6UoZAgMBAAECggEBAIhIPg6gK1dCdHfnXSVHenOxwrsjkxzm3zmWtQHG19vd\ngO3Ln+20oDpmTxS87dYqN+1D2FRyC3hMdCySrxrb/xSRxEYoRYgDSfxihgtsH+rd\ngGr3/SNGhLdHmCFqX8llxJOLpI3vsm82afBQ3sNHP+R6App0CRPhJpsZTlPts/Oe\nfaBnQz/5scxIxna33T2S8SIG45dUcDri+6JMCsWgn7lMf80E94rc2ZQosjbcv5Uw\nT1GSo8k4OKIW8lF0x08MTtgallDAbPETyyUOwj8K8eIVDgMCg4M7zrjLQTkw1DrN\nchjXnHtz5KgLegi/P+TcO3P90g72DV2zCwwm7bhZD+kCgYEA/4EENBTSung4LZlz\nhaZ/aqMr+wqVzKNWGmezudMjmhcFJHPr6YqElWbJt88U99db3X31gFxMv+NcCwf1\n0P46/BPwt6LtyQnJVoIFVrjpeHOjbzb2nP0OrUFUNuyp9Hz/0flOrIbjrofzy/0n\nn/xS4a8BBmRwcfxPpKUkvDVKQL8CgYEA1KcuhW3CMkNtoD9FvzJZTQ5fTREYiuW7\nlCxGD90dAhLbotjBe5gthJAzgB9NFfnou05Rhco/PHusFbOyBBxEaNKCpXOspfU6\nZv3GxZ2630QCvHP7fgMbPYyfkLRCQoW/ChiiJryGSCmpPU2ITbVRjKtxmbLB5sGD\njH9Z8CTE0ycCgYEAlUA9P1smmcyeLGzmIZ1X8ufsShIt3UNQic4oG5Wtx1ZJJ7kb\nhunmdwt7LAconXpM7H6myVuhbboXS05UFshblmLji7H+KyCvXvxGuBj+MOGEB/RY\nbO4aA7UUx5zJzsqx+WsjvP5yw8Ig9Pkli3wuwiyjcaN8V+lmcKwTYGnUvSsCgYEA\np68E0hYQkc31vezmtLOhE1AH+h9G+Q/acCbRQGUdIKt6IdlGCI2hJu0Gjzsfb/rW\neAxz4Enwv2LN+XbvIqqfjwCgIJMsStkqqlfmy6Fq3+8jMTNL1rvgWRJwKIzbytTo\nJa/y/RSf1ntzhnGCz7PwkDoIpCf/GlTxxHIPm3uC8PUCgYEAkUDRxj3i8mPXMje9\nJjVxQ9w4EVBqsjLiOdMYp5TFwK7ScDOVSpmJraaQbRE9C2roFwpUJkXpyJW6P/fy\nWHueM8fHJqzYuWN2zpRvHdjS93xn7Z9ADiLV4UV43XVXZAcV8obQaPbDzANFhNUe\nR59I27S9QkZQMX7Dojkpa6lz5/Q=\n-----END PRIVATE KEY-----\n",
          "client_id": "999999999999999999999",
          "client_email": "inactive@developer.gserviceaccount.com"}
        """), json_key_file)

    self.AssertFileExistsWithContents("""
[Credentials]
gs_service_key_file = {0}
""".strip().format(paths.LegacyCredentialsAdcPath(self.Account())),
                                      paths.LegacyCredentialsGSUtilPath(
                                          self.Account()))

    # Not SignedJwtAssertionCredentials
    self.AssertFileNotExists(paths.LegacyCredentialsP12KeyPath(self.Account()))


class BadServiceAccountTest(cli_test_base.CliTestBase):

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

  def testBadJsonFile(self):
    with self.assertRaises(auth_service_account.BadCredentialFileException):
      key_file = self.Resource('tests', 'unit', 'surface', 'auth', 'test_data',
                               'bad_key_file.json')
      self.Run('auth activate-service-account --key-file={key_file}'
               .format(key_file=key_file))


if __name__ == '__main__':
  test_case.main()
