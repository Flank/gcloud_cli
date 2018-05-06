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
"""Tests for the backend buckets add-signed-url-key alpha command."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import backend_buckets_test_base


class BackendBucketAddSignedUrlKeyTestBeta(
    backend_buckets_test_base.BackendBucketsTestBase):

  # Arbitrary base64url encoded 128-bit key.
  # Generated using:
  # base64.urlsafe_b64encode(bytearray(os.urandom(16)))
  KEY = '1KKDjXtxmwHrltVtXJPoLQ=='

  def SetUp(self):
    self._SetUpReleaseTrack()
    self.key_file = self.Touch(self.temp_path, 'test.key', contents=self.KEY)
    self.key_file_with_new_line = self.Touch(
        self.temp_path, 'test2.key', contents=self.KEY + '\n\n\r\n')

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)

  def testValidKey(self):
    """Tests adding a valid key is successful."""
    backend_bucket_ref = self.GetBackendBucketRef('backend-bucket-1')
    updated_backend_bucket = self.MakeBackendBucketMessage(
        backend_bucket_ref=backend_bucket_ref,
        gcs_bucket_name='gcs-bucket-1',
        enable_cdn=True,
        signed_url_key_names=['key1'])
    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(operation_ref, backend_bucket_ref)

    self.ExpectAddSignedUrlKeyRequest(backend_bucket_ref, 'key1', self.KEY,
                                      operation)
    self.ExpectOperationGetRequest(operation_ref, operation)
    self.ExpectGetRequest(backend_bucket_ref, updated_backend_bucket)

    response = self.RunBackendBuckets(
        'add-signed-url-key ' + backend_bucket_ref.Name() +
        ' --key-name key1 --key-file ' + self.key_file)
    self.assertEqual(response, updated_backend_bucket)

  def testValidKeyWithNewLine(self):
    """Tests adding a valid key with a newline is successful."""
    backend_bucket_ref = self.GetBackendBucketRef('backend-bucket-1')
    updated_backend_bucket = self.MakeBackendBucketMessage(
        backend_bucket_ref=backend_bucket_ref,
        gcs_bucket_name='gcs-bucket-1',
        enable_cdn=True,
        signed_url_key_names=['key1'])
    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(operation_ref, backend_bucket_ref)

    self.ExpectAddSignedUrlKeyRequest(backend_bucket_ref, 'key1', self.KEY,
                                      operation)
    self.ExpectOperationGetRequest(operation_ref, operation)
    self.ExpectGetRequest(backend_bucket_ref, updated_backend_bucket)

    response = self.RunBackendBuckets(
        'add-signed-url-key ' + backend_bucket_ref.Name() +
        ' --key-name key1 --key-file ' + self.key_file_with_new_line)
    self.assertEqual(response, updated_backend_bucket)

  def testWithoutKeyNameArg(self):
    """Tests failure when key name argument is not specified."""
    backend_bucket_ref = self.GetBackendBucketRef('backend-bucket-1')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --key-name: Must be specified.'):
      self.RunBackendBuckets('add-signed-url-key ' + backend_bucket_ref.Name() +
                             ' --key-file ' + self.key_file_with_new_line)

  def testWithoutKeyFileArg(self):
    """Tests failure when key file argument is not specified."""
    backend_bucket_ref = self.GetBackendBucketRef('backend-bucket-1')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --key-file: Must be specified.'):
      self.RunBackendBuckets('add-signed-url-key ' + backend_bucket_ref.Name() +
                             ' --key-name key1')

  def testKeyFileDoesNotExist(self):
    """Tests failure when key file does not exist."""
    backend_bucket_ref = self.GetBackendBucketRef('backend-bucket-1')
    with self.AssertRaisesToolExceptionRegexp(
        r'Could not read key from file \[non-existent-file\]: '
        r'No such file or directory'):
      self.RunBackendBuckets('add-signed-url-key ' + backend_bucket_ref.Name() +
                             ' --key-name key1 '
                             '--key-file non-existent-file')


class BackendBucketAddSignedUrlKeyTestAlpha(
    BackendBucketAddSignedUrlKeyTestBeta):

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
