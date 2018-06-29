# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the sign-url subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
import base64
import calendar
import hashlib
import hmac
import time

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import sign_url_utils
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import test_case

import httplib2
import mock


class SignUrlTestsBase(cli_test_base.CliTestBase):
  """A base test class for testing 'sign-url' command."""

  # Arbitrary 128-bit key generated using:
  # print ''.join('\\x{:02x}'.format(x) for x in bytearray(os.urandom(16)))
  KEY = bytearray(b'\x54\xe9\x99\x62\xbc\xe1\xec\x2a'
                  b'\x9f\x03\x71\xba\xaa\x76\xf5\x99')

  # Name of the Signed URL key.
  KEY_NAME = 'key1'

  # Fake current timestamp.
  TIME_NOW = float(
      calendar.timegm(
          time.strptime('2017 Jan 15 22:37:45', '%Y %b %d %H:%M:%S')))

  def SetUp(self):
    self._SetUpReleaseTrack()
    self.key_file = self.Touch(
        self.temp_path, 'test.key', contents=base64.urlsafe_b64encode(self.KEY))
    self.key_file_with_new_line = self.Touch(
        self.temp_path,
        'test2.key',
        contents=base64.urlsafe_b64encode(self.KEY) + b'\n\n\r\n')

  def _GetExpectedUrlToSign(self, input_url, has_query_params, expires):
    """Gets the expected URL string that will be used for signing."""
    return '{0}{1}Expires={2}&KeyName={3}'.format(input_url, '&'
                                                  if has_query_params else '?',
                                                  expires, self.KEY_NAME)

  def _GetExpectedSignature(self, url_to_sign):
    """Gets the expected signature for the URL to sign."""
    signature = hmac.new(self.KEY, url_to_sign.encode('utf-8'),
                         hashlib.sha1).digest()
    return base64.urlsafe_b64encode(signature)

  def _GetExpectedSignedUrl(self, input_url, has_query_params,
                            expected_expires_in_seconds):
    """Gets the expected Signed URL for the given input URL and parameters."""
    expected_expires = str(int(self.TIME_NOW + expected_expires_in_seconds))
    expected_url_to_sign = self._GetExpectedUrlToSign(
        input_url, has_query_params, expected_expires)
    expected_signature = self._GetExpectedSignature(expected_url_to_sign)
    expected_signed_url = '{url}&Signature={signature}'.format(
        url=expected_url_to_sign, signature=expected_signature)
    return expected_signed_url

  def _RunSignUrl(self, args_list):
    with mock.patch('time.time') as mock_time:
      mock_time.return_value = self.TIME_NOW
      return self.Run(' '.join(['compute sign-url'] + args_list))


class SigningTestsBeta(SignUrlTestsBase):
  """Tests related to signing the URL using beta 'sign-url' command."""

  def _SetUpReleaseTrack(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _VerifySignedUrl(self, input_url, has_query_params,
                       expected_expires_in_seconds, actual_signed_url):
    """Verifies the actual Signed URL matches the expectation."""
    self.assertTrue(actual_signed_url.startswith(input_url))

    expected_signed_url = self._GetExpectedSignedUrl(
        input_url, has_query_params, expected_expires_in_seconds)
    self.assertEqual(actual_signed_url, expected_signed_url)

  def testSigningSuccessUrlWithoutQueryParams(self):
    """Verfies Signed URL for a URL without query parameters."""
    input_url = 'https://www.example.com/foo/bar'
    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, '--expires-in', '60',
        input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=False,
        expected_expires_in_seconds=60,
        actual_signed_url=result['signedUrl'])

  def testSigningSuccessHttpsUrlWithQueryParams(self):
    """Verifies Signed URL for a HTTPS URL with query parameters."""
    input_url = 'https://www.example.com/foo/bar?q1=abc&q2=def'
    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
        '480', input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=True,
        expected_expires_in_seconds=480,
        actual_signed_url=result['signedUrl'])

  def testSigningSuccessHttpUrlWithQueryParams(self):
    """Verifies Signed URL for a HTTP URL with query parameters."""
    input_url = 'http://www.example.com/foo/bar?q1=abc'
    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, ' --expires-in',
        '1234', input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=True,
        expected_expires_in_seconds=1234,
        actual_signed_url=result['signedUrl'])

  def testSigningSuccessUrlWithEmptyQueryParams(self):
    """Verifies Signed URL for a URL with empty query parameters."""
    input_url = 'https://www.example.com/foo/bar?q1='
    result = self._RunSignUrl([
        '--key-name key1', '--key-file ', self.key_file, '--expires-in',
        '987654321', input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=True,
        expected_expires_in_seconds=987654321,
        actual_signed_url=result['signedUrl'])

  def testSigningSuccessKeyFileWithNewLine(self):
    """Verifies Signed URL when using a key file which contains a new line."""
    input_url = 'https://www.example.com/foo/bar?q1=abc'
    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file_with_new_line,
        '--expires-in', '1234', input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=True,
        expected_expires_in_seconds=1234,
        actual_signed_url=result['signedUrl'])

  def testSigningSuccessExpiresInSeconds(self):
    """Verifies Signed URL when --expires-in is set in seconds."""
    input_url = 'https://www.example.com/foo/bar?q1=abc'
    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
        '5678s', input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=True,
        expected_expires_in_seconds=5678,
        actual_signed_url=result['signedUrl'])

  def testSigningSuccessExpiresInMinutes(self):
    """Verifies Signed URL when --expires-in is set in minutes."""
    input_url = 'https://www.example.com/foo/bar?q1=abc'
    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
        '240m', input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=True,
        expected_expires_in_seconds=240 * 60,
        actual_signed_url=result['signedUrl'])

  def testSigningSuccessExpiresInHours(self):
    """Verifies Signed URL when --expires-in is set in hours."""
    input_url = 'https://www.example.com/foo/bar?q1=abc'
    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
        '14h', input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=True,
        expected_expires_in_seconds=14 * 60 * 60,
        actual_signed_url=result['signedUrl'])

  def testSigningSuccessExpiresInDays(self):
    """Verifies Signed URL when --expires-in is set in days."""
    input_url = 'https://www.example.com/foo/bar?q1=abc'
    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
        '151d', input_url
    ])
    self._VerifySignedUrl(
        input_url=input_url,
        has_query_params=True,
        expected_expires_in_seconds=151 * 24 * 60 * 60,
        actual_signed_url=result['signedUrl'])

  def testSigningFailureWithoutKeyName(self):
    """Verifies failure when signing a URL without a key name."""
    input_url = 'https://www.example.com/foo/bar?q1=abc&q2=def'
    with self.AssertRaisesArgumentErrorMatches(
        'argument --key-name: Must be specified.'):
      self._RunSignUrl(
          ['--key-file', self.key_file, '--expires-in', '1234', input_url])

  def testSigningFailureWithoutKeyFile(self):
    """Verifies failure when signing a URL without a key file."""
    input_url = 'https://www.example.com/foo/bar?q1=abc&q2=def'
    with self.AssertRaisesArgumentErrorMatches(
        'argument --key-file: Must be specified.'):
      self._RunSignUrl(
          ['--key-name', 'key1', '--expires-in', '1234', input_url])

  def testSigningFailureInvalidKeyFile(self):
    """Verifies failure when signing a URL with a non-existing key file."""
    input_url = 'https://www.example.com/foo/bar?q1=abc&q2=def'
    with self.assertRaisesRegex(
        files.Error,
        r'Unable to read file \[non-existent-file\]: '
        r'.*No such file or directory'):
      self._RunSignUrl([
          '--key-name', 'key1', '--key-file', 'non-existent-file',
          '--expires-in', '1234', input_url
      ])

  def testSigningFailureInvalidUrlSchema(self):
    """Verifies failure when signing a HTTP URL."""
    input_url = 'ftp://www.example.com/foo/bar'
    with self.assertRaisesRegex(
        sign_url_utils.InvalidCdnSignedUrlError,
        sign_url_utils._URL_SCHEME_MUST_BE_HTTP_HTTPS_MESSAGE):
      self._RunSignUrl([
          '--key-name', 'key1', '--key-file', self.key_file, ' --expires-in',
          '1234', input_url
      ])

  def testSigningFailureUrlWithoutScheme(self):
    """Verifies failure when signing a URL without a scheme."""
    input_url = 'www.example.com/foo/bar?q1=abc'
    with self.assertRaisesRegex(
        sign_url_utils.InvalidCdnSignedUrlError,
        sign_url_utils._URL_SCHEME_MUST_BE_HTTP_HTTPS_MESSAGE):
      self._RunSignUrl([
          '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
          '1234', input_url
      ])

  def testSigningFailureUrlWithFragment(self):
    """Verifies failure when signing a URL with a fragment."""
    input_url = '\'https://www.example.com/foo/bar?q1=abc#frag\''
    with self.assertRaisesRegex(
        sign_url_utils.InvalidCdnSignedUrlError,
        sign_url_utils._URL_MUST_NOT_HAVE_FRAGMENT_MESSAGE):
      self._RunSignUrl([
          '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
          '1234', input_url
      ])

  def testSigningFailureUrlWithExpiresQuery(self):
    """Verifies failure when signing a URL containing an 'Expires' query."""
    input_url = 'https://www.example.com/foo/bar?q1=abc&Expires=future&q2=def'
    with self.assertRaisesRegex(
        sign_url_utils.InvalidCdnSignedUrlError,
        sign_url_utils._URL_MUST_NOT_HAVE_PARAM_MESSAGE.format('Expires')):
      self._RunSignUrl([
          '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
          '1234', input_url
      ])

  def testSigningFailureUrlWithKeyNameQuery(self):
    """Verifies failure when signing a URL containing a 'Name' query."""
    input_url = 'https://www.example.com/foo/bar?q1=abc&KeyName=someKey&q2=def'
    with self.assertRaisesRegex(
        sign_url_utils.InvalidCdnSignedUrlError,
        sign_url_utils._URL_MUST_NOT_HAVE_PARAM_MESSAGE.format('KeyName')):
      self._RunSignUrl([
          '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
          '1234', input_url
      ])

  def testSigningFailureUrlWithSignatureQuery(self):
    """Verifies failure when signing a URL containing a 'Signature' query."""
    input_url = 'https://www.example.com/foo/bar?q1=abc&Signature=sig&q2=def'
    with self.assertRaisesRegex(
        sign_url_utils.InvalidCdnSignedUrlError,
        sign_url_utils._URL_MUST_NOT_HAVE_PARAM_MESSAGE.format('Signature')):
      self._RunSignUrl([
          '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
          '1234', input_url
      ])


class SigningTestsAlpha(SigningTestsBeta):
  """Tests related to signing the URL using alpha 'sign-url' command."""

  def _SetUpReleaseTrack(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class ValidationTestsBeta(SignUrlTestsBase):
  """Tests related to validating the URL using beta 'sign-url' command."""

  def SetUp(self):
    super(ValidationTestsBeta, self).SetUp()
    self.http_request_mock = self.StartObjectPatch(
        httplib2.Http, 'request', autospec=True)
    self.http_response_mock = self.StartObjectPatch(
        httplib2, 'Response', autospec=True)

  def _SetUpReleaseTrack(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _MockResponseForRequest(self, url, response_code):
    """Mocks the response for the specified request URL."""
    self.http_response_mock.status = response_code
    response_body = ''
    self.http_request_mock.return_value = (self.http_response_mock,
                                           response_body)

  def _VerifyValidationRequest(self, expected_signed_url):
    """Verifies the HEAD request was sent for the specified Signed URL."""
    self.http_request_mock.assert_called_once()
    args, kwargs = self.http_request_mock.call_args
    self.assertEqual(args[1], expected_signed_url)
    self.assertEqual(kwargs['method'], 'HEAD')

  def testValidationSuccess(self):
    """Verifies successful validation for a Signed URL."""
    input_url = 'https://www.example.com/foo/bar?q1=abc'
    expected_signed_url = self._GetExpectedSignedUrl(input_url, True, 300)
    self._MockResponseForRequest(expected_signed_url, 200)

    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
        '300', input_url, '--validate'
    ])
    self._VerifyValidationRequest(expected_signed_url)
    self.assertEqual(result['validationResponseCode'], 200)

  def testValidationFailure(self):
    """Verifies validation failure for a Signed URL."""
    input_url = 'https://www.example.com/foo/bar?q1=abc'
    expected_signed_url = self._GetExpectedSignedUrl(input_url, True, 300)
    self._MockResponseForRequest(expected_signed_url, 403)

    result = self._RunSignUrl([
        '--key-name', 'key1', '--key-file', self.key_file, '--expires-in',
        '300', input_url, '--validate'
    ])
    self._VerifyValidationRequest(expected_signed_url)
    self.assertEqual(result['validationResponseCode'], 403)


class ValidationTestsAlpha(ValidationTestsBeta):
  """Tests related to validating the URL using alpha 'sign-url' command."""

  def _SetUpReleaseTrack(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
