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

"""Tests for `gcloud iot devices list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class DevicesListTestGA(base.CloudIotDeviceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testList(self):
    devices = self._MakeDevices()
    self._ExpectListDevices(devices)

    results = self.Run('iot devices list '
                       '    --registry my-registry '
                       '    --region us-central1')

    self.assertEqual(results, devices)

  def testList_DeviceIds(self):
    devices = self._MakeDevices()
    self._ExpectListDevices(devices, device_ids=['d0', 'd1'],
                            device_num_ids=[3, 4])

    results = self.Run('iot devices list '
                       '    --device-ids d0,d1'
                       '    --device-num-ids 3,4'
                       '    --registry my-registry '
                       '    --region us-central1')

    self.assertEqual(results, devices)

  def testList_CheckFormat(self):
    devices = self._MakeDevices(n=3)
    self._ExpectListDevices(devices)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('iot devices list '
             '    --registry my-registry '
             '    --region us-central1')

    self.AssertOutputEquals("""\
        ID  NUM_ID  BLOCKED
        d0  0       False
        d1  1       False
        d2  2       False
        """, normalize_space=True)

  def testList_Uri(self):
    devices = self._MakeDevices(n=3)
    self._ExpectListDevices(devices)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('iot devices list '
             '    --registry my-registry '
             '    --region us-central1 '
             '    --uri')

    self.AssertOutputEquals(
        """\
        https://cloudiot.googleapis.com/v1/projects/{project}/locations/us-central1/registries/my-registry/devices/d0
        https://cloudiot.googleapis.com/v1/projects/{project}/locations/us-central1/registries/my-registry/devices/d1
        https://cloudiot.googleapis.com/v1/projects/{project}/locations/us-central1/registries/my-registry/devices/d2
        """.format(project=self.Project()), normalize_space=True)

  def testList_RelativeName(self):
    devices = self._MakeDevices()
    self._ExpectListDevices(devices)

    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())
    results = self.Run('iot devices list '
                       '    --registry {}'.format(registry_name))

    self.assertEqual(results, devices)


class DevicesListTestBeta(DevicesListTestGA, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.auth_enum = (
        self.messages.GatewayConfig.GatewayAuthMethodValueValuesEnum)
    self.gateway_enum = self.messages.GatewayConfig.GatewayTypeValueValuesEnum
    self.list_gateway_enum = (
        self.messages.CloudiotProjectsLocationsRegistriesDevicesListRequest.
        GatewayListOptionsGatewayTypeValueValuesEnum)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testList_CheckFormat(self):
    devices = self._MakeDevices(
        n=3,
        gateway_config=self.messages.GatewayConfig(
            gatewayType=self.gateway_enum.GATEWAY,
            gatewayAuthMethod=self.auth_enum.ASSOCIATION_AND_DEVICE_AUTH_TOKEN))
    self._ExpectListDevices(devices)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('iot devices list '
             '    --registry my-registry '
             '    --region us-central1')

    self.AssertOutputEquals(
        """\
        ID NUM_ID BLOCKED GATEWAY_TYPE GATEWAY_AUTH_METHOD
        d0 0 False GATEWAY ASSOCIATION_AND_DEVICE_AUTH_TOKEN
        d1 1 False GATEWAY ASSOCIATION_AND_DEVICE_AUTH_TOKEN
        d2 2 False GATEWAY ASSOCIATION_AND_DEVICE_AUTH_TOKEN
        """,
        normalize_space=True)

  @parameterized.parameters('non-gateway', 'gateway')
  def testList_GatewayType(self, gateway_type):
    # Filtering happens on backend so just checking for command workflow here.
    devices = self._MakeDevices(
        gateway_config=self.messages.GatewayConfig(
            gatewayType=self.gateway_enum.GATEWAY,
            gatewayAuthMethod=self.auth_enum.ASSOCIATION_AND_DEVICE_AUTH_TOKEN))
    gateway_val = self.list_gateway_enum.lookup_by_name(
        gateway_type.upper().replace('-', '_'))
    self._ExpectListDevices(devices, gateway_type=gateway_val)

    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())
    results = self.Run('iot devices list '
                       '    --registry {} --device-type {}'.format(
                           registry_name, gateway_type))

    self.assertEqual(results, devices)


class DevicesListTestAlpha(DevicesListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
