# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for `gcloud redis describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class DescribeTest(redis_test_base.UnitTestBase, parameterized.TestCase):

  def testDescribe(self, track):
    self.SetUpForTrack(track)
    expected_region = self.messages.Location(name=self.region_relative_name)
    self._ExpectDescribe(expected_region)

    actual_region = self.Run('redis regions describe {}'.format(self.region_id))

    self.assertEqual(actual_region, expected_region)

  def testDescribe_UsingRelativeRegionName(self, track):
    self.SetUpForTrack(track)
    expected_region = self.messages.Location(name=self.region_relative_name)
    self._ExpectDescribe(expected_region)

    actual_region = self.Run('redis regions describe {}'
                             .format(self.region_relative_name))

    self.assertEqual(actual_region, expected_region)

  def _ExpectDescribe(self, expected_region):
    self.locations_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsGetRequest(
            name=expected_region.name),
        response=expected_region)


if __name__ == '__main__':
  test_case.main()
