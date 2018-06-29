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
"""Tests for `gcloud tasks queues describe`."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.tasks import test_base


class QueuesDescribeTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.location_id = 'us-central1'
    self.location_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations', locationsId=self.location_id,
        projectsId=self.Project())
    self.queue_id = 'my-queue'
    self.queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId=self.location_id,
        projectsId=self.Project(), queuesId=self.queue_id)

    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())

    properties.VALUES.core.user_output_enabled.Set(False)

  def testDescribe(self):
    expected = self.messages.Queue(name=self.queue_ref.RelativeName())
    self.queues_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesGetRequest(
            name=self.queue_ref.RelativeName()),
        response=expected)

    actual = self.Run('tasks queues describe {}'.format(self.queue_id))

    self.assertEqual(expected, actual)

  def testDescribe_RelativeName(self):
    queue_name = 'projects/other-project/locations/us-central1/queues/my-queue'
    expected = self.messages.Queue(name=queue_name)
    self.queues_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesGetRequest(
            name=queue_name),
        response=expected)

    actual = self.Run('tasks queues describe {}'.format(queue_name))

    self.assertEqual(actual, expected)

  def testDescribe_NonExistentQueue(self):
    self.queues_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesGetRequest(
            name='projects/{}/locations/us-central1/queues/{}'.format(
                self.Project(), 'my-queue')),
        exception=http_error.MakeDetailedHttpError(
            code=404,
            message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run('tasks queues describe my-queue')

    self.AssertErrContains('Requested entity was not found.')

  def testDescribe_Location(self):
    location_id = 'us-central2'
    queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId=location_id,
        projectsId=self.Project(), queuesId=self.queue_id)

    expected = self.messages.Queue(name=self.queue_ref.RelativeName())
    self.queues_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesGetRequest(
            name=queue_ref.RelativeName()),
        response=expected)

    actual = self.Run(
        'tasks queues describe {} --location=us-central2'.format(self.queue_id))

    self.assertEqual(expected, actual)


if __name__ == '__main__':
  test_case.main()
