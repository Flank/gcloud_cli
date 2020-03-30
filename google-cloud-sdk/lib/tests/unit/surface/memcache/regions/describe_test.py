# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Unit tests for `gcloud memcache regions describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base


class DescribeTest(memcache_test_base.RegionsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectDescribe(self, expected_region):
    self.locations_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsGetRequest(
            name=expected_region.name),
        response=expected_region)

  def testDescribe(self):
    self.SetUpForTrack()
    expected_region = self.messages.Location(name=self.region_relative_name)
    self._ExpectDescribe(expected_region)

    actual_region = self.Run('memcache regions describe {}'.format(
        self.region_id))

    self.assertEqual(actual_region, expected_region)

  def testDescribe_UsingRelativeOperationName(self):
    self.SetUpForTrack()
    expected_region = self.messages.Location(name=self.region_relative_name)
    self._ExpectDescribe(expected_region)

    actual_region = self.Run('memcache regions describe {}'.format(
        self.region_relative_name))

    self.assertEqual(actual_region, expected_region)


if __name__ == '__main__':
  test_case.main()
