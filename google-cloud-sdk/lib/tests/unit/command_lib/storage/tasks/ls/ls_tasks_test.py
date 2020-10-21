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

import datetime
import textwrap

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import gcs_resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.ls import cloud_list_task
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util
from tests.lib.surface.storage import mock_cloud_api
from tests.lib.surface.storage import test_resources

import mock


DATETIME = datetime.datetime(1111, 1, 1)
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

    self.object1 = resource_reference.ObjectResource(
        storage_url.storage_url_from_string('gs://bucket1/object1#1'),
        creation_time=DATETIME, size=0)
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
    client.list_buckets.side_effect = [self.bucket_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1\ngs://bucket2\n'
    self.assertEqual(output, expected_output)

    client.list_buckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)

  @parameterized.parameters(('gs://*'), ('gs://**'))
  @mock_cloud_api.patch
  def test_execute_lists_provider_with_wildcards_properly(
      self, query_url, client):
    """Test if all buckets top-level contents are shown, even if '**'."""
    client.list_buckets.side_effect = [self.bucket_resources]
    client.list_objects.side_effect = [
        self.bucket1_top_level_resources, self.bucket2_top_level_resources
    ]

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

    client.list_buckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)
    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=None),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket2.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=None)
    ])

  @parameterized.parameters(('gs://bucket1'), ('gs://bucket1/'))
  @mock_cloud_api.patch
  def test_execute_lists_execute_lists_bucket_url_properly(self, query_url,
                                                           client):
    """Show top-level bucket items are shown but not subdirectory items."""
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

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

    client.get_bucket.assert_called_once_with(
        self.bucket1.name, cloud_api.FieldsScope.SHORT)
    client.list_objects.assert_called_once_with(
        all_versions=False, bucket_name=self.bucket1.name,
        delimiter='/', fields_scope=cloud_api.FieldsScope.SHORT, prefix=None)

  @parameterized.parameters(('gs://b*2'), ('gs://b**2'))
  @mock_cloud_api.patch
  def test_execute_lists_bucket_url_with_wildcard_properly(self, query_url,
                                                           client):
    """Test if list_buckets gets hit but only second bucket is shown."""
    client.list_buckets.side_effect = [self.bucket_resources]
    client.list_objects.side_effect = [self.bucket2_top_level_resources]

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

    client.list_buckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)
    client.list_objects.assert_called_once_with(
        all_versions=False,
        bucket_name=self.bucket2.name,
        delimiter='/',
        fields_scope=cloud_api.FieldsScope.SHORT,
        prefix=None)

  @mock_cloud_api.patch
  def test_execute_lists_object_url_properly(self, client):
    """Test if list_objects is hit and object name is shown."""
    client.get_object_metadata.side_effect = [self.object1]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/object1'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/object1\n'
    self.assertEqual(output, expected_output)

    self.assertFalse(client.list_objects.called)
    client.get_object_metadata.assert_called_once_with(
        self.bucket1.name, self.object1.name, None, cloud_api.FieldsScope.SHORT)

  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_wildcard_properly(self, client):
    """One recursion level of prefixes are shown and formatted."""
    client.list_objects.side_effect = [
        self.bucket1_top_level_resources, self.bucket1_dir1_resources,
        self.bucket1_dir2_resources
    ]

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

    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=None),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir1.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir2.prefix)
    ])

  @mock_cloud_api.patch
  def test_execute_lists_wildcard_followed_by_object_properly(self, client):
    """Any parent directory will do. Make sure object name matches."""
    client.list_objects.side_effect = [
        self.bucket1_top_level_resources, self.bucket1_dir1_resources,
        self.bucket1_dir2_resources
    ]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/*/object2'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/dir1/object2\n'
    self.assertEqual(output, expected_output)

    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=None),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='dir1/object2'),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='dir2/object2')
    ])

  # pylint:disable=line-too-long
  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_single_wildcard_followed_by_single_wildcard_properly(
      self, client):
    """Check if all subdirectories are matched and formatted."""
    client.list_objects.side_effect = [
        self.bucket1_top_level_resources, self.bucket1_dir1_resources,
        self.bucket1_dir1_subdir1_resources,
        self.bucket1_dir1_subdir2_resources, self.bucket1_dir2_resources,
        self.bucket1_dir2_subdir3_resources
    ]

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

    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=None),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir1.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir1.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir2.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir2.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir3.prefix)
    ])

  @mock_cloud_api.patch
  def test_execute_lists_single_prefix_properly(self, client):
    """API should return prefix contents. Task should display contents."""
    client.get_object_metadata.side_effect = api_errors.NotFoundError
    client.list_objects.side_effect = [[self.dir2], self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/dir2/'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/dir2/subdir3/\n'
    self.assertEqual(output, expected_output)

    client.get_object_metadata.assert_called_once_with(
        self.bucket1.name, 'dir2/', None, cloud_api.FieldsScope.SHORT)
    client.list_objects.assert_has_calls([
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='dir2'),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='dir2/')
    ])

  @mock_cloud_api.patch
  def test_execute_lists_prefix_no_trailing_delimiter(self, client):
    """Two API calls are made, and prefix top-level contents are shown."""
    client.get_object_metadata.side_effect = api_errors.NotFoundError
    client.list_objects.side_effect = [[self.dir2], self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/dir2'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/dir2/subdir3/\n'
    self.assertEqual(output, expected_output)

    client.get_object_metadata.assert_called_once_with(
        self.bucket1.name, 'dir2', None, cloud_api.FieldsScope.SHORT)
    client.list_objects.assert_has_calls([
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='dir2'),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir2.prefix)
    ])

  @mock_cloud_api.patch
  def test_execute_lists_prefix_with_center_wildcard(self, client):
    """Two API calls are made, and prefix top-level contents are shown."""
    client.list_objects.side_effect = [[self.dir2], self.bucket1_dir2_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/d*2/'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1/dir2/subdir3/\n'

    self.assertEqual(output, expected_output)
    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='d'),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir2.prefix)
    ])

  @mock_cloud_api.patch
  def test_execute_does_not_list_object_if_trailing_delimiter(self, client):
    """Gsutil would list an object matching the query. Breaking change."""
    client.list_objects.side_effect = [
        self.bucket2_top_level_resources, self.bucket2_dir_object_resources
    ]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket2/d*/'))
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket2/dir_object/object6\n'
    self.assertEqual(output, expected_output)

    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket2.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='d'),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket2.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='dir_object/')
    ])

  @parameterized.parameters(('gs://bucket1/dir*', 'dir'),
                            ('gs://bucket1/d*/', 'd'))
  @mock_cloud_api.patch
  def test_execute_lists_multiple_prefix_match_properly(
      self, query_url, query_prefix, client):
    """Test if top two levels of resources are shown with proper formatting."""
    client.list_objects.side_effect = [[self.dir1,
                                        self.dir2], self.bucket1_dir1_resources,
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

    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=query_prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir1.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir2.prefix)
    ])

  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_double_wildcard_properly(
      self, client):
    """Test if all contents of bucket are shown without formatting."""
    client.list_objects.side_effect = [self.bucket1_all_objects]

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

    client.list_objects.assert_called_once_with(
        all_versions=False,
        bucket_name=self.bucket1.name,
        delimiter=None,
        fields_scope=cloud_api.FieldsScope.SHORT,
        prefix=None)

  # pylint:disable=line-too-long
  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_double_wildcard_followed_by_single_wildcard_properly(
      self, client):
    """Should list all matches recursively without line breaks or colons."""

    client.list_objects.side_effect = [self.bucket1_all_objects]

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

    client.list_objects.assert_called_once_with(
        all_versions=False,
        bucket_name=self.bucket1.name,
        delimiter=None,
        fields_scope=cloud_api.FieldsScope.SHORT,
        prefix=None)

  @mock_cloud_api.patch
  def test_execute_raises_error_if_no_bucket_matches(self, client):
    """No buckets match pattern."""
    # We don't have to test a no-wildcard query that would trigger get_bucket
    # because Apitools has error handling for that.
    client.list_buckets.side_effect = [self.bucket_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://pail*'))

    with self.assertRaisesRegex(errors.InvalidUrlError,
                                'One or more URLs matched no objects.'):
      task.execute()

    client.list_buckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)

  @mock_cloud_api.patch
  def test_execute_raises_error_if_no_object_matches(self, client):
    """No objects or prefixes match."""
    client.get_object_metadata.side_effect = api_errors.NotFoundError
    client.list_objects.side_effect = [[]]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/potato'))

    with self.assertRaisesRegex(errors.InvalidUrlError,
                                'One or more URLs matched no objects.'):
      task.execute()

    client.get_object_metadata.assert_called_once_with(
        self.bucket1.name, 'potato', None, cloud_api.FieldsScope.SHORT)
    client.list_objects.assert_called_once_with(
        all_versions=False,
        bucket_name=self.bucket1.name,
        delimiter='/',
        fields_scope=cloud_api.FieldsScope.SHORT,
        prefix='potato')

  @mock_cloud_api.patch
  def test_execute_lists_provider_with_recursive_flag_properly(
      self, client):
    """Should be the same as no recursive flag."""
    client.list_buckets.side_effect = [self.bucket_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://'), recursion_flag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = 'gs://bucket1\ngs://bucket2\n'
    self.assertEqual(output, expected_output)

    client.list_buckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)

  @mock_cloud_api.patch
  def test_execute_lists_bucket_with_recursive_flag_properly(self, client):
    """Test if all bucket content is shown recursively."""
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [
        self.bucket1_top_level_resources, self.bucket1_dir1_resources,
        self.bucket1_dir1_subdir1_resources,
        self.bucket1_dir1_subdir2_resources, self.bucket1_dir2_resources,
        self.bucket1_dir2_subdir3_resources
    ]

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

    client.get_bucket.assert_called_once_with(self.bucket1.name,
                                              cloud_api.FieldsScope.SHORT)
    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=None),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir1.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir1.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir2.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir2.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir3.prefix)
    ])

  @mock_cloud_api.patch
  def test_execute_lists_multiple_buckets_with_recursive_flag_properly(
      self, client):
    """Test if all content of all buckets is shown recursively."""
    client.list_buckets.side_effect = [self.bucket_resources]
    client.list_objects.side_effect = [
        self.bucket1_top_level_resources, self.bucket1_dir1_resources,
        self.bucket1_dir1_subdir1_resources,
        self.bucket1_dir1_subdir2_resources, self.bucket1_dir2_resources,
        self.bucket1_dir2_subdir3_resources, self.bucket2_top_level_resources,
        self.bucket2_dir_object_resources
    ]

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

    client.list_buckets.assert_called_once_with(cloud_api.FieldsScope.SHORT)
    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=None),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir1.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir1.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir2.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir2.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir3.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket2.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=None),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket2.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir_duplicate_of_object.prefix)
    ])

  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_recursive_flag_properly(
      self, client):
    """Should list all contents matching flag recursively with formatting."""
    client.get_object_metadata.side_effect = api_errors.NotFoundError
    client.list_objects.side_effect = [[self.dir2], self.bucket1_dir2_resources,
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
    client.get_object_metadata.assert_called_once_with(
        self.bucket1.name, 'dir2', None, cloud_api.FieldsScope.SHORT)
    self.assertEqual(client.list_objects.mock_calls, [
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix='dir2'),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.dir2.prefix),
        mock.call(
            all_versions=False,
            bucket_name=self.bucket1.name,
            delimiter='/',
            fields_scope=cloud_api.FieldsScope.SHORT,
            prefix=self.subdir3.prefix)
    ])

  # pylint:disable=line-too-long
  @mock_cloud_api.patch
  def test_execute_lists_object_url_with_recursive_flag_and_double_wildcard_properly(
      self, client):
    """Should behave like recursive flag is not present."""
    client.list_objects.side_effect = [self.bucket1_all_objects]

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

    client.list_objects.assert_called_once_with(
        all_versions=False,
        bucket_name=self.bucket1.name,
        delimiter=None,
        fields_scope=cloud_api.FieldsScope.SHORT,
        prefix=None)

  @parameterized.parameters({
      cloud_list_task.DisplayDetail.SHORT: cloud_api.FieldsScope.SHORT,
      cloud_list_task.DisplayDetail.LONG: cloud_api.FieldsScope.SHORT,
      cloud_list_task.DisplayDetail.FULL: cloud_api.FieldsScope.FULL,
  }.items())
  @mock.patch.object(wildcard_iterator, 'CloudWildcardIterator')
  def test_execute_translates_display_detail_to_fields_scope_for_buckets(
      self, display_detail, fields_scope, mock_wildcard_iterator):
    """Should translate cloud_list_task arg to cloud_api arg."""
    cloud_url = storage_url.storage_url_from_string('gs://')
    # Will need get_metadata_dump for DisplayDetail.FULL.
    self.object1 = gcs_resource_reference.GcsObjectResource(
        cloud_url, metadata=self.messages.Object(name='o'))
    mock_wildcard_iterator.return_value = [self.object1]

    task = cloud_list_task.CloudListTask(
        cloud_url, display_detail=display_detail)
    task.execute()

    mock_wildcard_iterator.assert_called_once_with(
        cloud_url, fields_scope=fields_scope)

  @parameterized.parameters({
      cloud_list_task.DisplayDetail.SHORT: cloud_api.FieldsScope.SHORT,
      cloud_list_task.DisplayDetail.LONG: cloud_api.FieldsScope.NO_ACL,
      cloud_list_task.DisplayDetail.FULL: cloud_api.FieldsScope.FULL,
  }.items())
  @mock.patch.object(wildcard_iterator, 'CloudWildcardIterator')
  def test_execute_translates_display_detail_to_fields_scope_for_non_buckets(
      self, display_detail, fields_scope, mock_wildcard_iterator):
    """Should translate cloud_list_task arg to cloud_api arg."""
    cloud_url = storage_url.storage_url_from_string('gs://bucket1/object1')
    # Will need get_metadata_dump for DisplayDetail.FULL.
    self.object1 = gcs_resource_reference.GcsObjectResource(
        cloud_url, metadata=self.messages.Object(name='o'))
    mock_wildcard_iterator.return_value = [self.object1]

    task = cloud_list_task.CloudListTask(
        cloud_url, display_detail=display_detail)
    task.execute()

    mock_wildcard_iterator.assert_called_once_with(
        cloud_url, fields_scope=fields_scope)

  @mock_cloud_api.patch
  def test_execute_with_all_versions_displays_generation(self, client):
    """All versions flag should add generation to URL."""
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'), all_versions=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1/object1#1
        gs://bucket1/dir1/
        gs://bucket1/dir2/
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_prints_object_details_with_no_size(self, client):
    """Zero-size object metadata line is shown, and prefixes are aligned."""
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.LONG)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
                 0  1111-01-01T00:00:00Z  gs://bucket1/object1
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/
        TOTAL: 1 objects, 0 bytes (0B)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_prints_object_details_with_max_size_length(
      self, client):
    """Max-size object metadata line is shown, and prefixes are aligned."""
    self.object1.size = 9876543210
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.LONG)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        9876543210  1111-01-01T00:00:00Z  gs://bucket1/object1
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/
        TOTAL: 1 objects, 9876543210 bytes (9.20GiB)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_prints_object_details_with_etag(self, client):
    """Etag shown in metadata line, and prefixes are aligned."""
    self.object1.etag = 'CJqt6aup7uoCEAQ='
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.LONG,
        include_etag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
                 0  1111-01-01T00:00:00Z  gs://bucket1/object1  etag=CJqt6aup7uoCEAQ=
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/
        TOTAL: 1 objects, 0 bytes (0B)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_prints_object_details_with_metageneration(
      self, client):
    """Generation and metageneration shown, and prefixes are aligned."""
    self.object1.metageneration = 1
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.LONG,
        all_versions=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
                 0  1111-01-01T00:00:00Z  gs://bucket1/object1#1  metageneration=1
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/
        TOTAL: 1 objects, 0 bytes (0B)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_prints_object_etag_and_metageneration(
      self, client):
    """Etag, generation, and metageneration shown, and prefixes are aligned."""
    self.object1.etag = 'CJqt6aup7uoCEAQ='
    self.object1.metageneration = 1
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.LONG,
        all_versions=True,
        include_etag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
                 0  1111-01-01T00:00:00Z  gs://bucket1/object1#1  metageneration=1  etag=CJqt6aup7uoCEAQ=
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/
        TOTAL: 1 objects, 0 bytes (0B)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_prints_null_object_details(
      self, client):
    """Unknown values print 'None', and prefixes are aligned."""
    self.object1.creation_time = self.object1.size = None
    self.object1.storage_url = storage_url.storage_url_from_string(
        'gs://bucket1/object1')
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.LONG,
        all_versions=True,
        include_etag=True)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
              None                  None  gs://bucket1/object1  metageneration=None  etag=None
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/
        TOTAL: 1 objects, 0 bytes (0B)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_prints_multiple_object_details(
      self, client):
    """Long lists multiple objects and adds their sizes for a TOTAL stat."""
    self.object1.size = 1000
    self.object_duplicate_of_dir.size = 50000000
    self.object_duplicate_of_dir.creation_time = DATETIME
    client.list_buckets.side_effect = [self.bucket_resources]
    client.list_objects.side_effect = [
        self.bucket1_top_level_resources, self.bucket2_top_level_resources
    ]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://*'),
        display_detail=cloud_list_task.DisplayDetail.LONG)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        gs://bucket1:
              1000  1111-01-01T00:00:00Z  gs://bucket1/object1
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/

        gs://bucket2:
          50000000  1111-01-01T00:00:00Z  gs://bucket2/dir_object
                                          gs://bucket2/dir_object/
        TOTAL: 2 objects, 50001000 bytes (47.68MiB)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_converts_timezone_ahead_of_utc(
      self, client):
    """Long lists adds positive timedelta to creation_time."""
    self.object1.creation_time = datetime.datetime(
        1111, 1, 1, tzinfo=datetime.timezone(
            datetime.timedelta(hours=4, seconds=60)))
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.LONG)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
                 0  1110-12-31T19:59:00Z  gs://bucket1/object1
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/
        TOTAL: 1 objects, 0 bytes (0B)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_long_display_detail_converts_timezone_behind_utc(
      self, client):
    """Long lists adds negative timedelta to creation_time."""
    self.object1.creation_time = datetime.datetime(
        1111, 1, 1, tzinfo=datetime.timezone(datetime.timedelta(
            hours=-4, minutes=-40)))
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [self.bucket1_top_level_resources]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.LONG)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
                 0  1111-01-01T04:40:00Z  gs://bucket1/object1
                                          gs://bucket1/dir1/
                                          gs://bucket1/dir2/
        TOTAL: 1 objects, 0 bytes (0B)
        """
    )
    self.assertEqual(output, expected_output)

  @mock_cloud_api.patch
  def test_full_display_detail_prints_buckets_properly(self, client):
    """Test buckets are shown with formatted metadata."""
    bucket1 = gcs_resource_reference.GcsBucketResource(
        storage_url.storage_url_from_string('gs://bucket1'),
        metadata={'hey': 'there'})
    bucket2 = gcs_resource_reference.GcsBucketResource(
        storage_url.storage_url_from_string('gs://bucket2'),
        metadata=self.messages.Bucket(name='b'))
    client.list_buckets.side_effect = [[bucket1, bucket2]]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://'),
        display_detail=cloud_list_task.DisplayDetail.FULL)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        [
        {
          "url": "gs://bucket1",
          "type": "cloud_bucket",
          "metadata": {
            "hey": "there"
          }
        },
        {
          "url": "gs://bucket2",
          "type": "cloud_bucket",
          "metadata": {
            "name": "b"
          }
        }
        ]
        """
    )
    self.assertEqual(output, expected_output)

    client.list_buckets.assert_called_once_with(cloud_api.FieldsScope.FULL)

  @mock_cloud_api.patch
  def test_full_display_detail_prints_objects_properly(self, client):
    """Test objects are shown with formatted metadata."""
    object1 = gcs_resource_reference.GcsObjectResource(
        storage_url.storage_url_from_string('gs://bucket1/object1'),
        metadata=self.messages.Object(name='o'))
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [[object1, self.dir1, self.dir2]]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.FULL)
    task.execute()

    output = self.GetOutput()
    expected_output = textwrap.dedent(
        """\
        [
        {
          "url": "gs://bucket1/object1",
          "type": "cloud_object",
          "metadata": {
            "name": "o"
          }
        },
        {
          "url": "gs://bucket1/dir1/",
          "type": "prefix"
        },
        {
          "url": "gs://bucket1/dir2/",
          "type": "prefix"
        }
        ]
        """
    )
    self.assertEqual(output, expected_output)

    client.get_bucket.assert_called_once_with(
        self.bucket1.name, cloud_api.FieldsScope.FULL)
    client.list_objects.assert_called_once_with(
        all_versions=False, bucket_name=self.bucket1.name,
        delimiter='/', fields_scope=cloud_api.FieldsScope.FULL, prefix=None)

  @mock_cloud_api.patch
  def test_full_display_detail_prints_nothing_for_no_matches(self, client):
    """Test nothing is shown for no prefix match."""
    client.get_bucket.side_effect = [self.bucket1]
    client.list_objects.side_effect = [[]]

    task = cloud_list_task.CloudListTask(
        storage_url.storage_url_from_string('gs://bucket1/'),
        display_detail=cloud_list_task.DisplayDetail.FULL)
    task.execute()

    output = self.GetOutput()
    expected_output = '\n'
    self.assertEqual(output, expected_output)

    client.get_bucket.assert_called_once_with(
        self.bucket1.name, cloud_api.FieldsScope.FULL)
    client.list_objects.assert_called_once_with(
        all_versions=False, bucket_name=self.bucket1.name,
        delimiter='/', fields_scope=cloud_api.FieldsScope.FULL, prefix=None)


if __name__ == '__main__':
  test_case.main()
