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
"""Tests for `gcloud tasks queues list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.tasks import test_base
from six.moves import range


class QueuesListTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.location_name = 'projects/{}/locations/us-central1'.format(
        self.Project())
    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation(self.location_name).SelfLink())

  def _MakeQueues(self, n=10):
    queues = []
    for i in range(n):
      queue_name = '{}/queues/q{}'.format(self.location_name, i)
      q = self.messages.Queue(
          name=queue_name,
          appEngineHttpQueue=self.messages.AppEngineHttpQueue(),
          state=self.messages.Queue.StateValueValuesEnum.RUNNING,
          rateLimits=self.messages.RateLimits(
              maxConcurrentDispatches=10, maxDispatchesPerSecond=500))
      queues.append(q)
    return queues

  def testList(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    queues = self._MakeQueues()
    self.queues_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesListRequest(
            parent=self.location_name),
        response=self.messages.ListQueuesResponse(queues=queues))

    results = self.Run('tasks queues list')

    self.assertEqual(results, queues)

  def testList_Uri(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    queues = self._MakeQueues(n=3)
    self.queues_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesListRequest(
            parent=self.location_name),
        response=self.messages.ListQueuesResponse(queues=queues))

    self.Run('tasks queues list --uri')

    self.AssertOutputEquals("""\
        https://cloudtasks.googleapis.com/v2beta2/{0}/queues/q0
        https://cloudtasks.googleapis.com/v2beta2/{0}/queues/q1
        https://cloudtasks.googleapis.com/v2beta2/{0}/queues/q2
        """.format(self.location_name), normalize_space=True)

  def testList_Location(self):
    properties.VALUES.core.user_output_enabled.Set(False)

    location_name = 'projects/{}/locations/us-central2'.format(
        self.Project())

    queues = self._MakeQueues()
    self.queues_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesListRequest(
            parent=location_name),
        response=self.messages.ListQueuesResponse(queues=queues))

    results = self.Run('tasks queues list --location=us-central2')

    self.assertEqual(results, queues)

  def testList_CheckFormat(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    queues = self._MakeQueues(n=3)
    self.queues_service.List.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesListRequest(
            parent=self.location_name),
        response=self.messages.ListQueuesResponse(queues=queues))

    self.Run('tasks queues list')

    self.AssertOutputEquals("""\
        QUEUE_NAME  TYPE        STATE    MAX_NUM_OF_TASKS  MAX_RATE (/sec)  MAX_ATTEMPTS
        q0          app-engine  RUNNING  10                500.0            unlimited
        q1          app-engine  RUNNING  10                500.0            unlimited
        q2          app-engine  RUNNING  10                500.0            unlimited
        """, normalize_space=True)

if __name__ == '__main__':
  test_case.main()
