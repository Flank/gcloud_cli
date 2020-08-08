# Lint as: python3
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
"""Unit Tests for the gcloud storage list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.storage.gcs_api_unit_test_base import GcsApiUnitTestBase


class ListTestAlpha(GcsApiUnitTestBase):
  """Test cases for features in Alpha.

  When a feature moves to beta, move the corresponding tests to a superclass of
  this one where self.track = calliope_base.ReleaseTrack.BETA, details here:
  go/gcloud-test-howto#how-to-test-multiple-release-tracks.

  This will ensure that tests from past releases run for the alpha release.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.bucket_name = 'bucket1'
    self.object_names = ['file0', 'file1', 'asdf']

    self.bucket_contents = self.messages.Objects(
        items=[self.messages.Object(name=i) for i in self.object_names])

    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket=self.bucket_name),
        self.bucket_contents)

  def test_list_bucket(self):
    observed = self.Run('storage list gs://' + self.bucket_name)

    observed_paths = [i['path'] for i in observed]
    expected_paths = [
        'gs://%s/%s' % (self.bucket_name, i) for i in self.object_names
    ]
    self.assertCountEqual(observed_paths, expected_paths)


if __name__ == '__main__':
  test_case.main()
