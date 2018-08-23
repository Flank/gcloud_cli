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

"""Tests for `gcloud iot devices delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices as devices_api
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class DevicesDeleteTest(base.CloudIotBase):

  def SetUp(self):
    self.devices_client = devices_api.DevicesClient(self.client, self.messages)

  def testDelete(self, track):
    self.track = track
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Delete.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesDeleteRequest(
            name=device_name),
        self.messages.Empty())

    self.WriteInput('y\n')
    self.Run('iot devices delete my-device '
             '--registry my-registry '
             '--region us-central1')

    self.AssertLogContains('Deleted device [my-device].')

  def testDelete_RelativeName(self, track):
    self.track = track
    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.client.projects_locations_registries_devices.Delete.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDevicesDeleteRequest(
            name=device_name),
        self.messages.Empty())

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    self.WriteInput('y\n')
    self.Run('iot devices delete {}'.format(device_name))


if __name__ == '__main__':
  test_case.main()
