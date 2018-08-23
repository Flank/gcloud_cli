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
"""Unit tests for Cloud Tasks API tasks service in gcloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.py import encoding
from googlecloudsdk.api_lib.tasks import tasks as tasks_api
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.api_lib.util import list_slicer
from tests.lib.surface.tasks import test_base
from six.moves import range
from six.moves import zip


class TasksTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.location_ref = resources.REGISTRY.Parse(
        'us-central1', params={'projectsId': self.Project()},
        collection='cloudtasks.projects.locations')
    self.queue_ref = resources.REGISTRY.Parse(
        'my-queue', params={'projectsId': self.Project(),
                            'locationsId': 'us-central1'},
        collection='cloudtasks.projects.locations.queues')
    self.task_ref = resources.REGISTRY.Parse(
        'my-task', params={'projectsId': self.Project(),
                           'locationsId': 'us-central1',
                           'queuesId': 'my-queue'},
        collection='cloudtasks.projects.locations.queues.tasks')
    # Define separately from task_ref because we know that this is what the API
    # expects
    self.task_name = ('projects/{}/locations/us-central1/queues/my-queue/tasks/'
                      'my-task'.format(self.Project()))

  def _MakeScheduleTime(self):
    return datetime.datetime.utcnow().isoformat() + 'Z'

  def _ExpectList(self, tasks, limit=None, page_size=100):
    """Create expected List() call(s).

    Based on the number of tasks and batching parameters.

    Args:
      tasks: list of Tasks
      limit: int or None, the total number of tasks to limit
      page_size: int, the number of results in each page
    """
    if limit:
      tasks = tasks[:limit]
    slices, token_pairs = list_slicer.SliceList(tasks, page_size)
    for slice_, (current_token, next_token) in zip(slices, token_pairs):
      self.tasks_service.List.Expect(
          self.messages.CloudtasksProjectsLocationsQueuesTasksListRequest(
              parent=self.queue_ref.RelativeName(), pageToken=current_token,
              pageSize=page_size),
          self.messages.ListTasksResponse(tasks=tasks[slice_],
                                          nextPageToken=next_token))

  def testList(self):
    expected_task_list = [
        self.messages.Task(name='{}{}'.format(self.task_name, i))
        for i in range(200)]
    self._ExpectList(expected_task_list)
    actual_task_list = list(self.tasks_client.List(self.queue_ref))
    self.assertEqual(actual_task_list, expected_task_list)

  def testList_AllOptions(self):
    expected_task_list = [
        self.messages.Task(name='{}{}'.format(self.task_name, i))
        for i in range(200)]
    limit = 150
    page_size = 50
    self._ExpectList(expected_task_list, limit=limit, page_size=page_size)
    actual_task_list = list(self.tasks_client.List(
        self.queue_ref, limit=limit, page_size=page_size))
    # Verify that only `limit` items were returned
    self.assertEqual(actual_task_list, expected_task_list[:limit])

  def _TestTaskCreation(self, task_ref=None, schedule_time=None,
                        pull_message=None, app_engine_http_request=None):
    expected_task = self.messages.Task(
        name=task_ref.RelativeName() if task_ref else None,
        scheduleTime=schedule_time, pullMessage=pull_message,
        appEngineHttpRequest=app_engine_http_request)
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_ref.RelativeName(),
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        expected_task)
    actual_task = self.tasks_client.Create(
        parent_ref=self.queue_ref, task_ref=task_ref,
        schedule_time=schedule_time, pull_message=pull_message,
        app_engine_http_request=app_engine_http_request)
    self.assertEqual(actual_task, expected_task)

  def testCreate_NoOptions(self):
    self._TestTaskCreation()

  def testCreate_AllOptions_PullTask(self):
    task_ref = self.task_ref
    schedule_time = self._MakeScheduleTime()
    pull_message = self.messages.PullMessage(tag='tag', payload=b'payload')
    self._TestTaskCreation(task_ref=task_ref, schedule_time=schedule_time,
                           pull_message=pull_message)

  def testCreate_AllOptions_AppEngineTask(self):
    task_ref = self.task_ref
    schedule_time = self._MakeScheduleTime()
    app_engine_http_request = self.messages.AppEngineHttpRequest(
        appEngineRouting=self.messages.AppEngineRouting(service='abc'),
        headers=encoding.DictToAdditionalPropertyMessage(
            {'header': 'value'},
            self.messages.AppEngineHttpRequest.HeadersValue),
        httpMethod=self.messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
            'POST'),
        payload=b'payload', relativeUrl='/paths/a/')
    self._TestTaskCreation(task_ref=task_ref, schedule_time=schedule_time,
                           app_engine_http_request=app_engine_http_request)

  def testCreate_AttemptPullandAppEngineTask(self):
    task_ref = self.task_ref
    schedule_time = self._MakeScheduleTime()
    pull_message = self.messages.PullMessage(tag='tag', payload=b'payload')
    app_engine_http_request = self.messages.AppEngineHttpRequest(
        appEngineRouting=self.messages.AppEngineRouting(service='abc'),
        headers=encoding.DictToAdditionalPropertyMessage(
            {'header': 'value'},
            self.messages.AppEngineHttpRequest.HeadersValue),
        httpMethod=self.messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
            'POST'),
        payload=b'payload', relativeUrl='/paths/a/')
    with self.assertRaises(tasks_api.ModifyingPullAndAppEngineTaskError):
      self.tasks_client.Create(parent_ref=self.queue_ref, task_ref=task_ref,
                               schedule_time=schedule_time,
                               pull_message=pull_message,
                               app_engine_http_request=app_engine_http_request)

  def testGet(self):
    expected_task = self.messages.Task(name=self.task_name)
    self.tasks_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksGetRequest(
            name=self.task_name),
        response=expected_task)

    actual_task = self.tasks_client.Get(self.task_ref)

    self.assertEqual(actual_task, expected_task)

  def testDelete(self):
    self.tasks_service.Delete.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksDeleteRequest(
            name=self.task_name),
        response=self.messages.Empty())

    self.tasks_client.Delete(self.task_ref)

  def testRun(self):
    expected_task = self.messages.Task(name=self.task_name)
    self.tasks_service.Run.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksRunRequest(
            name=self.task_name),
        response=expected_task)

    actual_task = self.tasks_client.Run(self.task_ref)

    self.assertEqual(actual_task, expected_task)

  def testLease(self):
    expected_lease_tasks_request = self.messages.LeaseTasksRequest(
        filter='tag=tag', leaseDuration='20s', maxTasks=100)
    expected_tasks = [
        self.messages.Task(name='{}{}'.format(self.task_name, i))
        for i in range(100)]
    expected_response = self.messages.LeaseTasksResponse(tasks=expected_tasks)
    self.tasks_service.Lease.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksLeaseRequest(
            leaseTasksRequest=expected_lease_tasks_request,
            parent=self.queue_ref.RelativeName()),
        response=expected_response)

    actual_response = self.tasks_client.Lease(
        self.queue_ref, '20s', filter_string='tag=tag', max_tasks=100)

    self.assertEqual(actual_response, expected_response)

  def testAcknowledge(self):
    schedule_time = self._MakeScheduleTime()
    self.tasks_service.Acknowledge.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksAcknowledgeRequest(
            acknowledgeTaskRequest=self.messages.AcknowledgeTaskRequest(
                scheduleTime=schedule_time), name=self.task_name),
        response=self.messages.Empty())

    self.tasks_client.Acknowledge(self.task_ref, schedule_time)

  def testRenewLease(self):
    schedule_time = self._MakeScheduleTime()
    expected_renew_lease_request = self.messages.RenewLeaseRequest(
        scheduleTime=schedule_time, leaseDuration='20s')
    expected_task = self.messages.Task(name=self.task_name,
                                       scheduleTime=schedule_time)
    self.tasks_service.RenewLease.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksRenewLeaseRequest(
            renewLeaseRequest=expected_renew_lease_request,
            name=self.task_name),
        response=expected_task)

    actual_task = self.tasks_client.RenewLease(self.task_ref, schedule_time,
                                               '20s')

    self.assertEqual(actual_task, expected_task)

  def testCancelLease(self):
    schedule_time = self._MakeScheduleTime()
    expected_task = self.messages.Task(name=self.task_name)
    self.tasks_service.CancelLease.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCancelLeaseRequest(
            cancelLeaseRequest=self.messages.CancelLeaseRequest(
                scheduleTime=schedule_time), name=self.task_name),
        response=expected_task)

    actual_task = self.tasks_client.CancelLease(self.task_ref, schedule_time)

    self.assertEqual(actual_task, expected_task)


if __name__ == '__main__':
  test_case.main()
