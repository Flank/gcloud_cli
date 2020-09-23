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
"""Tests for googlecloudsdk.command_lib.storage.tasks.ls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.tasks.ls import cloud_list_task
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util
from tests.lib.surface.storage import mock_cloud_api
from tests.lib.surface.storage import test_resources

import mock


TEST_PROJECT = 'fake-project'


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CloudListTaskTest(cloud_storage_util.WithGCSCalls, parameterized.TestCase,
                        sdk_test_base.WithOutputCapture):
  """Tests logic of CloudListTaskTest."""

  def SetUp(self):
    properties.VALUES.core.project.Set(TEST_PROJECT)
    self.stdout_seek_position = 0
    self.messages = core_apis.GetMessagesModule('storage', 'v1')

    # bucket1:
    #   object1
    #   dir1/object2
    #   dir1/subdir1/object3
    #   dir1/subdir2/object4
    #   dir2/subdir3/object5
    # bucket2:
    #   dir_object
    #   dir_object/object6

    self.bucket1 = test_resources.from_url_string('gs://bucket1')
    self.bucket2 = test_resources.from_url_string('gs://bucket2')

    self.object1 = test_resources.from_url_string(
        'gs://bucket1/object1')
    self.object2 = test_resources.from_url_string(
        'gs://bucket1/dir1/object2')
    self.object3 = test_resources.from_url_string(
        'gs://bucket1/dir1/subdir1/object3')
    self.object4 = test_resources.from_url_string(
        'gs://bucket1/dir1/subdir2/object4')
    self.object5 = test_resources.from_url_string(
        'gs://bucket1/dir2/subdir3/object5')
    self.object6 = test_resources.from_url_string(
        'gs://bucket2/dir_object/object6')
    self.object_duplicate_of_dir = test_resources.from_url_string(
        'gs://bucket2/dir_object')

    self.dir1 = test_resources.from_url_string('gs://bucket1/dir1/')
    self.dir2 = test_resources.from_url_string('gs://bucket1/dir2/')
    self.subdir1 = test_resources.from_url_string('gs://bucket1/dir1/subdir1/')
    self.subdir2 = test_resources.from_url_string('gs://bucket1/dir1/subdir2/')
    self.subdir3 = test_resources.from_url_string('gs://bucket1/dir2/subdir3/')
    self.dir_duplicate_of_object = test_resources.from_url_string(
        'gs://bucket2/dir_object/')

    self.bucket_resources = [self.bucket1, self.bucket2]
    self.bucket1_top_level_resources = [self.object1, self.dir1, self.dir2]
    self.bucket1_dir1_resources = [self.object2, self.subdir1, self.subdir2]
    self.bucket1_dir1_subdir1_resources = [self.object3]
    self.bucket1_dir1_subdir2_resources = [self.object4]
    self.bucket1_dir2_resources = [self.subdir3]
    self.bucket1_dir2_subdir3_resources = [self.object5]
    self.bucket1_all_objects = [self.object1, self.object2, self.object3,
                                self.object4, self.object5]
    self.bucket2_top_level_resources = [self.object_duplicate_of_dir,
                                        self.dir_duplicate_of_object]
    self.bucket2_dir_object_resources = [self.object6]

  @mock_cloud_api.patch
  def test_execute_lists_provider_url_properly(self, client):
    """Test all buckets are shown."""
    client.ListBuckets.side_effect = [self.bucket_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1\ngs://bucket2\n'
    self.assertEqual(output, expected_output)

    client.ListBuckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)

  @parameterized.parameters(('gs://*'), ('gs://**'))
  @mock_cloud_api.patch
  def test_execute_lists_provider_with_wildcards_properly(
      self, query_url, client):
    """Test if all buckets top-level contents are shown, even if '**'."""
    client.ListBuckets.side_effect = [self.bucket_resources]
    client.ListObjects.side_effect = [
        self.bucket1_top_level_resources, self.bucket2_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string(query_url))
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1:
        gs://bucket1/object1
        gs://bucket1/dir1/
        gs://bucket1/dir2/

        gs://bucket2:
        gs://bucket2/dir_object
        gs://bucket2/dir_object/
        """
    )
    self.assertEqual(output, expected_output)

    client.ListBuckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)
    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT, prefix=None),
        mock.call(all_versions=False,
                  bucket_name=self.bucket2.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT, prefix=None)])

  @parameterized.parameters(('gs://bucket1'), ('gs://bucket1/'))
  @mock_cloud_api.patch
  def test_execute_lists_execute_lists_bucket_url_properly(self, query_url,
                                                           client):
    """Show top-level bucket items are shown but not subdirectory items."""
    client.GetBucket.side_effect = [self.bucket1]
    client.ListObjects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string(query_url))
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/object1
        gs://bucket1/dir1/
        gs://bucket1/dir2/
        """
    )
    self.assertEqual(output, expected_output)

    client.GetBucket.assert_called_once_with(
        self.bucket1.name, cloud_api.FieldsScope.SHORT,)
    client.ListObjects.assert_called_once_with(
        all_versions=False, bucket_name=self.bucket1.name,
        delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT, prefix=None)

  @parameterized.parameters(('gs://b*2'), ('gs://b**2'))
  @mock_cloud_api.patch
  def test_execute_lists_bucket_url_with_wildcard_properly(self, query_url,
                                                           client):
    """Test if ListBuckets gets hit but only second bucket is shown."""
    client.ListBuckets.side_effect = [self.bucket_resources]
    client.ListObjects.side_effect = [self.bucket2_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string(query_url))
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket2/dir_object
        gs://bucket2/dir_object/
        """
    )
    self.assertEqual(output, expected_output)

    client.ListBuckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)
    client.ListObjects.assert_called_once_with(
        all_versions=False, bucket_name=self.bucket2.name, delimiter='/',
        fields_scope=cloud_api.FieldsScope.SHORT, prefix=None)

  @mock_cloud_api.patch
  def test_execute_lists_object_url_properly(self, client):
    """Test if ListObjects is hit and object name is shown."""
    client.GetObjectMetadata.side_effect = [self.object1]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/object1'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/object1\n'
    self.assertEqual(output, expected_output)

    self.assertFalse(client.ListObjects.called)
    client.GetObjectMetadata.assert_called_once_with(
        self.bucket1.name, self.object1.name, None, cloud_api.FieldsScope.SHORT)

  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_wildcard_properly(self, client):
    """One recursion level of prefixes are shown and formatted."""
    client.ListObjects.side_effect = [
        self.bucket1_top_level_resources,
        self.bucket1_dir1_resources, self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/*'))
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/object1

        gs://bucket1/dir1/:
        gs://bucket1/dir1/object2
        gs://bucket1/dir1/subdir1/
        gs://bucket1/dir1/subdir2/

        gs://bucket1/dir2/:
        gs://bucket1/dir2/subdir3/
        """
    )
    self.assertEqual(output, expected_output)

    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT, prefix=None),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir1.prefix),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir2.prefix)])

  @mock_cloud_api.patch
  def test_execute_lists_wildcard_followed_by_object_properly(self, client):
    """Any parent directory will do. Make sure object name matches."""
    client.ListObjects.side_effect = [
        self.bucket1_top_level_resources,
        self.bucket1_dir1_resources, self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/*/object2'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/dir1/object2\n'
    self.assertEqual(output, expected_output)

    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT, prefix=None),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix='dir1/object2'),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix='dir2/object2')])

  # pylint:disable=line-too-long
  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_single_wildcard_followed_by_single_wildcard_properly(
      self, client):
    """Check if all subdirectories are matched and formatted."""
    client.ListObjects.side_effect = [self.bucket1_top_level_resources,
                                      self.bucket1_dir1_resources,
                                      self.bucket1_dir1_subdir1_resources,
                                      self.bucket1_dir1_subdir2_resources,
                                      self.bucket1_dir2_resources,
                                      self.bucket1_dir2_subdir3_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/*/*'))
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/dir1/object2

        gs://bucket1/dir1/subdir1/:
        gs://bucket1/dir1/subdir1/object3

        gs://bucket1/dir1/subdir2/:
        gs://bucket1/dir1/subdir2/object4

        gs://bucket1/dir2/subdir3/:
        gs://bucket1/dir2/subdir3/object5
        """
    )
    self.assertEqual(output, expected_output)

    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=None),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir1.prefix),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir1.prefix),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir2.prefix),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir2.prefix),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir3.prefix)])

  @mock_cloud_api.patch
  def test_execute_lists_single_prefix_properly(self, client):
    """API should return prefix contents. Task should display contents."""
    client.GetObjectMetadata.side_effect = api_errors.NotFoundError
    client.ListObjects.side_effect = [[self.dir2], self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/dir2/'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/dir2/subdir3/\n'
    self.assertEqual(output, expected_output)

    client.GetObjectMetadata.assert_called_once_with(
        self.bucket1.name, 'dir2/', None, cloud_api.FieldsScope.SHORT)
    client.ListObjects.assert_has_calls([
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT, prefix='dir2'),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT, prefix='dir2/')])

  @mock_cloud_api.patch
  def test_execute_lists_prefix_no_trailing_delimiter(self, client):
    """Two API calls are made, and prefix top-level contents are shown."""
    client.GetObjectMetadata.side_effect = api_errors.NotFoundError
    client.ListObjects.side_effect = [[self.dir2], self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/dir2'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/dir2/subdir3/\n'
    self.assertEqual(output, expected_output)

    client.GetObjectMetadata.assert_called_once_with(
        self.bucket1.name, 'dir2', None, cloud_api.FieldsScope.SHORT)
    client.ListObjects.assert_has_calls([
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT, prefix='dir2'),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir2.prefix)])

  @mock_cloud_api.patch
  def test_execute_lists_prefix_with_center_wildcard(self, client):
    """Two API calls are made, and prefix top-level contents are shown."""
    client.ListObjects.side_effect = [[self.dir2], self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/d*2/'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/dir2/subdir3/\n'

    self.assertEqual(output, expected_output)
    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT, prefix='d'),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir2.prefix)])

  @mock_cloud_api.patch
  def test_execute_does_not_list_object_if_trailing_delimiter(self, client):
    """Gsutil would list an object matching the query. Breaking change."""
    client.ListObjects.side_effect = [self.bucket2_top_level_resources,
                                      self.bucket2_dir_object_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket2/d*/'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket2/dir_object/object6\n'
    self.assertEqual(output, expected_output)

    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False,
                  bucket_name=self.bucket2.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix='d'),
        mock.call(all_versions=False,
                  bucket_name=self.bucket2.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix='dir_object/')])

  @parameterized.parameters(('gs://bucket1/dir*', 'dir'),
                            ('gs://bucket1/d*/', 'd'))
  @mock_cloud_api.patch
  def test_execute_lists_multiple_prefix_match_properly(
      self, query_url, query_prefix, client):
    """Test if top two levels of resources are shown with proper formatting."""
    client.ListObjects.side_effect = [[self.dir1, self.dir2],
                                      self.bucket1_dir1_resources,
                                      self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string(query_url))
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/dir1/:
        gs://bucket1/dir1/object2
        gs://bucket1/dir1/subdir1/
        gs://bucket1/dir1/subdir2/

        gs://bucket1/dir2/:
        gs://bucket1/dir2/subdir3/
        """
    )
    self.assertEqual(output, expected_output)

    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=query_prefix),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir1.prefix),
        mock.call(all_versions=False,
                  bucket_name=self.bucket1.name, delimiter='/',
                  fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir2.prefix)])

  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_double_wildcard_properly(
      self, client):
    """Test if all contents of bucket are shown without formatting."""
    client.ListObjects.side_effect = [self.bucket1_all_objects]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/**'))
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/object1
        gs://bucket1/dir1/object2
        gs://bucket1/dir1/subdir1/object3
        gs://bucket1/dir1/subdir2/object4
        gs://bucket1/dir2/subdir3/object5
        """
    )
    self.assertEqual(output, expected_output)

    client.ListObjects.assert_called_once_with(
        all_versions=False, bucket_name=self.bucket1.name,
        delimiter=None, fields_scope=cloud_api.FieldsScope.SHORT, prefix=None)

  # pylint:disable=line-too-long
  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_double_wildcard_followed_by_single_wildcard_properly(
      self, client):
    """Should list all matches recursively without line breaks or colons."""

    client.ListObjects.side_effect = [self.bucket1_all_objects]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/**/s*'))
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/dir1/subdir1/object3
        gs://bucket1/dir1/subdir2/object4
        gs://bucket1/dir2/subdir3/object5
        """
    )
    self.assertEqual(output, expected_output)

    client.ListObjects.assert_called_once_with(
        all_versions=False, bucket_name=self.bucket1.name,
        delimiter=None, fields_scope=cloud_api.FieldsScope.SHORT, prefix=None)

  @mock_cloud_api.patch
  def test_execute_raises_error_if_no_bucket_matches(self, client):
    """No buckets match pattern."""
    # We don't have to test a no-wildcard query that would trigger GetBucket
    # because Apitools has error handling for that.
    client.ListBuckets.side_effect = [self.bucket_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://pail*'))

    with self.assertRaisesRegex(errors.InvalidUrlError,
                                'One or more URLs matched no objects.'):
      task.execute()

    client.ListBuckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)

  @mock_cloud_api.patch
  def test_execute_raises_error_if_no_object_matches(self, client):
    """No objects or prefixes match."""
    client.GetObjectMetadata.side_effect = api_errors.NotFoundError
    client.ListObjects.side_effect = [[]]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/potato'))

    with self.assertRaisesRegex(errors.InvalidUrlError,
                                'One or more URLs matched no objects.'):
      task.execute()

    client.GetObjectMetadata.assert_called_once_with(
        self.bucket1.name, 'potato', None, cloud_api.FieldsScope.SHORT)
    client.ListObjects.assert_called_once_with(
        all_versions=False,
        bucket_name=self.bucket1.name,
        delimiter='/',
        fields_scope=cloud_api.FieldsScope.SHORT,
        prefix='potato')

  @mock_cloud_api.patch
  def test_execute_lists_provider_with_recursive_flag_properly(
      self, client):
    """Should be the same as no recursive flag."""
    client.ListBuckets.side_effect = [self.bucket_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://'), recursion_flag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1\ngs://bucket2\n'
    self.assertEqual(output, expected_output)

    client.ListBuckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)

  @mock_cloud_api.patch
  def test_execute_lists_bucket_with_recursive_flag_properly(self, client):
    """Test if all bucket content is shown recursively."""
    client.GetBucket.side_effect = [self.bucket1]
    client.ListObjects.side_effect = [self.bucket1_top_level_resources,
                                      self.bucket1_dir1_resources,
                                      self.bucket1_dir1_subdir1_resources,
                                      self.bucket1_dir1_subdir2_resources,
                                      self.bucket1_dir2_resources,
                                      self.bucket1_dir2_subdir3_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1'),
        recursion_flag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1:
        gs://bucket1/object1

        gs://bucket1/dir1/:
        gs://bucket1/dir1/object2

        gs://bucket1/dir1/subdir1/:
        gs://bucket1/dir1/subdir1/object3

        gs://bucket1/dir1/subdir2/:
        gs://bucket1/dir1/subdir2/object4

        gs://bucket1/dir2/:

        gs://bucket1/dir2/subdir3/:
        gs://bucket1/dir2/subdir3/object5
        """
    )
    self.assertEqual(output, expected_output)

    client.GetBucket.assert_called_once_with(
        self.bucket1.name, cloud_api.FieldsScope.SHORT)
    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=None),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir1.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir1.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir2.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir2.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir3.prefix)])

  @mock_cloud_api.patch
  def test_execute_lists_multiple_buckets_with_recursive_flag_properly(
      self, client):
    """Test if all content of all buckets is shown recursively."""
    client.ListBuckets.side_effect = [self.bucket_resources]
    client.ListObjects.side_effect = [self.bucket1_top_level_resources,
                                      self.bucket1_dir1_resources,
                                      self.bucket1_dir1_subdir1_resources,
                                      self.bucket1_dir1_subdir2_resources,
                                      self.bucket1_dir2_resources,
                                      self.bucket1_dir2_subdir3_resources,
                                      self.bucket2_top_level_resources,
                                      self.bucket2_dir_object_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket*'),
        recursion_flag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1:
        gs://bucket1/object1

        gs://bucket1/dir1/:
        gs://bucket1/dir1/object2

        gs://bucket1/dir1/subdir1/:
        gs://bucket1/dir1/subdir1/object3

        gs://bucket1/dir1/subdir2/:
        gs://bucket1/dir1/subdir2/object4

        gs://bucket1/dir2/:

        gs://bucket1/dir2/subdir3/:
        gs://bucket1/dir2/subdir3/object5

        gs://bucket2:
        gs://bucket2/dir_object

        gs://bucket2/dir_object/:
        gs://bucket2/dir_object/object6
        """
    )
    self.assertEqual(output, expected_output)

    client.ListBuckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)
    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=None),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir1.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir1.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir2.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir2.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir3.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket2.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=None),
        mock.call(all_versions=False, bucket_name=self.bucket2.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir_duplicate_of_object.prefix)])

  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_recursive_flag_properly(
      self, client):
    """Should list all contents matching flag recursively with formatting."""
    client.GetObjectMetadata.side_effect = api_errors.NotFoundError
    client.ListObjects.side_effect = [[self.dir2],
                                      self.bucket1_dir2_resources,
                                      self.bucket1_dir2_subdir3_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/dir2'),
        recursion_flag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/dir2/:

        gs://bucket1/dir2/subdir3/:
        gs://bucket1/dir2/subdir3/object5
        """
    )
    self.assertEqual(output, expected_output)
    client.GetObjectMetadata.assert_called_once_with(
        self.bucket1.name, 'dir2', None, cloud_api.FieldsScope.SHORT)
    self.assertEqual(client.ListObjects.mock_calls, [
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix='dir2'),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.dir2.prefix),
        mock.call(all_versions=False, bucket_name=self.bucket1.name,
                  delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT,
                  prefix=self.subdir3.prefix)])

  # pylint:disable=line-too-long
  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_recursive_flag_and_double_wildcard_properly(
      self, client):
    """Should behave like recursive flag is not present."""
    client.ListObjects.side_effect = [self.bucket1_all_objects]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/**'),
        recursion_flag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/object1
        gs://bucket1/dir1/object2
        gs://bucket1/dir1/subdir1/object3
        gs://bucket1/dir1/subdir2/object4
        gs://bucket1/dir2/subdir3/object5
        """
    )
    self.assertEqual(output, expected_output)

    client.ListObjects.assert_called_once_with(
        all_versions=False, bucket_name=self.bucket1.name,
        delimiter=None, fields_scope=cloud_api.FieldsScope.SHORT, prefix=None)

  @parameterized.parameters(
      cloud_list_task._DISPLAY_DETAIL_TO_FIELDS_SCOPE.items())
  @mock.patch.object(wildcard_iterator, 'CloudWildcardIterator')
  def test_execute_translates_display_detail_to_fields_scope(
      self, display_detail, fields_scope, mock_wildcard_iterator):
    """Should translate cloud_list_task arg to cloud_api arg."""
    mock_wildcard_iterator.return_value = [self.object1]
    cloud_url = storage_url.storage_url_from_string('gs://bucket1/object1')

    task = cloud_list_task.CloudListTask(
        cloud_url, display_detail=display_detail, recursion_flag=True)
    task.execute()

    mock_wildcard_iterator.assert_called_once_with(
        cloud_url, fields_scope=fields_scope)


if __name__ == '__main__':
  test_case.main()
