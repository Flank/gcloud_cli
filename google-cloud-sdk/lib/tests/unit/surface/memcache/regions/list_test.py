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
"""Unit tests for `gcloud memcache regions list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base


class ListTest(memcache_test_base.RegionsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectList(self, expected_regions):
    self.locations_service.List.Expect(
        request=self.messages.MemcacheProjectsLocationsListRequest(
            name=self.project_ref.RelativeName()),
        response=self.messages.ListLocationsResponse(
            locations=expected_regions))

  def _MakeRegions(self, region_ids):

    regions = []
    for region_id in region_ids:
      ref = resources.REGISTRY.Parse(
          region_id,
          collection='memcache.projects.locations',
          params={'projectsId': self.Project()},
          api_version=self.api_version)
      regions.append(
          self.messages.Location(name=ref.RelativeName(), locationId=region_id))

    return regions

  def testList(self):
    self.SetUpForTrack()
    self.SetUpOperationsForTrack()
    expected_regions = self._MakeRegions(['region1', 'region2', 'region3'])
    self._ExpectList(expected_regions)

    # Disable output so can capture returned lists instead of printing.
    properties.VALUES.core.user_output_enabled.Set(False)
    actual_regions = self.Run('memcache regions list')
    self.assertEqual(actual_regions, expected_regions)

  def testList_Uri(self):
    self.SetUpForTrack()
    self.SetUpOperationsForTrack()
    expected_regions = self._MakeRegions(['region1', 'region2', 'region3'])
    self._ExpectList(expected_regions)

    self.Run('memcache regions list --uri')

    self.AssertOutputEquals(
        """\
        https://memcache.googleapis.com/{api_version}/projects/{project}/locations/region1
        https://memcache.googleapis.com/{api_version}/projects/{project}/locations/region2
        https://memcache.googleapis.com/{api_version}/projects/{project}/locations/region3
        """.format(
            api_version=self.api_version,
            project=self.Project()),
        normalize_space=True)

  def testList_CheckFormat(self):
    self.SetUpForTrack()
    self.SetUpOperationsForTrack()
    expected_regions = self._MakeRegions(['region1', 'region2', 'region3'])
    self._ExpectList(expected_regions)

    self.Run('memcache regions list')

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        NAME
        region1
        region2
        region3
        """,
        normalize_space=True)
    # pylint: enable=line-too-long


if __name__ == '__main__':
  test_case.main()
