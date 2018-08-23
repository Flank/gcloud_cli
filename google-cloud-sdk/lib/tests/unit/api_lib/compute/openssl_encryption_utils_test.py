# -*- coding: utf-8 -*- #
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

"""Unit tests for openssl_encryption_utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import subprocess
import tempfile

from googlecloudsdk.api_lib.compute import openssl_encryption_utils
from googlecloudsdk.core.util import files
from tests.lib import test_case
import mock


MESSAGE = b'This is a test'
STATIC_PUBLIC_KEY = (
    b'-----BEGIN PUBLIC KEY-----\n'
    b'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvjrnuNYG8QtewB/mcbS9\n'
    b'uqyN3gCG+RulSv4FZAFVib+nbdFpQemcFHfKVk3tve+J24U3TW87B49mat3tvPPl\n'
    b's5y0N6esYEDyvaynP5ELdQWGSf9V9Kr6b2yBreyq03WpzlMRdLZ7Mj8W6SzK9BpJ\n'
    b'kGSiXRqG40OGll0sk1Ii7zahSCY0G4zYhrthW67G22ZsXFZYCByaNi4cXjMMo54p\n'
    b'6KWLqLHk3/ibteP1JLBl4A0L9jgrVOS8JDKWQrF6OnxoeILbDU/la4ePSHCqUYwL\n'
    b't5cmWm03YKNirNxdkck7Yut47U/7iYN6JSmiAFespOUIcgTyhoBsg9EoE48gnOSv\n'
    b'cwIDAQAB\n'
    b'-----END PUBLIC KEY-----')
MODULUS = (
    b'vjrnuNYG8QtewB/mcbS9uqyN3gCG+RulSv4FZAFVib+nbdFpQemcFHfKVk3tve+'
    b'J24U3TW87B49mat3tvPPls5y0N6esYEDyvaynP5ELdQWGSf9V9Kr6b2yBreyq03'
    b'WpzlMRdLZ7Mj8W6SzK9BpJkGSiXRqG40OGll0sk1Ii7zahSCY0G4zYhrthW67G2'
    b'2ZsXFZYCByaNi4cXjMMo54p6KWLqLHk3/ibteP1JLBl4A0L9jgrVOS8JDKWQrF6'
    b'OnxoeILbDU/la4ePSHCqUYwLt5cmWm03YKNirNxdkck7Yut47U/7iYN6JSmiAFe'
    b'spOUIcgTyhoBsg9EoE48gnOSvcw==')
EXPONENT = b'AQAB'

PUBLIC_KEY_MODULUS_PAIRS = [
    (1024,
     b'-----BEGIN PUBLIC KEY-----\n'
     b'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC56QfbvIlN0GAmZP6yzUIGJ9gU\n'
     b'LvXJhGP5guhdxfcErxk1wGfPYEFmMtm9JmYmCvPoiF+IK4O04n15LMukUI5feJJs\n'
     b'oX56ovQO4Mniqn0HodFE2dMj4snY1PiHFqRQvk7mCaBMxTCb1LG8nzjndYPaLWDD\n'
     b'wgppeL+coWAm4HCR4wIDAQAB\n'
     b'-----END PUBLIC KEY-----\n',
     b'uekH27yJTdBgJmT+ss1CBifYFC71yYRj+YLoXcX3BK8ZNcBnz2BBZjLZvSZmJgrz'
     b'6IhfiCuDtOJ9eSzLpFCOX3iSbKF+eqL0DuDJ4qp9B6HRRNnTI+LJ2NT4hxakUL5O'
     b'5gmgTMUwm9SxvJ8453WD2i1gw8IKaXi/nKFgJuBwkeM='),
    (2045,
     b'-----BEGIN PUBLIC KEY-----\n'
     b'MIIBITANBgkqhkiG9w0BAQEFAAOCAQ4AMIIBCQKCAQAW9ONVet6xe5lwn5G/vG4l\n'
     b'sVrHVNe6eEqBbe0iKqCjk7CbxHcEUI9ArD3Tbi8krLtfnsHol9L0haoAgaKO2RhB\n'
     b'niRQsvP3uAaZt54+s6hu+//hdoT5m+6x2+LqILnc+kRxZPPag5J8w+TFLv7VrMOk\n'
     b'+uKyO4TW3+w3U1WuWoaa45I9rfMLB2Otu5TkC8ViybdGDyfnsn/BO/0CXs5Agobw\n'
     b'YaFqYMKo6KqvCQocDdZt02AExZmfc2SzPYb7/XbePDLtNz5F5RygQ7ITfTnkFiI/\n'
     b'o6u8MlVtpJmPqEoJ+t4NFaGesd5XUN9KgKF8qAztrgrwScH8dtAEQrVnTyX+BL8d\n'
     b'AgMBAAE=\n'
     b'-----END PUBLIC KEY-----\n',
     b'FvTjVXresXuZcJ+Rv7xuJbFax1TXunhKgW3tIiqgo5Owm8R3BFCPQKw9024vJKy7'
     b'X57B6JfS9IWqAIGijtkYQZ4kULLz97gGmbeePrOobvv/4XaE+Zvusdvi6iC53PpE'
     b'cWTz2oOSfMPkxS7+1azDpPrisjuE1t/sN1NVrlqGmuOSPa3zCwdjrbuU5AvFYsm3'
     b'Rg8n57J/wTv9Al7OQIKG8GGhamDCqOiqrwkKHA3WbdNgBMWZn3Nksz2G+/123jwy'
     b'7Tc+ReUcoEOyE3055BYiP6OrvDJVbaSZj6hKCfreDRWhnrHeV1DfSoChfKgM7a4K'
     b'8EnB/HbQBEK1Z08l/gS/HQ=='),
    (2050,
     b'-----BEGIN PUBLIC KEY-----\n'
     b'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEDCCpF/eMHOVtFzRTJffFD\n'
     b'ncT0J6JWJMqnFcGALh+GxMo63ujo71pOD/tgw0hdb1YT/9yyMSjyCLFW2L/Cev5Y\n'
     b'E3e9GmAGMW6Hckn5LbRBRgE53hg3w9NTwBOY6cESTux+NIQHPdoLFmQI0840wl2u\n'
     b'PRLIjsE/xtE2mcyWB9t5l0uHvReP4Inh5npw/5QZGdC6hNzlZ2eDsVeQo+WQmr8m\n'
     b'4leQG142sNg+gSe9lq8rbusaltIhkvZKjhVd25vVIah0js0m3ok3btZXHKC7w4eo\n'
     b'k6fi4xMnAe4/NN4QbhdpaXwoQ86QJPOyhvQPNyJKSsVUDq89Kk+IMNXLbk5ig5fL\n'
     b'KwIDAQAB\n'
     b'-----END PUBLIC KEY-----\n',
     b'AwgqRf3jBzlbRc0UyX3xQ53E9CeiViTKpxXBgC4fhsTKOt7o6O9aTg/7YMNIXW9W'
     b'E//csjEo8gixVti/wnr+WBN3vRpgBjFuh3JJ+S20QUYBOd4YN8PTU8ATmOnBEk7s'
     b'fjSEBz3aCxZkCNPONMJdrj0SyI7BP8bRNpnMlgfbeZdLh70Xj+CJ4eZ6cP+UGRnQ'
     b'uoTc5Wdng7FXkKPlkJq/JuJXkBteNrDYPoEnvZavK27rGpbSIZL2So4VXdub1SGo'
     b'dI7NJt6JN27WVxygu8OHqJOn4uMTJwHuPzTeEG4XaWl8KEPOkCTzsob0DzciSkrF'
     b'VA6vPSpPiDDVy25OYoOXyys='),
    (4096,
     b'-----BEGIN PUBLIC KEY-----\n'
     b'MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAy78flNI4F4I44vxeFq9B\n'
     b'aqBXZGjmkELfatGSlsGwOBP9Xmhwh8jkCijdCgYcMEdpBWhHFwd50lJyO6wWQPCh\n'
     b'6/p3i4nA/mgQ9/3S6EMw+HPKO/IEpv7uOv7j0vT27jDoyopEDHU5a7IJctWq8Xyc\n'
     b'4euyd/xTG6v8X++UdJL1keS5Ftw3/FZfWt4iaDKzl/EPPNvYlh6YdVevxjmmyuHn\n'
     b'5gT+y8Qqj++zSe8wMls5t2/sTCcVi8p5ZP0HQvpmQVyAwlhNN6WmleE5r2LJpjtf\n'
     b'CfHwLOzgGEiS0zGSSAGOSdFwVA7rqCt1xvtYdyrphNXqi1vVERDvWox7sCypQeyN\n'
     b'kqMvYozqwOw1r0FgMVvgj7WTyT6rhfNmRR88o2+k/FvcTVZZJ0aJe0Hp3KwShq7k\n'
     b'klCwWHlNwdt2jRtCO8aHQiPGfEzpBBzJYAgmLq8xX7EzJ+ht1MVjMTIC//dkfUSy\n'
     b'mYgrVcUc7hBOuRpvoxo2Ze5zDsYXUf2Zj5vcBbbM/5bZmHwoE42y0NhAsaxilFyb\n'
     b'BNdDUpiFs0MMg28HcOUCXoUj5Ax3P4WmcUh4PDGqqenrGqCoIp1vkMmrDmQOIxHP\n'
     b'hMJT9edx8sYgzbk2fbB5Fty/byMlr6hlPmm7P8/qfctE/9b4qoiy+dxDe7rYnP4k\n'
     b'CfesnGxEEzpu66fb4M4S36sCAwEAAQ==\n'
     b'-----END PUBLIC KEY-----\n',
     b'y78flNI4F4I44vxeFq9BaqBXZGjmkELfatGSlsGwOBP9Xmhwh8jkCijdCgYcMEdp'
     b'BWhHFwd50lJyO6wWQPCh6/p3i4nA/mgQ9/3S6EMw+HPKO/IEpv7uOv7j0vT27jDo'
     b'yopEDHU5a7IJctWq8Xyc4euyd/xTG6v8X++UdJL1keS5Ftw3/FZfWt4iaDKzl/EP'
     b'PNvYlh6YdVevxjmmyuHn5gT+y8Qqj++zSe8wMls5t2/sTCcVi8p5ZP0HQvpmQVyA'
     b'wlhNN6WmleE5r2LJpjtfCfHwLOzgGEiS0zGSSAGOSdFwVA7rqCt1xvtYdyrphNXq'
     b'i1vVERDvWox7sCypQeyNkqMvYozqwOw1r0FgMVvgj7WTyT6rhfNmRR88o2+k/Fvc'
     b'TVZZJ0aJe0Hp3KwShq7kklCwWHlNwdt2jRtCO8aHQiPGfEzpBBzJYAgmLq8xX7Ez'
     b'J+ht1MVjMTIC//dkfUSymYgrVcUc7hBOuRpvoxo2Ze5zDsYXUf2Zj5vcBbbM/5bZ'
     b'mHwoE42y0NhAsaxilFybBNdDUpiFs0MMg28HcOUCXoUj5Ax3P4WmcUh4PDGqqenr'
     b'GqCoIp1vkMmrDmQOIxHPhMJT9edx8sYgzbk2fbB5Fty/byMlr6hlPmm7P8/qfctE'
     b'/9b4qoiy+dxDe7rYnP4kCfesnGxEEzpu66fb4M4S36s=')
]

_OPEN_SSL_EXECUTABLE = files.FindExecutableOnPath('openssl')


@test_case.Filters.RunOnlyIf(_OPEN_SSL_EXECUTABLE, 'No openssl found')
@test_case.Filters.DoNotRunOnWindows(
    'Windows uses Windows Crypto APIs instead of OpenSSL')
class OpensslEncryptionUtilsTest(test_case.TestCase):

  def SetUp(self):
    self.crypt = openssl_encryption_utils.OpensslCrypt(_OPEN_SSL_EXECUTABLE)

  def testStripKey(self):
    expected_output = (
        b'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvjrnuNYG8QtewB/mcbS9'
        b'uqyN3gCG+RulSv4FZAFVib+nbdFpQemcFHfKVk3tve+J24U3TW87B49mat3tvPPl'
        b's5y0N6esYEDyvaynP5ELdQWGSf9V9Kr6b2yBreyq03WpzlMRdLZ7Mj8W6SzK9BpJ'
        b'kGSiXRqG40OGll0sk1Ii7zahSCY0G4zYhrthW67G22ZsXFZYCByaNi4cXjMMo54p'
        b'6KWLqLHk3/ibteP1JLBl4A0L9jgrVOS8JDKWQrF6OnxoeILbDU/la4ePSHCqUYwL'
        b't5cmWm03YKNirNxdkck7Yut47U/7iYN6JSmiAFespOUIcgTyhoBsg9EoE48gnOSv'
        b'cwIDAQAB')
    stripped_key = openssl_encryption_utils.StripKey(STATIC_PUBLIC_KEY)
    self.assertEqual(stripped_key, expected_output)

    bad_key = STATIC_PUBLIC_KEY.strip(b'-')
    with self.assertRaisesRegex(
        openssl_encryption_utils.OpenSSLException,
        ('The following key does not appear to be in PEM format:')):
      openssl_encryption_utils.StripKey(bad_key)

  def testEncryptDecrypt(self):
    key = self.crypt.GetKeyPair()
    public_key = self.crypt.GetPublicKey(key)

    # Encrypt with public key.
    with tempfile.NamedTemporaryFile() as tf:
      tf.write(public_key)
      tf.flush()
      openssl_args = ['rsautl', '-encrypt', '-pubin',
                      '-oaep', '-inkey', tf.name]
      encrypted_message = self.crypt.RunOpenSSL(openssl_args, cmd_input=MESSAGE)
    encoded_message = base64.b64encode(encrypted_message)

    message = self.crypt.DecryptMessage(key, encoded_message)
    self.assertEqual(message, MESSAGE)

  def testEncryptDecryptWithVariousKeyLengths(self):
    for key_length in [1024, 2045, 2050, 4096]:
      key = self.crypt.GetKeyPair(key_length=key_length)
      public_key = self.crypt.GetPublicKey(key)

      # Encrypt with public key.
      with tempfile.NamedTemporaryFile() as tf:
        tf.write(public_key)
        tf.flush()
        openssl_args = ['rsautl', '-encrypt', '-pubin',
                        '-oaep', '-inkey', tf.name]
        encrypted_message = self.crypt.RunOpenSSL(openssl_args,
                                                  cmd_input=MESSAGE)
      encoded_message = base64.b64encode(encrypted_message)

      message = self.crypt.DecryptMessage(key, encoded_message)
      self.assertEqual(message, MESSAGE)

  def testGetModulusExponent(self):
    modulus, exponent = self.crypt.GetModulusExponentFromPublicKey(
        STATIC_PUBLIC_KEY)
    self.assertEqual(modulus, MODULUS)
    self.assertEqual(exponent, EXPONENT)

  def testGetModulusExponentVarious(self):
    for key_mod_pair in PUBLIC_KEY_MODULUS_PAIRS:
      key_length, public_key, expected_modulus = key_mod_pair
      modulus, exponent = self.crypt.GetModulusExponentFromPublicKey(
          public_key, key_length=key_length)
      self.assertEqual(modulus, expected_modulus)
      self.assertEqual(exponent, EXPONENT)

  @mock.patch.object(subprocess, 'Popen')
  def testOpenSSLError(self, subprocess_mock):
    error_msg = 'openssl returned an error'
    subprocess_mock.side_effect = OSError(1, error_msg)

    with self.assertRaisesRegex(openssl_encryption_utils.OpenSSLException,
                                error_msg):
      openssl_args = ['genrsa', 'foo']
      self.crypt.RunOpenSSL(openssl_args)

  @mock.patch.object(subprocess, 'Popen')
  def testOpenSSLNonZeroExit(self, subprocess_mock):
    mock_communicate = mock.Mock()
    mock_communicate.communicate.return_value = ('This is stdout',
                                                 'This is stderr')
    mock_communicate.returncode.return_value = 1
    subprocess_mock.return_value = mock_communicate

    with self.assertRaisesRegex(openssl_encryption_utils.OpenSSLException,
                                'This is stderr'):
      openssl_args = ['rsautil', '-decrypt']
      self.crypt.RunOpenSSL(openssl_args)

if __name__ == '__main__':
  test_case.main()
