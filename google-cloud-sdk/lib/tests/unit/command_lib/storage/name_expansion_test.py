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
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util
from tests.lib.surface.storage import mock_cloud_api
from tests.lib.surface.storage import test_resources

import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support python 2')
class NameExpansionTest(cloud_storage_util.WithGCSCalls):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)

    self.buckets_response = [test_resources.get_bucket_resource('gs', name) for
                             name in ['a1', 'a2', 'b1', 'c1']]

  @mock_cloud_api.patch
  def test_multiple_buckets_with_wildcards(self, mock_api_client):
    mock_api_client.ListBuckets.return_value = self.buckets_response

    names = ['gs://a*', 'gs://b*']
    bucket_iterator = name_expansion.NameExpansionIterator(names)
    self.assertEqual(list(bucket_iterator), self.buckets_response[:3])

    named_expansion_call = mock.call(cloud_api.FieldsScope.SHORT)
    mock_api_client.ListBuckets.assert_has_calls([named_expansion_call]*2)


if __name__ == '__main__':
  test_case.main()
