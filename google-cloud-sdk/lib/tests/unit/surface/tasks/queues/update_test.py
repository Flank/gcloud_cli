# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud tasks queues` update commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.tasks import test_base

import six


class UpdatePullQueueTest(test_base.CloudTasksAlphaTestBase):

  def SetUp(self):
    self.queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue')
    self.queue_name = self.queue_ref.RelativeName()

    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())

    properties.VALUES.core.user_output_enabled.Set(False)

  def testUpdate_NoOptions(self):
    with self.assertRaises(parsers.NoFieldsSpecifiedError):
      self.Run('tasks queues update-pull-queue my-queue')

  def testUpdate_AllOptions(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=self.messages.RetryConfig(
            maxAttempts=10, maxRetryDuration='5s'))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration')),
        response=expected_queue)

    actual_queue = self.Run('tasks queues update-pull-queue my-queue '
                            '--max-attempts=10 --max-retry-duration=5s')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_AllOptions_Location(self):
    queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central2',
        projectsId=self.Project(), queuesId='my-queue')
    queue_name = queue_ref.RelativeName()
    expected_queue = self.messages.Queue(
        name=queue_name, retryConfig=self.messages.RetryConfig(
            maxAttempts=10, maxRetryDuration='5s'))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration')),
        response=expected_queue)

    actual_queue = self.Run('tasks queues update-pull-queue my-queue '
                            '--max-attempts=10 --max-retry-duration=5s '
                            '--location=us-central2')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_AllOptions_MaxAttemptsUnlimited(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=self.messages.RetryConfig(
            unlimitedAttempts=True, maxRetryDuration='5s'))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration')),
        response=expected_queue)

    actual_queue = self.Run('tasks queues update-pull-queue my-queue '
                            '--max-attempts=unlimited --max-retry-duration=5s')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_ClearAll(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=self.messages.RetryConfig())
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration')),
        response=expected_queue)

    actual_queue = self.Run('tasks queues update-pull-queue my-queue '
                            '--clear-max-attempts --clear-max-retry-duration')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_IncludeAppEngineArgs(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('tasks queues update-pull-queue my-queue --max-attempts=10 '
               '--max-retry-duration=5s --max-doublings=4 --min-backoff=1s '
               '--max-backoff=10s --max-tasks-dispatched-per-second=100 '
               '--max-concurrent-tasks=10 --routing-override=service:abc')

  def testUpdate_NonExistentQueue(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=self.messages.RetryConfig(
            unlimitedAttempts=True, maxRetryDuration='5s'))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration')),
        exception=http_error.MakeDetailedHttpError(
            code=six.moves.http_client.NOT_FOUND,
            message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run('tasks queues update-pull-queue my-queue '
               '--max-attempts=unlimited --max-retry-duration=5s')

    self.AssertErrNotContains('Updated queue [my-queue].')
    self.AssertErrContains('Requested entity was not found.')

  def testUpdate_WrongQueueType(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=self.messages.RetryConfig(
            unlimitedAttempts=True, maxRetryDuration='5s'))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration')),
        exception=http_error.MakeDetailedHttpError(
            code=six.moves.http_client.BAD_REQUEST,
            message='Queue.target_type is immutable.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run('tasks queues update-pull-queue my-queue '
               '--max-attempts=unlimited --max-retry-duration=5s')

    self.AssertErrNotContains('Updated queue [my-queue].')


class UpdateAppEngineQueueTest(test_base.CloudTasksTestBase):

  def PreSetUp(self):
    self.command = 'tasks queues update'

  def SetUp(self):
    self.queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue')
    self.queue_name = self.queue_ref.RelativeName()

    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())

    properties.VALUES.core.user_output_enabled.Set(False)

  def testUpdate_NoOptions(self):
    with self.assertRaises(parsers.NoFieldsSpecifiedError):
      self.Run(self.command + ' my-queue')

  def testUpdate_AllOptions(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineRoutingOverride=self.messages.AppEngineRouting(service='abc'),
        retryConfig=self.messages.RetryConfig(maxAttempts=10,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=100, maxConcurrentDispatches=10),
        stackdriverLoggingConfig=self.messages.StackdriverLoggingConfig(
            samplingRatio=0.9))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff,'
                        'stackdriverLoggingConfig.samplingRatio')),
        response=expected_queue)

    actual_queue = self.Run(self.command + ' my-queue '
                            '--max-attempts=10 --max-retry-duration=5s '
                            '--max-doublings=4 --min-backoff=1s '
                            '--max-backoff=10s '
                            '--max-dispatches-per-second=100 '
                            '--max-concurrent-dispatches=10 '
                            '--routing-override=service:abc '
                            '--log-sampling-ratio=0.9')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_AllOptions_MaxAttemptsUnlimited(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineRoutingOverride=self.messages.AppEngineRouting(service='abc'),
        retryConfig=self.messages.RetryConfig(maxAttempts=-1,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=100, maxConcurrentDispatches=10),
        stackdriverLoggingConfig=self.messages.StackdriverLoggingConfig(
            samplingRatio=0.9))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff,'
                        'stackdriverLoggingConfig.samplingRatio')),
        response=expected_queue)

    actual_queue = self.Run(self.command + ' my-queue '
                            '--max-attempts=unlimited --max-retry-duration=5s '
                            '--max-doublings=4 --min-backoff=1s '
                            '--max-backoff=10s '
                            '--max-dispatches-per-second=100 '
                            '--max-concurrent-dispatches=10 '
                            '--routing-override=service:abc '
                            '--log-sampling-ratio=0.9')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_ClearAll(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineRoutingOverride=self.messages.AppEngineRouting(),
        retryConfig=self.messages.RetryConfig(),
        rateLimits=self.messages.RateLimits(),
        stackdriverLoggingConfig=self.messages.StackdriverLoggingConfig())
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff,'
                        'stackdriverLoggingConfig.samplingRatio')),
        response=expected_queue)

    actual_queue = self.Run(self.command + ' my-queue '
                            '--clear-max-attempts --clear-max-retry-duration '
                            '--clear-max-doublings --clear-min-backoff '
                            '--clear-max-backoff '
                            '--clear-max-dispatches-per-second '
                            '--clear-max-concurrent-dispatches '
                            '--clear-routing-override '
                            '--clear-log-sampling-ratio')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_NonExistentQueue(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineRoutingOverride=self.messages.AppEngineRouting(service='abc'),
        retryConfig=self.messages.RetryConfig(maxAttempts=-1,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=100, maxConcurrentDispatches=10))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff')),
        exception=http_error.MakeDetailedHttpError(
            code=six.moves.http_client.NOT_FOUND,
            message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.command + ' my-queue '
               '--max-attempts=unlimited --max-retry-duration=5s '
               '--max-doublings=4 --min-backoff=1s --max-backoff=10s '
               '--max-dispatches-per-second=100 '
               '--max-concurrent-dispatches=10 --routing-override=service:abc')

    self.AssertErrNotContains('Updated queue [my-queue].')
    self.AssertErrContains('Requested entity was not found.')

  def testUpdate_WrongQueueType(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineRoutingOverride=self.messages.AppEngineRouting(service='abc'),
        retryConfig=self.messages.RetryConfig(maxAttempts=-1,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=100, maxConcurrentDispatches=10))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff')),
        exception=http_error.MakeDetailedHttpError(
            code=six.moves.http_client.BAD_REQUEST,
            message='Queue.target_type is immutable.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.command + ' my-queue '
               '--max-attempts=unlimited --max-retry-duration=5s '
               '--max-doublings=4 --min-backoff=1s --max-backoff=10s '
               '--max-dispatches-per-second=100 '
               '--max-concurrent-dispatches=10 --routing-override=service:abc')

    self.AssertErrNotContains('Updated queue [my-queue].')


class UpdateAppEngineQueueTestBeta(UpdateAppEngineQueueTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.command = 'tasks queues update'

  def testUpdate_AllOptions(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineHttpQueue=self.messages.AppEngineHttpQueue(
            appEngineRoutingOverride=self.messages.AppEngineRouting(
                service='abc')),
        retryConfig=self.messages.RetryConfig(maxAttempts=10,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=100, maxConcurrentDispatches=10),
        stackdriverLoggingConfig=self.messages.StackdriverLoggingConfig(
            samplingRatio=0.9))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineHttpQueue.appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff,'
                        'stackdriverLoggingConfig.samplingRatio')),
        response=expected_queue)

    actual_queue = self.Run(self.command + ' my-queue '
                            '--max-attempts=10 --max-retry-duration=5s '
                            '--max-doublings=4 --min-backoff=1s '
                            '--max-backoff=10s '
                            '--max-dispatches-per-second=100 '
                            '--max-concurrent-dispatches=10 '
                            '--routing-override=service:abc '
                            '--log-sampling-ratio=0.9')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_AllOptions_MaxAttemptsUnlimited(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineHttpQueue=self.messages.AppEngineHttpQueue(
            appEngineRoutingOverride=self.messages.AppEngineRouting(
                service='abc')),
        retryConfig=self.messages.RetryConfig(maxAttempts=-1,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=100, maxConcurrentDispatches=10))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineHttpQueue.appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff')),
        response=expected_queue)

    actual_queue = self.Run(self.command + ' my-queue '
                            '--max-attempts=unlimited --max-retry-duration=5s '
                            '--max-doublings=4 --min-backoff=1s '
                            '--max-backoff=10s '
                            '--max-dispatches-per-second=100 '
                            '--max-concurrent-dispatches=10 '
                            '--routing-override=service:abc')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_ClearAll(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineHttpQueue=self.messages.AppEngineHttpQueue(),
        retryConfig=self.messages.RetryConfig(),
        rateLimits=self.messages.RateLimits(),
        stackdriverLoggingConfig=self.messages.StackdriverLoggingConfig())
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineHttpQueue.appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff,'
                        'stackdriverLoggingConfig.samplingRatio')),
        response=expected_queue)

    actual_queue = self.Run(self.command + ' my-queue '
                            '--clear-max-attempts --clear-max-retry-duration '
                            '--clear-max-doublings --clear-min-backoff '
                            '--clear-max-backoff '
                            '--clear-max-dispatches-per-second '
                            '--clear-max-concurrent-dispatches '
                            '--clear-routing-override '
                            '--clear-log-sampling-ratio')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_NonExistentQueue(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineHttpQueue=self.messages.AppEngineHttpQueue(
            appEngineRoutingOverride=self.messages.AppEngineRouting(
                service='abc')),
        retryConfig=self.messages.RetryConfig(maxAttempts=-1,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=100, maxConcurrentDispatches=10))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineHttpQueue.appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff')),
        exception=http_error.MakeDetailedHttpError(
            code=six.moves.http_client.NOT_FOUND,
            message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.command + ' my-queue '
               '--max-attempts=unlimited --max-retry-duration=5s '
               '--max-doublings=4 --min-backoff=1s --max-backoff=10s '
               '--max-dispatches-per-second=100 '
               '--max-concurrent-dispatches=10 --routing-override=service:abc')

    self.AssertErrNotContains('Updated queue [my-queue].')
    self.AssertErrContains('Requested entity was not found.')

  def testUpdate_WrongQueueType(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineHttpQueue=self.messages.AppEngineHttpQueue(
            appEngineRoutingOverride=self.messages.AppEngineRouting(
                service='abc')),
        retryConfig=self.messages.RetryConfig(maxAttempts=-1,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxDispatchesPerSecond=100, maxConcurrentDispatches=10))
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('appEngineHttpQueue.appEngineRoutingOverride,'
                        'rateLimits.maxConcurrentDispatches,'
                        'rateLimits.maxDispatchesPerSecond,'
                        'retryConfig.maxAttempts,'
                        'retryConfig.maxBackoff,'
                        'retryConfig.maxDoublings,'
                        'retryConfig.maxRetryDuration,'
                        'retryConfig.minBackoff')),
        exception=http_error.MakeDetailedHttpError(
            code=six.moves.http_client.BAD_REQUEST,
            message='Queue.target_type is immutable.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.command + ' my-queue '
               '--max-attempts=unlimited --max-retry-duration=5s '
               '--max-doublings=4 --min-backoff=1s --max-backoff=10s '
               '--max-dispatches-per-second=100 '
               '--max-concurrent-dispatches=10 --routing-override=service:abc')

    self.AssertErrNotContains('Updated queue [my-queue].')


class UpdateCloudTasksPullQueueTestBeta(test_base.CloudTasksTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.command = 'tasks queues update my-queue --type=pull '

  def SetUp(self):
    self.queue_type = self.messages.Queue.TypeValueValuesEnum.PULL
    self.queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue')
    self.queue_name = self.queue_ref.RelativeName()

    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())

    properties.VALUES.core.user_output_enabled.Set(False)

  def testUpdate_NoOptions(self):
    with self.assertRaises(parsers.NoFieldsSpecifiedError):
      self.Run(self.command)

  def testUpdate_AllOptions(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        retryConfig=self.messages.RetryConfig(maxAttempts=10,
                                              maxRetryDuration='5s'),
        type=self.queue_type)
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration,'
                        'type')),
        response=expected_queue)

    actual_queue = self.Run(self.command +
                            '--max-attempts=10 --max-retry-duration=5s')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_ClearAll(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        retryConfig=self.messages.RetryConfig(),
        type=self.queue_type)
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration,'
                        'type')),
        response=expected_queue)

    actual_queue = self.Run(self.command +
                            '--clear-max-attempts --clear-max-retry-duration')

    self.assertEqual(actual_queue, expected_queue)

  def testUpdate_NonExistentQueue(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        retryConfig=self.messages.RetryConfig(maxAttempts=-1,
                                              maxRetryDuration='5s'),
        type=self.queue_type)
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration,'
                        'type')),
        exception=http_error.MakeDetailedHttpError(
            code=six.moves.http_client.NOT_FOUND,
            message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.command +
               '--max-attempts=unlimited --max-retry-duration=5s')

    self.AssertErrNotContains('Updated queue [my-queue].')
    self.AssertErrContains('Requested entity was not found.')

  def testUpdate_WrongQueueType(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        retryConfig=self.messages.RetryConfig(maxAttempts=-1,
                                              maxRetryDuration='5s'),
        type=self.queue_type)
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue,
            updateMask=('retryConfig.maxAttempts,'
                        'retryConfig.maxRetryDuration,'
                        'type')),
        exception=http_error.MakeDetailedHttpError(
            code=six.moves.http_client.BAD_REQUEST,
            message='Queue.target_type is immutable.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(self.command +
               '--max-attempts=unlimited --max-retry-duration=5s ')

    self.AssertErrNotContains('Updated queue [my-queue].')


class UpdateAppEngineQueueTestBetaDeprecated(UpdateAppEngineQueueTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.command = 'tasks queues update-app-engine-queue'


if __name__ == '__main__':
  test_case.main()
