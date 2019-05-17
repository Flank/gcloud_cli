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

"""Tests for `gcloud iot gateways unbind`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class UnBindTestGA(base.CloudIotBase, parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectUnbind(self, device, gateway):
    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())

    device_collection = ('cloudiot.projects.locations.registries.devices')

    registry = resources.REGISTRY.Clone()
    device_ref = registry.Parse(device, collection=device_collection)

    gateway_ref = registry.Parse(
        gateway, collection='cloudiot.projects.locations.registries.devices')

    unbind_request = self.messages.UnbindDeviceFromGatewayRequest(
        deviceId=device_ref.Name(), gatewayId=gateway_ref.Name())
    service = self.client.projects_locations_registries
    service.UnbindDeviceFromGateway.Expect(
        request=self.messages.
        CloudiotProjectsLocationsRegistriesUnbindDeviceFromGatewayRequest(
            unbindDeviceFromGatewayRequest=unbind_request,
            parent=registry_name),
        response=self.messages.UnbindDeviceFromGatewayResponse())

  def testUnBind(self):
    gateway = self._GetGateway()

    gateway_name = ('projects/{}/'
                    'locations/us-central1/'
                    'registries/my-registry/'
                    'devices/{}').format(self.Project(), gateway.id)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())

    self._ExpectUnbind(device_name, gateway_name)

    self.Run(
        ('iot devices gateways unbind --device my-device '
         '    --device-registry my-registry'
         '    --device-region us-central1'
         '    --gateway {}'
         '    --gateway-registry my-registry'
         '    --gateway-region us-central1').format(gateway.id))

  def testUnBindWithRegistryFallthrough(self):
    gateway = self._GetGateway()

    gateway_name = ('projects/{}/'
                    'locations/us-central1/'
                    'registries/my-registry/'
                    'devices/{}').format(self.Project(), gateway.id)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())

    self._ExpectUnbind(device_name, gateway_name)

    self.Run(
        ('iot devices gateways unbind --device my-device '
         '    --device-region us-central1'
         '    --gateway {}'
         '    --gateway-registry my-registry'
         '    --gateway-region us-central1').format(gateway.id))

    self._ExpectUnbind(device_name, gateway_name)
    self.Run(
        ('iot devices gateways unbind --device my-device '
         '    --device-registry my-registry'
         '    --device-region us-central1'
         '    --gateway {}'
         '    --gateway-region us-central1').format(gateway.id))


class UnBindTestBeta(UnBindTestGA):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class UnBindTestAlpha(UnBindTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
