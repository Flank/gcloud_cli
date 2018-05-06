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
"""Unit tests for `gcloud redis zones list`."""

from __future__ import absolute_import
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class ListTest(redis_test_base.UnitTestBase, parameterized.TestCase):

  def testList(self, track):
    self.SetUpForTrack(track)
    expected_zones = ['zone1', 'zone2', 'zone3']
    expected_region_id = self.region_id
    expect_region = self._MakeRegion(expected_region_id, expected_zones)
    self._ExpectRegionsList([expect_region])

    self.Run('redis zones list')

    self.AssertOutputEquals(
        """\
        ZONE   REGION
        zone1  {region_id}
        zone2  {region_id}
        zone3  {region_id}
        """.format(region_id=expected_region_id), normalize_space=True)

  def testList_MultipleRegions(self, track):
    self.SetUpForTrack(track)
    region1 = self._MakeRegion('region1', ['zone1a', 'zone1b', 'zone1c'])
    region2 = self._MakeRegion('region2', ['zone2a', 'zone2b'])
    region_no_zones = self._MakeRegion('region_no_zones')
    self._ExpectRegionsList([region1, region2, region_no_zones])

    self.Run('redis zones list')

    self.AssertOutputEquals(
        """\
        ZONE    REGION
        zone1a  region1
        zone1b  region1
        zone1c  region1
        zone2a  region2
        zone2b  region2
        """, normalize_space=True)

  def testList_MultipleRegions_RegionFlag(self, track):
    self.SetUpForTrack(track)
    region1 = self._MakeRegion('region1', ['zone1a', 'zone1b', 'zone1c'])
    region2 = self._MakeRegion('region2', ['zone2a', 'zone2b'])
    region_no_zones = self._MakeRegion('region_no_zones')
    self._ExpectRegionsList([region1, region2, region_no_zones])

    self.Run('redis zones list --region region2')

    self.AssertOutputEquals(
        """\
        ZONE    REGION
        zone2a  region2
        zone2b  region2
        """, normalize_space=True)

  def testList_NoRegionsHaveZones(self, track):
    self.SetUpForTrack(track)
    region1_nozones = self._MakeRegion('region1_nozones', [])
    region2_nozones = self._MakeRegion('region2_nozones', [])
    self._ExpectRegionsList([region1_nozones, region2_nozones])

    self.Run('redis zones list')

    self.AssertOutputEquals('')

  def testList_NoRegionsHaveMetadata(self, track):
    self.SetUpForTrack(track)
    region1_nometadata = self._MakeRegion('region1_nometadata')
    region2_nometadata = self._MakeRegion('region2_nometadata')
    self._ExpectRegionsList([region1_nometadata, region2_nometadata])

    self.Run('redis zones list')

    self.AssertOutputEquals('')

  def _ExpectRegionsList(self, expected_regions):
    self.locations_service.List.Expect(
        request=self.messages.RedisProjectsLocationsListRequest(
            name=self.project_ref.RelativeName()),
        response=self.messages.ListLocationsResponse(
            locations=expected_regions))

  def _MakeRegion(self, region_id, zones=None):
    region_ref = resources.REGISTRY.Parse(
        region_id, params={'projectsId': self.Project()},
        collection='redis.projects.locations', api_version=self.api_version)
    region = self.messages.Location(name=region_ref.RelativeName(),
                                    locationId=region_id)

    if zones is not None:
      metadata_dict = {
          '@type': ('type.googleapis.com/google.cloud.redis.{}.LocationMetadata'
                    .format(self.api_version)),
          'availableZones': dict.fromkeys(zones, {})}
      region.metadata = encoding.DictToMessage(
          metadata_dict, self.messages.Location.MetadataValue)

    return region


if __name__ == '__main__':
  test_case.main()
