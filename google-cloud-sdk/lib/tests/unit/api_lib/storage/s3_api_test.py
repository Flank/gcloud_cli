# Lint as: python3
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
"""Tests for googlecloudsdk.api_lib.storage.s3_api.S3Api."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import datetime
import itertools

from botocore import stub
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.storage import s3_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import storage_url
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.storage import test_base

SCHEME = 's3'
OWNER_NAME = 'owner_name'
OWNER_ID = 'owner_id'
BUCKET_NAME = 'bucket_name'


@test_case.Filters.DoNotRunOnPy2('Storage does not support python2')
class ListBucketsTest(test_base.StorageTestBase):

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)
    self.messages = apis.GetMessagesModule('storage', 'v1')

    num_buckets = 2
    self.names = ['bucket_name_%d' % i for i in range(num_buckets)]
    self.dates = [datetime.datetime(i + 1, 1, 1) for i in range(num_buckets)]

  def stub_list_buckets(self):
    s3_response = {
        'Buckets': [
            {'Name': name, 'CreationDate': date}
            for name, date in zip(self.names, self.dates)
        ],
        'Owner': {
            'DisplayName': OWNER_NAME,
            'ID': OWNER_ID
        }
    }

    self.stubber.add_response(
        method='list_buckets', expected_params={}, service_response=s3_response)

  def test_list_buckets_translates_bucket_messages(self):
    self.stub_list_buckets()

    with self.stubber:
      bucket_resources = self.s3_api.ListBuckets()

      observed_buckets = [i.metadata_object for i in bucket_resources]
      expected_buckets = []
      for name, date in zip(self.names, self.dates):
        expected_buckets.append(self.messages.Bucket(
            name=name, timeCreated=date, owner=self.messages.Bucket.OwnerValue(
                entity=OWNER_NAME, entityId=OWNER_ID)))
      self.assertCountEqual(observed_buckets, expected_buckets)

  def test_list_buckets_populates_cloud_urls(self):
    self.stub_list_buckets()

    with self.stubber:
      bucket_resources = self.s3_api.ListBuckets()

      observed_urls = [i.storage_url for i in bucket_resources]
      expected_urls = [
          storage_url.CloudUrl(scheme=SCHEME, bucket_name=name)
          for name in self.names
      ]
      self.assertCountEqual(observed_urls, expected_urls)


@test_case.Filters.DoNotRunOnPy2('Storage does not support python2')
class ListObjectsTest(test_base.StorageTestBase):

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)
    self.messages = apis.GetMessagesModule('storage', 'v1')

    self.expected_objects = []
    num_objects = 2
    for i in range(num_objects):
      self.expected_objects.append(
          self.messages.Object(
              name='object_name_%d' % i,
              updated=datetime.datetime(i + 1, 1, 1),
              etag='etag_%d' % i,
              size=i,
              storageClass='class_%d' % i,
              bucket=BUCKET_NAME))

  def stub_list_objects(self):
    s3_objects = []
    for obj in self.expected_objects:
      s3_objects.append({
          'Key': obj.name,
          'LastModified': obj.updated,
          'ETag': obj.etag,
          'Size': obj.size,
          'StorageClass': obj.storageClass
      })

    response = {'Contents': s3_objects, 'Name': BUCKET_NAME}
    self.stubber.add_response(
        'list_objects_v2',
        service_response=response,
        expected_params={'Bucket': BUCKET_NAME})

  def test_list_objects_translates_object_messages(self):
    self.stub_list_objects()

    with self.stubber:
      object_resources = self.s3_api.ListObjects(BUCKET_NAME)

      observed_objects = [i.metadata_object for i in object_resources]
      self.assertCountEqual(observed_objects, self.expected_objects)

  def test_list_objects_populates_cloud_urls(self):
    self.stub_list_objects()

    with self.stubber:
      object_resources = self.s3_api.ListObjects(BUCKET_NAME)

      observed_cloud_urls = [i.storage_url for i in object_resources]
      expected_cloud_urls = []
      for obj in self.expected_objects:
        expected_cloud_urls.append(
            storage_url.CloudUrl(
                scheme=SCHEME,
                bucket_name=BUCKET_NAME,
                object_name=obj.name))
      self.assertCountEqual(observed_cloud_urls, expected_cloud_urls)


MockCall = collections.namedtuple(
    'MockCall',
    ['function_name', 'api_method', 'args']
)

MockError = collections.namedtuple(
    'MockError',
    ['http_status_code', 'error_class']
)


@test_case.Filters.DoNotRunOnPy2('Storage does not support python2')
class ErrorTranslationTest(test_base.StorageTestBase, parameterized.TestCase):

  mock_calls = [
      MockCall(
          function_name='ListBuckets',
          api_method='list_buckets',
          args=()),
      MockCall(
          function_name='ListObjects',
          api_method='list_objects_v2',
          args=(BUCKET_NAME,)),
  ]

  mock_errors = [
      MockError(
          http_status_code=404,
          error_class=errors.S3ApiError),
  ]

  def SetUp(self):
    self.s3_api = s3_api.S3Api()
    self.stubber = stub.Stubber(self.s3_api.client)

  @parameterized.parameters(itertools.product(mock_calls, mock_errors))
  def test_error_translation(self, mock_call, mock_error):
    self.stubber.add_client_error(
        mock_call.api_method, http_status_code=mock_error.http_status_code)

    with self.stubber:
      with self.assertRaises(mock_error.error_class):
        cloud_api_function = getattr(self.s3_api, mock_call.function_name)
        next(cloud_api_function(*mock_call.args))


if __name__ == '__main__':
  test_case.main()
