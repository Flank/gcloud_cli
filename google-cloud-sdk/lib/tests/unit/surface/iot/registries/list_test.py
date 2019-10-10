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

"""Tests for `gcloud iot registries list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class RegistriesListTestGA(base.CloudIotRegistryBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

    # For convenience
    self.mqtt_enum = self.registries_client.mqtt_config_enum

  def testList(self):
    registries = self._MakeRegistries()
    self._ExpectListRegistries(registries)

    results = self.Run('iot registries list --region us-central1')

    self.assertEqual(results, registries)

  def testList_CheckFormat(self):
    registries = [
        self.messages.DeviceRegistry(
            name='projects/{}/locations/us-central1/registries/r0'.format(
                self.Project()),
            mqttConfig=self.messages.MqttConfig(
                mqttEnabledState=self.mqtt_enum.MQTT_ENABLED)),
        self.messages.DeviceRegistry(
            name='projects/{}/locations/us-central1/registries/r1'.format(
                self.Project()),
            mqttConfig=self.messages.MqttConfig(
                mqttEnabledState=self.mqtt_enum.MQTT_DISABLED)),
        self.messages.DeviceRegistry(
            name='projects/{}/locations/us-central1/registries/r2'.format(
                self.Project()),
            mqttConfig=self.messages.MqttConfig(
                mqttEnabledState=self.mqtt_enum.MQTT_STATE_UNSPECIFIED))
    ]
    self._ExpectListRegistries(registries)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('iot registries list --region us-central1')

    self.AssertOutputEquals("""\
        ID    LOCATION     MQTT_ENABLED
        r0    us-central1  MQTT_ENABLED
        r1    us-central1  MQTT_DISABLED
        r2    us-central1  MQTT_STATE_UNSPECIFIED
        """, normalize_space=True)

  def testList_Uri(self):
    registries = self._MakeRegistries(n=3)
    self._ExpectListRegistries(registries)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('iot registries list --region us-central1 --uri')

    self.AssertOutputEquals("""\
        https://cloudiot.googleapis.com/v1/projects/fake-project/locations/us-central1/registries/r0
        https://cloudiot.googleapis.com/v1/projects/fake-project/locations/us-central1/registries/r1
        https://cloudiot.googleapis.com/v1/projects/fake-project/locations/us-central1/registries/r2
        """, normalize_space=True)


class RegistriesListTestBeta(RegistriesListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class RegistriesListTestAlpha(RegistriesListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
