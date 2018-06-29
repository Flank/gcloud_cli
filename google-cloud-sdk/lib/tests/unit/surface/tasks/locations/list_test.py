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
"""Tests for `gcloud tasks locations list`."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.tasks import test_base


class LocationsListTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(), collection='cloudtasks.projects')
    self.project_name = 'projects/{}'.format(self.Project())
    self.location_ids = ['us-central1', 'europe-west1', 'asia-northeast1']

  def _MakeLocations(self):
    locations = []
    for lid in self.location_ids:
      l = self.messages.Location(
          name='projects/{}/locations/{}'.format(self.Project(), lid))
      locations.append(l)
    return locations

  def testList(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    expected_locations = self._MakeLocations()
    self.locations_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsListRequest(
            name=self.project_name),
        response=self.messages.ListLocationsResponse(
            locations=expected_locations))

    actual_locations = self.Run('tasks locations list')

    self.assertEqual(actual_locations, expected_locations)

  def testList_Uri(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_locations = self._MakeLocations()
    self.locations_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsListRequest(
            name=self.project_name),
        response=self.messages.ListLocationsResponse(
            locations=expected_locations))

    self.Run('tasks locations list --uri')

    expected_location_uris = [l.name for l in expected_locations]
    self.AssertOutputEquals("""\
        https://cloudtasks.googleapis.com/v2beta2/{}
        https://cloudtasks.googleapis.com/v2beta2/{}
        https://cloudtasks.googleapis.com/v2beta2/{}
        """.format(*expected_location_uris), normalize_space=True)

  def testList_CheckFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_locations = self._MakeLocations()
    self.locations_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsListRequest(
            name=self.project_name),
        response=self.messages.ListLocationsResponse(
            locations=expected_locations))

    self.Run('tasks locations list')

    self.AssertOutputContains("""\
        NAME        FULL_NAME
        """, normalize_space=True)

if __name__ == '__main__':
  test_case.main()
