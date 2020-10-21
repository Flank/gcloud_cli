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

"""Unit tests for resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import textwrap

from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import s3_resource_reference
from tests.lib import test_case


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class S3BucketResourceTest(test_case.TestCase):
  """Tests for S3BucketResource."""

  def test_dumps_bucket_metadata_with_errors_in_correct_format(self):
    time = datetime.datetime(1111, 1, 1, tzinfo=datetime.timezone.utc)
    cors_error = errors.S3ApiError(
        'An error occurred () when calling the GetBucketCors operation: ')
    resource = s3_resource_reference.S3BucketResource(
        storage_url.CloudUrl(
            storage_url.ProviderPrefix.S3, bucket_name='bucket'),
        metadata={
            'Error': cors_error,
            'List': [{'TimeInListInDict': time}],
            'Nested': {'ZeroInt': 0, 'DoubleNested': {'NestedTime': time}},
            'String': 'abc',
            'Time': time})

    expected_dump = textwrap.dedent("""\
    {
      "url": "s3://bucket",
      "type": "cloud_bucket",
      "metadata": {
        "Error": "An error occurred () when calling the GetBucketCors operation: ",
        "List": [
          {
            "TimeInListInDict": "1111-01-01T00:00:00+0000"
          }
        ],
        "Nested": {
          "DoubleNested": {
            "NestedTime": "1111-01-01T00:00:00+0000"
          },
          "ZeroInt": 0
        },
        "String": "abc",
        "Time": "1111-01-01T00:00:00+0000"
      }
    }""")
    self.assertEqual(resource.get_metadata_dump(), expected_dump)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class S3ObjectResourceTest(test_case.TestCase):
  """Tests for S3ObjectResource."""

  def test_dumps_object_metadata_with_errors_in_correct_format(self):
    time = datetime.datetime(1111, 1, 1)
    cors_error = errors.S3ApiError(
        'An error occurred () when calling the GetBucketCors operation: ')
    resource = s3_resource_reference.S3ObjectResource(
        storage_url.CloudUrl(
            storage_url.ProviderPrefix.S3, bucket_name='bucket'),
        metadata={
            'Error': cors_error,
            'List': [{'TimeInListInDict': time}],
            'Nested': {'ZeroInt': 0, 'DoubleNested': {'NestedTime': time}},
            'String': 'abc',
            'Time': time})

    expected_dump = textwrap.dedent("""\
    {
      "url": "s3://bucket",
      "type": "cloud_object",
      "metadata": {
        "Error": "An error occurred () when calling the GetBucketCors operation: ",
        "List": [
          {
            "TimeInListInDict": "1111-01-01T00:00:00"
          }
        ],
        "Nested": {
          "DoubleNested": {
            "NestedTime": "1111-01-01T00:00:00"
          },
          "ZeroInt": 0
        },
        "String": "abc",
        "Time": "1111-01-01T00:00:00"
      }
    }""")
    self.assertEqual(resource.get_metadata_dump(), expected_dump)


if __name__ == '__main__':
  test_case.main()
