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
"""Tests for the backend buckets create subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class BackendBucketCreateGaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')

  def RunCreate(self, command):
    """Runs the compute backend-buckets create command with the arguments."""
    self.Run('compute backend-buckets create ' + command)

  def testSimpleCase(self):
    messages = self.messages
    self.make_requests.side_effect = [[
        messages.BackendBucket(
            name='my-backend-bucket', bucketName='gcs-bucket-1', enableCdn=True)
    ]]

    self.RunCreate("""
        my-backend-bucket
          --gcs-bucket-name gcs-bucket-1
          --description "My backend bucket"
          --enable-cdn
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Insert',
          messages.ComputeBackendBucketsInsertRequest(
              backendBucket=messages.BackendBucket(
                  bucketName='gcs-bucket-1',
                  description='My backend bucket',
                  enableCdn=True,
                  name='my-backend-bucket'),
              project='my-project'))])

    self.AssertOutputEquals("""\
      NAME               GCS_BUCKET_NAME  ENABLE_CDN
      my-backend-bucket  gcs-bucket-1     True
      """, normalize_space=True)

  def testWithoutDescription(self):
    messages = self.messages
    self.RunCreate("""
        my-backend-bucket
          --gcs-bucket-name gcs-bucket-1
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Insert',
          messages.ComputeBackendBucketsInsertRequest(
              backendBucket=messages.BackendBucket(
                  bucketName='gcs-bucket-1',
                  enableCdn=False,
                  name='my-backend-bucket'),
              project='my-project'))])

  def testWithoutBucketName(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --gcs-bucket-name: Must be specified.'):
      self.RunCreate("""
          my-backend-bucket
          """)

    self.CheckRequests()

  def testWithEnableCdnFalse(self):
    messages = self.messages
    self.RunCreate("""
        my-backend-bucket
          --gcs-bucket-name gcs-bucket-1
          --no-enable-cdn
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Insert',
          messages.ComputeBackendBucketsInsertRequest(
              backendBucket=messages.BackendBucket(
                  bucketName='gcs-bucket-1',
                  enableCdn=False,
                  name='my-backend-bucket'),
              project='my-project'))])


class BackendBucketCreateBetaTest(BackendBucketCreateGaTest):

  def SetUp(self):
    self.SelectApi('beta')

  def RunCreate(self, command):
    """Runs the compute backend-buckets create command with the arguments."""
    self.Run('beta compute backend-buckets create ' + command)

  def CheckRequestMadeWithCdnPolicy(self, expected_cdn_policy):
    """Verifies the request was made with the expected CDN policy."""
    messages = self.messages
    self.CheckRequests([(self.compute.backendBuckets, 'Insert',
                         messages.ComputeBackendBucketsInsertRequest(
                             backendBucket=messages.BackendBucket(
                                 bucketName='gcs-bucket-1',
                                 cdnPolicy=expected_cdn_policy,
                                 enableCdn=False,
                                 name='my-backend-bucket'),
                             project='my-project'))])

  def testCreateWithoutCacheMaxAge(self):
    """Tests creating backend bucket without cache max age."""
    self.RunCreate('my-backend-bucket --gcs-bucket-name gcs-bucket-1')
    self.CheckRequestMadeWithCdnPolicy(None)

  def testCreateWithCacheMaxAgeSeconds(self):
    """Tests creating backend bucket with cache max age in seconds."""
    self.RunCreate('my-backend-bucket --gcs-bucket-name gcs-bucket-1 '
                   '--signed-url-cache-max-age 7890')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(signedUrlCacheMaxAgeSec=7890))

  def testCreateWithCacheMaxAgeMinutes(self):
    """Tests creating backend bucket with cache max age in minutes."""
    self.RunCreate('my-backend-bucket --gcs-bucket-name gcs-bucket-1 '
                   '--signed-url-cache-max-age 234m')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(signedUrlCacheMaxAgeSec=234 * 60))

  def testCreateWithCacheMaxAgeHours(self):
    """Tests creating backend bucket with cache max age in hours."""
    self.RunCreate('my-backend-bucket --gcs-bucket-name gcs-bucket-1 '
                   '--signed-url-cache-max-age 38h')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(
            signedUrlCacheMaxAgeSec=38 * 60 * 60))

  def testCreateWithCacheMaxAgeDays(self):
    """Tests creating backend bucket with cache max age in days."""
    self.RunCreate('my-backend-bucket --gcs-bucket-name gcs-bucket-1 '
                   '--signed-url-cache-max-age 99d')
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendBucketCdnPolicy(
            signedUrlCacheMaxAgeSec=99 * 24 * 60 * 60))

  def testSetInvalidCacheMaxAge(self):
    """Tests creating backend bucket with an invalid cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --signed-url-cache-max-age: given value must be of the form '
        r'INTEGER\[UNIT\] where units can be one of s, m, h, d; received: '
        r'invalid-value'):
      self.RunCreate('my-backend-bucket --gcs-bucket-name gcs-bucket-1 '
                     '--signed-url-cache-max-age invalid-value')

  def testSetCacheMaxAgeNegative(self):
    """Tests creating backend bucket with a negative cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --signed-url-cache-max-age: given value must be of the form '
        r'INTEGER\[UNIT\] where units can be one of s, m, h, d; received: -1'):
      self.RunCreate('my-backend-bucket --gcs-bucket-name gcs-bucket-1 '
                     '--signed-url-cache-max-age -1')


class BackendBucketCreateAlphaTest(BackendBucketCreateBetaTest):

  def SetUp(self):
    self.SelectApi('alpha')

  def RunCreate(self, command):
    """Runs the compute backend-buckets create command with the arguments."""
    self.Run('alpha compute backend-buckets create ' + command)


if __name__ == '__main__':
  test_case.main()
