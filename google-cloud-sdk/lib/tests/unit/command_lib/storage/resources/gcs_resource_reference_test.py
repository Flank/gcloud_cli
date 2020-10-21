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

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import gcs_resource_reference
from tests.lib import test_case


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GcsBucketResourceTest(test_case.TestCase):
  """Tests for GcsBucketResource."""

  def test_dumps_bucket_metadata_with_nested_objects_in_correct_format(self):
    time = datetime.datetime(1111, 1, 1, tzinfo=datetime.timezone.utc)
    messages = apis.GetMessagesModule('storage', 'v1')
    apitools_bucket = messages.Bucket(
        acl=[messages.BucketAccessControl(bucket='bucket')],
        name='bucket',
        metageneration=0,
        retentionPolicy=messages.Bucket.RetentionPolicyValue(
            effectiveTime=time),
        timeCreated=time,
        website=messages.Bucket.WebsiteValue(notFoundPage='some_url'),
        zoneAffinity=['zebra_zone'],
    )
    resource = gcs_resource_reference.GcsBucketResource(
        storage_url.CloudUrl(
            storage_url.ProviderPrefix.GCS, bucket_name='bucket'),
        metadata=apitools_bucket)

    expected_dump = textwrap.dedent("""\
    {
      "url": "gs://bucket",
      "type": "cloud_bucket",
      "metadata": {
        "acl": [
          {
            "bucket": "bucket"
          }
        ],
        "metageneration": 0,
        "name": "bucket",
        "retentionPolicy": {
          "effectiveTime": "1111-01-01T00:00:00+0000"
        },
        "timeCreated": "1111-01-01T00:00:00+0000",
        "website": {
          "notFoundPage": "some_url"
        },
        "zoneAffinity": [
          "zebra_zone"
        ]
      }
    }""")
    self.assertEqual(resource.get_metadata_dump(), expected_dump)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GcsObjectResourceTest(test_case.TestCase):
  """Tests for GcsObjectResource."""

  def test_dumps_object_metadata_with_nested_objects_in_correct_format(self):
    time = datetime.datetime(1111, 1, 1)
    messages = apis.GetMessagesModule('storage', 'v1')
    apitools_customer_encryption = messages.Object.CustomerEncryptionValue(
        encryptionAlgorithm='md6')
    apitools_object = messages.Object(
        name='object',
        generation=0,
        acl=[messages.ObjectAccessControl(bucket='bucket')],
        timeCreated=time,
        customerEncryption=apitools_customer_encryption,
        eventBasedHold=False,
    )
    resource = gcs_resource_reference.GcsObjectResource(
        storage_url.CloudUrl(
            storage_url.ProviderPrefix.GCS, bucket_name='bucket'),
        metadata=apitools_object)

    expected_dump = textwrap.dedent("""\
    {
      "url": "gs://bucket",
      "type": "cloud_object",
      "metadata": {
        "acl": [
          {
            "bucket": "bucket"
          }
        ],
        "customerEncryption": {
          "encryptionAlgorithm": "md6"
        },
        "eventBasedHold": false,
        "generation": 0,
        "name": "object",
        "timeCreated": "1111-01-01T00:00:00"
      }
    }""")
    self.assertEqual(resource.get_metadata_dump(), expected_dump)


if __name__ == '__main__':
  test_case.main()
