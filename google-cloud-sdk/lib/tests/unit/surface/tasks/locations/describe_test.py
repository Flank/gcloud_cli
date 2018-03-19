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
"""Tests for `gcloud tasks locations describe`."""

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.tasks import test_base


class LocationsDescribeTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Create('cloudtasks.projects',
                                                 projectsId=self.Project())
    self.location_id = 'us-central1'
    self.location_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations', locationsId=self.location_id,
        projectsId=self.Project())

    properties.VALUES.core.user_output_enabled.Set(False)

  def testDescribe(self):
    expected = self.messages.Location(name=self.location_ref.RelativeName())
    self.locations_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsGetRequest(
            name=self.location_ref.RelativeName()),
        response=expected)

    actual = self.Run('tasks locations describe {}'.format(self.location_id))

    self.assertEqual(expected, actual)

  def testDescribe_RelativeName(self):
    location_name = 'projects/other-project/locations/us-central1'
    expected = self.messages.Location(name=location_name)
    self.locations_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsGetRequest(
            name=location_name),
        response=expected)

    actual = self.Run('tasks locations describe {}'.format(location_name))

    self.assertEqual(actual, expected)

  def testDescribe_NonExistentLocation(self):
    self.locations_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsGetRequest(
            name='projects/{}/locations/bad-region'.format(self.Project())),
        exception=http_error.MakeDetailedHttpError(
            code=404,
            message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run('tasks locations describe bad-region')

    self.AssertErrContains('Requested entity was not found.')


if __name__ == '__main__':
  test_case.main()
