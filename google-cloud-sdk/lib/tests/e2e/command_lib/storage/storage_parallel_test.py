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
"""e2e tests for Cloud Storage parallel file operations.

This code is readily adaptable to do performance testing, especially for
determining what parallelism works best on different platforms.

It tests

- Small number of small files
- Moderate number of moderate files

with 16 threads (after experimentation, this was the point at which we hit
diminishing returns).

Adding more test cases is easy. To add a case for another number/size of files
to upload, subclass FewSmallFilesTest and change NUM_FILES/FILE_SIZE. To add a
case for a different type of parallelism (e.g. number of threads), add
a new test method to FewSmallFilesTest that invokes _RunTest().
"""
from __future__ import absolute_import
from __future__ import unicode_literals
import itertools

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.command_lib.storage import storage_parallel
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.api_lib import storage_e2e_util


BUCKET_PREFIX = 'cloud-sdk-parallel-upload-test-bucket'


_NUM_RETRIES = 100
_WAIT_MS = 1000


class FewSmallFilesTest(e2e_base.WithServiceAuth):
  """Test uploading a small number of small files to Cloud Storage."""

  NUM_FILES = 3
  FILE_SIZE = 2**10  # 1KB

  def SetUp(self):
    self.bucket_name = next(e2e_utils.GetResourceNameGenerator(
        prefix=BUCKET_PREFIX))
    self.storage_client = storage_api.StorageClient()
    self.file_path = self.Touch(self.temp_path, 'test_file',
                                contents=(' ' * self.FILE_SIZE))

  def _MakeFileUploadTasks(self, bucket_ref):
    tasks = []
    name_generator = e2e_utils.GetResourceNameGenerator(prefix='storage-file')
    for remote_file in itertools.islice(name_generator, self.NUM_FILES):
      task = storage_parallel.FileUploadTask(self.file_path,
                                             bucket_ref.ToBucketUrl(),
                                             remote_file)
      tasks.append(task)
    return tasks

  @retry.RetryOnException(max_retrials=_NUM_RETRIES, sleep_ms=_WAIT_MS)
  def _AssertFilesUploaded(self, bucket_ref, expected_files):
    remote_files = set(o.name for o in
                       self.storage_client.ListBucket(bucket_ref))
    self.assertSetEqual(set(remote_files), set(expected_files))

  def _RunTest(self, num_threads):
    with storage_e2e_util.CloudStorageBucket(self.storage_client,
                                             self.bucket_name,
                                             self.Project()) as bucket_ref:
      file_upload_tasks = self._MakeFileUploadTasks(bucket_ref)
      storage_parallel.UploadFiles(file_upload_tasks, num_threads)
      object_names = [f.remote_path for f in file_upload_tasks]
      self._AssertFilesUploaded(bucket_ref, object_names)

  def test16Threads(self):
    self._RunTest(16)


class ModerateNumberModerateFiles(FewSmallFilesTest):
  """Tests uploading a moderate number (20) of medium-sized (0.5MB) files."""
  NUM_FILES = 20
  FILE_SIZE = 2**19  # 0.5MB


if __name__ == '__main__':
  test_case.main()
