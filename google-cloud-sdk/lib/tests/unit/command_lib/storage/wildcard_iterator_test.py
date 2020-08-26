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

"""Unit tests for path expansion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import gcs_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util
import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CloudWildCardIteratorTest(cloud_storage_util.WithGCSCalls):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)

    self.messages = apis.GetMessagesModule('storage', 'v1')

    self.bucket1 = self.messages.Bucket(name='bucket1')
    self.bucket2 = self.messages.Bucket(name='bucket2')
    self.buckets_response = self.messages.Buckets(items=[self.bucket1,
                                                         self.bucket2])

    self.object_with_generation = self.messages.Object(
        name='a.txt', generation=1)
    self.object1 = self.messages.Object(name='dir1/sub1/a.txt')
    self.objects = [
        self.messages.Object(name='dir1/sub1/a.txt'),
        self.messages.Object(name='dir1/sub1/aab.txt'),
        self.messages.Object(name='dir1/sub2/aaaa.txt'),
        self.messages.Object(name='dir1/sub2/c.txt'),
        self.messages.Object(name='dir2/sub1/aaaaaa.txt'),
        self.messages.Object(name='dir2/sub1/d.txt'),
        self.messages.Object(name='dir2/sub2/aaaaaaaa.txt'),
        self.messages.Object(name='dir2/sub2/e.txt'),
        self.messages.Object(name='dir3/deeper/sub1/a.txt'),
        self.messages.Object(name='dir3/deeper/sub2/b.txt')
    ]
    self.bucket1_resp = self.messages.Objects(
        items=self.objects,
        prefixes=[
            'dir1', 'dir2', 'dir3'
        ]
    )

  @mock.patch.object(api_factory, 'get_api')
  def test_gcs_root_listing(self, mock_get_api):
    """Test retrieving provider URL with no specified resource."""
    mock_get_api.return_value = gcs_api.GcsApi()
    self.apitools_client.buckets.List.Expect(
        self.messages.StorageBucketsListRequest(
            project=self.project,
            projection=(self.messages.StorageBucketsListRequest.
                        ProjectionValueValuesEnum.noAcl)
        ),
        response=self.buckets_response
    )

    bucket_iterator = wildcard_iterator.get_wildcard_iterator('gs://')
    actual = sorted([bucket.metadata_object.name for bucket in bucket_iterator])
    self.assertEqual(sorted({'bucket1', 'bucket2'}), actual)

  @mock.patch.object(api_factory, 'get_api')
  def test_gcs_bucket_url_with_wildcard(self, mock_get_api):
    """Test bucket with no bucket-level expansion."""
    # Quick fix for flaky tests.
    # TODO(b/163796935) Replace with mock_cloud_api once cl/326521545 is out.
    mock_get_api.return_value = gcs_api.GcsApi()
    self.apitools_client.buckets.List.Expect(
        self.messages.StorageBucketsListRequest(
            project=self.project,
            projection=(self.messages.StorageBucketsListRequest.
                        ProjectionValueValuesEnum.noAcl)
        ),
        response=self.buckets_response
    )
    bucket_iterator = wildcard_iterator.get_wildcard_iterator('gs://bucket*')
    actual = []
    for bucket in bucket_iterator:
      self.assertIsInstance(bucket, resource_reference.BucketResource)
      actual.append(bucket.metadata_object.name)
    self.assertCountEqual(actual, ['bucket1', 'bucket2'])

  @mock.patch.object(api_factory, 'get_api')
  def test_gcs_bucket_url_without_wildcard(self, mock_get_api):
    """Test bucket with no bucket-level expansion."""
    mock_get_api.return_value = gcs_api.GcsApi()
    self.apitools_client.buckets.Get.Expect(
        self.messages.StorageBucketsGetRequest(
            bucket='bucket1',
            projection=(self.messages.StorageBucketsGetRequest.
                        ProjectionValueValuesEnum.noAcl)
        ),
        response=self.bucket1
    )
    bucket_iterator = wildcard_iterator.get_wildcard_iterator('gs://bucket1')
    bucket_list = list(bucket_iterator)
    self.assertEqual(len(bucket_list), 1)
    self.assertIsInstance(bucket_list[0], resource_reference.BucketResource)
    self.assertEqual(bucket_list[0].metadata_object, self.bucket1)

  @mock.patch.object(api_factory, 'get_api')
  def test_gcs_object_url_without_wildcard(self, mock_get_api):
    """Test object with no object-level expansion."""
    mock_get_api.return_value = gcs_api.GcsApi()
    self.apitools_client.objects.Get.Expect(
        self.messages.StorageObjectsGetRequest(
            bucket='bucket1',
            object='sub1/a.txt',
            projection=(self.messages.StorageObjectsGetRequest.
                        ProjectionValueValuesEnum.noAcl)
        ),
        response=self.object1
    )
    object_iterator = wildcard_iterator.get_wildcard_iterator(
        'gs://bucket1/sub1/a.txt')
    object_list = list(object_iterator)
    self.assertEqual(len(object_list), 1)
    self.assertIsInstance(object_list[0], resource_reference.ObjectResource)
    self.assertEqual(object_list[0].metadata_object, self.object1)

  @mock.patch.object(api_factory, 'get_api')
  def test_gcs_object_url_with_generation_without_wildcard(self, mock_get_api):
    """Test object with a generation parameter and no object-level expansion."""
    mock_get_api.return_value = gcs_api.GcsApi()
    self.apitools_client.objects.Get.Expect(
        self.messages.StorageObjectsGetRequest(
            bucket='bucket1',
            object='a.txt',
            generation=1,
            projection=(self.messages.StorageObjectsGetRequest.
                        ProjectionValueValuesEnum.noAcl)
        ),
        response=self.object_with_generation
    )
    object_iterator = wildcard_iterator.get_wildcard_iterator(
        'gs://bucket1/a.txt#1')
    object_list = list(object_iterator)
    self.assertEqual(len(object_list), 1)
    self.assertIsInstance(object_list[0], resource_reference.ObjectResource)
    self.assertEqual(object_list[0].metadata_object,
                     self.object_with_generation)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GcsWildCardWithoutApitoolsMockTest(parameterized.TestCase,
                                         sdk_test_base.SdkBase):
  """Test class to test ListObjects without using apitools.mock.

  apitools_client.objects.List.Expect does work for testing global_params or
  for cases where we make multiple API calls. Hence, instead of relying on
  apitools.mock, we will mock api client directly in each test case.
  """

  def SetUp(self):
    self.messages = apis.GetMessagesModule('storage', 'v1')
    self.default_projection = (self.messages.StorageObjectsListRequest
                               .ProjectionValueValuesEnum.noAcl)
    self.object_names = [
        'dir1/sub1/a.txt',
        'dir1/sub1/aab.txt',
        'dir1/sub2/aaaa.txt',
        'dir1/sub2/c.txt',
        'dir2/sub1/aaaaaa.txt',
        'dir2/sub1/d.txt',
        'dir2/sub2/aaaaaaaa.txt',
        'dir2/sub2/e.txt',
        'dir3/deeper/sub1/a.txt',
        'dir3/deeper/sub2/b.txt',
        'dir3/deeper/sub3/a.txt',
        'f.txt'
    ]

  def _list_objects_side_effect(self, request, *unused_args, **unused_kwargs):
    """Mock the ListObjects API method.

    Args:
      request (apitools.messages.StorageObjectsListRequest): request object
        that holds the prefix and delimiter information.
    Returns:
      apitools.messages.Objects instance consisting of list of
        apitools.messages.Object instances and list of prefix strings
        filtered based on the request.prefix and request.delimiter.
    """
    objects = []
    prefixes = set([])

    request_prefix = request.prefix or ''
    filtered_object_suffixes = [
        object_name[len(request_prefix):] for object_name in self.object_names
        if object_name.startswith(request_prefix)
    ]

    for object_suffix in filtered_object_suffixes:
      if request.delimiter:
        name, _, suffix = object_suffix.partition(request.delimiter)
        if not suffix:  # Leaf object.
          objects.append(
              self.messages.Object(name=request_prefix + object_suffix))
        else:
          prefixes.add('%s%s%s' % (request_prefix, name, request.delimiter))
      else:
        objects.append(
            self.messages.Object(name=request_prefix + object_suffix))

    prefixes = sorted(list(prefixes))
    return self.messages.Objects(items=objects, prefixes=prefixes)

  @parameterized.named_parameters([
      {
          'testcase_name': '_list_a_bucket',
          'wildcard_url': 'gs://bucket1/*',
          'expected_prefixes': ['dir1/', 'dir2/', 'dir3/'],
          'expected_objects': ['f.txt']
      },
      {
          'testcase_name': '_list_a_dir',
          'wildcard_url': 'gs://bucket1/dir1/*',
          'expected_prefixes': ['dir1/sub1/', 'dir1/sub2/'],
          'expected_objects': []
      },
      {
          'testcase_name': '_list_all_files_with_extension_two_level_deep',
          'wildcard_url': 'gs://bucket1/*/sub1/*.txt',
          'expected_prefixes': [],
          'expected_objects': [
              'dir1/sub1/a.txt',
              'dir1/sub1/aab.txt',
              'dir2/sub1/aaaaaa.txt',
              'dir2/sub1/d.txt'
          ]
      },
      {
          'testcase_name': '_folder_wildcard_and_suffix_object_name',
          'wildcard_url': 'gs://bucket1/dir*/sub1/a.txt',
          'expected_prefixes': [],
          'expected_objects': ['dir1/sub1/a.txt']
      },
      {
          'testcase_name': '_list_with_leaf_wildcard',
          'wildcard_url': 'gs://bucket1/dir3/deeper/sub2/*.txt',
          'expected_prefixes': [],
          'expected_objects': ['dir3/deeper/sub2/b.txt']
      },
      {
          'testcase_name': '_list_with_double_asterisk',
          'wildcard_url': 'gs://bucket1/dir3/deep**',
          'expected_prefixes': [],
          'expected_objects': ['dir3/deeper/sub1/a.txt',
                               'dir3/deeper/sub2/b.txt',
                               'dir3/deeper/sub3/a.txt']
      },
      {
          'testcase_name': '_list_with_double_asterisk_and_suffix_object_name',
          'wildcard_url': 'gs://bucket1/dir3/deep**/a.txt',
          'expected_prefixes': [],
          'expected_objects': ['dir3/deeper/sub1/a.txt',
                               'dir3/deeper/sub3/a.txt']
      },
      {
          'testcase_name': '_combine_double_and_single_asterisk',
          'wildcard_url': 'gs://bucket1/dir3/deep**/sub*/a.txt',
          'expected_prefixes': [],
          'expected_objects': ['dir3/deeper/sub1/a.txt',
                               'dir3/deeper/sub3/a.txt']
      },
      {
          'testcase_name': '_bad_prefix_with_double_asterisks',
          'wildcard_url': 'gs://bucket1/dir3/bad**',
          'expected_prefixes': [],
          'expected_objects': []
      },
      {
          'testcase_name': '_bad_suffix_with_double_asterisks',
          'wildcard_url': 'gs://bucket1/dir3/deep**/bad/a.txt',
          'expected_prefixes': [],
          'expected_objects': []
      },
      {
          'testcase_name': '_suffix_directory',
          'wildcard_url': 'gs://bucket1/dir*/sub1',
          'expected_prefixes': ['dir1/sub1/', 'dir2/sub1/'],
          'expected_objects': []
      },
      {
          'testcase_name': '_suffix_directory_with_trailing_slash',
          'wildcard_url': 'gs://bucket1/dir*/sub1/',
          'expected_prefixes': [],
          'expected_objects': []
      },
  ])
  @mock.patch.object(api_factory, 'get_api')
  @mock.patch.object(apis, 'GetClientInstance')
  def test_gcs_list_with_wildcard(self, mock_get_client_instance, mock_get_api,
                                  wildcard_url, expected_prefixes,
                                  expected_objects):
    mock_api_client = mock.MagicMock(spec=['objects'])
    mock_api_client.objects.List.side_effect = self._list_objects_side_effect
    mock_get_client_instance.return_value = mock_api_client

    mock_get_api.return_value = gcs_api.GcsApi()

    resource_iterator = wildcard_iterator.get_wildcard_iterator(wildcard_url)
    mock_get_api.assert_called_once_with(cloud_api.ProviderPrefix.GCS)
    mock_get_client_instance.assert_called_once_with('storage', 'v1')

    prefixes, object_names = _get_prefixes_and_object_names(resource_iterator)
    self.assertEqual(prefixes, expected_prefixes)
    self.assertEqual(object_names, expected_objects)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class FileWildcardIteratorTest(parameterized.TestCase, sdk_test_base.SdkBase):

  def SetUp(self):
    self._Touch('dir1/sub1/a.txt')
    self._Touch('dir1/sub1/aab.txt')
    self._Touch('dir1/sub2/aaaa.txt')
    self._Touch('dir1/sub2/c.txt')
    self._Touch('dir1/f.txt')
    self._Touch('dir2/sub1/aaaaaa.txt')
    self._Touch('dir2/sub1/d.txt')
    self._Touch('dir2/sub2/aaaaaaaa.txt')
    self._Touch('dir2/sub2/e.txt')
    self._Touch('dir3/deeper/sub1/a.txt')
    self._Touch('dir3/deeper/sub2/b.txt')
    self._Touch('dir3/deeper/sub3/a.txt')

  def _Touch(self, path):
    dir_path, filename = path.rsplit('/', 1)
    self.Touch(os.path.join(self.root_path, dir_path), filename, makedirs=True)

  @parameterized.named_parameters([
      {
          'testcase_name': '_list_a_dir',
          'wildcard_url': 'dir1/*',
          'expected_dirs': ['dir1/sub1', 'dir1/sub2'],
          'expected_files': ['dir1/f.txt']
      },
      {
          'testcase_name': '_list_all_files_with_extension_two_level_deep',
          'wildcard_url': '*/sub1/*.txt',
          'expected_dirs': [],
          'expected_files': [
              'dir1/sub1/a.txt',
              'dir1/sub1/aab.txt',
              'dir2/sub1/aaaaaa.txt',
              'dir2/sub1/d.txt'
          ]
      },
      {
          'testcase_name': '_folder_wildcard_and_suffix_file_name',
          'wildcard_url': 'dir*/sub1/a.txt',
          'expected_dirs': [],
          'expected_files': ['dir1/sub1/a.txt']
      },
      {
          'testcase_name': '_list_with_leaf_wildcard',
          'wildcard_url': 'dir3/deeper/sub2/*.txt',
          'expected_dirs': [],
          'expected_files': ['dir3/deeper/sub2/b.txt']
      },
      {
          'testcase_name': '_list_with_double_asterisk',
          'wildcard_url': 'dir3/**',
          'expected_dirs': ['dir3/deeper',
                            'dir3/deeper/sub1',
                            'dir3/deeper/sub2',
                            'dir3/deeper/sub3'],
          'expected_files': ['dir3/deeper/sub1/a.txt',
                             'dir3/deeper/sub2/b.txt',
                             'dir3/deeper/sub3/a.txt']
      },
      {
          'testcase_name': '_list_with_double_asterisk_and_suffix_file_name',
          'wildcard_url': 'dir3/**/a.txt',
          'expected_dirs': [],
          'expected_files': ['dir3/deeper/sub1/a.txt',
                             'dir3/deeper/sub3/a.txt']
      },
      {
          'testcase_name': '_combine_double_and_single_asterisk',
          'wildcard_url': 'dir3/**/sub*/a.txt',
          'expected_dirs': [],
          'expected_files': ['dir3/deeper/sub1/a.txt',
                             'dir3/deeper/sub3/a.txt']
      },
      {
          'testcase_name': '_bad_prefix_with_double_asterisks',
          'wildcard_url': 'dir3/bad/**',
          'expected_dirs': [],
          'expected_files': []
      },
      {
          'testcase_name': '_bad_suffix_with_double_asterisks',
          'wildcard_url': 'dir3/**/bad/a.txt',
          'expected_dirs': [],
          'expected_files': []
      },
      {
          'testcase_name': '_suffix_directory',
          'wildcard_url': 'dir*/sub1',
          'expected_dirs': ['dir1/sub1', 'dir2/sub1'],
          'expected_files': []
      },
      {
          'testcase_name': '_suffix_directory_with_trailing_slash',
          'wildcard_url': 'dir*/sub1/',
          'expected_dirs': ['dir1/sub1/', 'dir2/sub1/'],
          'expected_files': []
      },
  ])
  def test_file_wildcard(self, wildcard_url, expected_dirs, expected_files):
    processed_url_str = os.path.join(self.root_path,
                                     wildcard_url.replace('/', os.sep))
    processed_expected_dirs = [
        os.path.join(self.root_path, d.replace('/', os.sep))
        for d in expected_dirs
    ]
    processed_expected_files = [
        os.path.join(self.root_path, f.replace('/', os.sep))
        for f in expected_files
    ]

    file_wildcard_iterator = wildcard_iterator.get_wildcard_iterator(
        processed_url_str)
    dirs, files = _get_prefixes_and_object_names(file_wildcard_iterator)
    self.assertCountEqual(dirs, processed_expected_dirs)
    self.assertCountEqual(files, processed_expected_files)


def _get_prefixes_and_object_names(resource_iterator):
  """Iterate over resources and return lists of names of prefixes and objects.

  Args:
    resource_iterator (WildcardIterator): This can be an instance of the
      CloudWildcardIterator or the FileWildcardIterator.
  Returns:
    A tuple of two lists where the first list is a list of all prefix names
    (dir names in case of FileWildcardIterator) and the second list is
    a list of all object names (file names in case of FileWildcardIterator).
  """
  if isinstance(resource_iterator, wildcard_iterator.FileWildcardIterator):
    prefix_resource_type = resource_reference.FileDirectoryResource
    object_resource_type = resource_reference.FileObjectResource
  else:
    prefix_resource_type = resource_reference.PrefixResource
    object_resource_type = resource_reference.ObjectResource

  prefixes = []
  object_names = []
  for resource in resource_iterator:
    if isinstance(resource, prefix_resource_type):
      prefixes.append(resource.storage_url.object_name)
    elif isinstance(resource, object_resource_type):
      object_names.append(resource.storage_url.object_name)
    else:
      break
  return prefixes, object_names


if __name__ == '__main__':
  test_case.main()
