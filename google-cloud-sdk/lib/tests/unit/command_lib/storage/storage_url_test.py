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

"""Unit tests for Storage URL."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import os

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


ExpectedStorageUrl = collections.namedtuple(
    'ExpectedStorageUrl',
    ['scheme', 'bucket', 'obj', 'gen']
)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class CloudStorageUrlTest(sdk_test_base.WithFakeAuth, parameterized.TestCase):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)
    self.client = api_mock.Client(
        client_class=apis.GetClientClass('storage', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

    self.messages = apis.GetMessagesModule('storage', 'v1')

  @parameterized.named_parameters([
      {
          'testcase_name': '_object_without_version',
          'url_str': 'gs://bucket/obj/a/b/c',
          'expected_url_obj': ExpectedStorageUrl(
              scheme='gs', bucket='bucket', obj='obj/a/b/c', gen=None)
      },
      {
          'testcase_name': '_object_with_version',
          'url_str': 'gs://bucket/obj/a/b/c#1234',
          'expected_url_obj': ExpectedStorageUrl(
              scheme='gs', bucket='bucket', obj='obj/a/b/c', gen='1234')
      },
      {
          'testcase_name': '_bucketurl',
          'url_str': 'gs://bucket/',
          'expected_url_obj': ExpectedStorageUrl(
              scheme='gs', bucket='bucket', obj=None, gen=None)
      },
      {
          'testcase_name': '_s3provider',
          'url_str': 's3://bucket/obj/a/b/c',
          'expected_url_obj': ExpectedStorageUrl(
              scheme='s3', bucket='bucket', obj='obj/a/b/c', gen=None)
      },
      {
          'testcase_name': '_providerurl',
          'url_str': 'gs://',
          'expected_url_obj': ExpectedStorageUrl(
              scheme='gs', bucket=None, obj=None, gen=None)
      }
  ])
  def test_url_from_string(self, url_str, expected_url_obj):
    cloud_url_obj = storage_url.storage_url_from_string(url_str)
    self.assertEqual(cloud_url_obj.scheme, expected_url_obj.scheme)
    self.assertEqual(cloud_url_obj.bucket_name, expected_url_obj.bucket,)
    self.assertEqual(cloud_url_obj.object_name, expected_url_obj.obj)
    self.assertEqual(cloud_url_obj.generation, expected_url_obj.gen)

  @parameterized.named_parameters([
      {
          'testcase_name': '_invalid_scheme',
          'url_str': 'invalid://bucket'
      },
      {
          'testcase_name': '_invalid_object_single_period',
          'url_str': 'gs://bucket/.'
      },
      {
          'testcase_name': '_invalid_object_double_period',
          'url_str': 'gs://bucket/..'
      },
  ])
  def test_invalid_url(self, url_str):
    self.assertRaises(errors.InvalidUrlError,
                      storage_url.storage_url_from_string, url_str)

  @parameterized.named_parameters([
      {
          'testcase_name': '_provider',
          'cloudurl_args': ('gs',),
          'expected': 'gs://'
      },
      {
          'testcase_name': '_bucketurl',
          'cloudurl_args': ('gs', 'bucket'),
          'expected': 'gs://bucket'
      },
      {
          'testcase_name': '_objecturl',
          'cloudurl_args': ('gs', 'bucket', 'obj/a/b'),
          'expected': 'gs://bucket/obj/a/b'
      },
      {
          'testcase_name': '_objecturl_with_version',
          'cloudurl_args': ('gs', 'bucket', 'obj/a/b', '1212'),
          'expected': 'gs://bucket/obj/a/b#1212'
      },
  ])
  def test_url_string_property(self, cloudurl_args, expected):
    cloudurl = storage_url.CloudUrl(*cloudurl_args)
    self.assertEqual(cloudurl.url_string, expected)

  @parameterized.named_parameters([
      {
          'testcase_name': '_objecturl',
          'cloudurl_args': ('gs', 'bucket', 'obj/a/b'),
          'expected': 'gs://bucket/obj/a/b'
      },
      {
          'testcase_name': '_objecturl_with_version',
          'cloudurl_args': ('gs', 'bucket', 'obj/a/b', '1212'),
          'expected': 'gs://bucket/obj/a/b'
      },
  ])
  def test_versionless_url_string_property(self, cloudurl_args, expected):
    cloudurl = storage_url.CloudUrl(*cloudurl_args)
    self.assertEqual(cloudurl.versionless_url_string, expected)


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class FileStorageUrlTest(parameterized.TestCase, sdk_test_base.SdkBase):

  def SetUp(self):
    # self.root_path is a temp dir which gets deleted during TearDown.
    self.local_file = self.Touch(
        os.path.join(self.root_path, 'fake'), 'file.txt')
    self.local_file_url = storage_url.storage_url_from_string(self.local_file)

  @parameterized.named_parameters([
      {
          'testcase_name': '_file_path',
          'url_str': '/random/path.txt',
          'expected_url_obj': ExpectedStorageUrl(
              scheme='file', bucket=None, obj='/random/path.txt', gen=None)
      },
      {
          'testcase_name': '_with_file_scheme',
          'url_str': 'file:///random/a.txt',
          'expected_url_obj': ExpectedStorageUrl(
              scheme='file', bucket=None, obj='/random/a.txt', gen=None)
      }
  ])
  def test_file_url_from_string(self, url_str, expected_url_obj):
    file_url_object = storage_url.storage_url_from_string(url_str)
    self.assertEqual(file_url_object.scheme, expected_url_obj.scheme)
    self.assertEqual(file_url_object.bucket_name, expected_url_obj.bucket,)
    self.assertEqual(file_url_object.object_name, expected_url_obj.obj)
    self.assertEqual(file_url_object.generation, expected_url_obj.gen)
    self.assertEqual(
        file_url_object.url_string,
        '%s://%s' % (file_url_object.scheme, file_url_object.object_name))

  def test_file_url_exists(self):
    self.assertTrue(self.local_file_url.exists())

  def test_file_url_exists_with_invalid_path(self):
    file_url_object = storage_url.storage_url_from_string('invalid/path.txt')
    self.assertFalse(file_url_object.exists())

  def test_file_url_isdir(self):
    file_url_object = storage_url.storage_url_from_string(
        os.path.dirname(self.local_file))
    self.assertTrue(file_url_object.isdir())

  def test_file_url_isdir_with_invalid_path(self):
    file_url_object = storage_url.storage_url_from_string('invalid/dirpath')
    self.assertFalse(file_url_object.isdir())

  def test_url_string(self):
    file_url = storage_url.FileUrl(os.path.join('dir', 'a.txt'))
    self.assertEqual(file_url.url_string,
                     'file://' + os.path.join('dir', 'a.txt'))

  def test_versionless_url_string(self):
    file_url = storage_url.FileUrl(os.path.join('dir', 'a.txt'))
    self.assertEqual(file_url.versionless_url_string,
                     'file://' + os.path.join('dir', 'a.txt'))


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class StorageUrlTest(parameterized.TestCase, sdk_test_base.SdkBase):

  @parameterized.named_parameters([
      {
          'testcase_name': '_cloud_url_with_trailing_slash',
          'url_str': 'gs://bucket/dir/',
          'part': '**',
          'expected_string': 'gs://bucket/dir/**'
      },
      {
          'testcase_name': '_with_cloud_url_without_trailing_slash',
          'url_str': 'gs://bucket/dir',
          'part': '**',
          'expected_string': 'gs://bucket/dir/**'
      },
      {
          'testcase_name': '_with_leading_slash_in_part',
          'url_str': 'gs://bucket/dir',
          'part': '/**',
          'expected_string': 'gs://bucket/dir/**'
      },
      {
          'testcase_name': '_with_multiple_slashes_only_removes_one_slash',
          'url_str': 'gs://bucket/dir//',
          'part': '///**',
          'expected_string': 'gs://bucket/dir////**'
      },
      {
          'testcase_name': '_with_file_url',
          'url_str': os.path.join('file://fakedir', 'dir'),
          'part': '**',
          'expected_string': os.path.join('file://fakedir', 'dir', '**')
      }
  ])
  def test_join_returns_new_url_with_appended_part(self, url_str,
                                                   part, expected_string):
    url = storage_url.storage_url_from_string(url_str)
    new_url = url.join(part)
    self.assertEqual(new_url.url_string, expected_string)
    self.assertEqual(type(url), type(new_url))

  def test_equality(self):
    url1 = storage_url.CloudUrl.from_url_string('gs://bucket/obj.txt#1234')
    url2 = storage_url.CloudUrl('gs', 'bucket', 'obj.txt', '1234')
    self.assertEqual(url1, url2)

  def test_not_equal_with_different_type(self):
    url1 = storage_url.CloudUrl.from_url_string('gs://bucket/obj.txt#1234')
    url2 = storage_url.FileUrl('gs://bucket/obj.txt#1234')
    self.assertNotEqual(url1, url2)

  def test_not_equal_with_different_data(self):
    url1 = storage_url.CloudUrl.from_url_string('gs://bucket/obj.txt#1234')
    url2 = storage_url.CloudUrl.from_url_string('gs://bucket/obj.txt#5678')
    self.assertNotEqual(url1, url2)

  def test_hash(self):
    url = storage_url.CloudUrl('gs', 'bucket', 'obj.txt', '1234')
    self.assertEqual(hash(url), hash('gs://bucket/obj.txt#1234'))
