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
"""Tests for the Cloud IoT Devices library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.command_lib.iot import util
from tests.lib import test_case
from tests.lib.api_lib.util import list_slicer
from tests.lib.surface.cloudiot import base

from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


class DevicesTest(base.CloudIotBase):

  def SetUp(self):
    self.devices_client = devices_api.DevicesClient(self.client,
                                                    self.messages)
    self.registry_ref = util.GetRegistry().Create(
        'cloudiot.projects.locations.registries',
        locationsId='us-central1', projectsId=self.Project(),
        registriesId='my-registry')
    self.device_ref = util.GetRegistry().Create(
        'cloudiot.projects.locations.registries.devices',
        locationsId='us-central1', projectsId=self.Project(),
        registriesId='my-registry', devicesId='my-device')

    # Define separately from registry_ref because we know that this is what the
    # API expects
    self.registry_name = (
        'projects/{}/locations/us-central1/registries/my-registry'.format(
            self.Project()))
    self.device_name = (
        'projects/{}/locations/us-central1/registries/my-registry/'
        'devices/my-device').format(self.Project())

  def _ExpectCreate(self, device):
    self.client.projects_locations_registries_devices.Create.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesCreateRequest(
            parent=self.registry_name,
            device=device),
        device)

  def testCreate_NoOptions(self):
    device = self.messages.Device(id='my-device')
    self._ExpectCreate(device)

    result = self.devices_client.Create(self.registry_ref, 'my-device')

    self.assertEqual(result, device)

  def testCreate_AllOptions(self):
    blocked = False
    format_enum = self.messages.PublicKeyCredential.FormatValueValuesEnum
    credential = self.messages.DeviceCredential(
        expirationTime='2017-01-01T00:00:00',
        publicKey=self.messages.PublicKeyCredential(
            format=format_enum.ES256_PEM,
            key='-----BEGIN PUBLIC KEY-----\n00000000\n-----END PUBLIC KEY-----'
        )
    )
    metadata = self.messages.Device.MetadataValue(
        additionalProperties=[self._CreateAdditionalProperty('key', 'value')])
    device = self.messages.Device(
        id='my-device',
        blocked=blocked,
        credentials=[credential],
        metadata=metadata
    )
    self._ExpectCreate(device)

    result = self.devices_client.Create(
        self.registry_ref, 'my-device',
        blocked=blocked,
        credentials=[credential],
        metadata=metadata
    )

    self.assertEqual(result, device)

  def testDelete(self):
    self.client.projects_locations_registries_devices.Delete.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesDeleteRequest(
            name=self.device_name),
        self.messages.Empty())

    result = self.devices_client.Delete(self.device_ref)

    self.assertEqual(result, self.messages.Empty())

  def testGet(self):
    device = self.messages.Device(id='my-device')
    self.client.projects_locations_registries_devices.Get.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesGetRequest(
            name=self.device_name),
        device)

    result = self.devices_client.Get(self.device_ref)

    self.assertEqual(result, device)

  def _ExpectList(self, devices, batch_size=100, limit=None, device_ids=None,
                  device_num_ids=None, field_mask=None):
    """Create expected List() call(s).

    Based on the number of devices and batching parameters.

    Args:
      devices: list of Device
      batch_size: int, the number of results in each page
      limit: int or None, the total number of devices to limit
      device_ids: list of str or None, the device IDs requested
      device_num_ids: list of int or None, the numerical device IDs requested
      field_mask: str or None, the requested fields
    """
    if limit:
      devices = devices[:limit]

    slices, token_pairs = list_slicer.SliceList(devices, batch_size)

    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())
    for slice_, (current_token, next_token) in zip(slices, token_pairs):
      self.client.projects_locations_registries_devices.List.Expect(
          self.messages.CloudiotProjectsLocationsRegistriesDevicesListRequest(
              parent=registry_name,
              pageToken=current_token,
              pageSize=batch_size,
              deviceIds=device_ids or [],
              deviceNumIds=device_num_ids or [],
              fieldMask=field_mask),
          self.messages.ListDevicesResponse(
              devices=devices[slice_],
              nextPageToken=next_token))

  def testList(self):
    devices = [self.messages.Device() for _ in range(200)]
    self._ExpectList(devices)

    result = self.devices_client.List(self.registry_ref)

    self.assertEqual(list(result), devices)

  def testList_ListingOptions(self):
    """Tests parameters that affect mechanics of the list calls."""
    limit = 150
    page_size = 50
    devices = [self.messages.Device() for _ in range(200)]
    self._ExpectList(devices, batch_size=page_size, limit=limit)

    result = self.devices_client.List(
        self.registry_ref,
        limit=limit,
        page_size=page_size)

    # Verify that only `limit` items were returned
    self.assertEqual(list(result), devices[:limit])

  def testList_FilteringOptions(self):
    devices = [self.messages.Device(id='device{}'.format(i)) for i in range(90)]
    self._ExpectList(devices, device_ids=['device1', 'device2'],
                     device_num_ids=[1, 2, 3],
                     field_mask='blocked')

    result = self.devices_client.List(
        self.registry_ref,
        device_ids=['device1', 'device2'],
        device_num_ids=[1, 2, 3],
        field_mask=['blocked'])

    self.assertEqual(list(result), devices)

  def testPatch_NoOptions(self):
    with self.AssertRaisesExceptionMatches(
        devices_api.NoFieldsSpecifiedError, 'at least one field to update'):
      self.devices_client.Patch(self.registry_ref)

  def testPatch_SomeOptions(self):
    blocked = False
    device = self.messages.Device(
        blocked=blocked
    )
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=self.device_name,
            device=device,
            updateMask=('blocked')),
        device)

    result = self.devices_client.Patch(
        self.device_ref,
        blocked=blocked)

    self.assertEqual(result, device)

  def testPatch_AllOptions(self):
    blocked = False
    format_enum = self.messages.PublicKeyCredential.FormatValueValuesEnum
    credential = self.messages.DeviceCredential(
        expirationTime='2017-01-01T00:00:00',
        publicKey=self.messages.PublicKeyCredential(
            format=format_enum.ES256_PEM,
            key='-----BEGIN PUBLIC KEY-----\n00000000\n-----END PUBLIC KEY-----'
        )
    )
    device = self.messages.Device(
        blocked=blocked,
        credentials=[credential]
    )
    self.client.projects_locations_registries_devices.Patch.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest(
            name=self.device_name,
            device=device,
            updateMask=('blocked,credentials')),
        device)

    result = self.devices_client.Patch(
        self.device_ref,
        blocked=blocked,
        credentials=[credential])

    self.assertEqual(result, device)

  def testModifyConfig(self):
    data = b'\x00\x01\x02\x03'
    device_config = self.messages.DeviceConfig(
        cloudUpdateTime='2017-01-01T00:00Z',
        binaryData=data,
        version=10
    )
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistriesDevices'
                           'ModifyCloudToDeviceConfigRequest')
    sub_request_type = self.messages.ModifyCloudToDeviceConfigRequest
    request = request_type(
        name=self.device_name,
        modifyCloudToDeviceConfigRequest=sub_request_type(
            binaryData=data,
            versionToUpdate=None
        )
    )
    service = self.client.projects_locations_registries_devices
    service.ModifyCloudToDeviceConfig.Expect(request, device_config)

    result = self.devices_client.ModifyConfig(self.device_ref, data)

    self.assertEqual(result, device_config)


class DeviceConfigsTest(base.CloudIotBase):

  def SetUp(self):
    self.device_configs_client = devices_api.DeviceConfigsClient(
        self.client, self.messages)
    self.device_ref = util.GetRegistry().Create(
        'cloudiot.projects.locations.registries.devices',
        locationsId='us-central1', projectsId=self.Project(),
        registriesId='my-registry', devicesId='my-device')
    self.config_version_name = (
        'projects/{}/locations/us-central1/registries/my-registry/'
        'devices/my-device').format(self.Project())

  def _MakeDeviceConfigs(self, num=10):
    device_configs = []
    for i in range(num):
      device_configs.append(self.messages.DeviceConfig(binaryData=bytes(i)))
    return device_configs

  def testList(self):
    device_configs = self._MakeDeviceConfigs()
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistriesDevices'
                           'ConfigVersionsListRequest')
    service = self.client.projects_locations_registries_devices_configVersions
    service.List.Expect(request_type(name=self.config_version_name),
                        self.messages.ListDeviceConfigVersionsResponse(
                            deviceConfigs=device_configs))

    result = self.device_configs_client.List(self.device_ref)

    self.assertEqual(list(result), device_configs)

  def testList_NumVersions(self):
    device_configs = self._MakeDeviceConfigs(3)
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistriesDevices'
                           'ConfigVersionsListRequest')
    service = self.client.projects_locations_registries_devices_configVersions
    service.List.Expect(request_type(name=self.config_version_name,
                                     numVersions=3),
                        self.messages.ListDeviceConfigVersionsResponse(
                            deviceConfigs=device_configs))

    result = self.device_configs_client.List(self.device_ref,
                                             num_versions=3)

    self.assertEqual(list(result), device_configs)


class DeviceStatesTest(base.CloudIotBase):

  def SetUp(self):
    self.device_states_client = devices_api.DeviceStatesClient(
        self.client, self.messages)
    self.device_name = (
        'projects/{}/locations/us-central1/registries/my-registry/'
        'devices/my-device').format(self.Project())
    self.device_ref = util.GetRegistry().Create(
        'cloudiot.projects.locations.registries.devices',
        locationsId='us-central1', projectsId=self.Project(),
        registriesId='my-registry', devicesId='my-device')
    self.request_type = getattr(self.messages,
                                'CloudiotProjectsLocationsRegistries'
                                'DevicesStatesListRequest')
    self.service = self.client.projects_locations_registries_devices_states

  def _MakeDeviceStates(self, num=10):
    device_states = []
    for i in range(num):
      device_states.append(self.messages.DeviceState(binaryData=bytes(i)))
    return device_states

  def testList(self):
    device_states = self._MakeDeviceStates()
    self.service.List.Expect(self.request_type(name=self.device_name),
                             self.messages.ListDeviceStatesResponse(
                                 deviceStates=device_states))

    result = self.device_states_client.List(self.device_ref)

    self.assertEqual(list(result), device_states)

  def testList_NumVersions(self):
    device_states = self._MakeDeviceStates(3)
    self.service.List.Expect(self.request_type(name=self.device_name,
                                               numStates=3),
                             self.messages.ListDeviceStatesResponse(
                                 deviceStates=device_states))

    result = self.device_states_client.List(self.device_ref,
                                            num_states=3)

    self.assertEqual(list(result), device_states)


if __name__ == '__main__':
  test_case.main()
