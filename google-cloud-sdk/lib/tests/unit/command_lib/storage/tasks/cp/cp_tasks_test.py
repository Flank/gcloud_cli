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
"""Tests for googlecloudsdk.command_lib.storage.tasks.cp."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks.cp import intra_cloud_copy_task
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.storage import mock_cloud_api


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class IntraCloudCopyTaskTest(sdk_test_base.SdkBase):
  """Tests logic of IntraCloudCopyTask."""

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self.default_projection = (self.messages.StorageBucketsGetRequest
                               .ProjectionValueValuesEnum.noAcl)
    self.source_metadata = self.messages.Object(name='hello')
    self.destination_metadata = self.messages.Object(name='greetings')

  @mock_cloud_api.patch_cloud_api
  def test_intra_cloud_copy(self, mock_client):
    source_reference = resource_reference.BucketResource(
        storage_url.storage_url_from_string('gs://b/o1.txt'),
        self.source_metadata)
    destination_reference = resource_reference.BucketResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'),
        self.destination_metadata)
    mock_client.CopyObject.expect([source_reference.metadata_object,
                                   destination_reference.metadata_object])

    task = intra_cloud_copy_task.IntraCloudCopyTask(source_reference,
                                                    destination_reference)
    task.execute()

  def test_local_to_cloud_copy(self):
    source_reference = resource_reference.BucketResource(
        storage_url.storage_url_from_string('file://o1.txt'),
        self.source_metadata)
    destination_reference = resource_reference.BucketResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'),
        self.destination_metadata)

    with self.assertRaises(ValueError):
      intra_cloud_copy_task.IntraCloudCopyTask(source_reference,
                                               destination_reference)

  def test_different_clouds_copy(self):
    source_reference = resource_reference.BucketResource(
        storage_url.storage_url_from_string('s3://b/o1.txt'),
        self.source_metadata)
    destination_reference = resource_reference.BucketResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'),
        self.destination_metadata)

    with self.assertRaises(ValueError):
      intra_cloud_copy_task.IntraCloudCopyTask(source_reference,
                                               destination_reference)


if __name__ == '__main__':
  test_case.main()
