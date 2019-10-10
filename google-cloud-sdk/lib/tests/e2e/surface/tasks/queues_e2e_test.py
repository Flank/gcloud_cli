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
"""End-to-end tests for the `gcloud tasks` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


class QueuesTest(e2e_base.WithServiceAuth):

  def SetUp(self):
    self.retryer = retry.Retryer(max_wait_ms=60000)

  def TearDown(self):
    # There is delay between when a queue is created and when it can be deleted
    self.retryer.RetryOnException(
        self.Run, args=['alpha tasks queues delete {}'.format(self.queue_id)])
    self.AssertErrContains('Deleted queue [{}].'.format(self.queue_id))

  def testUsePullQueue(self):
    self.queue_id = next(e2e_utils.GetResourceNameGenerator('queue'))
    expected_queue = self.Run('alpha tasks queues create-pull-queue {}'.format(
        self.queue_id))
    actual_queue = self.retryer.RetryOnException(  # Creation can take 1 minute
        self.Run,
        args=['alpha tasks queues describe {}'.format(self.queue_id)])
    self.assertEqual(actual_queue, expected_queue)
    self.Run(
        'alpha tasks queues get-iam-policy {} --location us-central1'.format(
            self.queue_id))
    self.Run('alpha tasks queues pause {}'.format(self.queue_id))
    self.ClearOutput()
    self.Run('alpha tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('state: PAUSED')
    self.Run('alpha tasks queues resume {}'.format(self.queue_id))
    self.ClearOutput()
    self.Run('alpha tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('state: RUNNING')
    self.Run('alpha tasks queues purge {}'.format(self.queue_id))
    self.Run('alpha tasks queues update-pull-queue {} --max-attempts=6'.format(
        self.queue_id))
    self.ClearOutput()
    self.Run('alpha tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxAttempts: 6')
    self.Run(
        'alpha tasks queues update-pull-queue {} --clear-max-attempts'.format(
            self.queue_id))
    self.ClearOutput()
    self.Run('alpha tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxAttempts: 100')
    self.Run('alpha tasks queues update-pull-queue {} --max-retry-duration=66s'.
             format(self.queue_id))
    self.ClearOutput()
    self.Run('alpha tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxRetryDuration: 66s')
    self.Run(
        'alpha tasks queues update-pull-queue {} --clear-max-retry-duration'.
        format(self.queue_id))
    self.ClearOutput()
    self.Run('alpha tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputNotContains('maxRetryDuration')

  def testUseBetaAppengineQueue(self):
    self.queue_id = next(e2e_utils.GetResourceNameGenerator('queue'))
    expected_queue = self.Run(
        'beta tasks queues create-app-engine-queue {}'.format(self.queue_id))
    actual_queue = self.retryer.RetryOnException(  # Creation can take 1 minute
        self.Run,
        args=['beta tasks queues describe {}'.format(self.queue_id)])
    self.assertEqual(actual_queue, expected_queue)
    self.Run(
        'beta tasks queues get-iam-policy {} --location us-central1'.format(
            self.queue_id))
    self.Run('beta tasks queues pause {}'.format(self.queue_id))
    self.ClearOutput()
    self.Run('beta tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('state: PAUSED')
    self.Run('beta tasks queues resume {}'.format(self.queue_id))
    self.ClearOutput()
    self.Run('beta tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('state: RUNNING')
    self.Run('beta tasks queues purge {}'.format(self.queue_id))
    self.Run(
        'beta tasks queues update-app-engine-queue {} --max-attempts=6'.format(
            self.queue_id))
    self.ClearOutput()
    self.Run('beta tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxAttempts: 6')
    self.Run(
        'beta tasks queues update-app-engine-queue {} --clear-max-attempts'.
        format(self.queue_id))
    self.ClearOutput()
    self.Run('beta tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxAttempts: 100')
    self.Run(
        'beta tasks queues update-app-engine-queue {} --max-retry-duration=66s'.
        format(self.queue_id))
    self.ClearOutput()
    self.Run('beta tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxRetryDuration: 66s')
    self.Run(
        ('beta tasks queues update-app-engine-queue {}' +
         ' --clear-max-retry-duration').format(self.queue_id))
    self.ClearOutput()
    self.Run('beta tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputNotContains('maxRetryDuration')

  def testUseBetaQueueLogSamplingFlag(self):
    self.queue_id = next(e2e_utils.GetResourceNameGenerator('queue'))
    expected_queue = self.Run(
        'beta tasks queues create {}'.format(self.queue_id))
    actual_queue = self.retryer.RetryOnException(  # Creation can take 1 minute
        self.Run,
        args=['beta tasks queues describe {}'.format(self.queue_id)])
    self.assertEqual(actual_queue, expected_queue)
    self.Run(
        'beta tasks queues update {} --log-sampling-ratio=0.5'.format(
            self.queue_id))
    self.ClearOutput()
    self.Run('beta tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('samplingRatio: 0.5')
    self.Run(
        'beta tasks queues update {} --clear-log-sampling-ratio'.format(
            self.queue_id))
    self.ClearOutput()
    self.Run('beta tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputNotContains('samplingRatio')

  def testUsePushQueue(self):
    self.queue_id = next(e2e_utils.GetResourceNameGenerator('queue'))
    expected_queue = self.Run(
        'tasks queues create {}'.format(self.queue_id))
    actual_queue = self.retryer.RetryOnException(  # Creation can take 1 minute
        self.Run,
        args=['tasks queues describe {}'.format(self.queue_id)])
    self.assertEqual(actual_queue, expected_queue)
    self.Run(
        'tasks queues get-iam-policy {} --location us-central1'.format(
            self.queue_id))
    self.Run('tasks queues pause {}'.format(self.queue_id))
    self.ClearOutput()
    self.Run('tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('state: PAUSED')
    self.Run('tasks queues resume {}'.format(self.queue_id))
    self.ClearOutput()
    self.Run('tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('state: RUNNING')
    self.Run('tasks queues purge {}'.format(self.queue_id))
    self.Run(
        'tasks queues update {} --max-attempts=6'.format(
            self.queue_id))
    self.ClearOutput()
    self.Run('tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxAttempts: 6')
    self.Run(
        'tasks queues update {} --clear-max-attempts'.
        format(self.queue_id))
    self.ClearOutput()
    self.Run('tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxAttempts: 100')
    self.Run(
        'tasks queues update {} --max-retry-duration=66s'.
        format(self.queue_id))
    self.ClearOutput()
    self.Run('tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputContains('maxRetryDuration: 66s')
    self.Run(
        ('tasks queues update {}' +
         ' --clear-max-retry-duration').format(self.queue_id))
    self.ClearOutput()
    self.Run('tasks queues describe {}'.format(self.queue_id))
    self.AssertOutputNotContains('maxRetryDuration')

if __name__ == '__main__':
  test_case.main()
