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
"""Tests for `gcloud tasks list`."""

from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.command_lib.util import time_util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.tasks import test_base


class TasksListTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.queue_name = (
        'projects/{}/locations/us-central1/queues/my-queue'.format(
            self.Project()))
    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())

    self.task_create_time = time_util.CalculateExpiration(10)
    self.task_schedule_time = time_util.CalculateExpiration(20)

  def _MakeTasks(self, n=10):
    tasks = []
    for i in range(n):
      task_name = '{}/tasks/t{}'.format(self.queue_name, i)
      t = self.messages.Task(
          name=task_name,
          appEngineHttpRequest=self.messages.AppEngineHttpRequest(),
          createTime=self.task_create_time,
          scheduleTime=self.task_schedule_time,
          status=self.messages.TaskStatus(attemptDispatchCount=i+1,
                                          attemptResponseCount=i+1))
      tasks.append(t)
    return tasks

  def testList(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    tasks = self._MakeTasks()
    self.tasks_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksListRequest(
            parent=self.queue_name),
        response=self.messages.ListTasksResponse(tasks=tasks))

    results = self.Run('tasks list --queue my-queue')

    self.assertEqual(results, tasks)

  def testList_Uri(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    tasks = self._MakeTasks(n=3)
    self.tasks_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksListRequest(
            parent=self.queue_name),
        response=self.messages.ListTasksResponse(tasks=tasks))

    self.Run('tasks list --queue my-queue --uri')

    self.AssertOutputEquals("""\
        https://cloudtasks.googleapis.com/v2beta2/{0}/tasks/t0
        https://cloudtasks.googleapis.com/v2beta2/{0}/tasks/t1
        https://cloudtasks.googleapis.com/v2beta2/{0}/tasks/t2
        """.format(self.queue_name), normalize_space=True)

  def testList_Location(self):
    queue_name = (
        'projects/{}/locations/us-central2/queues/my-queue'.format(
            self.Project()))

    properties.VALUES.core.user_output_enabled.Set(False)
    tasks = self._MakeTasks()
    self.tasks_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksListRequest(
            parent=queue_name),
        response=self.messages.ListTasksResponse(tasks=tasks))

    results = self.Run('tasks list --queue my-queue --location=us-central2')

    self.assertEqual(results, tasks)

  def testList_CheckFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    tasks = self._MakeTasks(n=3)
    self.tasks_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksListRequest(
            parent=self.queue_name),
        response=self.messages.ListTasksResponse(tasks=tasks))

    self.Run('tasks list --queue my-queue')

    self.AssertOutputEquals("""\
        TASK_NAME  TYPE        CREATE_TIME      SCHEDULE_TIME      DISPATCH_ATTEMPTS  RESPONSE_ATTEMPTS  LAST_ATTEMPT_STATUS
        t0         app-engine  {0}              {1}                1                  1                  Unknown
        t1         app-engine  {0}              {1}                2                  2                  Unknown
        t2         app-engine  {0}              {1}                3                  3                  Unknown
        """.format(self.task_create_time,
                   self.task_schedule_time), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
