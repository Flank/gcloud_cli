# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests for `gcloud iot gateways list-associations`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class ListBoundDevicesTestGA(base.CloudIotDeviceBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)

  def testListResults(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    devices = self._MakeDevices(n=5)
    gateway = self._GetGateway()
    registry_name = 'projects/{}/locations/us-central1/registries/{}'.format(
        self.Project(), 'my-registry')

    self._ExpectListDevices(devices, field_mask='blocked,name,gatewayConfig',
                            gateway_list_device='my-gateway')
    results = self.Run('iot devices gateways list-bound-devices --gateway {} '
                       '--registry {}'.format(gateway.id, registry_name))

    self.assertEqual(devices, results)

  def testList_CheckFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    devices = self._MakeDevices(n=5)
    gateway = self._GetGateway()
    self._ExpectListDevices(devices, field_mask='blocked,name,gatewayConfig',
                            gateway_list_device='my-gateway')
    registry_name = 'projects/{}/locations/us-central1/registries/{}'.format(
        self.Project(), 'my-registry')
    self.Run('iot devices gateways list-bound-devices --gateway {} '
             '--registry {}'.format(gateway.id, registry_name))
    self.AssertOutputEquals(
        """\
        NUM-IDS
        0
        1
        2
        3
        4
        """, normalize_space=True)

  def testRegistriesDevicesListRequestHook(self):
    list_request = (
        self.messages.CloudiotProjectsLocationsRegistriesDevicesListRequest(
            parent='foo'))
    util.RegistriesDevicesListRequestHook(None, None, list_request)
    for python_name, json_name in util._CUSTOM_JSON_FIELD_MAPPINGS.items():
      self.assertEqual(json_name, encoding.GetCustomJsonFieldMapping(
          type(list_request), python_name=python_name))


class ListBoundDevicesTestBeta(ListBoundDevicesTestGA):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ListBoundDevicesTestAlpha(ListBoundDevicesTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
