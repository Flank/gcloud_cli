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
"""E2E Tests for the gcloud storage list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.storage.e2e_test_base import StorageE2ETestBase


class ListTestAlpha(StorageE2ETestBase):
  """Test cases for features in Alpha.

  When a feature moves to beta, move the corresponding tests to a superclass of
  this one where self.track = calliope_base.ReleaseTrack.BETA, details here:
  go/gcloud-test-howto#how-to-test-multiple-release-tracks.

  This will ensure that tests from past releases run for the alpha release.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def test_list_bucket(self):
    with self.create_bucket() as test_bucket:
      objects = [self.create_object(test_bucket) for _ in range(3)]

      observed = self.Run('storage list gs://' + test_bucket.bucket)

      observed_paths = [i['path'] for i in observed]
      expected_paths = [i.ToUrl() for i in objects]
      self.assertCountEqual(observed_paths, expected_paths)


if __name__ == '__main__':
  test_case.main()
