# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Unit tests for path expansion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util


@test_case.Filters.DoNotRunOnPy2('Storage does not support python 2')
class CloudWildCardIteratorTest(cloud_storage_util.WithGCSCalls):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)

    self.messages = apis.GetMessagesModule('storage', 'v1')

    self.buckets_response = self.messages.Buckets(items=[
        self.messages.Bucket(name='bucket1'),
        self.messages.Bucket(name='bucket2'),
    ])

  def test_gcs_root_listing(self):
    self.apitools_client.buckets.List.Expect(
        self.messages.StorageBucketsListRequest(
            project=self.project,
            projection=(self.messages.StorageBucketsListRequest.
                        ProjectionValueValuesEnum.noAcl)
        ),
        response=self.buckets_response
    )
    bucket_iterator = wildcard_iterator.CloudWildcardIterator('gs://')
    actual = sorted([bucket.root_object.name for bucket in bucket_iterator])
    self.assertEqual(sorted({'bucket1', 'bucket2'}), actual)

  def test_gcs_bucket_url_with_wildcard(self):
    """Test bucket with no bucket-level expansion."""
    self.apitools_client.buckets.List.Expect(
        self.messages.StorageBucketsListRequest(
            project=self.project,
            projection=(self.messages.StorageBucketsListRequest.
                        ProjectionValueValuesEnum.noAcl)
        ),
        response=self.buckets_response
    )
    bucket_iterator = wildcard_iterator.CloudWildcardIterator('gs://bucket*')
    actual = []
    for bucket in bucket_iterator:
      self.assertIsInstance(bucket, resource_reference.BucketReference)
      actual.append(bucket.root_object.name)
    self.assertCountEqual(actual, ['bucket1', 'bucket2'])


if __name__ == '__main__':
  test_case.main()
