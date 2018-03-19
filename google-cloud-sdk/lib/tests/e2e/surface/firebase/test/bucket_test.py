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

from googlecloudsdk.api_lib.firebase.test import results_bucket
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.firebase.test import e2e_base


class ResultsBucketOpsIntegrationTests(e2e_base.TestIntegrationTestBase):
  """Integration tests for ResultsBucketOps.

  These tests use a pre-existing, empty bucket with read-only public access
  (i.e. gs://bucket-for-gcloud-e2e-testing-public) and another with no public
  ACLs (i.e. gs://bucket-for-gcloud-e2e-testing-private).
  """

  PROJECT_ID = 'cloud-test-example'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT_ID)

  def _CreateBucketOps(self, bucket_name):
    gcs_client = core_apis.GetClientInstance('storage', 'v1')
    return results_bucket.ResultsBucketOps(
        self.PROJECT_ID, bucket_name, 'unique-object_wxyz', None,
        core_apis.GetMessagesModule('toolresults', 'v1beta3'), gcs_client)

  def testBucketCreation_HaveAccessToExistingBucket(self):
    # Test a bucket that already exists for which we have read privileges.
    self._CreateBucketOps('bucket-for-gcloud-e2e-testing-public')
    self.AssertOutputEquals('')
    self.AssertErrNotContains('Creating results bucket')

  def testBucketCreation_DontHaveAccessToExistingBucket(self):
    # Test a bucket that already exists but for which we have no privileges.
    with self.assertRaises(exceptions.BadFileException):
      self._CreateBucketOps('bucket-for-gcloud-e2e-testing-private')

    self.AssertOutputEquals('')
    self.AssertErrNotContains('Creating results bucket')

  def testBucketCreation_TriesToCreateBucketThatDoesNotExist(self):
    bucket_name = 'bucket-we-know-does-not-exist-xyz'

    with self.assertRaises(exceptions.BadFileException):
      # Note: this will still raise a BadFileEx because the test doesn't have
      # privileges to actually create a bucket in the project, which is great
      # because the bucket still won't exist the next time this test is run.
      # Even so, this test verifies that the method TRIES to create the bucket.
      self._CreateBucketOps(bucket_name)
    self.AssertErrContains('Creating results bucket')

  def testUploadApkToGcs_FileDoesNotExist_BucketExists(self):
    bucket_ops = self._CreateBucketOps('bucket-for-gcloud-e2e-testing-public')

    with self.assertRaises(exceptions.BadFileException) as ex_ctx:
      bucket_ops.UploadFileToGcs('missing-file.apk')
    self.AssertErrContains('Uploading [missing-file.apk]')
    self.assertIn('[missing-file.apk] not found', ex_ctx.exception.message)

  def testUploadApkToGcs_FileExists_BucketNotWritable(self):
    apk_path = self.Touch(directory=self.temp_path,
                          name='my-app.apk', contents='blah, blah, blah')

    with self.assertRaises(exceptions.BadFileException) as ex_ctx:
      bucket_ops = self._CreateBucketOps(
          'bucket-for-gcloud-e2e-testing-private')
      bucket_ops.UploadFileToGcs(apk_path)
    msg = ex_ctx.exception.message
    self.assertIn('[bucket-for-gcloud-e2e-testing-private]', msg)
    self.assertIn('error 403', msg)


if __name__ == '__main__':
  test_case.main()
