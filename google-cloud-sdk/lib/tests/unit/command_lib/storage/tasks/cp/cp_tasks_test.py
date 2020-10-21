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

import io

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_factory
from googlecloudsdk.command_lib.storage.tasks.cp import daisy_chain_copy_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_upload_task
from googlecloudsdk.command_lib.storage.tasks.cp import intra_cloud_copy_task
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.storage import mock_cloud_api
from tests.lib.surface.storage import test_resources

import mock


BINARY_DATA = b'cool data'
ETAG = 'e'


def _write_to_stream_side_effect(stream):
  """Helper that simulates writing to a stream.

  Args:
    stream (io.ByteIO | mock.mock_open): Stream to write to.

  Returns:
    Function that can be used as side effect for writing to stream.
  """
  def inner_wrapper(*unused_args):
    """Needed to absorb normal stream arguments."""
    stream.write(BINARY_DATA)
  return inner_wrapper


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class FileDownloadTaskTest(sdk_test_base.SdkBase):
  """Tests logic of FileDownloadTask."""

  @mock_cloud_api.patch
  @mock.patch.object(files, 'BinaryFileWriter', new_callable=mock.mock_open)
  def test_execute_downloads_file(self, mock_client, mock_file_writer):
    source_url = storage_url.storage_url_from_string('gs://b/o1.txt')
    source_resource = resource_reference.ObjectResource(source_url)
    destination_resource = resource_reference.FileObjectResource(
        storage_url.storage_url_from_string('file://o2.txt'))

    task = file_download_task.FileDownloadTask(source_resource,
                                               destination_resource)
    task.execute()

    mock_file_writer.assert_called_once_with('o2.txt', create_path=True)
    mock_stream = mock_file_writer()

    mock_client.download_object.assert_called_once_with(source_url.bucket_name,
                                                        source_url.object_name,
                                                        mock_stream)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class FileUploadTaskTest(sdk_test_base.SdkBase):
  """Tests logic of FileUploadTask."""

  @mock_cloud_api.patch
  @mock.patch.object(files, 'BinaryFileReader', new_callable=mock.mock_open)
  def test_execute_uploads_file(self, mock_client, mock_stream):
    source_resource = resource_reference.FileObjectResource(
        storage_url.storage_url_from_string('file://o1.txt'))
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'))

    task = file_upload_task.FileUploadTask(source_resource,
                                           destination_resource)
    task.execute()

    mock_stream.assert_called_once_with('o1.txt')
    # We create a new instance of mock_stream to emulate "with ... as ..."
    # syntax in the task. However, this means "assert_called_once" must be above
    # because now mock_stream is called twice.
    mock_client.upload_object.assert_called_once_with(mock_stream(),
                                                      destination_resource)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class DaisyChainCopyTaskTest(sdk_test_base.SdkBase):
  """Tests logic of DaisyChainCopyTask."""

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self.source_metadata = self.messages.Object(name='o.txt', bucket='b')

  def _assert_upload_stream_has_correct_data(self, stream, *unused_args):
    self.assertEqual(stream.getvalue(), BINARY_DATA)

  @mock_cloud_api.patch
  def test_execute_copies_file_between_clouds(self, mock_client):
    test_stream = io.BytesIO()
    mock_client.download_object.side_effect = _write_to_stream_side_effect(
        test_stream)
    mock_client.upload_object.side_effect = (
        self._assert_upload_stream_has_correct_data)

    with mock.patch.object(io, 'BytesIO') as mock_stream_creator:
      mock_stream_creator.return_value = test_stream
      source_resource = resource_reference.ObjectResource(
          storage_url.storage_url_from_string('gs://b/o.txt'),
          metadata=self.source_metadata)
      destination_resource = resource_reference.UnknownResource(
          storage_url.storage_url_from_string('s3://b/o2.txt'))

      task = daisy_chain_copy_task.DaisyChainCopyTask(source_resource,
                                                      destination_resource)
      task.execute()

    mock_client.download_object.assert_called_once_with(source_resource.bucket,
                                                        source_resource.name,
                                                        test_stream)
    mock_client.upload_object.assert_called_once_with(test_stream,
                                                      destination_resource)

  def test_execute_fails_for_cloud_to_local_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://b/o.txt'),
        metadata=self.source_metadata)
    destination_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('file://o.txt'))

    with self.assertRaises(ValueError):
      daisy_chain_copy_task.DaisyChainCopyTask(source_resource,
                                               destination_resource)

  def test_execute_fails_for_local_to_cloud_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o.txt'),
        metadata=self.source_metadata)
    destination_resource = resource_reference.UnknownResource(
        storage_url.storage_url_from_string('gs://b/o.txt'))

    with self.assertRaises(ValueError):
      daisy_chain_copy_task.DaisyChainCopyTask(source_resource,
                                               destination_resource)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class IntraCloudCopyTaskTest(sdk_test_base.SdkBase):
  """Tests logic of IntraCloudCopyTask."""

  @mock_cloud_api.patch
  def test_execute_copies_file(self, mock_client):
    source_resource = test_resources.from_url_string('gs://b/o1.txt')
    destination_resource = test_resources.from_url_string('gs://b/o2.txt')

    task = intra_cloud_copy_task.IntraCloudCopyTask(source_resource,
                                                    destination_resource)
    task.execute()

    mock_client.copy_object.assert_called_once_with(source_resource,
                                                    destination_resource)

  def test_execute_fails_for_local_to_cloud_copy(self):
    source_resource = test_resources.from_url_string('file://o1.txt')
    destination_resource = test_resources.from_url_string('gs://b/o2.txt')

    with self.assertRaises(ValueError):
      intra_cloud_copy_task.IntraCloudCopyTask(source_resource,
                                               destination_resource)

  def test_execute_fails_for_inter_cloud_copy(self):
    source_resource = test_resources.from_url_string('s3://b/o1.txt')
    destination_resource = test_resources.from_url_string('gs://b/o2.txt')

    with self.assertRaises(ValueError):
      intra_cloud_copy_task.IntraCloudCopyTask(source_resource,
                                               destination_resource)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GetCopyTaskTest(sdk_test_base.SdkBase):
  """Tests logic of get_copy_task factory method."""

  def test_fails_for_local_to_local_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o1.txt'))
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o2.txt'))

    with self.assertRaises(ValueError):
      copy_task_factory.get_copy_task(source_resource, destination_resource)

  def test_gets_download_task_for_cloud_to_local_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://b/o1.txt'))
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o2.txt'))

    task = copy_task_factory.get_copy_task(source_resource,
                                           destination_resource)
    self.assertIsInstance(task, file_download_task.FileDownloadTask)

  def test_gets_upload_task_for_local_to_cloud_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('file://o1.txt'))
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'))

    task = copy_task_factory.get_copy_task(source_resource,
                                           destination_resource)
    self.assertIsInstance(task, file_upload_task.FileUploadTask)

  def test_gets_intra_cloud_copy_task_for_intra_cloud_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://b/o1.txt'))
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://b/o2.txt'))

    task = copy_task_factory.get_copy_task(source_resource,
                                           destination_resource)
    self.assertIsInstance(task, intra_cloud_copy_task.IntraCloudCopyTask)

  def test_fails_for_daisy_chaining_cloud_copy(self):
    source_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://b/o1.txt'))
    destination_resource = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('s3://b/o2.txt'))

    task = copy_task_factory.get_copy_task(source_resource,
                                           destination_resource)
    self.assertIsInstance(task, daisy_chain_copy_task.DaisyChainCopyTask)


if __name__ == '__main__':
  test_case.main()
