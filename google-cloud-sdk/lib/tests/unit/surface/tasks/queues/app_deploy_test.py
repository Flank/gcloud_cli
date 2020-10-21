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
"""Tests for `gcloud app deploy queue.yaml --use-ct-apis` command.

Underneath we have migrated all functionality to Cloud Tasks APIs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.tasks import test_base


class TestAppDeployTestBeta(test_base.CloudTasksTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.location = 'projects/{}/locations/us-central1'.format(
        self.Project())
    self.yaml_file_path = self.Resource(
        'tests', 'unit', 'surface', 'tasks', 'queues', 'test_data',
        'queue.yaml')
    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())
    properties.VALUES.core.user_output_enabled.Set(False)
    self._GetQueues()

  def _GetFullQueuePath(self, queue_name):
    return '{}/queues/{}'.format(self.location, queue_name)

  def _GetQueues(self):
    # Queues to simulate queue states in our database
    defaults = constants.PULL_QUEUES_APP_DEPLOY_DEFAULT_VALUES
    self.queues = (
        self.messages.Queue(
            name=self._GetFullQueuePath('RunningPushQueue'),
            state=self.messages.Queue.StateValueValuesEnum.RUNNING,
            appEngineHttpQueue=self.messages.AppEngineHttpQueue(
                appEngineRoutingOverride=self.messages.AppEngineRouting(
                    host='version.omega.{}.uk.r.appspot.com'.format(
                        self.Project()),
                    version='version',
                    service='omega',
                )
            ),
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=500,
                maxDispatchesPerSecond=10,
                maxBurstSize=20),
            retryConfig=self.messages.RetryConfig(
                maxAttempts=13,
                maxRetryDuration='3600s',
                maxDoublings=4,
                minBackoff='0.3s',
                maxBackoff='400s'),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('RunningPullQueue'),
            state=self.messages.Queue.StateValueValuesEnum.RUNNING,
            retryConfig=self.messages.RetryConfig(maxAttempts=12),
            type=self.messages.Queue.TypeValueValuesEnum.PULL
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('DisabledPushQueue'),
            state=self.messages.Queue.StateValueValuesEnum.DISABLED,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=10,
                maxDispatchesPerSecond=0,
                maxBurstSize=10),
            retryConfig=self.messages.RetryConfig(
                maxAttempts=10,
                maxRetryDuration='10s',
                maxDoublings=10,
                minBackoff='10s',
                maxBackoff='10s'),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('PausedPushQueue'),
            state=self.messages.Queue.StateValueValuesEnum.PAUSED,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=40,
                maxDispatchesPerSecond=50,
                maxBurstSize=5),
            retryConfig=self.messages.RetryConfig(
                maxAttempts=15,
                maxRetryDuration='150s',
                maxDoublings=10,
                minBackoff='200s',
                maxBackoff='200s'),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('ToBePausedAndUpdatedPushQueue'),
            state=self.messages.Queue.StateValueValuesEnum.RUNNING,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=10,
                maxDispatchesPerSecond=10,
                maxBurstSize=35),
            retryConfig=self.messages.RetryConfig(
                maxAttempts=20,
                maxRetryDuration='86402s',
                maxDoublings=10,
                minBackoff='10s',
                maxBackoff='40s'),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('QueueNotInYamlAndPaused'),
            state=self.messages.Queue.StateValueValuesEnum.PAUSED,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=10,
                maxDispatchesPerSecond=10),
            retryConfig=self.messages.RetryConfig(
                maxAttempts=20,
                maxRetryDuration='86402s',
                maxDoublings=10,
                minBackoff='10s',
                maxBackoff='40s'),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('QueueNotInYamlAndNeedsToBePaused'),
            state=self.messages.Queue.StateValueValuesEnum.RUNNING,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=10,
                maxDispatchesPerSecond=10),
            retryConfig=self.messages.RetryConfig(
                maxAttempts=20,
                maxRetryDuration='86402s',
                maxDoublings=10,
                minBackoff='10s',
                maxBackoff='40s'),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('OnlyMinBackOffSpecifiedPushQueue'),
            state=self.messages.Queue.StateValueValuesEnum.RUNNING,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=10,
                maxDispatchesPerSecond=10,
                maxBurstSize=5),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('OnlyMaxBackOffSpecifiedPushQueue'),
            state=self.messages.Queue.StateValueValuesEnum.RUNNING,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=10,
                maxDispatchesPerSecond=1),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('OnlyMinBackOffSpecifiedPushQueueVar'),
            state=self.messages.Queue.StateValueValuesEnum.RUNNING,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=10,
                maxDispatchesPerSecond=3),
            retryConfig=self.messages.RetryConfig(
                maxBackoff=defaults['max_backoff']),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
        self.messages.Queue(
            name=self._GetFullQueuePath('OnlyMaxBackOffSpecifiedPushQueueVar'),
            state=self.messages.Queue.StateValueValuesEnum.RUNNING,
            rateLimits=self.messages.RateLimits(
                maxConcurrentDispatches=10,
                maxDispatchesPerSecond=1),
            retryConfig=self.messages.RetryConfig(
                minBackoff=defaults['min_backoff']),
            type=self.messages.Queue.TypeValueValuesEnum.PUSH
        ),
    )
    self.queues_dict = {os.path.basename(q.name): q for q in self.queues}

  def _MockCalls(self):
    # Before processing we need to fetch all existing queues data
    request = self.messages.CloudtasksProjectsLocationsQueuesListRequest(
        parent=self.location)
    request.pageSize = 100
    self.queues_service.List.Expect(
        request,
        response=self.messages.ListQueuesResponse(queues=self.queues))

    # We skipped the first two queues since they do not have any data or states
    # that needs to be changed. Disabled queue needs to be resumed and its rate
    # set appropriately.
    before_queue = self.queues_dict['DisabledPushQueue']
    self.queues_service.Resume.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesResumeRequest(
            name=before_queue.name),
        response=self.messages.Queue())
    after_queue = self.messages.Queue(
        name=before_queue.name,
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=10.0, maxConcurrentDispatches=10,
            maxBurstSize=10))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=before_queue.name,
            queue=after_queue,
            updateMask='rateLimits.maxDispatchesPerSecond'),
        response=after_queue)

    # Only resume this paused queue. All other attributes are unchanged.
    before_queue = self.queues_dict['PausedPushQueue']
    self.queues_service.Resume.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesResumeRequest(
            name=before_queue.name),
        response=self.messages.Queue())

    # Need to both Pause and Update the ToBePausedAndUpdatedPushQueue
    before_queue = self.queues_dict['ToBePausedAndUpdatedPushQueue']
    self.queues_service.Pause.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPauseRequest(
            name=before_queue.name),
        response=self.messages.Queue())
    after_queue = self.messages.Queue(
        name=before_queue.name,
        appEngineHttpQueue=self.messages.AppEngineHttpQueue(
            appEngineRoutingOverride=self.messages.AppEngineRouting(
                service='alpha')),
        retryConfig=self.messages.RetryConfig(
            maxAttempts=30, maxRetryDuration='86400s', maxDoublings=30,
            minBackoff='30.0s', maxBackoff='30.0s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=0, maxConcurrentDispatches=30,
            maxBurstSize=10))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=before_queue.name,
            queue=after_queue,
            updateMask=(
                'appEngineHttpQueue.appEngineRoutingOverride,'
                'rateLimits.maxBurstSize,'
                'rateLimits.maxConcurrentDispatches,'
                'retryConfig.maxAttempts,'
                'retryConfig.maxBackoff,'
                'retryConfig.maxDoublings,'
                'retryConfig.maxRetryDuration,'
                'retryConfig.minBackoff')),
        response=after_queue)

    # This is a brand new queue with minimum attributes defined, the rest are
    # set appropriately to default values. This queue also needs to be paused.
    defaults = constants.PUSH_QUEUES_APP_DEPLOY_DEFAULT_VALUES
    after_queue = self.messages.Queue(
        name=self._GetFullQueuePath('ToBePausedNewMinimumPushQueue'),
        retryConfig=self.messages.RetryConfig(
            maxAttempts=defaults['max_attempts'],
            maxRetryDuration=defaults['max_retry_duration'],
            maxDoublings=defaults['max_doublings'],
            minBackoff=defaults['min_backoff'],
            maxBackoff=defaults['max_backoff']),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=0,
            maxConcurrentDispatches=defaults['max_concurrent_dispatches'],
            maxBurstSize=defaults['max_burst_size'],))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=after_queue.name,
            queue=after_queue,
            updateMask=(
                'rateLimits.maxBurstSize,'
                'rateLimits.maxConcurrentDispatches,'
                'rateLimits.maxDispatchesPerSecond,'
                'retryConfig.maxAttempts,'
                'retryConfig.maxBackoff,'
                'retryConfig.maxDoublings,'
                'retryConfig.maxRetryDuration,'
                'retryConfig.minBackoff')),
        response=after_queue)
    self.queues_service.Pause.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPauseRequest(
            name=after_queue.name),
        response=self.messages.Queue())

    # The following interactions test behavior when only one of the backoff
    # timers is defined in a way that forces the other to be unable to use
    # their default values.
    defaults = constants.PUSH_QUEUES_APP_DEPLOY_DEFAULT_VALUES
    after_queue = self.messages.Queue(
        name=self._GetFullQueuePath('OnlyMinBackOffSpecifiedPushQueue'),
        retryConfig=self.messages.RetryConfig(
            maxAttempts=defaults['max_attempts'],
            maxRetryDuration=defaults['max_retry_duration'],
            maxDoublings=defaults['max_doublings'],
            minBackoff='3800.0s',
            maxBackoff='3800.0s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=2,
            maxConcurrentDispatches=defaults['max_concurrent_dispatches'],
            maxBurstSize=defaults['max_burst_size']))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=after_queue.name,
            queue=after_queue,
            updateMask=(
                'rateLimits.maxConcurrentDispatches,'
                'rateLimits.maxDispatchesPerSecond,'
                'retryConfig.maxAttempts,'
                'retryConfig.maxBackoff,'
                'retryConfig.maxDoublings,'
                'retryConfig.maxRetryDuration,'
                'retryConfig.minBackoff')),
        response=after_queue)
    after_queue = self.messages.Queue(
        name=self._GetFullQueuePath('OnlyMaxBackOffSpecifiedPushQueue'),
        retryConfig=self.messages.RetryConfig(
            maxAttempts=defaults['max_attempts'],
            maxRetryDuration=defaults['max_retry_duration'],
            maxDoublings=defaults['max_doublings'],
            minBackoff='0.05s',
            maxBackoff='0.05s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=3,
            maxConcurrentDispatches=defaults['max_concurrent_dispatches'],
            maxBurstSize=defaults['max_burst_size']))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=after_queue.name,
            queue=after_queue,
            updateMask=(
                'rateLimits.maxConcurrentDispatches,'
                'rateLimits.maxDispatchesPerSecond,'
                'retryConfig.maxAttempts,'
                'retryConfig.maxBackoff,'
                'retryConfig.maxDoublings,'
                'retryConfig.maxRetryDuration,'
                'retryConfig.minBackoff')),
        response=after_queue)

    # This tests some other variations on min & max backoff interactions.
    defaults = constants.PUSH_QUEUES_APP_DEPLOY_DEFAULT_VALUES
    after_queue = self.messages.Queue(
        name=self._GetFullQueuePath('OnlyMinBackOffSpecifiedPushQueueVar'),
        appEngineHttpQueue=self.messages.AppEngineHttpQueue(
            appEngineRoutingOverride=self.messages.AppEngineRouting(
                service='beta', version='version')),
        retryConfig=self.messages.RetryConfig(
            maxAttempts=None,
            maxRetryDuration=defaults['max_retry_duration'],
            maxDoublings=defaults['max_doublings'],
            minBackoff='3800.0s',
            maxBackoff='3800.0s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=1,
            maxConcurrentDispatches=defaults['max_concurrent_dispatches'],
            maxBurstSize=defaults['max_burst_size']))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=after_queue.name,
            queue=after_queue,
            updateMask=(
                'appEngineHttpQueue.appEngineRoutingOverride,'
                'rateLimits.maxConcurrentDispatches,'
                'rateLimits.maxDispatchesPerSecond,'
                'retryConfig.maxBackoff,'
                'retryConfig.minBackoff')),
        response=after_queue)
    after_queue = self.messages.Queue(
        name=self._GetFullQueuePath('OnlyMaxBackOffSpecifiedPushQueueVar'),
        retryConfig=self.messages.RetryConfig(
            maxAttempts=None,
            maxRetryDuration=defaults['max_retry_duration'],
            maxDoublings=defaults['max_doublings'],
            minBackoff='0.05s',
            maxBackoff='0.05s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=3,
            maxConcurrentDispatches=defaults['max_concurrent_dispatches'],
            maxBurstSize=defaults['max_burst_size']))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=after_queue.name,
            queue=after_queue,
            updateMask=(
                'rateLimits.maxConcurrentDispatches,'
                'rateLimits.maxDispatchesPerSecond,'
                'retryConfig.maxBackoff,'
                'retryConfig.minBackoff')),
        response=after_queue)

    # There are two queues defined above that are not defined in the YAML file.
    # These two queues should be paused (or disabled) if they are not already
    # in that state. Only one of these two queues qualifies for that.
    before_queue = self.queues_dict['QueueNotInYamlAndNeedsToBePaused']
    self.queues_service.Pause.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPauseRequest(
            name=before_queue.name),
        response=self.messages.Queue())

  def testCompleteDeployment(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self._MockCalls()
    response = self.Run(
        'app deploy {} --use-ct-apis'.format(self.yaml_file_path))
    self.assertEqual(response['configs'], ['queue'])


if __name__ == '__main__':
  test_case.main()

