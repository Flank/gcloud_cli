# Lint as: python3
# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for listing reusable configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from surface.privateca.reusable_configs import list as list_command
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ListReusableConfigsTest(cli_test_base.CliTestBase,
                              sdk_test_base.WithFakeAuth):

  _PROJECT_ID = 'fake-project'
  _REUSABLE_CONFIG_PROJECT_ID = 'privateca-data'
  _LOCATIONS = ['europe-west1', 'east-us1', 'west-us1']

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    properties.VALUES.core.project.Set('fake-project')
    self.messages = privateca_base.GetMessagesModule()
    self.mock_client = api_mock.Client(
        client_class=privateca_base.GetClientClass(),
        real_client=privateca_base.GetClientInstance())
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def _ExpectGetLocations(self):
    self.mock_client.projects_locations.List.Expect(
        request=self.messages.PrivatecaProjectsLocationsListRequest(
            name='projects/{}'.format(self._PROJECT_ID)),
        response=self.messages.ListLocationsResponse(
            locations=
            [self.messages.Location(locationId=location)
             for location in self._LOCATIONS]))

  def _ExpectGetReusableConfig(self, location, resource_id):
    resource_name = 'projects/{}/locations/{}/reusableConfigs/{}'.format(
        self._REUSABLE_CONFIG_PROJECT_ID, location, resource_id)
    self.mock_client.projects_locations_reusableConfigs.Get.Expect(
        request=self.messages.
        PrivatecaProjectsLocationsReusableConfigsGetRequest(name=resource_name),
        response=self.messages.ReusableConfig(
            name=resource_name,
            description='Description of {}'.format(resource_id)))

  def _ValidateExpectedOutput(self, location, resource_ids):
    output_rows = [
        '{resource_id} {location} Description of {resource_id}'.format(
            resource_id=resource_id, location=location)
        for resource_id in resource_ids]
    self.AssertOutputEquals(
        'NAME LOCATION DESCRIPTION\n{}\n'.format('\n'.join(output_rows)),
        normalize_space=True)

  def testNoArgsUsesFirstSupportedLocation(self):
    self._ExpectGetLocations()
    location = self._LOCATIONS[0]
    for resource_id in list_command._KnownResourceIds:
      self._ExpectGetReusableConfig(location, resource_id)

    self.Run('privateca reusable-configs list')

    self._ValidateExpectedOutput(location, list_command._KnownResourceIds)

  def testUsesGivenLocation(self):
    location = 'us-west1'
    for resource_id in list_command._KnownResourceIds:
      self._ExpectGetReusableConfig(location, resource_id)

    self.Run('privateca reusable-configs list --location {}'.format(location))

    self._ValidateExpectedOutput(location, list_command._KnownResourceIds)

  def testLimit(self):
    self._ExpectGetLocations()
    location = self._LOCATIONS[0]
    for resource_id in list_command._KnownResourceIds:
      self._ExpectGetReusableConfig(location, resource_id)

    self.Run('privateca reusable-configs list --limit 1')

    self._ValidateExpectedOutput(location, [list_command._KnownResourceIds[0]])

  def testFilter(self):
    self._ExpectGetLocations()
    location = self._LOCATIONS[0]
    for resource_id in list_command._KnownResourceIds:
      self._ExpectGetReusableConfig(location, resource_id)

    self.Run('privateca reusable-configs list --filter name:subordinate')

    self._ValidateExpectedOutput(location, [
        resource_id for resource_id in list_command._KnownResourceIds
        if 'subordinate' in resource_id
    ])

  def testSortBy(self):
    self._ExpectGetLocations()
    location = self._LOCATIONS[0]
    for resource_id in list_command._KnownResourceIds:
      self._ExpectGetReusableConfig(location, resource_id)

    self.Run('privateca reusable-configs list --sort-by ~name')

    self._ValidateExpectedOutput(
        location, sorted(list_command._KnownResourceIds, reverse=True))
