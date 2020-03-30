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
"""Tests for google3.third_party.py.googlecloudsdk.api_lib.privateca.locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.privateca import base
from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case


class LocationsApiTest(sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.messages = base.GetMessagesModule()
    self.client = mock.Client(
        client_class=apis.GetClientClass('privateca', 'v1alpha1'),
        real_client=base.GetClientInstance())
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

  def testGetLocationsReturnsLocationIds(self):
    properties.VALUES.core.project.Set('p1')
    self.client.projects_locations.List.Expect(
        request=self.messages.PrivatecaProjectsLocationsListRequest(
            name='projects/p1'),
        response=self.messages.ListLocationsResponse(
            locations=[
                self.messages.Location(locationId='us-west1'),
                self.messages.Location(locationId='europe-west1'),
            ]))

    result = locations.GetSupportedLocations()
    self.assertCountEqual(['us-west1', 'europe-west1'], result)


if __name__ == '__main__':
  test_case.main()
