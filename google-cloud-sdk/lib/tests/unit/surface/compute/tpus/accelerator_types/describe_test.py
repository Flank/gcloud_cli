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
"""tpus accelerator-types describe tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class DescribeTest(base.TpuUnitTestBase):

  def SetUp(self):
    self.zone = 'us-central1-c'
    properties.VALUES.compute.zone.Set(self.zone)

  def testDescribe(self, track):
    self._SetTrack(track)
    location_ref = resources.REGISTRY.Parse(
        self.zone,
        params={'projectsId': self.Project()},
        collection='tpu.projects.locations')
    acc_type = self.GetTestAccType()
    self.mock_client.projects_locations_acceleratorTypes.Get.Expect(
        self.messages.TpuProjectsLocationsAcceleratorTypesGetRequest(
            name='{}/acceleratorTypes/{}'.format(
                location_ref.RelativeName(), 'v2-8')),
        acc_type)

    self.assertEqual(acc_type,
                     self.Run('compute tpus accelerator-types describe v2-8'))


if __name__ == '__main__':
  test_case.main()
