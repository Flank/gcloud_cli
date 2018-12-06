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

"""Tests for `gcloud iot registries describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import registries as registries_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


class RegistriesDescribeTestGA(base.CloudIotBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.registries_client = registries_api.RegistriesClient(self.client,
                                                             self.messages)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testDescribe(self):
    registry_name = 'projects/{}/locations/us-central1/registries/{}'.format(
        self.Project(), 'my-registry')
    registry = self.messages.DeviceRegistry(name=registry_name)
    self.client.projects_locations_registries.Get.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesGetRequest(
            name=registry_name),
        registry)

    result = self.Run(
        'iot registries describe my-registry --region us-central1')

    self.assertEqual(result, registry)

  def testDescribe_RelativeName(self):
    registry_name = 'projects/{}/locations/us-central1/registries/{}'.format(
        self.Project(), 'my-registry')
    registry = self.messages.DeviceRegistry(name=registry_name)
    self.client.projects_locations_registries.Get.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesGetRequest(
            name=registry_name),
        registry)

    result = self.Run(
        'iot registries describe {}'.format(registry_name))

    self.assertEqual(result, registry)


class RegistriesDescribeTestBeta(RegistriesDescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class RegistriesDescribeTestAlpha(RegistriesDescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
