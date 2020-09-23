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
"""Tests for tests.lib.surface.storage.mock_cloud_api."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.command_lib.storage import storage_url
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.storage import test_resources

import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class GetResourceFromUrlStringTest(sdk_test_base.SdkBase):
  """Tests for the from_url_string function."""

  def test_gets_file_directory_resource(self):
    url_string = 'hi' + os.path.sep
    parsed_url = storage_url.storage_url_from_string(url_string)
    resource = resource_reference.FileDirectoryResource(parsed_url)
    self.assertEqual(test_resources.from_url_string(url_string), resource)

  def test_gets_file_object_resource(self):
    url_string = 'hi.txt'
    parsed_url = storage_url.storage_url_from_string(url_string)
    resource = resource_reference.FileObjectResource(parsed_url)
    self.assertEqual(test_resources.from_url_string(url_string), resource)

  def test_gets_bucket_resource(self):
    url_string = 'gs://bucket'
    cloud_url = storage_url.storage_url_from_string(url_string)
    resource = resource_reference.BucketResource(cloud_url)
    self.assertEqual(test_resources.from_url_string(url_string), resource)

  def test_gets_object_resource(self):
    url_string = 'gs://bucket/object'
    parsed_url = storage_url.storage_url_from_string(url_string)
    resource = resource_reference.ObjectResource(parsed_url)
    self.assertEqual(test_resources.from_url_string(url_string), resource)

  def test_gets_prefix_resource(self):
    url_string = 'gs://bucket/prefix/'
    parsed_url = storage_url.storage_url_from_string(url_string)
    resource = resource_reference.PrefixResource(parsed_url, 'prefix/')
    self.assertEqual(test_resources.from_url_string(url_string), resource)

  @mock.patch.object(storage_url, 'storage_url_from_string')
  def test_gets_unknown_resource(self, mock_storage_url_from_string):
    parsed_url = storage_url.CloudUrl.from_url_string('gs://to/mutate')
    parsed_url.scheme = parsed_url.bucket_name = None

    mock_storage_url_from_string.return_value = parsed_url
    resource = resource_reference.UnknownResource(parsed_url)
    self.assertEqual(test_resources.from_url_string(None), resource)

if __name__ == '__main__':
  test_case.main()
