# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for googlecloudsdk.api_lib.storage.storage_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import io
import string
import subprocess
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import config
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files as files_util
from tests.lib import subtests
from tests.lib import test_case
import mock


class RunGsutilCommandTest(subtests.Base):

  def _MockPopen(self):
    popen_mock = mock.MagicMock()
    popen_mock.stdin = io.StringIO()
    popen_mock.communicate.return_value = ('[]\n', '')
    popen_mock.returncode = 0
    return self.StartObjectPatch(subprocess, 'Popen',
                                 return_value=popen_mock, autospec=True)

  def _MockFindExecutableOnPath(self, return_value='/usr/bin/gsutil'):
    self.StartObjectPatch(files_util, 'FindExecutableOnPath',
                          return_value=return_value)

  def testUploadFileWithSpacesInFilename(self):
    popen_mock = self._MockPopen()
    self._MockFindExecutableOnPath()
    storage_util.RunGsutilCommand(
        'cp', ['my local file.txt', 'gs://bucket/my-file.txt'])
    self.assertEqual(popen_mock.call_count, 1)
    args, _ = popen_mock.call_args
    self.assertEqual(
        args[0][-3:], ['cp', 'my local file.txt', 'gs://bucket/my-file.txt'])

  def testUploadFileWithBackslashesInFilePath(self):
    popen_mock = self._MockPopen()
    self._MockFindExecutableOnPath()
    storage_util.RunGsutilCommand(
        'cp', ['C:\\Users\\foo\\file.txt', 'gs://bucket/my-file.txt'])
    self.assertEqual(popen_mock.call_count, 1)
    args, _ = popen_mock.call_args
    self.assertEqual(
        args[0][-3:],
        ['cp', 'C:\\Users\\foo\\file.txt', 'gs://bucket/my-file.txt'])

  def testRaisesErrorIfGsutilNotFound(self):
    mock_paths = mock.MagicMock()
    mock_paths.sdk_bin_path = None
    self.StartObjectPatch(config, 'Paths', return_value=mock_paths)
    self._MockFindExecutableOnPath(return_value=None)
    with self.assertRaisesRegex(
        storage_util.GsutilError,
        'A path to the storage client `gsutil` could not be found. Please '
        'check your SDK installation.'):
      storage_util.RunGsutilCommand('cp', [])


class BucketReferenceFromArgumentTest(subtests.Base):

  def RunSubTest(self, url, message=None):
    """Run a subtest for Argument().

    The reason this is so tricky is that it has to accommodate both error and
    non-error cases (because subtests doesn't allow for matching exception
    text).

    Roughly, what it does is the following:
      - If message is given, asserts that the Argument(url) call fails
        with an InvalidBucketNameError containing message as a substring
      - Otherwise, returns the bucket resulting from parsing Argument(url)

    Args:
      url: str, the url or name of the bucket to parse
      message: if a failure is expected, the message for the failure

    Returns:
      the bucket resulting from parsing FromBucketUrl(url) if message is None
    """
    # To prevent scope problems
    bucket_ref = None
    try:
      bucket_ref = storage_util.BucketReference.FromArgument(url)
    except argparse.ArgumentTypeError as err:
      if message:
        # Check that the expected ArgumentTypeError contains the right message
        # text
        self.assertIn(message, str(err))
      else:
        # ArgumentTypeError where none was expected
        raise
    else:
      # If there was no ArgumentTypeError but there was a message, fail.
      if message:
        self.fail('Should have raised ArgumentTypeError.')
      else:
        return bucket_ref.bucket

  def testArgument(self):
    bucket_ref = storage_util.BucketReference.FromArgument('gs://bucket-name/')
    self.assertEqual(
        bucket_ref,
        storage_util.BucketReference.FromArgument('gs://bucket-name'))

  def testArgumentValid(self):
    def T(name):
      # self.Run(name, name, depth=2)
      self.Run(name, 'gs://' + name, depth=2)
    # 3 characters minimum
    T('a' * 3)
    # 63 characters maximum (unless there are dot-separated components)
    T('a' * 63)
    # 222 characters maximum (each component can be up to 63 chars)
    T('.'.join(['a' * 63] * 3) + '.' + 'a' * 30)
    # Names may start and end with a number
    T('111')
    # Names contain lowercase letters, numbers, dashes, underscores, and dots
    T('a1-_.a')
    # Buckets with 'goog' at the start are okay (even though the API will reject
    # these when creating buckets), since some exist already
    T('goog')
    T('goog0')
    # Buckets with 'google' okay (even though the API will reject these when
    # creating buckets), since some exist already
    T('agooglea')
    # Things that aren't quite dotted-decimal IP addresses are okay
    T('1.2.3')
    T('1.2.3.4.5')
    T('1.2.3.a')
    # The following guideline is *only* a guideline:
    # - Also, for DNS compliance and future compatibility, you should not use
    #   underscores (_) or have a period adjacent to another period or dash. For
    #   example, ".." or "-." or ".-" are not valid in DNS names.
    T('aa_aa')
    T('a..aa')
    T('a-.aa')
    T('a.-aa')

  def testArgumentValidWithoutPrefix(self):
    bucket_ref = storage_util.BucketReference.FromArgument('foo',
                                                           require_prefix=False)

    self.assertEqual(bucket_ref.ToUrl(), 'gs://foo')

    with self.assertRaises(argparse.ArgumentTypeError):
      storage_util.BucketReference.FromArgument('foo')

  def testArgumentInvalid(self):
    def T(name, message):
      self.Run(None, 'gs://' + name, message=message, depth=2)

    T('', storage_util.VALID_BUCKET_LENGTH_MESSAGE)
    # This was a tricky one, because it usually makes it to the bucket-parsing
    # phase and fails with a bad message. Leave this case in.
    T('/', storage_util.VALID_BUCKET_LENGTH_MESSAGE)
    T('a' * 2, storage_util.VALID_BUCKET_LENGTH_MESSAGE)
    T('a' * 64, storage_util.VALID_BUCKET_LENGTH_MESSAGE)
    T('' + '.'.join(['a' * 63] * 3) + '.' + 'a' * 31,  # total chars: 223
      'Names containing dots can contain up to 222 characters')
    T('.'.join(['a' * 64] * 3) + '.' + 'a' * 27,  # total chars: 222
      'but each dot-separated component can be no longer than 63 characters.')

    valid_chars = set(string.ascii_lowercase + string.digits + '-_.')
    special_error_chars = set()
    for invalid_char in (set(string.printable)
                         - valid_chars
                         - special_error_chars):
      T('aaa' + invalid_char + 'aaa', storage_util.VALID_BUCKET_CHARS_MESSAGE)

    for ip_addr in ['0.0.0.0', '127.0.0.1', '192.168.5.4']:
      T(ip_addr, storage_util.VALID_BUCKET_DOTTED_DECIMAL_MESSAGE)


class BucketReferenceTest(subtests.Base):

  def testUrlConversion(self):
    """Test converting from/to gs:// URL and public reference URL."""
    bucket_ref = storage_util.BucketReference.FromUrl('gs://bucket-name/')
    self.assertEqual(bucket_ref.bucket, 'bucket-name')
    self.assertEqual(bucket_ref.ToUrl(), 'gs://bucket-name')
    self.assertEqual(bucket_ref.GetPublicUrl(),
                     'https://storage.googleapis.com/bucket-name')
    # Make sure that 'gs://' is optional
    self.assertEqual(
        bucket_ref,
        storage_util.BucketReference.FromUrl('bucket-name'))

  def RunSubTest(self, url, message=None):
    """Run a subtest for FromBucketUrl.

    The reason this is so tricky is that it has to accommodate both error and
    non-error cases (because subtests doesn't allow for matching exception
    text).

    Roughly, what it does is the following:
      - If message is given, asserts that the FromBucketUrl(url) call fails
        with an InvalidBucketNameError containing message as a substring
      - Otherwise, returns the bucket resulting from parsing FromBucketUrl(url)

    Args:
      url: str, the url or name of the bucket to parse
      message: if a failure is expected, the message for the failure

    Returns:
      the bucket resulting from parsing FromBucketUrl(url) if message is None
    """
    # To prevent scope problems
    bucket_ref = None
    try:
      bucket_ref = storage_util.BucketReference.FromUrl(url)
    except storage_util.InvalidBucketNameError as err:
      if message:
        # Check that the expected InvalidBucketNameError contains the right
        # message text
        self.assertIn(message, str(err))
      else:
        # InvalidBucketNameError where none was expected
        raise
    else:
      # If there was no InvalidBucketNameError but there was a message, fail.
      if message:
        self.fail('Should have raised InvalidBucketNameError.')
      else:
        return bucket_ref.bucket

  def testFromBucketUrl_InvalidNames(self):
    """Test that bucket names we think should be invalid *are* accepted."""
    def T(name):
      self.Run(name, name, depth=2)
      self.Run(name, 'gs://' + name, depth=2)

    T('a' * 2)
    T('a' * 64)
    T('' + '.'.join(['a' * 63] * 3) + '.' + 'a' * 31)  # total chars: 223
    T('.'.join(['a' * 64] * 3) + '.' + 'a' * 27)  # total chars: 222

    valid_chars = set(string.ascii_lowercase + string.digits + '-_.')
    special_error_chars = set('/')  # Handled in the _Error test case
    for invalid_char in (set(string.printable)
                         - valid_chars
                         - special_error_chars):
      T('aaa' + invalid_char + 'aaa')

    for ip_addr in ['0.0.0.0', '127.0.0.1', '192.168.5.4']:
      T(ip_addr)

  def testFromBucketUrl_Error(self):
    """Test that unparseable bucket names result in appropriate errors."""
    def T(name, exception):
      self.Run(name, name, exception=exception, depth=2)

    T('gs://', resources.RequiredFieldOmittedException)
    T('gs:///', resources.RequiredFieldOmittedException)
    T('gs://aaa/aaa', resources.WrongResourceCollectionException)

  def testFromBucketUrl_ValidNames(self):
    """Test that bucket names we think should be valid are accepted."""
    def T(name):
      self.Run(name, name, depth=2)
      self.Run(name, 'gs://' + name, depth=2)
    # 3 characters minimum
    T('a' * 3)
    # 63 characters maximum (unless there are dot-separated components)
    T('a' * 63)
    # 222 characters maximum (each component can be up to 63 chars)
    T('.'.join(['a' * 63] * 3) + '.' + 'a' * 30)
    # Names may start and end with a number
    T('111')
    # Names contain lowercase letters, numbers, dashes, underscores, and dots
    T('a1-_.a')
    # Buckets with 'goog' at the start are okay (even though the API will reject
    # these when creating buckets), since some exist already
    T('goog')
    T('goog0')
    # Buckets with 'google' okay (even though the API will reject these when
    # creating buckets), since some exist already
    T('agooglea')
    # Things that aren't quite dotted-decimal IP addresses are okay
    T('1.2.3')
    T('1.2.3.4.5')
    T('1.2.3.a')
    # The following guideline is *only* a guideline:
    # - Also, for DNS compliance and future compatibility, you should not use
    #   underscores (_) or have a period adjacent to another period or dash. For
    #   example, ".." or "-." or ".-" are not valid in DNS names.
    T('aa_aa')
    T('a..aa')
    T('a-.aa')
    T('a.-aa')


class ObjectReferenceTests(subtests.Base):

  def RunSubTest(self, url, message=None):
    # To prevent scope problems
    object_ref = None
    try:
      object_ref = storage_util.ObjectReference.FromUrl(url)
    except storage_util.InvalidObjectNameError as err:
      if message:
        # Check that the expected InvalidObjectNameError contains the right
        # message text
        self.assertIn(message, str(err))
      else:
        # InvalidObjectNameError where none was expected
        raise
    else:
      # If there was no InvalidObjectNameError but there was a message, fail.
      if message:
        self.fail('Should have raised InvalidObjectNameError.')
      else:
        return object_ref.ToUrl()

  def testObjectReference(self):
    object_ref = storage_util.ObjectReference.FromUrl('gs://bucket/object')
    self.assertEqual(object_ref.name, 'object')
    self.assertEqual(object_ref.bucket, 'bucket')
    self.assertEqual(object_ref.bucket_ref.ToUrl(), 'gs://bucket')
    self.assertEqual(object_ref.ToUrl(), 'gs://bucket/object')

  def testObjectReference_NoObject(self):
    for url in ['gs://bucket', 'gs://bucket/']:
      object_ref = storage_util.ObjectReference.FromUrl(url,
                                                        allow_empty_object=True)
      self.assertEqual(object_ref.name, '')
      self.assertEqual(object_ref.bucket, 'bucket')
      self.assertEqual(object_ref.bucket_ref.ToUrl(), 'gs://bucket')
      self.assertEqual(object_ref.ToUrl(), 'gs://bucket/')

  def testIsStorageUrl(self):
    def Good(path):
      self.assertTrue(
          storage_util.ObjectReference.IsStorageUrl(path),
          '[{}] is a valid storage URL but was called invalid.'.format(path))
    def Bad(path):
      self.assertFalse(
          storage_util.ObjectReference.IsStorageUrl(path),
          '[{}] is an invalid storage URL but was called valid.'.format(path))
    Bad('bucket')
    Bad('bucket/object')
    Bad('gs://bucket/')
    Bad('file:///bucket/')
    Bad('file:///bucket/object')
    Bad('http://www.example.com/')
    Bad('http://www.example.com/foo.tar.gz')
    Good('gs://bucket/path')
    Good('gs://bucket/path/to/object')

  def testObjectReference_BadBuckets(self):
    def T(url):
      self.Run(url, url, exception=ValueError)
    T('gs://')
    T('gs://bucket')
    T('gs:///')
    T('gs:///object')
    T('gs:///bucket/object')
    T('bucket/object')
    T('gs://a')

  def testObjectReference_ValidNames(self):
    def T(name):
      url = 'gs://bucket/' + name
      return self.Run(url, url, depth=2)
    T('a')
    T('a' * 1024)
    for valid_char in set(string.printable) - set('\r\n'):
      T(valid_char)

  def testObjectReference_InvalidNames(self):
    def T(name, message):
      url = 'gs://bucket/' + name
      return self.Run(None, url, message=message, depth=2)
    T('', 'Empty object name is not allowed')
    T('a' * 1025, 'of length 1-1024 bytes when UTF-8 encoded')
    T('a\na', 'must not contain Carriage Return or Line Feed characters')
    T('a\ra', 'must not contain Carriage Return or Line Feed characters')

  def testObjectReference_FromArgument(self):
    object_ref = storage_util.ObjectReference.FromArgument('gs://bucket/object')
    self.assertEqual(object_ref.ToUrl(), 'gs://bucket/object')
    object_ref = storage_util.ObjectReference.FromArgument(
        'gs://bucket', allow_empty_object=True)
    self.assertEqual(object_ref.ToUrl(), 'gs://bucket/')

  def testObjectReference_FromArgument_Error(self):
    with self.assertRaisesRegex(argparse.ArgumentTypeError,
                                'Must be of form gs://bucket/object'):
      storage_util.ObjectReference.FromArgument('asdf')
    with self.assertRaisesRegex(argparse.ArgumentTypeError,
                                'Empty object name is not allowed'):
      storage_util.ObjectReference.FromArgument('gs://bucket')

if __name__ == '__main__':
  test_case.main()
