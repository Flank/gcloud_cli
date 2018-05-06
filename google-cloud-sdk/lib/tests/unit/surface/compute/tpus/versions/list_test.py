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
"""tpus versions list tests."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class ListTest(base.TpuUnitTestBase):

  def _GetListResponse(self, num=3):
    test_versions = [
        self.GetTestTFVersion(version='1.{}'.format(i))
        for i in xrange(1, num+1)
    ]
    return self.messages.ListTensorFlowVersionsResponse(
        tensorflowVersions=test_versions)

  def SetUp(self):
    self.zone = 'us-central1-c'
    properties.VALUES.compute.zone.Set(self.zone)
    self.location_ref = resources.REGISTRY.Parse(
        self.zone,
        params={'projectsId': self.Project()},
        collection='tpu.projects.locations')

  def testList(self, track):
    self._SetTrack(track)

    self.mock_client.projects_locations_tensorflowVersions.List.Expect(
        self.messages.TpuProjectsLocationsTensorflowVersionsListRequest(
            parent=self.location_ref.RelativeName()),
        self._GetListResponse()
    )

    self.assertEqual(
        list(self.Run('compute tpus versions list')),
        self._GetListResponse().tensorflowVersions)

  def testListDefaultFormat(self, track):
    self._SetTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    self.mock_client.projects_locations_tensorflowVersions.List.Expect(
        self.messages.TpuProjectsLocationsTensorflowVersionsListRequest(
            parent=self.location_ref.RelativeName()),
        self._GetListResponse()
    )

    self.Run('compute tpus versions list')
    self.AssertOutputEquals("""\
TENSORFLOW_VERSION
1.1
1.2
1.3
""", normalize_space=True)

  def testListWithPaging(self, track):
    self._SetTrack(track)
    all_response_versions = self._GetListResponse(2).tensorflowVersions

    first_response = self.messages.ListTensorFlowVersionsResponse(
        tensorflowVersions=all_response_versions[:1],
        nextPageToken='thereisanotherpage')

    second_response = self.messages.ListTensorFlowVersionsResponse(
        tensorflowVersions=all_response_versions[1:])

    self.mock_client.projects_locations_tensorflowVersions.List.Expect(
        request=self.messages.TpuProjectsLocationsTensorflowVersionsListRequest(
            pageSize=1,
            parent=self.location_ref.RelativeName()),
        response=first_response
    )

    self.mock_client.projects_locations_tensorflowVersions.List.Expect(
        request=self.messages.TpuProjectsLocationsTensorflowVersionsListRequest(
            pageSize=1,
            pageToken='thereisanotherpage',
            parent=self.location_ref.RelativeName()),
        response=second_response
    )

    self.assertEqual(
        list(self.Run('compute tpus versions list --page-size=1')),
        list(all_response_versions))


if __name__ == '__main__':
  test_case.main()
