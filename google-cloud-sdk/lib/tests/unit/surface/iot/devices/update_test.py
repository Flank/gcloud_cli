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
"""Tests for `gcloud iot devices update`."""
import itertools
from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class DevicesUpdateTest(base.CloudIotBase, parameterized.TestCase):

  def SetUp(self):
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)

    properties.VALUES.core.user_output_enabled.Set(False)

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testUpdate_NoOptions(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(devices_api.NoFieldsSpecifiedError,
                                           'at least one field'):
      self.Run(
          'iot devices update my-device '
          '    --registry my-registry'
          '    --region us-central1')

  @parameterized.parameters(itertools.product(
      [calliope_base.ReleaseTrack.ALPHA, calliope_base.ReleaseTrack.BETA,
       calliope_base.ReleaseTrack.GA],
      [(True, '--blocked'),
       (False, '--no-blocked'),]
  ))
  def testUpdate_BlockedFlags(self, track, data):
    blocked, blocked_flag = data
    self.track = track
    device = self.messages.Device(
        blocked=blocked,
    )
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name,
            device=device,
            updateMask='blocked'),
        device,
    )

    results = self.Run(
        'iot devices update my-device '
        '    --registry my-registry'
        '    --region us-central1'
        '    {} '.format(blocked_flag)
    )

    self.assertEqual(results, device)
    self.AssertLogContains('Updated device [my-device].')

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testUpdate_Metadata(self, track):
    self.track = track
    device = self.messages.Device(
        metadata=self.messages.Device.MetadataValue(
            additionalProperties=[
                self._CreateAdditionalProperty('key', 'value')]
        )
    )
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name,
            device=device,
            updateMask='metadata'),
        device,
    )

    results = self.Run(
        'iot devices update my-device '
        '    --registry my-registry'
        '    --region us-central1'
        '    --metadata=key=value'
    )

    self.assertEqual(results, device)
    self.AssertLogContains('Updated device [my-device].')

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA,
                            calliope_base.ReleaseTrack.GA)
  def testUpdate_RelativeName(self, track):
    self.track = track
    device = self.messages.Device(
        blocked=True,
    )
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name,
            device=device,
            updateMask='blocked'),
        device,
    )

    results = self.Run(
        'iot devices update {} '
        '    --blocked '.format(device_name))

    self.assertEqual(results, device)


if __name__ == '__main__':
  test_case.main()
