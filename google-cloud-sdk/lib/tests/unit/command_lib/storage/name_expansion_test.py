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

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import gcs_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import resource_reference
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.app import cloud_storage_util
import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support python 2')
class NameExpansionTest(cloud_storage_util.WithGCSCalls):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)

    self.messages = apis.GetMessagesModule('storage', 'v1')

    self.buckets_response = self.messages.Buckets(items=[
        self.messages.Bucket(name='a1'),
        self.messages.Bucket(name='a2'),
        self.messages.Bucket(name='b1'),
        self.messages.Bucket(name='c1'),
    ])

  @mock.patch.object(api_factory, 'get_api')
  def test_multiple_buckets_with_wildcards(self, mock_get_api):
    # Quick fix for flaky tests.
    # TODO(b/163796935) Replace with mock_cloud_api once cl/326521545 is out.
    mock_get_api.return_value = gcs_api.GcsApi()

    names = ['gs://a*', 'gs://b*']
    for _ in names:
      # The logic tested below makes a list buckets request for each name in
      # names, so queue all the necessary list buckets responses to avoid an
      # apitools.base.py.testing.mock.UnexpectedRequestException.
      self.apitools_client.buckets.List.Expect(
          self.messages.StorageBucketsListRequest(
              project=self.project,
              projection=(self.messages.StorageBucketsListRequest.
                          ProjectionValueValuesEnum.noAcl)
          ),
          response=self.buckets_response
      )

    bucket_iterator = name_expansion.NameExpansionIterator(names)

    observed = []
    for bucket in bucket_iterator:
      self.assertIsInstance(bucket, resource_reference.BucketResource)
      observed.append(bucket.metadata_object.name)
    self.assertCountEqual(observed, ['a1', 'a2', 'b1'])


if __name__ == '__main__':
  test_case.main()
