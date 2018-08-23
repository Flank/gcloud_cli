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
"""Tests for `gcloud scheduler jobs create-pubsub-job`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.scheduler import base


@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,))
class JobsCreateTest(base.SchedulerTestBase):

  _PUBSUB_MESSAGE_URL = 'type.googleapis.com/google.pubsub.v1.PubsubMessage'

  def _MakeJob(self):
    pubsub_message_type = self.messages.PubsubTarget.PubsubMessageValue
    name = 'projects/{}/locations/us-central1/jobs/my-job'.format(
        self.Project())
    return self.messages.Job(
        name=name,
        schedule=self.messages.Schedule(
            schedule='every tuesday',
            timeZone='Etc/UTC'),
        pubsubTarget=self.messages.PubsubTarget(
            topicName='projects/other-project/topics/my-topic',
            pubsubMessage=pubsub_message_type(
                additionalProperties=[
                    pubsub_message_type.AdditionalProperty(
                        key='@type',
                        value=extra_types.JsonValue(
                            string_value=self._PUBSUB_MESSAGE_URL)),
                    pubsub_message_type.AdditionalProperty(
                        key='data',
                        value=extra_types.JsonValue(string_value='YXNkZg==')),
                ]
            )
        )
    )

  def _ExpectCreate(self, location_name, job):
    self.client.projects_locations_jobs.Create.Expect(
        self.messages.CloudschedulerProjectsLocationsJobsCreateRequest(
            parent=location_name,
            job=job),
        job)

  def testCreate_MissingArguments(self, track):
    self.track = track

    with self.AssertRaisesArgumentErrorMatches('must be specified'):
      self.Run('scheduler jobs create-pubsub-job')

  def testCreate(self, track):
    self.track = track
    job = self._MakeJob()
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run('scheduler jobs create-pubsub-job my-job '
             '    --topic projects/other-project/topics/my-topic '
             '    --schedule "every tuesday" '
             '    --message-body asdf')

  def testCreateFromFile(self, track):
    self.track = track
    payload_file = self.Touch(self.temp_path, 'payload_file', 'asdf')
    job = self._MakeJob()
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run('scheduler jobs create-pubsub-job my-job '
             '    --topic projects/other-project/topics/my-topic '
             '    --schedule "every tuesday" '
             '    --message-body-from-file {}'.format(payload_file))

  def testCreate_TopicUrl(self, track):
    self.track = track
    job = self._MakeJob()
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    topic_url = ('https://pubsub.googleapis.com/v1/projects/other-project'
                 '/topics/my-topic')
    self.Run(('scheduler jobs create-pubsub-job my-job '
              '    --topic {} '
              '    --schedule "every tuesday" '
              '    --message-body asdf').format(topic_url))

  def testCreate_TopicInSameProject(self, track):
    self.track = track
    job = self._MakeJob()
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    job.pubsubTarget.topicName = 'projects/{}/topics/my-topic'.format(
        self.Project())
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run('scheduler jobs create-pubsub-job my-job '
             '    --topic my-topic '
             '    --schedule "every tuesday" '
             '    --message-body asdf')

  def testCreate_AllArguments(self, track):
    self.track = track
    job = self._MakeJob()
    job.description = 'my super cool job'
    job.schedule.timeZone = 'America/New_York'
    job.pubsubTarget.pubsubMessage.additionalProperties.append(
        job.pubsubTarget.pubsubMessage.AdditionalProperty(
            key='attributes',
            value=extra_types.JsonValue(
                object_value=extra_types.JsonObject(
                    properties=[
                        extra_types.JsonObject.Property(
                            key='key1',
                            value=extra_types.JsonValue(string_value='value1')),
                        extra_types.JsonObject.Property(
                            key='key2',
                            value=extra_types.JsonValue(string_value='value2'))
                    ]
                )
            )
        )
    )
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run('scheduler jobs create-pubsub-job my-job '
             '    --description "my super cool job" '
             '    --topic projects/other-project/topics/my-topic '
             '    --schedule "every tuesday" '
             '    --message-body asdf '
             '    --attributes key1=value1,key2=value2 '
             '    --time-zone America/New_York')


if __name__ == '__main__':
  test_case.main()
