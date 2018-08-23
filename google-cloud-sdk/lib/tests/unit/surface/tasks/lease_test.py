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
"""Tests for `gcloud tasks lease`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import time_util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.tasks import test_base
from six.moves import range


class TasksLeaseTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.queue_name = (
        'projects/{}/locations/us-central1/queues/my-queue'.format(
            self.Project()))
    self.task_name = '{}/tasks/my-task'.format(self.queue_name)

    self.task_create_time = time_util.CalculateExpiration(0) + 'Z'
    self.original_schedule_time = time_util.CalculateExpiration(10) + 'Z'
    self.lease_duration = 20
    self.new_schedule_time = time_util.CalculateExpiration(
        10 + self.lease_duration) + 'Z'

    properties.VALUES.core.user_output_enabled.Set(False)

  def testLease(self):
    expected_lease_tasks_request = self.messages.LeaseTasksRequest(
        leaseDuration='{}s'.format(self.lease_duration), maxTasks=1000)
    expected_tasks = [
        self.messages.Task(name='{}{}'.format(self.task_name, i),
                           pullMessage=self.messages.PullMessage(),
                           createTime=self.task_create_time,
                           scheduleTime=self.new_schedule_time,
                           status=self.messages.TaskStatus(
                               attemptDispatchCount=1))
        for i in range(100)]
    expected_response = self.messages.LeaseTasksResponse(tasks=expected_tasks)
    self.tasks_service.Lease.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksLeaseRequest(
            leaseTasksRequest=expected_lease_tasks_request,
            parent=self.queue_name),
        response=expected_response)

    actual_response = self.Run('tasks lease --queue {} --lease-duration {}'
                               .format(self.queue_name, self.lease_duration))

    self.assertEqual(list(actual_response), expected_response.tasks)

  def testLease_Location(self):
    queue_name = (
        'projects/{}/locations/us-central2/queues/my-queue'.format(
            self.Project()))
    task_name = '{}/tasks/my-task'.format(queue_name)

    expected_lease_tasks_request = self.messages.LeaseTasksRequest(
        leaseDuration='{}s'.format(self.lease_duration), maxTasks=1000)
    expected_tasks = [
        self.messages.Task(name='{}{}'.format(task_name, i),
                           pullMessage=self.messages.PullMessage(),
                           createTime=self.task_create_time,
                           scheduleTime=self.new_schedule_time,
                           status=self.messages.TaskStatus(
                               attemptDispatchCount=1))
        for i in range(100)]
    expected_response = self.messages.LeaseTasksResponse(tasks=expected_tasks)
    self.tasks_service.Lease.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksLeaseRequest(
            leaseTasksRequest=expected_lease_tasks_request,
            parent=self.queue_name),
        response=expected_response)

    actual_response = self.Run(
        'tasks lease --queue {} --lease-duration {} '
        '--location=us-central2'.format(self.queue_name, self.lease_duration))

    self.assertEqual(list(actual_response), expected_response.tasks)

  def testLease_CheckFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_lease_tasks_request = self.messages.LeaseTasksRequest(
        leaseDuration='{}s'.format(self.lease_duration), maxTasks=1000)
    expected_tasks = [
        self.messages.Task(name='{}{}'.format(self.task_name, i),
                           pullMessage=self.messages.PullMessage(),
                           createTime=self.task_create_time,
                           scheduleTime=self.new_schedule_time,
                           status=self.messages.TaskStatus(
                               attemptDispatchCount=1))
        for i in range(3)]
    expected_response = self.messages.LeaseTasksResponse(tasks=expected_tasks)
    self.tasks_service.Lease.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksLeaseRequest(
            leaseTasksRequest=expected_lease_tasks_request,
            parent=self.queue_name),
        response=expected_response)

    self.Run('tasks lease --queue {} --lease-duration {}'.format(
        self.queue_name, self.lease_duration))

    self.AssertOutputEquals("""\
        TASK_NAME  TYPE   CREATE_TIME      SCHEDULE_TIME      DISPATCH_ATTEMPTS  RESPONSE_ATTEMPTS  LAST_ATTEMPT_STATUS
        my-task0   pull   {0}              {1}                1                  0                  Unknown
        my-task1   pull   {0}              {1}                1                  0                  Unknown
        my-task2   pull   {0}              {1}                1                  0                  Unknown
        """.format(self.task_create_time,
                   self.new_schedule_time), normalize_space=True)

  def testLease_Filter(self):
    expected_lease_tasks_request = self.messages.LeaseTasksRequest(
        leaseDuration='{}s'.format(self.lease_duration), maxTasks=1000,
        filter='tag="tag"')
    expected_tasks = [
        self.messages.Task(name='{}{}'.format(self.task_name, i),
                           pullMessage=self.messages.PullMessage(tag='tag'),
                           createTime=self.task_create_time,
                           scheduleTime=self.new_schedule_time,
                           status=self.messages.TaskStatus(
                               attemptDispatchCount=1))
        for i in range(100)]
    expected_response = self.messages.LeaseTasksResponse(tasks=expected_tasks)
    self.tasks_service.Lease.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksLeaseRequest(
            leaseTasksRequest=expected_lease_tasks_request,
            parent=self.queue_name),
        response=expected_response)

    actual_response = self.Run(
        'tasks lease --queue {} --lease-duration {} --tag tag'.format(
            self.queue_name, self.lease_duration))

    self.assertEqual(list(actual_response), expected_response.tasks)

  def testLease_FilterOldestTag(self):
    expected_lease_tasks_request = self.messages.LeaseTasksRequest(
        leaseDuration='{}s'.format(self.lease_duration), maxTasks=1000,
        filter='tag_function=oldest_tag()')
    expected_tasks = [
        self.messages.Task(name='{}{}'.format(self.task_name, i),
                           pullMessage=self.messages.PullMessage(tag='tag'),
                           createTime=self.task_create_time,
                           scheduleTime=self.new_schedule_time,
                           status=self.messages.TaskStatus(
                               attemptDispatchCount=1))
        for i in range(100)]
    expected_response = self.messages.LeaseTasksResponse(tasks=expected_tasks)
    self.tasks_service.Lease.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksLeaseRequest(
            leaseTasksRequest=expected_lease_tasks_request,
            parent=self.queue_name),
        response=expected_response)

    actual_response = self.Run(
        'tasks lease --queue {} --lease-duration {} --oldest-tag'.format(
            self.queue_name, self.lease_duration))

    self.assertEqual(list(actual_response), expected_response.tasks)

if __name__ == '__main__':
  test_case.main()
