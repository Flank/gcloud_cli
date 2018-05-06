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

"""Tests for `gcloud iot devices describe`."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class DevicesDescribeTest(base.CloudIotBase):

  def SetUp(self):
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)

    properties.VALUES.core.user_output_enabled.Set(False)

  def testDescribe(self, track):
    self.track = track
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    device = self.messages.Device(name=device_name, numId=10)
    self.client.projects_locations_registries_devices.Get.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesGetRequest(
            name=device_name),
        device)

    result = self.Run('iot devices describe my-device '
                      '    --registry my-registry '
                      '    --region us-central1')

    self.assertEqual(result, device)

  def testDescribe_RelativeName(self, track):
    self.track = track
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    device = self.messages.Device(name=device_name, numId=10)
    self.client.projects_locations_registries_devices.Get.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesGetRequest(
            name=device_name),
        device)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    result = self.Run('iot devices describe {}'.format(device_name))

    self.assertEqual(result, device)


if __name__ == '__main__':
  test_case.main()
