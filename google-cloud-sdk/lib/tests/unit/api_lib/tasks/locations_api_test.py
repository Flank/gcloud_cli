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
"""Unit tests for Cloud Tasks API locations service in gcloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.tasks import test_base
from six.moves import range


class LocationsTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(), collection='cloudtasks.projects')
    self.location = 'us-central1'
    self.location_ref = resources.REGISTRY.Parse(
        self.location, params={'projectsId': self.Project()},
        collection='cloudtasks.projects.locations')
    # Define separately from location_ref because we know that this is what the
    # API expects
    self.location_name = 'projects/{}/locations/{}'.format(
        self.Project(), self.location)

  def testGet(self):
    expected_location = self.messages.Location(name=self.location_name)
    self.locations_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsGetRequest(
            name=self.location_name),
        expected_location)
    actual_location = self.locations_client.Get(self.location_ref)
    self.assertEqual(actual_location, expected_location)

  def testList(self):
    expected_location_list = [
        self.messages.Location(name='{}{}'.format(self.location_name, i))
        for i in range(10)]
    self.locations_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsListRequest(
            name=self.project_ref.RelativeName(), pageSize=100),
        response=self.messages.ListLocationsResponse(
            locations=expected_location_list))

    actual_location_list = list(self.locations_client.List(self.project_ref))

    self.assertEqual(actual_location_list, expected_location_list)


if __name__ == '__main__':
  test_case.main()
