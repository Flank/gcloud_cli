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
"""Tests for `gcloud tasks delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.tasks import test_base


class TasksDeleteTest(test_base.CloudTasksTestBase,
                      sdk_test_base.WithLogCapture):

  def SetUp(self):
    self.location_id = 'us-central1'
    self.location_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations', locationsId=self.location_id,
        projectsId=self.Project())
    self.queue_id = 'my-queue'
    self.task_id = 'my-task'
    self.task_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues.tasks',
        locationsId=self.location_id, projectsId=self.Project(),
        queuesId=self.queue_id, tasksId=self.task_id)

    self.resolve_loc_mock = self.StartObjectPatch(
        app, 'ResolveAppLocation',
        return_value=parsers.ParseLocation('us-central1').SelfLink())

    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectDelete(self, name=None, exception=None):
    name = name or self.task_ref.RelativeName()
    response = self.messages.Empty() if exception is None else None
    self.tasks_service.Delete.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksDeleteRequest(
            name=name),
        response=response, exception=exception)

  def testDelete(self):
    self._ExpectDelete()

    actual = self.Run('tasks delete {} --queue {}'.format(self.task_id,
                                                          self.queue_id))

    self.assertIsNone(actual)
    self.resolve_loc_mock.assert_called_once_with(parsers.ParseProject())
    self.AssertLogContains('Deleted task [my-task].')

  def testDelete_RelativeName(self):
    task_name = ('projects/other-project/locations/us-central1/queues/my-queue'
                 '/tasks/my-task')
    self._ExpectDelete(name=task_name)

    actual = self.Run('tasks delete {}'.format(task_name))

    self.assertIsNone(actual)
    self.resolve_loc_mock.assert_not_called()

  def testDelete_Location(self):
    location_id = 'us-central2'
    self.task_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues.tasks',
        locationsId=location_id, projectsId=self.Project(),
        queuesId=self.queue_id, tasksId=self.task_id)

    self._ExpectDelete()

    actual = self.Run(
        'tasks delete {} --queue {} --location=us-central2'.format(
            self.task_id, self.queue_id))

    self.assertIsNone(actual)
    self.AssertLogContains('Deleted task [my-task].')

  def testDelete_NonExistentTask(self):
    self._ExpectDelete(exception=http_error.MakeDetailedHttpError(
        code=404, message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run('tasks delete {} --queue {}'.format(self.task_id, self.queue_id))

    self.AssertErrContains('Requested entity was not found.')


class TasksDeleteTestBeta(TasksDeleteTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
