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
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_factory
from googlecloudsdk.command_lib.storage.tasks.cp import file_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_upload_task
from googlecloudsdk.command_lib.storage.tasks.cp import intra_cloud_copy_task
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.storage import mock_cloud_api

import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class FileDownloadTaskTest(sdk_test_base.SdkBase):
  """Tests logic of FileDownloadTask."""

  @mock_cloud_api.patch
  @mock.patch.object(files, 'BinaryFileWriter')
  def test_execute_downloads_file(self, mock_client, mock_file_writer):
    source_url = storage_url.storage_url_from_string('gs://b/o1.txt')
    source_resource = resource_reference.ObjectResource(source_url, None)
    destination_resource = resource_reference.FileObjectResource(
        storage_url.storage_url_from_string('file://o2.txt'))

    mock_stream = mock.Mock()
    mock_file_writer.return_value = mock_stream

    task = file_download_task.FileDownloadTask(source_resource,
                                               destination_resource)
    task.execute()

    mock_client.DownloadObject.assert_called_once_with(
        source_url.bucket_name, source_url.object_name, mock_stream)
    mock_file_writer.assert_called_once_with('o2.txt', create_path=True)
    mock_stream.close.assert_called_once()


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class FileUploadTaskTest(sdk_test_base.SdkBase):
  """Tests logic of FileUploadTask."""

  @mock_cloud_api.patch
  @mock.patch.object(files, 'BinaryFileReader')
  def test_execute_uploads_file(self, mock_client, mock_file_reader):
    messages = core_apis.GetMessagesModule('storage', 'v1')

    source_resource = resource_reference.FileObjectResource(
        storage_url.storage_url_from_string('file://o1.txt'))
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'),
        messages.Object(name='o2', bucket='b'))

    mock_stream = mock.Mock()
    mock_file_reader.return_value = mock_stream

    task = file_upload_task.FileUploadTask(source_resource,
                                           destination_resource)
    task.execute()

    mock_client.UploadObject.assert_called_once_with(
        mock_stream, destination_resource.metadata_object)
    mock_file_reader.assert_called_once_with('o1.txt')
    mock_stream.close.assert_called_once()


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class IntraCloudCopyTaskTest(sdk_test_base.SdkBase):
  """Tests logic of IntraCloudCopyTask."""

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self.source_metadata = self.messages.Object(name='hello')
    self.destination_metadata = self.messages.Object(name='greetings')

  @mock_cloud_api.patch
  def test_execute_copies_file(self, mock_client):
    source_resource = resource_reference.BucketResource(
        storage_url.storage_url_from_string('gs://b/o1.txt'),
        self.source_metadata)
    destination_resource = resource_reference.BucketResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'),
        self.destination_metadata)

    task = intra_cloud_copy_task.IntraCloudCopyTask(source_resource,
                                                    destination_resource)
    task.execute()

    mock_client.CopyObject.assert_called_once_with(
        source_resource.metadata_object, destination_resource.metadata_object)

  def test_execute_fails_for_local_to_cloud_copy(self):
    source_resource = resource_reference.BucketResource(
        storage_url.storage_url_from_string('file://o1.txt'),
        self.source_metadata)
    destination_resource = resource_reference.BucketResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'),
        self.destination_metadata)

    with self.assertRaises(ValueError):
      intra_cloud_copy_task.IntraCloudCopyTask(source_resource,
                                               destination_resource)

  def test_execute_fails_for_inter_cloud_copy(self):
    source_resource = resource_reference.BucketResource(
        storage_url.storage_url_from_string('s3://b/o1.txt'),
        self.source_metadata)
    destination_resource = resource_reference.BucketResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'),
        self.destination_metadata)

    with self.assertRaises(ValueError):
      intra_cloud_copy_task.IntraCloudCopyTask(source_resource,
                                               destination_resource)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GetCopyTaskTest(sdk_test_base.SdkBase):
  """Tests logic of get_copy_task factory method."""

  def test_fails_for_local_to_local_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o1.txt'), None)
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o2.txt'), None)

    with self.assertRaises(ValueError):
      copy_task_factory.get_copy_task(source_resource, destination_resource)

  def test_gets_download_task_for_cloud_to_local_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://o1.txt'), None)
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o2.txt'), None)

    task = copy_task_factory.get_copy_task(source_resource,
                                           destination_resource)
    self.assertIsInstance(task, file_download_task.FileDownloadTask)

  def test_gets_upload_task_for_local_to_cloud_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o1.txt'), None)
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://o2.txt'), None)

    task = copy_task_factory.get_copy_task(source_resource,
                                           destination_resource)
    self.assertIsInstance(task, file_upload_task.FileUploadTask)

  def test_gets_intra_cloud_copy_task_for_intra_cloud_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://o1.txt'), None)
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://o2.txt'), None)

    task = copy_task_factory.get_copy_task(source_resource,
                                           destination_resource)
    self.assertIsInstance(task, intra_cloud_copy_task.IntraCloudCopyTask)

  def test_fails_for_daisy_chaining_cloud_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://o1.txt'), None)
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('s3://o2.txt'), None)

    with self.assertRaises(NotImplementedError):
      copy_task_factory.get_copy_task(source_resource, destination_resource)

if __name__ == '__main__':
  test_case.main()
