# -*- coding: utf-8 -*- #
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

"""Tests for `gcloud iot gateways bind`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class BindTestGA(base.CloudIotBase, parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _ExpectBind(self, device, gateway):
    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())

    registry = resources.REGISTRY.Clone()

    device_collection = ('cloudiot.projects.locations.registries.devices')
    device_ref = registry.Parse(device, collection=device_collection)

    gateway_ref = registry.Parse(
        gateway, collection='cloudiot.projects.locations.registries.devices')

    bind_request = self.messages.BindDeviceToGatewayRequest(
        deviceId=device_ref.Name(), gatewayId=gateway_ref.Name())
    self.client.projects_locations_registries.BindDeviceToGateway.Expect(
        request=self.messages.
        CloudiotProjectsLocationsRegistriesBindDeviceToGatewayRequest(
            bindDeviceToGatewayRequest=bind_request,
            parent=registry_name),
        response=self.messages.BindDeviceToGatewayResponse())

  def testBind(self):
    gateway = self._GetGateway()

    gateway_name = ('projects/{}/'
                    'locations/us-central1/'
                    'registries/my-registry/'
                    'devices/{}').format(self.Project(), gateway.id)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())

    self._ExpectBind(device_name, gateway_name)

    self.Run(
        ('iot devices gateways bind --device my-device '
         '    --device-registry my-registry'
         '    --device-region us-central1'
         '    --gateway {}'
         '    --gateway-registry my-registry'
         '    --gateway-region us-central1').format(gateway.id))

  def testBindWithRegistryFallthrough(self):
    gateway = self._GetGateway()

    gateway_name = ('projects/{}/'
                    'locations/us-central1/'
                    'registries/my-registry/'
                    'devices/{}').format(self.Project(), gateway.id)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())

    self._ExpectBind(device_name, gateway_name)

    self.Run(
        ('iot devices gateways bind --device my-device '
         '    --device-region us-central1'
         '    --gateway {}'
         '    --gateway-registry my-registry'
         '    --gateway-region us-central1').format(gateway.id))

    self._ExpectBind(device_name, gateway_name)
    self.Run(
        ('iot devices gateways bind --device my-device '
         '    --device-registry my-registry'
         '    --device-region us-central1'
         '    --gateway {}'
         '    --gateway-region us-central1').format(gateway.id))


class BindTestBeta(BindTestGA):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class BindTestAlpha(BindTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
