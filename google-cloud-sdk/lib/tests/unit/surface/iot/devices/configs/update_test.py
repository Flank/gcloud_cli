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
"""Tests for `gcloud iot config update`."""
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class ConfigsUpdateTest(base.CloudIotBase):

  def _ExpectModifyConfig(self, data, version=None):
    service = self.client.projects_locations_registries_devices
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistriesDevices'
                           'ModifyCloudToDeviceConfigRequest')
    name = ('projects/{}/locations/us-central1/registries/my-registry/'
            'devices/my-device'.format(self.Project()))
    sub_request_type = self.messages.ModifyCloudToDeviceConfigRequest

    service.ModifyCloudToDeviceConfig.Expect(
        request_type(
            modifyCloudToDeviceConfigRequest=sub_request_type(
                binaryData=data,
                versionToUpdate=version
            ),
            name=name
        ),
        self.messages.DeviceConfig(
            binaryData=data,
            version=(version or 1)
        )
    )

  def testUpdate_ConfigFlagRequired(self, track):
    self.track = track
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--config-data | --config-file) must be specified.'):
      self.Run(
          'iot devices configs update '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1')

  def testUpdate_ConfigFlagsExclusive(self, track):
    self.track = track
    with self.AssertRaisesArgumentErrorMatches(
        'argument --config-data: Exactly one of (--config-data | '
        '--config-file) must be specified.'):
      self.Run(
          'iot devices configs update '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1 '
          '    --config-data foo '
          '    --config-file bar')

  def testUpdate(self, track):
    self.track = track
    self._ExpectModifyConfig('abcd')

    result = self.Run(
        'iot devices configs update '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --config-data abcd')

    expected_config = self.messages.DeviceConfig(
        binaryData='abcd',
        version=1
    )
    self.assertEqual(result, expected_config)
    self.AssertLogContains('Updated configuration for device [my-device].')

  def testUpdate_EmptyData(self, track):
    self.track = track
    self._ExpectModifyConfig('')

    result = self.Run(
        'iot devices configs update '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --config-data ""')

    expected_config = self.messages.DeviceConfig(
        binaryData='',
        version=1
    )
    self.assertEqual(result, expected_config)

  def testUpdate_FromFile(self, track):
    self.track = track
    data = ''.join(map(chr, range(256)))
    self._ExpectModifyConfig(data)
    data_file = self.Touch(self.temp_path, 'data', contents=data)

    result = self.Run(
        'iot devices configs update '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --config-file {}'.format(data_file))

    expected_config = self.messages.DeviceConfig(
        binaryData=data,
        version=1
    )
    self.assertEqual(result, expected_config)

  def testUpdate_Version(self, track):
    self.track = track
    self._ExpectModifyConfig('abcd', version=10)

    result = self.Run(
        'iot devices configs update '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1 '
        '    --config-data abcd '
        '    --version-to-update 10')

    expected_config = self.messages.DeviceConfig(
        binaryData='abcd',
        version=10
    )
    self.assertEqual(result, expected_config)

  def testUpdate_RelativeName(self, track):
    self.track = track
    self._ExpectModifyConfig('abcd')

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    result = self.Run(
        'iot devices configs update '
        '    --config-data abcd'
        '    --device {} '.format(device_name))

    expected_config = self.messages.DeviceConfig(
        binaryData='abcd',
        version=1
    )
    self.assertEqual(result, expected_config)


if __name__ == '__main__':
  test_case.main()
