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
"""Integration tests for backend buckets."""

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_test_base


class BackendBucketsTestBase(e2e_test_base.BaseTest):

  GSUTIL_BUCKET_PREFIX = 'gs://'

  def UniqueName(self, name):
    return e2e_utils.GetResourceNameGenerator(
        prefix='compute-backend-test-' + name).next()

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

    # Containers for created resources
    self.backend_bucket_names = []
    self.gcs_bucket_names = []

  @sdk_test_base.Retry(
      why=('gsutil may return a 409 even if bucket creation succeeds'),
      max_retrials=3,
      sleep_ms=300)
  def CreateGcsBucket(self):
    """Creates the specified GCS bucket."""
    name = self.UniqueName('gcs-bucket')
    storage_api.StorageClient().CreateBucketIfNotExists(name, self.Project())
    self.gcs_bucket_names.append(name)
    return name

  def CreateBackendBucketTest(self, cache_max_age_sec=None):
    """Creates and verifies the backend bucket resource."""
    gcs_bucket_name = self.CreateGcsBucket()
    name = self.UniqueName('bb')
    signed_url_args = '--signed-url-cache-max-age {0} '.format(
        cache_max_age_sec) if cache_max_age_sec else ''

    # Create the resource and verify the result.
    result = self.Run('compute backend-buckets create {0} '
                      '--description description '
                      '--gcs-bucket-name {1} --enable-cdn '
                      '{2}'.format(name, gcs_bucket_name, signed_url_args))
    self.backend_bucket_names.append(name)

    result_list = list(result)
    self.assertEqual(1, len(result_list))
    self.assertEqual(name, result_list[0].name)
    self.assertEqual('description', result_list[0].description)
    self.assertEqual(gcs_bucket_name, result_list[0].bucketName)
    self.assertTrue(result_list[0].enableCdn)
    if cache_max_age_sec:
      self.assertEqual(cache_max_age_sec,
                       result_list[0].cdnPolicy.signedUrlCacheMaxAgeSec)

    # Describe the resource and verify the fields.
    result = self.Run('compute backend-buckets describe {0}'.format(name))
    self.assertEqual(name, result.name)
    self.assertEqual('description', result.description)
    self.assertEqual(gcs_bucket_name, result.bucketName)
    self.assertTrue(result.enableCdn)
    if cache_max_age_sec:
      self.assertEqual(cache_max_age_sec,
                       result.cdnPolicy.signedUrlCacheMaxAgeSec)

    return name

  def UpdateDescriptionTest(self, backend_bucket_name):
    """Updates the description and verifies the result."""
    result = self.Run('compute backend-buckets update {0} '
                      '--description description2'.format(backend_bucket_name))
    self.assertEqual(1, len(result))
    self.assertEqual('description2', result[0].description)

  def UpdateGcsBucketTest(self, backend_bucket_name):
    """Updates the GCS bucket and verifies the result."""
    new_gcs_bucket_name = self.CreateGcsBucket()
    result = self.Run('compute backend-buckets update {0} '
                      '--gcs-bucket-name {1}'.format(backend_bucket_name,
                                                     new_gcs_bucket_name))
    self.assertEqual(1, len(result))
    self.assertEqual(new_gcs_bucket_name, result[0].bucketName)

  def UpdateEnableCdnTest(self, backend_bucket_name):
    """Updates Enable Cloud CDN and verifies the result."""
    result = self.Run(
        'compute backend-buckets update {0} --no-enable-cdn'.format(
            backend_bucket_name))
    self.assertEqual(1, len(result))
    self.assertFalse(result[0].enableCdn)

  def UpdateCdnSignedUrlCacheMaxAgeTest(self, backend_bucket_name,
                                        cache_max_age_sec):
    """Updates CDN Signed URL Cache Max Age and verifies the result."""
    result = self.Run(
        'compute backend-buckets update {0} --signed-url-cache-max-age {1}'.
        format(backend_bucket_name, cache_max_age_sec))
    self.assertEqual(1, len(result))
    self.assertEqual(cache_max_age_sec,
                     result[0].cdnPolicy.signedUrlCacheMaxAgeSec)

  def DeleteGcsBucket(self, name):
    """Deletes the specified GCS bucket."""
    bucket_ref = storage_util.BucketReference.FromBucketUrl(
        '{0}{1}/'.format(self.GSUTIL_BUCKET_PREFIX, name))
    storage_api.StorageClient().DeleteBucket(bucket_ref)

  def TearDown(self):
    # Delete the BackendBuckets
    self.DeleteResources(self.backend_bucket_names, self.DeleteBackendBucket,
                         'backend bucket')
    # Delete the GCS Buckets
    self.DeleteResources(self.gcs_bucket_names, self.DeleteGcsBucket,
                         'gcs bucket')


class BackendBucketsTestAlpha(BackendBucketsTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    super(BackendBucketsTestAlpha, self).SetUp()

  def testBackendBucket(self):
    """Tests backend bucket operations using Alpha API."""
    backend_bucket_name = self.CreateBackendBucketTest(
        cache_max_age_sec=33445566)
    self.UpdateDescriptionTest(backend_bucket_name)
    self.UpdateGcsBucketTest(backend_bucket_name)
    self.UpdateEnableCdnTest(backend_bucket_name)
    self.UpdateCdnSignedUrlCacheMaxAgeTest(
        backend_bucket_name, cache_max_age_sec=1234)


class BackendBucketsTestBeta(BackendBucketsTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    super(BackendBucketsTestBeta, self).SetUp()

  def testBackendBucket(self):
    """Tests backend bucket operations using Beta API."""
    backend_bucket_name = self.CreateBackendBucketTest()
    self.UpdateDescriptionTest(backend_bucket_name)
    self.UpdateGcsBucketTest(backend_bucket_name)
    self.UpdateEnableCdnTest(backend_bucket_name)


class BackendBucketsTestGA(BackendBucketsTestBase):

  def testBackendBucket(self):
    """Tests backend bucket operations using GA API."""
    backend_bucket_name = self.CreateBackendBucketTest()
    self.UpdateDescriptionTest(backend_bucket_name)
    self.UpdateGcsBucketTest(backend_bucket_name)
    self.UpdateEnableCdnTest(backend_bucket_name)


if __name__ == '__main__':
  e2e_test_base.main()
