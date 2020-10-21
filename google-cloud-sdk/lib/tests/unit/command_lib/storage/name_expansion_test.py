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
"""Unit tests for name expansion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import storage_url
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util
from tests.lib.surface.storage import mock_cloud_api
from tests.lib.surface.storage import test_resources
import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class NameExpansionTest(cloud_storage_util.WithGCSCalls,
                        parameterized.TestCase):

  def SetUp(self):

    self.messages = apis.GetMessagesModule('storage', 'v1')

    # Test resources tree structure:
    # bucket1:
    #   dir1
    #     b/c/d.txt
    #     b.txt
    #   dir2/
    #     b/c/d.txt
    #     b/e.txt
    #   dirobj.txt
    #   foo/
    #     b/c/d.txt
    #     b/e.txt

    self.dir1 = test_resources.from_url_string('gs://bucket/dir1/')
    self.dir2 = test_resources.from_url_string('gs://bucket/dir2/')
    self.foo_dir = test_resources.from_url_string('gs://bucket/foo/')
    self.dirobj = test_resources.from_url_string('gs://bucket/dirobj.txt')
    self.objects_with_dir_prefix = [self.dir1, self.dir2, self.dirobj]
    self.dir1_objects = [
        test_resources.from_url_string('gs://bucket/dir1/b/c/d.txt'),
        test_resources.from_url_string('gs://bucket/dir1/b.txt')
    ]
    self.dir2_objects = [
        test_resources.from_url_string('gs://bucket/dir2/b/c/d.txt'),
        test_resources.from_url_string('gs://bucket/dir2/b/e.txt'),
    ]

    self.foo_dir_objects = [
        test_resources.from_url_string('gs://bucket/foo/b/c/d.txt'),
        test_resources.from_url_string('gs://bucket/foo/b/e.txt'),
    ]

  @mock_cloud_api.patch
  def test_invalid_url(self, client):
    """Test that invalid URL raises InvalidUrlError."""
    client.list_objects.return_value = []

    with self.assertRaisesRegex(errors.InvalidUrlError,
                                r'gs://bucket/bad1\* matched no objects'):
      list(name_expansion.NameExpansionIterator([
          'gs://bucket/bad1*', 'gs://bucket/bad2*']))

    client.list_objects.assert_called_once_with(
        all_versions=False,
        bucket_name='bucket',
        delimiter='/',
        fields_scope=cloud_api.FieldsScope.NO_ACL,
        prefix='bad1')

  @mock_cloud_api.patch
  def test_expansion_without_recursion(self, client):
    client.list_objects.side_effect = [
        # Response for 'gs://a_bucket1/dir*' expansion.
        self.objects_with_dir_prefix,
        # Response for 'gs://a_bucket1/foo'.
        [self.foo_dir]
    ]

    name_expansion_results = list(name_expansion.NameExpansionIterator(
        ['gs://bucket/dir*', 'gs://bucket/foo*']))

    expected_name_expansion_results = [
        name_expansion.NameExpansionResult(resource, resource.storage_url)
        for resource in self.objects_with_dir_prefix + [self.foo_dir]
    ]
    expected_list_objects_calls = [
        mock.call(all_versions=False, bucket_name='bucket', delimiter='/',
                  fields_scope=cloud_api.FieldsScope.NO_ACL, prefix='dir'),
        mock.call(all_versions=False, bucket_name='bucket', delimiter='/',
                  fields_scope=cloud_api.FieldsScope.NO_ACL, prefix='foo'),
    ]

    self.assertEqual(name_expansion_results, expected_name_expansion_results)
    self.assertEqual(client.list_objects.mock_calls,
                     expected_list_objects_calls)

  @mock_cloud_api.patch
  def test_expansion_with_recursion(self, client):
    client.list_objects.side_effect = [
        # Response for 'gs://bucket/dir*' expansion.
        self.objects_with_dir_prefix,
        # Response for 'gs://bucket/dir1/**' expansion.
        self.dir1_objects,
        # Response for 'gs://bucket/dir2/**' expansion.
        self.dir2_objects,
        # Response for 'gs://bucket/foo'.
        [self.foo_dir],
        # Response for 'gs://bucket/foo/**'.
        self.foo_dir_objects
    ]

    name_expansion_results = list(name_expansion.NameExpansionIterator(
        ['gs://bucket/dir*', 'gs://bucket/foo*'],
        recursion_requested=True))

    expected_nam_expansion_results = []
    # Result for gs://bucket/dir*. All objects under dir1.
    for resource in self.dir1_objects:
      expected_nam_expansion_results.append(name_expansion.NameExpansionResult(
          resource, self.dir1.storage_url))
    # Result for gs://bucket/dir*. All objects under dir2.
    for resource in self.dir2_objects:
      expected_nam_expansion_results.append(name_expansion.NameExpansionResult(
          resource, self.dir2.storage_url))
  # Result for gs://bucket/dir*. The dirobj.txt object.
    expected_nam_expansion_results.append(name_expansion.NameExpansionResult(
        self.dirobj, self.dirobj.storage_url))
    # Result for gs://bucket/foo*.
    for resource in self.foo_dir_objects:
      expected_nam_expansion_results.append(name_expansion.NameExpansionResult(
          resource, self.foo_dir.storage_url))

    expected_list_objects_calls = [
        mock.call(all_versions=False, bucket_name='bucket', delimiter='/',
                  fields_scope=cloud_api.FieldsScope.NO_ACL, prefix='dir'),
        mock.call(all_versions=False, bucket_name='bucket', delimiter=None,
                  fields_scope=cloud_api.FieldsScope.NO_ACL, prefix='dir1/'),
        mock.call(all_versions=False, bucket_name='bucket', delimiter=None,
                  fields_scope=cloud_api.FieldsScope.NO_ACL, prefix='dir2/'),
        mock.call(all_versions=False, bucket_name='bucket', delimiter='/',
                  fields_scope=cloud_api.FieldsScope.NO_ACL, prefix='foo'),
        mock.call(all_versions=False, bucket_name='bucket', delimiter=None,
                  fields_scope=cloud_api.FieldsScope.NO_ACL, prefix='foo/')
    ]
    self.assertEqual(name_expansion_results, expected_nam_expansion_results)
    self.assertEqual(client.list_objects.mock_calls,
                     expected_list_objects_calls)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class NameExpansionResultTest(test_case.TestCase):

  def test_equality(self):
    object1 = name_expansion.NameExpansionResult(
        test_resources.from_url_string('gs://bucket/dir1/obj1.txt'),
        storage_url.storage_url_from_string('gs://bucket/dir1/'))
    object2 = name_expansion.NameExpansionResult(
        test_resources.from_url_string('gs://bucket/dir1/obj1.txt'),
        storage_url.storage_url_from_string('gs://bucket/dir1/'))
    self.assertEqual(object1, object2)

  def test_non_equality_with_different_resources(self):
    """Test with different resources but same expanded urls."""
    object1 = name_expansion.NameExpansionResult(
        test_resources.from_url_string('gs://bucket/dir1/obj1.txt'),
        storage_url.storage_url_from_string('gs://bucket/dir1/'))
    object2 = name_expansion.NameExpansionResult(
        test_resources.from_url_string('gs://bucket/dir1/obj2.txt'),
        storage_url.storage_url_from_string('gs://bucket/dir1/'))
    self.assertNotEqual(object1, object2)

  def test_non_equality_with_different_expanded_urls(self):
    """Test with same resources but different expanded URLs."""
    object1 = name_expansion.NameExpansionResult(
        test_resources.from_url_string('gs://bucket/dir1/obj1.txt'),
        storage_url.storage_url_from_string('gs://bucket/dir1/'))
    object2 = name_expansion.NameExpansionResult(
        test_resources.from_url_string('gs://bucket/dir1/obj1.txt'),
        storage_url.storage_url_from_string('gs://bucket/dir2/'))
    self.assertNotEqual(object1, object2)

  def test_str_method(self):
    expanded_result = name_expansion.NameExpansionResult(
        test_resources.from_url_string('gs://bucket/dir1/obj1.txt'),
        storage_url.storage_url_from_string('gs://bucket/dir1/'))
    self.assertEqual(str(expanded_result), 'gs://bucket/dir1/obj1.txt')


if __name__ == '__main__':
  test_case.main()
