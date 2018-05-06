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
"""Unit tests for `gcloud redis regions list`."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base
from six.moves import range  # pylint: disable=redefined-builtin


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class ListTest(redis_test_base.UnitTestBase):

  def testList(self, track):
    self.SetUpForTrack(track)
    expected_regions = self._MakeRegions(3)
    self._ExpectList(expected_regions)

    # Disable output so can capture returned list instead of printing
    properties.VALUES.core.user_output_enabled.Set(False)
    actual_regions = self.Run('redis regions list')

    self.assertEqual(actual_regions, expected_regions)

  def testList_Uri(self, track):
    self.SetUpForTrack(track)
    expected_regions = self._MakeRegions(3)
    self._ExpectList(expected_regions)

    self.Run('redis regions list --uri')

    self.AssertOutputEquals(
        """\
        https://redis.googleapis.com/{api_version}/{region_name}_0
        https://redis.googleapis.com/{api_version}/{region_name}_1
        https://redis.googleapis.com/{api_version}/{region_name}_2
        """.format(api_version=self.api_version,
                   region_name=self.region_relative_name),
        normalize_space=True)

  def testList_CheckFormat(self, track):
    self.SetUpForTrack(track)
    expected_regions = self._MakeRegions(3)
    self._ExpectList(expected_regions)

    self.Run('redis regions list')

    self.AssertOutputEquals(
        """\
        NAME
        {region_id}_0
        {region_id}_1
        {region_id}_2
        """.format(region_id=self.region_id), normalize_space=True)

  def _ExpectList(self, expected_regions):
    self.locations_service.List.Expect(
        request=self.messages.RedisProjectsLocationsListRequest(
            name=self.project_ref.RelativeName()),
        response=self.messages.ListLocationsResponse(
            locations=expected_regions))

  def _MakeRegions(self, n):
    regions = []
    for i in range(n):
      name = '{}_{}'.format(self.region_relative_name, i)
      location_id = '{}_{}'.format(self.region_id, i)
      region = self.messages.Location(name=name, locationId=location_id)
      regions.append(region)
    return regions


if __name__ == '__main__':
  test_case.main()
