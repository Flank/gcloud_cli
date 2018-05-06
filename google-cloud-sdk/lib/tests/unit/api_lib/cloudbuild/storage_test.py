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
"""Tests that exercise cloudbuild interaction with Google Cloud Storage."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import exceptions as api_exceptions
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import e2e_base
from tests.lib import test_case
from tests.lib.apitools import http_error


# TODO(b/29358031): Move WithMockHttp somewhere more appropriate for unit tests.
class StorageTest(e2e_base.WithMockHttp):

  def SetUp(self):
    self.mocked_storage_v1 = mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_v1_messages = core_apis.GetMessagesModule(
        'storage', 'v1')

  def testCreateSuccess(self):
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name='bucket-456',
            ),
            project='proj-123',
        ),
        response='foo')

    client = storage_api.StorageClient()
    client.CreateBucketIfNotExists('bucket-456', 'proj-123')

  def testCreateAlreadyExists(self):

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name='bucket-456',
            ),
            project='proj-123',
        ),
        exception=http_error.MakeHttpError(
            code=409, url=('https://www.googleapis.com/storage/v1/buckets/'
                           'bucket-456?alt=json')))
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket='bucket-456',
        ),
        response='foo')

    client = storage_api.StorageClient()
    client.CreateBucketIfNotExists('bucket-456', 'proj-123')

  def testCreateForbidden(self):
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name='bucket-456',
            ),
            project='proj-123',
        ),
        exception=http_error.MakeHttpError(
            code=409, url=('https://www.googleapis.com/storage/v1/buckets/'
                           'bucket-456?alt=json')))
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket='bucket-456',
        ),
        exception=http_error.MakeHttpError(
            code=403, url=('https://www.googleapis.com/storage/v1/buckets/'
                           'bucket-456?alt=json')))

    client = storage_api.StorageClient()

    with self.assertRaisesRegex(api_exceptions.HttpError, 'Permission denied'):
      client.CreateBucketIfNotExists('bucket-456', 'proj-123')


if __name__ == '__main__':
  test_case.main()
