# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class DevicesUpdateTestGA(base.CloudIotBase, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)

    properties.VALUES.core.user_output_enabled.Set(False)

  def testUpdate_NoOptions(self):
    with self.AssertRaisesExceptionMatches(devices_api.NoFieldsSpecifiedError,
                                           'at least one field'):
      self.Run('iot devices update my-device '
               '    --registry my-registry'
               '    --region us-central1')

  @parameterized.parameters(
      (True, '--blocked'),
      (False, '--no-blocked'),
  )
  def testUpdate_BlockedFlags(self, blocked, blocked_flag):
    device = self.messages.Device(blocked=blocked,)
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name, device=device, updateMask='blocked'),
        device,
    )

    results = self.Run('iot devices update my-device '
                       '    --registry my-registry'
                       '    --region us-central1'
                       '    {} '.format(blocked_flag))

    self.assertEqual(results, device)
    self.AssertLogContains('Updated device [my-device].')

  def testUpdate_Metadata(self):
    device = self.messages.Device(
        metadata=self.messages.Device.MetadataValue(additionalProperties=[
            self._CreateAdditionalProperty('key', 'value')
        ]))
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name, device=device, updateMask='metadata'),
        device,
    )

    results = self.Run('iot devices update my-device '
                       '    --registry my-registry'
                       '    --region us-central1'
                       '    --metadata=key=value')

    self.assertEqual(results, device)
    self.AssertLogContains('Updated device [my-device].')

  def testUpdate_RelativeName(self):
    device = self.messages.Device(
        blocked=True,
    )
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name, device=device, updateMask='blocked'),
        device,
    )

    results = self.Run('iot devices update {} '
                       '    --blocked '.format(device_name))

    self.assertEqual(results, device)


class DevicesUpdateTestBeta(DevicesUpdateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectUpdate(self, device_name, device, update_mask):
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name, device=device, updateMask=update_mask),
        device,
    )

  @parameterized.parameters(
      ('none', 'NONE'), ('info', 'INFO'), ('error', 'ERROR'), ('Info', 'INFO'),
      ('ErRoR', 'ERROR'), ('NONE', 'NONE'), ('debug', 'DEBUG'),
      ('dEbUg', 'DEBUG'), ('DEBUG', 'DEBUG'))
  def testUpdate_LogLevel(self, log_level, log_level_enum):
    device_name = ('projects/my-project/locations/us-central1/registries/'
                   'my-registry/devices/my-device')
    device = self.messages.Device(
        logLevel=self.messages.Device.LogLevelValueValuesEnum(log_level_enum))
    update_mask = 'logLevel'
    self._ExpectUpdate(device_name, device, update_mask)

    result = self.Run('iot devices update my-device '
                      '    --registry my-registry'
                      '    --region us-central1'
                      '    --project my-project'
                      '    --log-level {}'.format(log_level))

    self.assertEqual(result, device)
    self.AssertLogContains('Updated device [my-device].')

  @parameterized.parameters('association-only', 'device-auth-token-only',
                            'association-and-device-auth-token')
  def testUpdate_AuthMethod(self, auth_method):
    auth_method_enum = (
        self.messages.GatewayConfig.GatewayAuthMethodValueValuesEnum
        .lookup_by_name(auth_method.upper().replace('-', '_')))
    device = self.messages.Device(
        gatewayConfig=self.messages.GatewayConfig(
            gatewayAuthMethod=auth_method_enum))

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name,
            device=device,
            updateMask='gatewayConfig.gatewayAuthMethod'),
        device,
    )

    results = self.Run('iot devices update my-device '
                       '    --registry my-registry'
                       '    --region us-central1'
                       '    --auth-method {}'.format(auth_method))

    self.assertEqual(results, device)
    self.AssertLogContains('Updated device [my-device].')

  def testUpdateAll(self):
    auth_method_enum = (
        self.messages.GatewayConfig.GatewayAuthMethodValueValuesEnum
        .ASSOCIATION_AND_DEVICE_AUTH_TOKEN)
    device = self.messages.Device(
        blocked=True,
        metadata=self.messages.Device.MetadataValue(additionalProperties=[
            self._CreateAdditionalProperty('key', 'value')
        ]),
        gatewayConfig=self.messages.GatewayConfig(
            gatewayAuthMethod=auth_method_enum))

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=device_name,
            device=device,
            updateMask='blocked,metadata,gatewayConfig.gatewayAuthMethod'),
        device,
    )

    results = self.Run('iot devices update my-device '
                       '    --registry my-registry'
                       '    --region us-central1'
                       '    --auth-method association-and-device-auth-token'
                       '    --metadata=key=value'
                       '    --blocked')

    self.assertEqual(results, device)
    self.AssertLogContains('Updated device [my-device].')


class DevicesUpdateTestAlpha(DevicesUpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
