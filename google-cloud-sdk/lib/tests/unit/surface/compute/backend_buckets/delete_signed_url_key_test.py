# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the backend buckets delete-signed-url-key alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import backend_buckets_test_base


class BackendBucketDeleteSignedUrlKeyTestGA(
    backend_buckets_test_base.BackendBucketsTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def testWithKeyNameArg(self):
    """Tests deleting a key is successful."""
    backend_bucket_ref = self.GetBackendBucketRef('backend-bucket-1')
    updated_backend_bucket = self.MakeBackendBucketMessage(
        backend_bucket_ref=backend_bucket_ref,
        gcs_bucket_name='gcs-bucket-1',
        enable_cdn=True,
        signed_url_key_names=['key1', 'key3'])
    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(operation_ref, backend_bucket_ref)

    self.ExpectDeleteSignedUrlKeyRequest(backend_bucket_ref, 'key2', operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(backend_bucket_ref, updated_backend_bucket)

    response = self.RunBackendBuckets('delete-signed-url-key ' +
                                      backend_bucket_ref.Name() +
                                      ' --key-name key2')
    self.assertEqual(response, updated_backend_bucket)

  def testWithoutKeyNameArg(self):
    """Tests failure when the key name argument is not specified."""
    backend_bucket_ref = self.GetBackendBucketRef('backend-bucket-1')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --key-name: Must be specified.'):
      self.RunBackendBuckets('delete-signed-url-key ' +
                             backend_bucket_ref.Name())


class BackendBucketDeleteSignedUrlKeyTestBeta(
    BackendBucketDeleteSignedUrlKeyTestGA):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class BackendBucketDeleteSignedUrlKeyTestAlpha(
    BackendBucketDeleteSignedUrlKeyTestBeta):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
