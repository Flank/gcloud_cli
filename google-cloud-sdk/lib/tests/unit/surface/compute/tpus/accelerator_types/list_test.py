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
"""tpus accelerator-types list tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base
from six.moves import range


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class ListTest(base.TpuUnitTestBase):

  def _GetListResponse(self, num=3):
    test_types = [
        self.GetTestAccType(acc_type='tpu-v.{}'.format(i))
        for i in range(1, num+1)
    ]
    return self.messages.ListAcceleratorTypesResponse(
        acceleratorTypes=test_types)

  def SetUp(self):
    self.zone = 'us-central1-c'
    properties.VALUES.compute.zone.Set(self.zone)
    self.location_ref = resources.REGISTRY.Parse(
        self.zone,
        params={'projectsId': self.Project()},
        collection='tpu.projects.locations')

  def testList(self, track):
    self._SetTrack(track)

    self.mock_client.projects_locations_acceleratorTypes.List.Expect(
        self.messages.TpuProjectsLocationsAcceleratorTypesListRequest(
            parent=self.location_ref.RelativeName()),
        self._GetListResponse()
    )

    self.assertEqual(self._GetListResponse().acceleratorTypes,
                     list(self.Run('compute tpus accelerator-types list')))

  def testListDefaultFormat(self, track):
    self._SetTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    self.mock_client.projects_locations_acceleratorTypes.List.Expect(
        self.messages.TpuProjectsLocationsAcceleratorTypesListRequest(
            parent=self.location_ref.RelativeName()),
        self._GetListResponse()
    )

    self.Run('compute tpus accelerator-types list')
    self.AssertOutputEquals("""\
ACCELERATOR_TYPE
tpu-v.1
tpu-v.2
tpu-v.3
""", normalize_space=True)

  def testListWithPaging(self, track):
    self._SetTrack(track)
    all_response_types = self._GetListResponse(2).acceleratorTypes

    first_response = self.messages.ListAcceleratorTypesResponse(
        acceleratorTypes=all_response_types[:1],
        nextPageToken='thereisanotherpage')

    second_response = self.messages.ListAcceleratorTypesResponse(
        acceleratorTypes=all_response_types[1:])

    self.mock_client.projects_locations_acceleratorTypes.List.Expect(
        request=self.messages.TpuProjectsLocationsAcceleratorTypesListRequest(
            pageSize=1,
            parent=self.location_ref.RelativeName()),
        response=first_response
    )

    self.mock_client.projects_locations_acceleratorTypes.List.Expect(
        request=self.messages.TpuProjectsLocationsAcceleratorTypesListRequest(
            pageSize=1,
            pageToken='thereisanotherpage',
            parent=self.location_ref.RelativeName()),
        response=second_response
    )

    self.assertEqual(
        list(all_response_types),
        list(self.Run('compute tpus accelerator-types list --page-size=1')))


if __name__ == '__main__':
  test_case.main()
