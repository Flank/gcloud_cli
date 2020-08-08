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

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


ExpectedStorageUrl = collections.namedtuple(
    'ExpectedStorageUrl',
    ['scheme', 'bucket', 'obj', 'gen']
)


@test_case.Filters.DoNotRunOnPy2('Storage does not support python 2')
class CloudStorageUrlTest(sdk_test_base.WithFakeAuth, parameterized.TestCase):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)
    self.client = mock.Client(client_class=apis.GetClientClass('storage', 'v1'))
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
    self.assertRaises(storage_url.InvalidUrlError,
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
