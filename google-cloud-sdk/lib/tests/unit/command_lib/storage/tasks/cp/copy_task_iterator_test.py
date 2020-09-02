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

"""Unit tests for cp helper functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_iterator
from googlecloudsdk.command_lib.storage.tasks.cp import file_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_upload_task
from googlecloudsdk.command_lib.storage.tasks.cp import intra_cloud_copy_task
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.storage import test_resources
import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CopyTaskIteratorTest(parameterized.TestCase):
  """Unit tests for CopyTaskIterator."""

  @parameterized.named_parameters([
      {
          'testcase_name': '_intra_cloud_copy',
          'source_resource':
              test_resources.get_object_resource('gs', 'src', 'obj1'),
          'destination_string': 'gs://dest/obj2',
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_file_upload',
          'source_resource': test_resources.get_file_object_resource('file'),
          'destination_string': 'gs://dest/obj2',
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_file_download',
          'source_resource':
              test_resources.get_object_resource('gs', 'src', 'obj1'),
          'destination_string': 'file',
          'task_type': file_download_task.FileDownloadTask
      },
  ])
  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_single_source_and_destination(self, wildcard_factory,
                                         source_resource, destination_string,
                                         task_type):
    wildcard_factory.return_value = mock.MagicMock()
    tasks = list(copy_task_iterator.CopyTaskIterator(
        iter([source_resource]), destination_string))

    self.assertEqual(len(tasks), 1)
    self.assertIsInstance(tasks[0], task_type)
    self.assertEqual(tasks[0]._source_resource, source_resource)
    self.assertEqual(tasks[0]._destination_resource,
                     test_resources.get_unknown_resource(destination_string))

  @parameterized.named_parameters([
      {
          'testcase_name': '_objects_to_bucket_with_delimiter',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'gs://dest/',
          'expected_destination_strings': ['gs://dest/obj1', 'gs://dest/obj2'],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_objects_to_bucket_without_delimiter',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'gs://dest',
          'expected_destination_strings': ['gs://dest/obj1', 'gs://dest/obj2'],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_objects_to_prefix_with_delimiter',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'gs://dest/dir/',
          'expected_destination_strings': [
              'gs://dest/dir/obj1', 'gs://dest/dir/obj2'
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_objects_to_prefix_without_delimiter',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'gs://dest/dir',
          'expected_destination_strings': [
              'gs://dest/dir/obj1', 'gs://dest/dir/obj2'
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_files_to_prefix_with_delimiter',
          'source_resources': [
              test_resources.get_file_object_resource(
                  os.path.join('dir', 'obj1')),
              test_resources.get_file_object_resource(
                  os.path.join('dir', 'obj2')),
          ],
          'destination_string': 'gs://dest/dir/',
          'expected_destination_strings': [
              'gs://dest/dir/obj1', 'gs://dest/dir/obj2'
          ],
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_files_to_prefix_without_delimiter',
          'source_resources': [
              test_resources.get_file_object_resource(
                  os.path.join('dir', 'obj1')),
              test_resources.get_file_object_resource(
                  os.path.join('dir', 'obj2')),
          ],
          'destination_string': 'gs://dest/dir',
          'expected_destination_strings': [
              'gs://dest/dir/obj1', 'gs://dest/dir/obj2'
          ],
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_objects_to_directory_with_delimiter',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'dir' + os.path.sep,
          'expected_destination_strings': [
              os.path.join('dir', 'obj1'),
              os.path.join('dir', 'obj2'),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_objects_to_directory_without_delimiter',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'dir',
          'expected_destination_strings': [
              os.path.join('dir', 'obj1'),
              os.path.join('dir', 'obj2'),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
  ])
  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_multiple_source(self, wildcard_factory, source_resources,
                           destination_string, expected_destination_strings,
                           task_type):
    wildcard_factory.return_value = mock.MagicMock()
    tasks = list(copy_task_iterator.CopyTaskIterator(
        iter(source_resources), destination_string))

    self.assertEqual(len(tasks), len(source_resources))
    for task, source, destination in zip(tasks, source_resources,
                                         expected_destination_strings):
      self.assertIsInstance(task, task_type)
      self.assertEqual(task._source_resource, source)
      self.assertEqual(task._destination_resource,
                       test_resources.get_unknown_resource(destination))

  @parameterized.named_parameters([
      {
          'testcase_name': '_existing_object_single_source',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
          ],
          'destination_string': 'gs://dest/obj*',
          'expected_dest_resources': [
              test_resources.get_object_resource('gs', 'dest', 'obj1'),
          ],
          'wildcard_output': [
              test_resources.get_object_resource('gs', 'dest', 'obj1'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_object_multiple_sources',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'gs://dest/obj*',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/obj1/obj1'),
              test_resources.get_unknown_resource('gs://dest/obj1/obj2'),
          ],
          'wildcard_output': [
              test_resources.get_object_resource('gs', 'dest', 'obj1'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_file_single_source',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
          ],
          'destination_string': 'dir/obj*',
          'expected_dest_resources': [
              test_resources.get_file_object_resource(
                  os.path.join('dir', 'obj1')),
          ],
          'wildcard_output': [
              test_resources.get_file_object_resource(
                  os.path.join('dir', 'obj1')),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_existing_file_multiple_sources',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'dir/obj*',
          'expected_dest_resources': [
              test_resources.get_unknown_resource(
                  os.path.join('dir', 'obj1', 'obj1')),
              test_resources.get_unknown_resource(
                  os.path.join('dir', 'obj1', 'obj2')),
          ],
          'wildcard_output': [
              test_resources.get_file_object_resource(
                  os.path.join('dir', 'obj1')),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_existing_bucket',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'gs://dest/',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/obj1'),
              test_resources.get_unknown_resource('gs://dest/obj2'),
          ],
          'wildcard_output': [test_resources.get_bucket_resource('gs', 'dest')],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_prefix',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'gs://dest/dir/',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/dir/obj1'),
              test_resources.get_unknown_resource('gs://dest/dir/obj2'),
          ],
          'wildcard_output': [
              test_resources.get_prefix_resource('gs', 'dest', 'dir'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_dir',
          'source_resources': [
              test_resources.get_object_resource('gs', 'src', 'obj1'),
              test_resources.get_object_resource('gs', 'src', 'obj2'),
          ],
          'destination_string': 'dir',
          'expected_dest_resources': [
              test_resources.get_unknown_resource(os.path.join('dir', 'obj1')),
              test_resources.get_unknown_resource(os.path.join('dir', 'obj2')),
          ],
          'wildcard_output': [
              test_resources.get_file_directory_resource('dir'),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
  ])
  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_wildcard_destination(self, wildcard_factory, source_resources,
                                destination_string, wildcard_output,
                                expected_dest_resources, task_type):
    wildcard_instance = mock.MagicMock()
    wildcard_instance.__iter__.return_value = iter(wildcard_output)
    wildcard_factory.return_value = wildcard_instance

    tasks = list(copy_task_iterator.CopyTaskIterator(
        iter(source_resources), destination_string))

    self.assertEqual(len(tasks), len(source_resources))
    for task, source, destination in zip(tasks, source_resources,
                                         expected_dest_resources):
      self.assertIsInstance(task, task_type)
      self.assertEqual(task._source_resource, source)
      self.assertEqual(task._destination_resource, destination)

  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_multiple_destinations_with_wildcard(self, wildcard_factory):
    wildcard_instance = mock.MagicMock()
    wildcard_instance.__iter__.return_value = iter([
        test_resources.get_object_resource('gs', 'dest', 'obj1'),
        test_resources.get_object_resource('gs', 'dest', 'obj2')
    ])
    wildcard_factory.return_value = wildcard_instance

    with self.assertRaises(ValueError):
      list(
          copy_task_iterator.CopyTaskIterator(
              iter([test_resources.get_object_resource('gs', 'src', 'obj1')]),
              'gs://dest/obj*'))

  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_no_destination_with_wildcard(self, wildcard_factory):
    wildcard_factory.return_value = mock.MagicMock()

    with self.assertRaises(ValueError):
      list(
          copy_task_iterator.CopyTaskIterator(
              iter([test_resources.get_object_resource('gs', 'src', 'obj1')]),
              'gs://dest/obj*'))

  def test_provider_destination_throws_error(self):
    with self.assertRaises(ValueError):
      list(copy_task_iterator.CopyTaskIterator(iter([]), 'gs://'))

  def test_destination_with_version_throws_error(self):
    with self.assertRaises(ValueError):
      list(copy_task_iterator.CopyTaskIterator(iter([]), 'gs://dest/obj#1'))
