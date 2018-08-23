# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""e2e tests for Cloud Storage parallel file operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import filecmp

import os

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import transfer

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core.util import files
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.api_lib import storage_e2e_util


BUCKET_PREFIX = 'cloud-sdk-upload-test-bucket'


class UploadDownloadTest(e2e_base.WithServiceAuth):
  """Test uploading a small number of small files to Cloud Storage."""

  _GSUTIL_EXECUTABLE = files.FindExecutableOnPath('gsutil')

  def SetUp(self):
    self.storage_client = storage_api.StorageClient()
    self.files_to_upload = []
    self.object_path = next(e2e_utils.GetResourceNameGenerator(prefix='object'))
    self.bucket_name = next(e2e_utils.GetResourceNameGenerator(
        prefix=BUCKET_PREFIX))

  def _AssertFileUploaded(self, bucket_ref, expected_file):
    object_ = storage_util.ObjectReference(bucket_ref, expected_file)
    try:
      self.storage_client.GetObject(object_)
    except apitools_exceptions.HttpError as err:
      self.fail('Object [{}] not successfully uploaded:\n\n{}'.format(
          object_.ToUrl(), str(err)))

  def _TestUploadAndDownload(self, contents):
    with storage_e2e_util.CloudStorageBucket(self.storage_client,
                                             self.bucket_name,
                                             self.Project()) as bucket:
      file_path = self.Touch(
          self.temp_path, 'test_file', contents=contents.encode('utf-8'))
      with storage_e2e_util.GcsFile(self.storage_client, bucket, file_path,
                                    self.object_path):
        self._AssertFileUploaded(bucket, self.object_path)

        download_path = os.path.join(self.temp_path, 'download_file')
        self.storage_client.CopyFileFromGCS(bucket, self.object_path,
                                            download_path)

        # Now download again using ReadObject, the in-memory version of
        # CopyFileFromGCS
        object_ref = storage_util.ObjectReference(bucket, self.object_path)
        stream = self.storage_client.ReadObject(object_ref)

    # Check regular file download
    self.AssertFileExists(download_path)
    actual_contents = files.ReadFileContents(download_path)
    self.assertEqual(contents, actual_contents)

    # Check stream download
    self.assertEqual(stream.getvalue().decode('utf-8'), contents)

  def testCopyFileToAndFromGcs(self):
    self._TestUploadAndDownload('test file content.')

  def testCopyFileToAndFromGcs_NonAscii(self):
    self._TestUploadAndDownload('\u0394')

  @test_case.Filters.skip('Flaky.', 'b/38446187')
  def testCopyFileToAndFromGcs_LargeFile(self):
    """Tests file uploads that require chunking."""
    # Default chunk size isn't available as a constant
    # Need 10 multiples until issue with copied stream chunks appears.
    file_length = transfer.Upload(None, '').chunksize * 10
    # There's a check for large files accidentally left in the temporary
    # directory; we're okay with it in this case, since this deliberately tests
    # a large file.
    self._dirs_size_limit_method = file_length * 2
    file_path = self.Touch(self.temp_path, 'test_file',
                           contents=('.' * file_length))
    with storage_e2e_util.CloudStorageBucket(self.storage_client,
                                             self.bucket_name,
                                             self.Project()) as bucket:
      with storage_e2e_util.GcsFile(self.storage_client, bucket, file_path,
                                    self.object_path):
        self._AssertFileUploaded(bucket, self.object_path)
    # Don't run the download portion of the test as a time-saving measure

  @test_case.Filters.RunOnlyIf(_GSUTIL_EXECUTABLE, 'No gsutil found')
  def testRunGsutilCommand(self):
    self.assertEqual(0, storage_util.RunGsutilCommand('help'))

  @test_case.Filters.RunOnlyIf(_GSUTIL_EXECUTABLE, 'No gsutil found')
  def testGsutilCopy(self):
    file_length = 1024
    file_path = self.Touch(self.temp_path, 'test_file',
                           contents=('.' * file_length))
    with storage_e2e_util.CloudStorageBucket(self.storage_client,
                                             self.bucket_name,
                                             self.Project()) as bucket:
      # Test upload
      object_uri = 'gs://{bucket}/{object_path}'.format(
          bucket=self.bucket_name,
          object_path=self.object_path)
      exit_code = storage_util.RunGsutilCommand('cp', [file_path, object_uri])
      self.assertEqual(0, exit_code)
      self._AssertFileUploaded(bucket, self.object_path)

      # Test download
      download_file_path = os.path.join(self.temp_path, 'download_file')
      download_exit_code = storage_util.RunGsutilCommand(
          'cp', [object_uri, download_file_path])
      self.assertEqual(0, download_exit_code)
      self.assertTrue(os.path.exists(download_file_path))
      self.assertTrue(filecmp.cmp(file_path, download_file_path))

      # Try to clean up
      self.storage_client.DeleteObject(bucket, self.object_path)

if __name__ == '__main__':
  test_case.main()
