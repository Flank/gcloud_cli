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
"""tpus locations list tests."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class ListTest(base.TpuUnitTestBase):

  def _GetListResponse(self, num=3):
    test_locations = [
        self.GetTestLocation(name='us-east-{}'.format(i))
        for i in xrange(1, num+1)
    ]
    return self.messages.ListLocationsResponse(locations=test_locations)

  def SetUp(self):
    self.zone = 'us-central1-c'
    properties.VALUES.compute.zone.Set(self.zone)

  def testList(self, track):
    self._SetTrack(track)
    self.mock_client.projects_locations.List.Expect(
        self.messages.TpuProjectsLocationsListRequest(
            name='projects/{}'.format(self.Project())),
        self._GetListResponse()
    )

    self.assertEqual(
        list(self.Run('compute tpus locations list')),
        self._GetListResponse().locations)

  def testListDefaultFormat(self, track):
    self._SetTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    self.mock_client.projects_locations.List.Expect(
        self.messages.TpuProjectsLocationsListRequest(
            name='projects/{}'.format(self.Project())),
        self._GetListResponse()
    )

    self.Run('compute tpus locations list')
    self.AssertOutputEquals("""\
LOCATION LOCATION_NAME
projects/fake-project/locations/us-east-1 us-east-1
projects/fake-project/locations/us-east-2 us-east-2
projects/fake-project/locations/us-east-3 us-east-3
""", normalize_space=True)

  def testListWithPaging(self, track):
    self._SetTrack(track)
    all_response_locations = self._GetListResponse(2).locations

    first_response = self.messages.ListLocationsResponse(
        locations=all_response_locations[:1],
        nextPageToken='thereisanotherpage')

    second_response = self.messages.ListLocationsResponse(
        locations=all_response_locations[1:])

    self.mock_client.projects_locations.List.Expect(
        request=self.messages.TpuProjectsLocationsListRequest(
            pageSize=1,
            name='projects/{}'.format(self.Project())),
        response=first_response
    )

    self.mock_client.projects_locations.List.Expect(
        request=self.messages.TpuProjectsLocationsListRequest(
            pageSize=1,
            pageToken='thereisanotherpage',
            name='projects/{}'.format(self.Project())),
        response=second_response
    )

    self.assertEqual(
        list(self.Run('compute tpus locations list --page-size=1')),
        list(all_response_locations))


if __name__ == '__main__':
  test_case.main()
