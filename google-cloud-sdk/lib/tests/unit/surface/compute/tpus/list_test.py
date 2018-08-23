# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""tpus list tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base
from six.moves import range


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA,
                           calliope_base.ReleaseTrack.GA])
class ListTest(base.TpuUnitTestBase):

  def _GetListResponse(self, num=3):
    test_nodes = [
        self.GetTestTPU(
            '/projects/{0}/locations/{1}/nodes/tpu-{2}'.format(
                self.Project(), self.zone, i),
            ip_address='10.142.0.1',
            accelerator_type='zones/us-central1-c/acceleratorTypes/v2-8')
        for i in range(1, num+1)
    ]
    return self.messages.ListNodesResponse(nodes=test_nodes)

  def SetUp(self):
    self.zone = 'us-central1-c'
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.compute.zone.Set(self.zone)

  def testList(self, track):
    self._SetTrack(track)
    location_ref = resources.REGISTRY.Parse(
        self.zone,
        params={
            'projectsId': self.Project()},
        collection='tpu.projects.locations')

    self.mock_client.projects_locations_nodes.List.Expect(
        self.messages.TpuProjectsLocationsNodesListRequest(
            parent=location_ref.RelativeName()),
        self._GetListResponse()
    )

    self.assertEqual(
        list(self.Run('compute tpus list')),
        self._GetListResponse().nodes)

  def testListDefaultFormat(self, track):
    self._SetTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    location_ref = resources.REGISTRY.Parse(
        self.zone,
        params={
            'projectsId': self.Project()},
        collection='tpu.projects.locations')

    self.mock_client.projects_locations_nodes.List.Expect(
        self.messages.TpuProjectsLocationsNodesListRequest(
            parent=location_ref.RelativeName()),
        self._GetListResponse()
    )
    self.Run('compute tpus list')
    self.AssertOutputEquals("""\
NAME ZONE ACCELERATOR_TYPE NETWORK_ENDPOINTS NETWORK RANGE STATUS
tpu-1 us-central1-c v2-8 10.142.0.1:2222,10.142.0.2:2222 data-test 10.142.0.0/29 READY
tpu-2 us-central1-c v2-8 10.142.0.1:2222,10.142.0.2:2222 data-test 10.142.0.0/29 READY
tpu-3 us-central1-c v2-8 10.142.0.1:2222,10.142.0.2:2222 data-test 10.142.0.0/29 READY
""", normalize_space=True)

  def testListWithPaging(self, track):
    self._SetTrack(track)
    location_ref = resources.REGISTRY.Parse(
        self.zone,
        params={
            'projectsId': self.Project()},
        collection='tpu.projects.locations')

    all_response_nodes = self._GetListResponse(2).nodes

    first_response = self.messages.ListNodesResponse(
        nodes=all_response_nodes[:1],
        nextPageToken='thereisanotherpage')

    second_response = self.messages.ListNodesResponse(
        nodes=all_response_nodes[1:])

    self.mock_client.projects_locations_nodes.List.Expect(
        request=self.messages.TpuProjectsLocationsNodesListRequest(
            pageSize=1,
            parent=location_ref.RelativeName()),
        response=first_response
    )

    self.mock_client.projects_locations_nodes.List.Expect(
        request=self.messages.TpuProjectsLocationsNodesListRequest(
            pageSize=1,
            pageToken='thereisanotherpage',
            parent=location_ref.RelativeName()),
        response=second_response
    )

    self.assertEqual(
        list(self.Run('compute tpus list --page-size=1')),
        list(all_response_nodes))


if __name__ == '__main__':
  test_case.main()

