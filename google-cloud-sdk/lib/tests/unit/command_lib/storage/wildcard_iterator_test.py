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

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.api_lib.storage import gcs_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util
from tests.lib.surface.storage import mock_cloud_api
from tests.lib.surface.storage import test_resources

import mock

TEST_BUCKET_NAME = 'bucket1'
TEST_OBJECT_NAMES = [
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
    'f.txt',
    'f_dir/a.txt',
    '$.txt',
]


class ContainsWildcardTests(sdk_test_base.SdkBase):
  """Unit tests for contains_wildcard function."""

  def test_confirms_wildcard_is_present(self):
    """Tests contains_wildcard call."""
    self.assertTrue(wildcard_iterator.contains_wildcard('a*.txt'))
    self.assertTrue(wildcard_iterator.contains_wildcard('?.txt'))
    self.assertTrue(wildcard_iterator.contains_wildcard('a[0-9].txt'))

  def test_confirms_wildcard_is_not_present(self):
    self.assertFalse(wildcard_iterator.contains_wildcard('0-9.txt'))

  def test_ignores_unsupported_wildcards(self):
    self.assertFalse(wildcard_iterator.contains_wildcard('^a.txt'))
    self.assertFalse(wildcard_iterator.contains_wildcard('a.txt$'))


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CloudWildcardIteratorTest(cloud_storage_util.WithGCSCalls,
                                parameterized.TestCase):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)

    self.messages = apis.GetMessagesModule('storage', 'v1')

    self.bucket1 = self.messages.Bucket(name='bucket1')
    self.bucket2 = self.messages.Bucket(name='bucket2')
    self.buckets = [self.bucket1, self.bucket2]
    self.buckets_response = [
        gcs_api._bucket_resource_from_metadata(bucket)
        for bucket in self.buckets
    ]

    self._object_resources_with_generation = [
        test_resources.get_object_resource(
            storage_url.ProviderPrefix.GCS, 'bucket1', 'a.txt', '1'),
        test_resources.get_object_resource(
            storage_url.ProviderPrefix.GCS, 'bucket1', 'a.txt', '2'),
        test_resources.get_object_resource(
            storage_url.ProviderPrefix.GCS, 'bucket1', 'b.txt', '3'),
        test_resources.get_object_resource(
            storage_url.ProviderPrefix.S3, 'bucket1', 'c.txt', 'a1')
    ]

  @parameterized.parameters(cloud_api.FieldsScope)
  @mock_cloud_api.patch
  def test_gcs_root_listing(self, fields_scope, client):
    """Test retrieving provider URL with no specified resource."""
    client.list_buckets.side_effect = [self.buckets_response]

    resource_iterator = wildcard_iterator.get_wildcard_iterator(
        'gs://', fields_scope=fields_scope)
    actual = [resource.metadata.name for resource in resource_iterator]
    expected = [b.name for b in self.buckets]
    self.assertEqual(actual, expected)

    client.list_buckets.assert_called_once_with(
        cloud_api.FieldsScope(fields_scope))

  def test_invalid_scheme_raises_error(self):
    """Test wildcard iterator refuses invalid URL scheme."""
    with self.assertRaises(command_errors.InvalidUrlError):
      wildcard_iterator.get_wildcard_iterator(
          'invalid://', fields_scope=cloud_api.FieldsScope.SHORT)

  @parameterized.parameters(cloud_api.FieldsScope)
  @mock_cloud_api.patch
  def test_gcs_bucket_url_with_wildcard_gets_all_buckets(
      self, fields_scope, client):
    """Test multiple bucket with bucket-level expansion."""
    client.list_buckets.side_effect = [self.buckets_response]

    resource_iterator = wildcard_iterator.get_wildcard_iterator(
        'gs://bucket*', fields_scope=fields_scope)

    self.assertEqual(list(resource_iterator), self.buckets_response)
    client.list_buckets.assert_called_once_with(
        cloud_api.FieldsScope(fields_scope))

  @parameterized.parameters(cloud_api.FieldsScope)
  @mock_cloud_api.patch
  def test_gcs_bucket_url_with_wildcard_gets_single_bucket(
      self, fields_scope, client):
    """Test single bucket with bucket-level expansion."""
    client.list_buckets.side_effect = [self.buckets_response]

    resource_iterator = wildcard_iterator.get_wildcard_iterator(
        'gs://buck*1', fields_scope=fields_scope)

    self.assertEqual(
        list(resource_iterator),
        [gcs_api._bucket_resource_from_metadata(self.bucket1)])
    client.list_buckets.assert_called_once_with(
        cloud_api.FieldsScope(fields_scope))

  @parameterized.parameters(cloud_api.FieldsScope)
  @mock_cloud_api.patch
  def test_gcs_bucket_url_without_wildcard(self, fields_scope, client):
    """Test bucket with no bucket-level expansion."""
    client.get_bucket.side_effect = [self.buckets_response[0]]

    resource_iterator = wildcard_iterator.get_wildcard_iterator(
        'gs://bucket1', fields_scope=fields_scope)
    expected = self.buckets_response[:1]

    self.assertEqual(list(resource_iterator), expected)
    client.get_bucket.assert_called_once_with(
        self.bucket1.name, cloud_api.FieldsScope(fields_scope))

  @parameterized.parameters(cloud_api.FieldsScope)
  @mock_cloud_api.patch
  def test_gcs_bucket_wildcard_and_object_wildcard(self, fields_scope, client):
    """Test multiple object matches in multiple buckets."""
    self.bucket1_object = test_resources.get_object_resource(
        storage_url.ProviderPrefix.GCS, 'bucket1', 'a.txt')
    self.bucket2_object = test_resources.get_object_resource(
        storage_url.ProviderPrefix.GCS, 'bucket2', 'a.txt')
    client.list_buckets.side_effect = [self.buckets_response]
    client.list_objects.side_effect = [[self.bucket1_object],
                                       [self.bucket2_object]]

    resource_iterator = wildcard_iterator.get_wildcard_iterator(
        'gs://bucket*/*', fields_scope=fields_scope)

    self.assertEqual(
        list(resource_iterator), [self.bucket1_object, self.bucket2_object])
    client.list_buckets.assert_called_once_with(
        cloud_api.FieldsScope(fields_scope))
    client.list_objects.mock_calls = [
        mock.call(
            all_versions=False,
            bucket_name='bucket1',
            delimiter='/',
            fields_scope=fields_scope,
            prefix=None),
        mock.call(
            all_versions=False,
            bucket_name='bucket2',
            delimiter='/',
            fields_scope=fields_scope,
            prefix=None)
    ]

  @parameterized.named_parameters([{
      'testcase_name':
          '_list_with_generation_and_wildcard',
      'wildcard_url':
          'gs://bucket1/*.txt#3',
      'request_prefix':
          None,
      'expected_resources': [
          test_resources.get_object_resource(storage_url.ProviderPrefix.GCS,
                                             'bucket1', 'b.txt', '3')
      ],
  }, {
      'testcase_name':
          '_list_with_alphanumeric_generation_and_wildcard',
      'wildcard_url':
          's3://bucket1/*.txt#a1',
      'request_prefix':
          None,
      'expected_resources': [
          test_resources.get_object_resource(storage_url.ProviderPrefix.S3,
                                             'bucket1', 'c.txt', 'a1')
      ],
  }])
  @mock_cloud_api.patch
  def test_object_with_generation(self, client, wildcard_url,
                                  request_prefix, expected_resources):
    """Test with generation."""
    client.list_objects.return_value = self._object_resources_with_generation
    resource_list = list(wildcard_iterator.get_wildcard_iterator(wildcard_url))
    self.assertEqual(resource_list, expected_resources)
    self.assertFalse(client.get_object_metadata.called)
    client.list_objects.assert_called_once_with(
        all_versions=True,
        bucket_name='bucket1',
        delimiter='/',
        fields_scope=cloud_api.FieldsScope.NO_ACL,
        prefix=request_prefix,
    )

  @mock_cloud_api.patch
  def test_object_with_incorrect_generation(self, client):
    """Test with generation."""
    client.get_object_metadata.side_effect = api_errors.NotFoundError
    client.list_objects.return_value = self._object_resources_with_generation

    resources = list(
        wildcard_iterator.get_wildcard_iterator('gs://bucket1/b.txt#2'))

    self.assertEqual(resources, [])
    client.get_object_metadata.assert_called_once_with(
        'bucket1', 'b.txt', '2', cloud_api.FieldsScope.NO_ACL)
    client.list_objects.assert_called_once_with('bucket1', 'b.txt', '/', True,
                                                cloud_api.FieldsScope.NO_ACL)

  @mock_cloud_api.patch
  def test_object_with_generation_without_wildcard(self, client):
    """Test with generation."""
    resource = test_resources.get_object_resource(
        storage_url.ProviderPrefix.GCS, 'bucket1', 'a.txt', '1')
    client.get_object_metadata.return_value = resource
    resource_list = list(
        wildcard_iterator.get_wildcard_iterator('gs://bucket1/a.txt#1'))
    self.assertEqual(resource_list, [resource])
    client.get_object_metadata.assert_called_once_with(
        'bucket1', 'a.txt', '1', cloud_api.FieldsScope.NO_ACL)
    self.assertFalse(client.list_objects.called)

  @mock_cloud_api.patch
  def test_gcs_list_all_object_versions(self, client):
    """Test with generation."""
    client.list_objects.return_value = self._object_resources_with_generation
    resource_list = list(wildcard_iterator.get_wildcard_iterator(
        'gs://bucket1/a.txt', all_versions=True))
    expected_resources = [
        test_resources.get_object_resource(
            storage_url.ProviderPrefix.GCS, 'bucket1', 'a.txt', '1'),
        test_resources.get_object_resource(
            storage_url.ProviderPrefix.GCS, 'bucket1', 'a.txt', '2'),
    ]
    self.assertEqual(resource_list, expected_resources)
    client.list_objects.assert_called_once_with(
        all_versions=True,
        bucket_name='bucket1',
        delimiter='/',
        fields_scope=cloud_api.FieldsScope.NO_ACL,
        prefix='a.txt',
    )

  @parameterized.parameters(cloud_api.FieldsScope)
  @mock_cloud_api.patch
  def test_gcs_get_object_metadata_with_fields_scope(
      self, fields_scope, client):
    """Test if get_object_metadata gets correct fields_scope."""
    test_resource = test_resources.get_object_resource(
        storage_url.ProviderPrefix.GCS, 'b', 'o.txt')
    expected_resources = [test_resource]
    client.get_object_metadata.side_effect = [test_resource]

    resource_list = list(wildcard_iterator.get_wildcard_iterator(
        'gs://b/o.txt', fields_scope=fields_scope))

    self.assertEqual(resource_list, expected_resources)
    client.get_object_metadata.assert_called_once_with(
        bucket_name='b',
        fields_scope=fields_scope,
        generation=None,
        object_name='o.txt',
    )

  @parameterized.parameters(cloud_api.FieldsScope)
  @mock_cloud_api.patch
  def test_gcs_list_object_with_fields_scope(self, fields_scope, client):
    """Test if list_objects gets correct fields_scope."""
    test_resource = test_resources.get_object_resource(
        storage_url.ProviderPrefix.GCS, 'b', 'o.txt')
    expected_resources = [test_resource]
    client.list_objects.side_effect = [expected_resources]

    resource_list = list(wildcard_iterator.get_wildcard_iterator(
        'gs://b/o*', fields_scope=fields_scope))

    self.assertEqual(resource_list, expected_resources)
    client.list_objects.assert_called_once_with(
        all_versions=False,
        bucket_name='b',
        delimiter='/',
        fields_scope=fields_scope,
        prefix='o',
    )

  @parameterized.parameters([
      ('gs://*', 'gs://*'),
      ('gs://**', 'gs://**'),
      ('gs://***', 'gs://*'),
      ('gs://*******', 'gs://*'),
      ('gs://b/***', 'gs://b/*'),
      ('gs://b/o#***', 'gs://b/o#***'),
  ])
  def test_compresses_url_wildcards(self, observed_url_string,
                                    expected_url_string):
    """Test if CloudWildcardIterator compresses URL wildcards correctly."""
    iterator = wildcard_iterator.get_wildcard_iterator(observed_url_string)
    self.assertEqual(iterator._url.url_string, expected_url_string)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class WildcardWithoutApitoolsMockTest(parameterized.TestCase,
                                      sdk_test_base.SdkBase):
  """Test class to test list_objects when multiple API calls may be used."""

  def SetUp(self):
    self.messages = apis.GetMessagesModule('storage', 'v1')
    self.default_projection = (self.messages.StorageObjectsListRequest
                               .ProjectionValueValuesEnum.noAcl)

  def _list_objects_side_effect(self, *unused_args, **kwargs):
    """Mock the list_objects API method sourcing data from TEST_OBJECT_NAMES.

    Args:
      **kwargs (dict): Contains arguments dict for list_objects.

    Yields:
      resource_reference.Resource instances consisting of list of
        ObjectResource and/or PrefixResource instanes
        filtered based on the request prefix and request delimiter.
    """
    objects = []
    prefixes = set([])

    request_prefix = kwargs['prefix'] or ''
    request_delimiter = kwargs['delimiter']
    filtered_object_suffixes = [
        object_name[len(request_prefix):]
        for object_name in TEST_OBJECT_NAMES
        if object_name.startswith(request_prefix)
    ]

    for object_suffix in filtered_object_suffixes:
      if request_delimiter:
        name, _, suffix = object_suffix.partition(request_delimiter)
        if not suffix:  # Leaf object.
          objects.append(
              self.messages.Object(
                  name=request_prefix + object_suffix, bucket=TEST_BUCKET_NAME))
        else:
          prefixes.add('%s%s%s' % (request_prefix, name, request_delimiter))
      else:
        objects.append(
            self.messages.Object(
                name=request_prefix + object_suffix, bucket=TEST_BUCKET_NAME))

    prefixes = sorted(list(prefixes))
    objects = self.messages.Objects(items=objects, prefixes=prefixes)

    for o in objects.items:
      yield gcs_api._object_resource_from_metadata(o)

    for prefix_string in objects.prefixes:
      yield resource_reference.PrefixResource(
          storage_url_object=storage_url.CloudUrl(
              scheme=cloud_api.DEFAULT_PROVIDER,
              bucket_name=kwargs['bucket_name'],
              object_name=prefix_string
          ),
          prefix=prefix_string
      )

  @parameterized.named_parameters([
      {
          'testcase_name': '_list_an_object',
          'wildcard_url': 'gs://bucket1/f.txt',
          'expected_prefixes': [],
          'expected_objects': ['f.txt'],
      },
      {
          'testcase_name': '_list_a_prefix',
          'wildcard_url': 'gs://bucket1/dir1',
          'expected_prefixes': ['dir1/'],
          'expected_objects': [],
      },
      {
          'testcase_name': '_list_a_prefix_with_trailing_delimiter',
          'wildcard_url': 'gs://bucket1/dir1/',
          'expected_prefixes': ['dir1/'],
          'expected_objects': [],
      },
      {
          'testcase_name': '_list_a_bucket',
          'wildcard_url': 'gs://bucket1/*',
          'expected_prefixes': ['dir1/', 'dir2/', 'dir3/', 'f_dir/'],
          'expected_objects': ['f.txt', '$.txt'],
      },
      {
          'testcase_name': '_list_objects_with_double_question_mark_wildcard',
          'wildcard_url': 'gs://bucket1/f.t??',
          'expected_prefixes': [],
          'expected_objects': ['f.txt'],
      },
      {
          'testcase_name': '_list_object_with_prefix_question_mark_wildcard',
          'wildcard_url': 'gs://bucket1/?.txt',
          'expected_prefixes': [],
          'expected_objects': ['f.txt', '$.txt'],
      },
      {
          'testcase_name': '_list_a_dir',
          'wildcard_url': 'gs://bucket1/dir1/*',
          'expected_prefixes': ['dir1/sub1/', 'dir1/sub2/'],
          'expected_objects': [],
      },
      {
          'testcase_name':
              '_list_all_files_with_dir_between_wildcards',
          'wildcard_url':
              'gs://bucket1/*/sub1/*',
          'expected_prefixes': [],
          'expected_objects': [
              'dir1/sub1/a.txt',
              'dir1/sub1/aab.txt',
              'dir2/sub1/aaaaaa.txt',
              'dir2/sub1/d.txt',
          ],
      },
      {
          'testcase_name':
              '_list_all_files_with_extension_two_level_deep',
          'wildcard_url':
              'gs://bucket1/*/sub1/*.txt',
          'expected_prefixes': [],
          'expected_objects': [
              'dir1/sub1/a.txt',
              'dir1/sub1/aab.txt',
              'dir2/sub1/aaaaaa.txt',
              'dir2/sub1/d.txt',
          ],
      },
      {
          'testcase_name': '_folder_wildcard_and_suffix_object_name',
          'wildcard_url': 'gs://bucket1/dir*/sub1/a.txt',
          'expected_prefixes': [],
          'expected_objects': ['dir1/sub1/a.txt'],
      },
      {
          'testcase_name': '_wildcard_before_last_character_of_subdir',
          'wildcard_url': 'gs://bucket1/dir1/su*1/a.txt',
          'expected_prefixes': [],
          'expected_objects': ['dir1/sub1/a.txt'],
      },
      {
          'testcase_name': '_list_with_leaf_wildcard',
          'wildcard_url': 'gs://bucket1/dir3/deeper/sub2/*.txt',
          'expected_prefixes': [],
          'expected_objects': ['dir3/deeper/sub2/b.txt'],
      },
      {
          'testcase_name':
              '_list_with_double_asterisk',
          'wildcard_url':
              'gs://bucket1/dir3/deep**',
          'expected_prefixes': [],
          'expected_objects': [
              'dir3/deeper/sub1/a.txt', 'dir3/deeper/sub2/b.txt',
              'dir3/deeper/sub3/a.txt'
          ],
      },
      {
          'testcase_name':
              '_list_with_double_asterisk_and_suffix_object_name',
          'wildcard_url':
              'gs://bucket1/dir3/deep**/a.txt',
          'expected_prefixes': [],
          'expected_objects': [
              'dir3/deeper/sub1/a.txt', 'dir3/deeper/sub3/a.txt'
          ],
      },
      {
          'testcase_name':
              '_combine_double_and_single_asterisk',
          'wildcard_url':
              'gs://bucket1/dir3/deep**/sub*/a.txt',
          'expected_prefixes': [],
          'expected_objects': [
              'dir3/deeper/sub1/a.txt', 'dir3/deeper/sub3/a.txt'
          ],
      },
      {
          'testcase_name': '_bad_prefix_with_double_asterisks',
          'wildcard_url': 'gs://bucket1/dir3/bad**',
          'expected_prefixes': [],
          'expected_objects': [],
      },
      {
          'testcase_name': '_bad_suffix_with_double_asterisks',
          'wildcard_url': 'gs://bucket1/dir3/deep**/bad/a.txt',
          'expected_prefixes': [],
          'expected_objects': [],
      },
      {
          'testcase_name': '_suffix_directory',
          'wildcard_url': 'gs://bucket1/dir*/sub1',
          'expected_prefixes': ['dir1/sub1/', 'dir2/sub1/'],
          'expected_objects': [],
      },
      {
          'testcase_name': '_suffix_directory_with_trailing_slash',
          'wildcard_url': 'gs://bucket1/dir*/sub1/',
          'expected_prefixes': ['dir1/sub1/', 'dir2/sub1/'],
          'expected_objects': [],
      },
      {
          'testcase_name': '_two_single_wildcards_one_delimiter_apart',
          'wildcard_url': 'gs://bucket1/*/*',
          'expected_prefixes': [
              'dir1/sub1/', 'dir1/sub2/', 'dir2/sub1/', 'dir2/sub2/',
              'dir3/deeper/'
          ],
          'expected_objects': ['f_dir/a.txt'],
      },
      {
          'testcase_name': '_trailing_delimiter_does_not_match_object',
          'wildcard_url': 'gs://bucket1/f*/',
          'expected_prefixes': ['f_dir/'],
          'expected_objects': [],
      },
      {
          'testcase_name': '_matches_everything_in_bucket',
          'wildcard_url': 'gs://bucket1/**',
          'expected_prefixes': [],
          'expected_objects': TEST_OBJECT_NAMES,
      },
      {
          'testcase_name': '_no_matches',
          'wildcard_url': 'gs://bucket1/x0',
          'expected_prefixes': [],
          'expected_objects': [],
      },
  ])
  @mock_cloud_api.patch
  def test_list_objects(self, mock_client, wildcard_url, expected_prefixes,
                        expected_objects):
    mock_client.get_object_metadata.side_effect = api_errors.NotFoundError
    mock_client.list_objects.side_effect = self._list_objects_side_effect

    resource_iterator = wildcard_iterator.get_wildcard_iterator(wildcard_url)
    prefixes, object_names = _get_prefixes_and_object_names(resource_iterator)

    self.assertEqual(prefixes, expected_prefixes)
    self.assertEqual(object_names, expected_objects)

  @mock_cloud_api.patch
  def test_list_objects_without_wildcard(self, mock_client):
    resource = test_resources.get_object_resource(
        storage_url.ProviderPrefix.GCS, 'bucket', 'a/b.txt')
    mock_client.get_object_metadata.side_effect = [resource]

    resources = list(
        wildcard_iterator.get_wildcard_iterator('gs://bucket/a/b.txt'))

    self.assertEqual(resources, [resource])
    mock_client.get_object_metadata.assert_called_once_with(
        'bucket', 'a/b.txt', None, cloud_api.FieldsScope.NO_ACL)
    self.assertFalse(mock_client.list_objects.called)


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


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class FileWildcardIteratorTest(parameterized.TestCase, sdk_test_base.SdkBase):

  def _touch(self, path):
    if os.sep in path:
      dir_path, filename = path.rsplit(os.sep, 1)
      self.Touch(
          os.path.join(self.root_path, dir_path), filename, makedirs=True)
    else:
      self.Touch(self.root_path, path)

  def SetUp(self):
    for file in TEST_OBJECT_NAMES:
      self._touch(file)

  @parameterized.named_parameters([
      {
          'testcase_name': '_list_a_dir',
          'wildcard_url': 'dir1/*',
          'expected_dirs': ['dir1/sub1', 'dir1/sub2'],
          'expected_files': []
      },
      {
          'testcase_name': '_list_a_dir_path_no_wildcard',
          'wildcard_url': 'dir1',
          'expected_dirs': ['dir1'],
          'expected_files': []
      },
      {
          'testcase_name': '_list_no_matching_dir',
          'wildcard_url': 'non_existent_dir',
          'expected_dirs': [],
          'expected_files': []
      },
      {
          'testcase_name': '_list_dir_with_non_existent_file',
          'wildcard_url': 'dir1/non_existent_file',
          'expected_dirs': [],
          'expected_files': []
      },
      {
          'testcase_name': '_list_an_object_no_wildcard',
          'wildcard_url': 'f.txt',
          'expected_dirs': [],
          'expected_files': ['f.txt']
      },
      {
          'testcase_name': '_ignore_unsupported_regex',
          'wildcard_url': '$.txt',
          'expected_dirs': [],
          'expected_files': ['$.txt']
      },
      {
          'testcase_name': '_use_wildcard_and_ignore_unsupported_regex',
          'wildcard_url': '$*txt',
          'expected_dirs': [],
          'expected_files': ['$.txt']
      },
      {
          'testcase_name':
              '_list_all_files_with_extension_two_level_deep',
          'wildcard_url':
              '*/sub1/*.txt',
          'expected_dirs': [],
          'expected_files': [
              'dir1/sub1/a.txt', 'dir1/sub1/aab.txt', 'dir2/sub1/aaaaaa.txt',
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
          'testcase_name':
              '_list_with_double_asterisk',
          'wildcard_url':
              'dir3/**',
          'expected_dirs': [],
          'expected_files': [
              'dir3/deeper/sub1/a.txt', 'dir3/deeper/sub2/b.txt',
              'dir3/deeper/sub3/a.txt'
          ]
      },
      {
          'testcase_name':
              '_list_double_asterisk_followed_by_single_asterisk',
          'wildcard_url':
              'dir3/**/*',
          'expected_dirs': [
              'dir3/deeper', 'dir3/deeper/sub1', 'dir3/deeper/sub2',
              'dir3/deeper/sub3'
          ],
          'expected_files': [
              'dir3/deeper/sub1/a.txt', 'dir3/deeper/sub2/b.txt',
              'dir3/deeper/sub3/a.txt'
          ]
      },
      {
          'testcase_name': '_list_with_double_asterisk_and_suffix_file_name',
          'wildcard_url': 'dir3/**/a.txt',
          'expected_dirs': [],
          'expected_files': [
              'dir3/deeper/sub1/a.txt', 'dir3/deeper/sub3/a.txt'
          ]
      },
      {
          'testcase_name': '_combine_double_and_single_asterisk',
          'wildcard_url': 'dir3/**/sub*/a.txt',
          'expected_dirs': [],
          'expected_files': [
              'dir3/deeper/sub1/a.txt', 'dir3/deeper/sub3/a.txt'
          ]
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
      {
          'testcase_name': '_list_files_with_double_question_mark_wildcard',
          'wildcard_url': 'f.t??',
          'expected_dirs': [],
          'expected_files': ['f.txt'],
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

  @parameterized.parameters([
      ('file://*', '*'),
      ('file://**', '**'),
      ('file://***', '*'),
      ('file://*******', '*'),
      ('file://b/***', 'b/*'),
      ('file://b/o#***', 'b/o#*'),
      ('***', '*'),
  ])
  def test_compresses_url_wildcards(self, observed_url_string,
                                    expected_url_string):
    """Test if FileWildcardIterator compresses URL wildcards correctly."""
    iterator = wildcard_iterator.get_wildcard_iterator(observed_url_string)
    self.assertEqual(iterator._path, expected_url_string)


if __name__ == '__main__':
  test_case.main()
