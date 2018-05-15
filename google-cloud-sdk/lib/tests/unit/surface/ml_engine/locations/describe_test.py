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
"""Tests for `gcloud ml-engine locations describe`."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import properties
from tests.lib.surface.ml_engine import base


class LocationsDescribeTest(base.MlAlphaPlatformTestBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    m = self.short_msgs
    # Capability Types
    training = m.Capability.TypeValueValuesEnum.TRAINING
    # Accelerator Types
    k80 = (m.Capability.AvailableAcceleratorsValueListEntryValuesEnum
           .NVIDIA_TESLA_K80)
    p100 = (m.Capability.AvailableAcceleratorsValueListEntryValuesEnum
            .NVIDIA_TESLA_P100)
    cap1 = m.Capability(type=training, availableAccelerators=[k80, p100])
    self.loc1 = m.Location(name='loc1', capabilities=[cap1])

  def _ExpectDescribe(self):
    location_name = ('projects/{}/locations/loc1').format(self.Project())
    self.client.projects_locations.Get.Expect(
        self.msgs.MlProjectsLocationsGetRequest(name=location_name), self.loc1)

  def testDescribe(self):
    self._ExpectDescribe()
    result = self.Run('ml-engine locations describe loc1')
    self.assertEqual(self.loc1, result)

  def testDescribeFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    self._ExpectDescribe()
    self.Run('ml-engine locations describe loc1')
    self.AssertOutputEquals(
        """\
        {
          "capabilities": [
            {
              "availableAccelerators": [
                "NVIDIA_TESLA_K80",
                "NVIDIA_TESLA_P100"
              ],
              "type": "TRAINING"
            }
          ],
          "name": "loc1"
        }
        """, normalize_space=True)
