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

from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_iterator
from googlecloudsdk.command_lib.storage.tasks.cp import file_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_upload_task
from googlecloudsdk.command_lib.storage.tasks.cp import intra_cloud_copy_task
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.storage import test_resources
import mock


def _normalize_path(filename):
  """Returns a platform specific filepath."""
  return os.path.join(*filename.split('/'))


def _get_name_expansion_result(resource_url, expanded_url=None):
  """Returns a NameExpansionResult instance.

  If unix-like file system paths are passed, we normalize them using
  os.path.join to make them platform independent.

  Args:
    resource_url (str): URL path representing the resource.
    expanded_url (str): Path representing the expanded prefix in case of
      recursion. Otherwise, it is same as the resource_url.

  Returns:
    A NameExpansionResult instance.
  """

  expanded_url = expanded_url or resource_url
  if isinstance(
      storage_url.storage_url_from_string(resource_url), storage_url.FileUrl):
    resource_url = _normalize_path(resource_url)
    expanded_url = _normalize_path(expanded_url)

  return name_expansion.NameExpansionResult(
      resource=test_resources.from_url_string(resource_url),
      expanded_url=storage_url.storage_url_from_string(expanded_url))


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CopyTaskIteratorTest(parameterized.TestCase):
  """Unit tests for CopyTaskIterator."""

  @parameterized.named_parameters([
      {
          'testcase_name': '_intra_cloud_copy',
          'source': _get_name_expansion_result('gs://src/obj1'),
          'destination_string': 'gs://dest/obj2',
          'expected_destination': 'gs://dest/obj2',
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_file_upload',
          'source': _get_name_expansion_result('file'),
          'destination_string': 'gs://dest/obj2',
          'expected_destination': 'gs://dest/obj2',
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_file_upload_with_delimiter',
          'source': _get_name_expansion_result('file'),
          'destination_string': 'gs://dest/obj2/',
          'expected_destination': 'gs://dest/obj2/file',
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name':
              '_file_upload_recursive',
          'source':
              _get_name_expansion_result(
                  os.path.join('a', 'b', 'c', 'd.txt'), os.path.join('a', 'b')),
          'destination_string':
              'gs://dest/obj',
          'expected_destination':
              'gs://dest/obj/c/d.txt',
          'task_type':
              file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_file_download',
          'source': _get_name_expansion_result('gs://src/obj1'),
          'destination_string': 'file',
          'expected_destination': 'file',
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_file_download_recursive',
          'source': _get_name_expansion_result('gs://a/b/c/d.txt', 'gs://a/b'),
          'destination_string': os.path.join('dir1', 'dir2'),
          'expected_destination': os.path.join('dir1', 'dir2', 'c', 'd.txt'),
          'task_type': file_download_task.FileDownloadTask
      },
  ])
  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_single_source_and_non_existing_destination(self, wildcard_factory,
                                                      source,
                                                      destination_string,
                                                      expected_destination,
                                                      task_type):
    # Destination is not present
    wildcard_factory.side_effect = [[]]
    tasks = list(
        copy_task_iterator.CopyTaskIterator([source], destination_string))

    self.assertEqual(len(tasks), 1)
    self.assertIsInstance(tasks[0], task_type)
    self.assertEqual(tasks[0]._source_resource, source.resource)
    self.assertEqual(tasks[0]._destination_resource,
                     test_resources.get_unknown_resource(expected_destination))
    wildcard_factory.assert_called_once_with(destination_string)

  @parameterized.named_parameters([
      {
          'testcase_name': '_objects_to_bucket_with_delimiter',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'gs://dest/',
          'expected_destination_strings': ['gs://dest/obj1', 'gs://dest/obj2'],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_objects_to_bucket_without_delimiter',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'gs://dest',
          'expected_destination_strings': ['gs://dest/obj1', 'gs://dest/obj2'],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_objects_to_prefix_with_delimiter',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'gs://dest/dir/',
          'expected_destination_strings': [
              'gs://dest/dir/obj1', 'gs://dest/dir/obj2'
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_objects_to_prefix_without_delimiter',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'gs://dest/dir',
          'expected_destination_strings': [
              'gs://dest/dir/obj1', 'gs://dest/dir/obj2'
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_files_to_prefix_with_delimiter',
          'sources': [
              _get_name_expansion_result(os.path.join('dir', 'obj1')),
              _get_name_expansion_result(os.path.join('dir', 'obj2'))
          ],
          'destination_string': 'gs://dest/dir/',
          'expected_destination_strings': [
              'gs://dest/dir/obj1', 'gs://dest/dir/obj2'
          ],
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_files_to_prefix_with_delimiter_recursive',
          'sources': [
              _get_name_expansion_result('a/b/c/d.txt', 'a/b'),
              _get_name_expansion_result('e/f/g/h.txt', 'e/f')
          ],
          'destination_string': 'gs://dest/dir/',
          'expected_destination_strings': [
              'gs://dest/dir/c/d.txt', 'gs://dest/dir/g/h.txt'
          ],
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_files_to_prefix_without_delimiter',
          'sources': [
              _get_name_expansion_result(os.path.join('dir', 'obj1')),
              _get_name_expansion_result(os.path.join('dir', 'obj2'))
          ],
          'destination_string': 'gs://dest/dir',
          'expected_destination_strings': [
              'gs://dest/dir/obj1', 'gs://dest/dir/obj2'
          ],
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_files_to_prefix_without_delimiter_recursive',
          'sources': [
              _get_name_expansion_result('a/b/c/d.txt', 'a/b'),
              _get_name_expansion_result('e/f/g/h.txt', 'e/f')
          ],
          'destination_string': 'gs://dest/dir',
          'expected_destination_strings': [
              'gs://dest/dir/c/d.txt', 'gs://dest/dir/g/h.txt'
          ],
          'task_type': file_upload_task.FileUploadTask
      },
      {
          'testcase_name': '_objects_to_directory_with_delimiter',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
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
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'dir',
          'expected_destination_strings': [
              os.path.join('dir', 'obj1'),
              os.path.join('dir', 'obj2'),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_objects_to_directory_with_delimiter_recursive',
          'sources': [
              _get_name_expansion_result('gs://a/b/c/d.txt', 'gs://a/b'),
              _get_name_expansion_result('gs://e/f/g/h.txt', 'gs://e/f')
          ],
          'destination_string': 'dir' + os.path.sep,
          'expected_destination_strings': [
              os.path.join('dir', 'c', 'd.txt'),
              os.path.join('dir', 'g', 'h.txt'),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
  ])
  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_multiple_source_non_existing_destination(
      self, wildcard_factory, sources, destination_string,
      expected_destination_strings, task_type):
    # Result from expanding the destination_string.
    wildcard_factory.side_effect = [[]]
    tasks = list(
        copy_task_iterator.CopyTaskIterator(sources, destination_string))

    self.assertEqual(len(tasks), len(sources))
    for task, source, destination in zip(tasks, sources,
                                         expected_destination_strings):
      self.assertIsInstance(task, task_type)
      self.assertEqual(task._source_resource, source.resource)
      self.assertEqual(task._destination_resource,
                       test_resources.get_unknown_resource(destination))
    wildcard_factory.assert_called_once_with(destination_string)

  @parameterized.named_parameters([
      {
          'testcase_name': '_existing_object_single_source',
          'sources': [_get_name_expansion_result('gs://src/obj1')],
          'destination_string': 'gs://dest/obj1',
          'expected_dest_resources': [
              test_resources.get_object_resource('gs', 'dest', 'obj1'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_object_single_source_recursive',
          'sources': [
              _get_name_expansion_result('gs://a/b/c/d.txt', 'gs://a/b')
          ],
          'destination_string': 'gs://dest/obj1',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/obj1/c/d.txt'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_prefix_single_source_recursive',
          'sources': [
              _get_name_expansion_result('gs://a/b/c/d.txt', 'gs://a/b')
          ],
          'destination_string': 'gs://dest/obj1/',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/obj1/b/c/d.txt'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_object_multiple_sources',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'gs://dest/obj1',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/obj1/obj1'),
              test_resources.get_unknown_resource('gs://dest/obj1/obj2'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_file_single_source',
          'sources': [_get_name_expansion_result('gs://src/obj1'),],
          'destination_string': _normalize_path('dir/obj1'),
          'expected_dest_resources': [
              test_resources.from_url_string(os.path.join('dir', 'obj1')),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_existing_file_multiple_sources',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': _normalize_path('dir/obj1'),
          'expected_dest_resources': [
              test_resources.get_unknown_resource(
                  os.path.join('dir', 'obj1', 'obj1')),
              test_resources.get_unknown_resource(
                  os.path.join('dir', 'obj1', 'obj2')),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_existing_file_multiple_sources_recursive',
          'sources': [
              _get_name_expansion_result('gs://a/b/c/d.txt', 'gs://a/b'),
              _get_name_expansion_result('gs://a/b/e/f.txt', 'gs://a/b'),
              _get_name_expansion_result('gs://g/h/i/j.txt', 'gs://g/h')
          ],
          'destination_string': _normalize_path('dir1/obj1'),
          'expected_dest_resources': [
              test_resources.get_unknown_resource(
                  os.path.join('dir1', 'obj1', 'c', 'd.txt')),
              test_resources.get_unknown_resource(
                  os.path.join('dir1', 'obj1', 'e', 'f.txt')),
              test_resources.get_unknown_resource(
                  os.path.join('dir1', 'obj1', 'i', 'j.txt')),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_existing_bucket',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'gs://dest/',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/obj1'),
              test_resources.get_unknown_resource('gs://dest/obj2'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_prefix',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'gs://dest/dir/',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/dir/obj1'),
              test_resources.get_unknown_resource('gs://dest/dir/obj2'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_prefix_recursive',
          'sources': [
              _get_name_expansion_result('gs://a/b/c/d.txt', 'gs://a/b'),
              _get_name_expansion_result('gs://e/f/g/h.txt', 'gs://e/f')
          ],
          'destination_string': 'gs://dest/dir/',
          'expected_dest_resources': [
              test_resources.get_unknown_resource('gs://dest/dir/b/c/d.txt'),
              test_resources.get_unknown_resource('gs://dest/dir/f/g/h.txt'),
          ],
          'task_type': intra_cloud_copy_task.IntraCloudCopyTask
      },
      {
          'testcase_name': '_existing_dir',
          'sources': [
              _get_name_expansion_result('gs://src/obj1'),
              _get_name_expansion_result('gs://src/obj2')
          ],
          'destination_string': 'dir' + os.sep,
          'expected_dest_resources': [
              test_resources.get_unknown_resource(os.path.join('dir', 'obj1')),
              test_resources.get_unknown_resource(os.path.join('dir', 'obj2')),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_existing_dir_recursive',
          'sources': [
              _get_name_expansion_result('gs://a/b/c/d.txt', 'gs://a/b'),
              _get_name_expansion_result('gs://a/b/e/f.txt', 'gs://a/b'),
              _get_name_expansion_result('gs://g/h/i/j.txt', 'gs://g/h')
          ],
          'destination_string': 'dir1' + os.sep,
          'expected_dest_resources': [
              test_resources.get_unknown_resource(
                  os.path.join('dir1', 'b', 'c', 'd.txt')),
              test_resources.get_unknown_resource(
                  os.path.join('dir1', 'b', 'e', 'f.txt')),
              test_resources.get_unknown_resource(
                  os.path.join('dir1', 'h', 'i', 'j.txt')),
          ],
          'task_type': file_download_task.FileDownloadTask
      },
  ])
  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_existing_single_destination(self, wildcard_factory, sources,
                                       destination_string,
                                       expected_dest_resources, task_type):
    fake_destination_string = 'random/dest'
    resources_from_destination_expansion = [
        test_resources.from_url_string(destination_string)
    ]

    wildcard_factory.side_effect = [resources_from_destination_expansion]

    tasks = list(
        copy_task_iterator.CopyTaskIterator(sources, fake_destination_string))

    self.assertEqual(len(tasks), len(sources))
    for task, source, destination in zip(tasks, sources,
                                         expected_dest_resources):
      self.assertIsInstance(task, task_type)
      self.assertEqual(task._source_resource, source.resource)
      self.assertEqual(task._destination_resource, destination)
    wildcard_factory.assert_called_once_with(fake_destination_string)

  @parameterized.named_parameters([
      {
          'testcase_name': '_download_to_windows',
          'sources': [_get_name_expansion_result('gs://a/b/c.txt', 'gs://a')],
          'destination': 'dir1\\dir2',
          'expected_destination': 'dir1\\dir2\\b\\c.txt',
          'task_type': file_download_task.FileDownloadTask
      },
      {
          'testcase_name': '_upload_from_windows',
          'sources': [_get_name_expansion_result('a\\b\\c.txt', 'a')],
          'destination': 'gs://dest/dir',
          'expected_destination': 'gs://dest/dir/b/c.txt',
          'task_type': file_upload_task.FileUploadTask
      },
  ])
  @mock.patch.object(os, 'sep', '\\')  # Simulate Windows.
  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_different_delimiter(self, wildcard_factory, sources, destination,
                               expected_destination, task_type):
    """Test that source delimiter gets converted to destination delimiter."""
    fake_destination_string = 'fake_destination_string_with_wildcard'
    resources_from_destination_expansion = [
        test_resources.from_url_string(destination)
    ]

    wildcard_factory.side_effect = [resources_from_destination_expansion]

    tasks = list(
        copy_task_iterator.CopyTaskIterator(sources, fake_destination_string))

    self.assertEqual(len(tasks), 1)
    self.assertIsInstance(tasks[0], task_type)
    self.assertEqual(tasks[0]._source_resource, sources[0].resource)
    self.assertEqual(tasks[0]._destination_resource,
                     test_resources.get_unknown_resource(expected_destination))
    wildcard_factory.assert_called_once_with(fake_destination_string)

  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_multiple_destinations_with_wildcard(self, wildcard_factory):
    fake_destination_string = 'fake_destination_string_with_wildcard'
    resources_from_destination_expansion = [
        test_resources.from_url_string('gs://bucket/obj1'),
        test_resources.from_url_string('gs://bucket/obj2'),
    ]

    wildcard_factory.side_effect = [resources_from_destination_expansion]

    with self.assertRaises(ValueError):
      list(
          copy_task_iterator.CopyTaskIterator(
              [_get_name_expansion_result('fake_source')],
              fake_destination_string))

  @mock.patch.object(wildcard_iterator, 'get_wildcard_iterator')
  def test_no_destination_with_wildcard(self, wildcard_factory):
    # Destination expansion returns empty result.
    wildcard_factory.side_effect = [[]]

    with self.assertRaises(ValueError):
      list(
          copy_task_iterator.CopyTaskIterator(
              [_get_name_expansion_result('fake_source')], 'gs://dest/obj*'))

  def test_provider_destination_throws_error(self):
    with self.assertRaises(ValueError):
      list(copy_task_iterator.CopyTaskIterator(iter([]), 'gs://'))

  def test_destination_with_version_throws_error(self):
    with self.assertRaises(ValueError):
      list(copy_task_iterator.CopyTaskIterator(iter([]), 'gs://dest/obj#1'))


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class HelperFunctonsTest(parameterized.TestCase):

  @parameterized.named_parameters([
      {
          'testcase_name':
              '_cloud_path_with_expanded_url_as_none',
          'resource_url':
              'gs://a/b/c/d.txt',
          'expanded_url':
              None,
          'expected_resource':
              resource_reference.ObjectResource(
                  storage_url.storage_url_from_string('gs://a/b/c/d.txt')),
          'expected_expanded_url':
              'gs://a/b/c/d.txt'
      },
      {
          'testcase_name':
              '_cloud_path_with_expanded_url_present',
          'resource_url':
              'gs://a/b/c/d.txt',
          'expanded_url':
              'gs://a/b',
          'expected_resource':
              resource_reference.ObjectResource(
                  storage_url.storage_url_from_string('gs://a/b/c/d.txt')),
          'expected_expanded_url':
              'gs://a/b'
      },
      {
          'testcase_name':
              '_file_path_with_expanded_url_as_none',
          'resource_url':
              'a/b/c/d.txt',
          'expanded_url':
              None,
          'expected_resource':
              resource_reference.FileObjectResource(
                  storage_url.storage_url_from_string(
                      os.path.join('a', 'b', 'c', 'd.txt'))),
          'expected_expanded_url':
              os.path.join('a', 'b', 'c', 'd.txt')
      },
      {
          'testcase_name':
              '_file_path_with_expanded_url_present',
          'resource_url':
              'a/b/c/d.txt',
          'expanded_url':
              'a/b',
          'expected_resource':
              resource_reference.FileObjectResource(
                  storage_url.storage_url_from_string(
                      os.path.join('a', 'b', 'c', 'd.txt'))),
          'expected_expanded_url':
              os.path.join('a', 'b')
      },
  ])
  def test_get_name_expansion_result(self, resource_url, expanded_url,
                                     expected_resource, expected_expanded_url):
    expanded_result = _get_name_expansion_result(resource_url, expanded_url)

    self.assertEqual(expanded_result.resource, expected_resource)
    self.assertEqual(expanded_result.expanded_url,
                     storage_url.storage_url_from_string(expected_expanded_url))
