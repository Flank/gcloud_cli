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

"""Tests for `gcloud iot config list`."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base

from six.moves import range  # pylint: disable=redefined-builtin


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class ConfigsListTest(base.CloudIotBase):

  def _MakeConfigs(self, num=10):
    configs = []
    for idx in range(num):
      configs.append(
          self.messages.DeviceConfig(
              cloudUpdateTime='2017-01-01T00:00Z',
              deviceAckTime='2017-01-01T00:00Z',
              version=(idx + 1),
              binaryData=bytes(idx)
          )
      )
    return configs

  def SetUp(self):
    self.parent_device_name = (
        'projects/{}/locations/us-central1/registries/'
        'my-registry/devices/my-device'.format(self.Project()))

  def _ExpectListConfigVersions(self, configs, num_versions=None,
                                parent_name=None):
    """Helper function to add expected request & response for listing configs.

    Args:
      configs: [cloudiot_v1_messages.DeviceConfig], the configs to return.
      num_versions: int, the number of versions.
      parent_name: str, the URI of the parent device if not the default
        (self.parent_device_name).
    """
    parent_name = parent_name or self.parent_device_name
    service = self.client.projects_locations_registries_devices_configVersions
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistriesDevices'
                           'ConfigVersionsListRequest')
    service.List.Expect(
        request_type(name=parent_name,
                     numVersions=num_versions),
        self.messages.ListDeviceConfigVersionsResponse(deviceConfigs=configs)
    )

  def testList(self, track):
    self.track = track
    configs = self._MakeConfigs()
    self._ExpectListConfigVersions(configs)

    results = self.Run(
        'iot devices configs list'
        '    --format disable '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(list(results), configs)

  def testList_Flags(self, track):
    self.track = track
    configs = self._MakeConfigs()
    self._ExpectListConfigVersions(
        configs,
        parent_name=(
            'projects/{}/locations/fakelocation/registries/fakeregistry'
            '/devices/fakedevice'.format(self.Project())))

    results = self.Run(
        'iot devices configs list'
        '    --format disable '
        '    --device fakedevice '
        '    --registry fakeregistry '
        '    --region fakelocation')

    self.assertEqual(list(results), configs)

  def testList_Limit(self, track):
    self.track = track
    configs = self._MakeConfigs()
    self._ExpectListConfigVersions(configs[-3:], num_versions=3)

    self.Run(
        'iot devices configs list'
        '    --limit 3 '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')
    self.AssertOutputEquals("""\
        VERSION  CLOUD_UPDATE_TIME  DEVICE_ACK_TIME
        8        2017-01-01T00:00Z  2017-01-01T00:00Z
        9        2017-01-01T00:00Z  2017-01-01T00:00Z
        10       2017-01-01T00:00Z  2017-01-01T00:00Z
        """, normalize_space=True)

  def testList_RelativeName(self, track):
    self.track = track
    configs = self._MakeConfigs()
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-other-registry/'
                   'devices/my-other-device').format(self.Project())
    self._ExpectListConfigVersions(configs, parent_name=device_name)

    results = self.Run(
        'iot devices configs list'
        '    --format disable '
        '    --device {}'.format(device_name))

    self.assertEqual(list(results), configs)


if __name__ == '__main__':
  test_case.main()
