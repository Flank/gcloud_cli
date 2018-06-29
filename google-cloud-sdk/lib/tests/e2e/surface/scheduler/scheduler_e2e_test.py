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
"""End-to-end tests for the `gcloud scheduler` commands."""
from __future__ import absolute_import
from __future__ import unicode_literals
import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


class JobsTest(e2e_base.WithServiceAuth):

  PUBSUB_MESSAGE_BODY = 'my-message-body'
  APP_ENGINE_JOB_FLAGS = """
      --relative-url /foo/bar
      --http-method GET
      --version version
      --service service
      --max-attempts 4
      --max-backoff 30m
      --max-doublings 8
      --max-retry-duration 10h
      --min-backoff 0.5s
      --schedule "1 of feb 00:00"
      --time-zone America/New_York
      """
  PUBSUB_JOB_FLAGS = """
      --message-body {}
      --schedule "1 of jan 00:00"
      --attributes key1=value1,key2=value2
      --time-zone America/New_York
      --topic my-topic
      """.format(PUBSUB_MESSAGE_BODY)

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.id_generator = e2e_utils.GetResourceNameGenerator('scheduler')
    self.retryer = retry.Retryer(max_wait_ms=60000)

  @contextlib.contextmanager
  def _CreateResource(self, create_command, delete_command):
    self.Run(create_command)
    try:
      yield
    finally:
      self.retryer.RetryOnException(self.Run, args=[delete_command])

  @contextlib.contextmanager
  def _CreateJob(self, create_command):
    job = self.Run(create_command)
    job_id = job.name.split('/')[-1]
    try:
      yield job_id
    finally:
      delete_command = 'scheduler jobs delete --quiet {}'.format(job_id)
      self.retryer.RetryOnException(self.Run, args=[delete_command])

  @contextlib.contextmanager
  def _CreatePubsubTopic(self):
    topic_id = next(self.id_generator)
    with self._CreateResource('pubsub topics create {}'.format(topic_id),
                              'pubsub topics delete {}'.format(topic_id)):
      yield topic_id

  @contextlib.contextmanager
  def _CreatePubsubSubscription(self, topic_id):
    subscription_id = next(self.id_generator)
    with self._CreateResource(
        'pubsub subscriptions create --topic {} {}'.format(topic_id,
                                                           subscription_id),
        'pubsub subscriptions delete {}'.format(subscription_id)):
      yield subscription_id

  @contextlib.contextmanager
  def _CreatePubsubJob(self, flags, job_id):
    create_command = 'scheduler jobs create-pubsub-job {} {}'.format(job_id,
                                                                     flags)
    with self._CreateJob(create_command) as job_id:
      yield job_id

  @contextlib.contextmanager
  def _CreateAppEngineJob(self, flags, job_id):
    create_command = 'scheduler jobs create-app-engine-job {} {}'.format(job_id,
                                                                         flags)
    with self._CreateJob(create_command) as job_id:
      yield job_id

  def _CheckForPubsubMessage(self, subscription_id, message):
    self.Run('pubsub subscriptions pull --auto-ack {}'.format(subscription_id))
    self.AssertOutputContains(message)

  def _AssertPubsubMessageExists(self, topic_id, message):
    with self._CreatePubsubSubscription(topic_id) as subscription_id:
      new_retryer = retry.Retryer(max_wait_ms=600000)
      new_retryer.RetryOnException(self._CheckForPubsubMessage,
                                   args=(subscription_id, message),
                                   sleep_ms=5000)
      self.ClearOutput()

  def _AssertJobExists(self, job_id, key_text=None):
    self.Run('scheduler jobs describe ' + job_id)
    self.AssertOutputContains(key_text)
    self.ClearOutput()

  def testPubSubJob(self):
    job_id = next(self.id_generator)
    with self._CreatePubsubTopic() as unused_topic_id, \
         self._CreatePubsubJob(self.PUBSUB_JOB_FLAGS, job_id) as pubsub_job:
      self.assertEquals(job_id, pubsub_job)
      self._AssertJobExists(pubsub_job, key_text='1 of jan')

      self.Run('scheduler jobs run ' + pubsub_job)
      # TODO:(b/68131380): call _AssertPubsubMessageExists. Right now it fails.
      self.Run('scheduler jobs list')
      self.AssertOutputContains(pubsub_job)
      self.AssertOutputContains('Pub/Sub')

  def testAppEngineJob(self):
    job_id = next(self.id_generator)
    with self._CreateAppEngineJob(
        self.APP_ENGINE_JOB_FLAGS, job_id) as app_engine_job:
      self.assertEquals(job_id, app_engine_job)
      self._AssertJobExists(app_engine_job, key_text='1 of feb')

      self.Run('scheduler jobs list')
      self.AssertOutputContains(app_engine_job)
      self.AssertOutputContains('App Engine')


if __name__ == '__main__':
  test_case.main()
