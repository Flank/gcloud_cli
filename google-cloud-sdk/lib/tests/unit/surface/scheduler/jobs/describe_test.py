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
"""Tests for `gcloud scheduler jobs describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.scheduler import base


@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,))
class JobsDescribeTest(base.SchedulerTestBase):

  def _MakeJob(self):
    pubsub_target = self.messages.PubsubTarget(
        pubsubMessage=self.messages.PubsubTarget.PubsubMessageValue(),
        topicName='projects/other-project/topic/my-topic')
    job_name = ('projects/{}/'
                'locations/us-central1/'
                'jobs/my-job').format(self.Project())
    return self.messages.Job(
        name=job_name,
        schedule=self.messages.Schedule(schedule='every tuesday',
                                        timeZone='utc'),
        pubsubTarget=pubsub_target,
        state=self.messages.Job.StateValueValuesEnum.ENABLED,
        userUpdateTime='2017-01-01T00:00:00Z'
    )

  def _ExpectDescribe(self, job):
    self.client.projects_locations_jobs.Get.Expect(
        self.messages.CloudschedulerProjectsLocationsJobsGetRequest(
            name=job.name),
        job)

  def testDescribe(self, track):
    self.track = track
    job = self._MakeJob()
    self._ExpectDescribe(job)
    self._ExpectGetApp()

    self.Run('scheduler jobs describe my-job')

  def testDescribe_Uri(self, track):
    self.track = track
    job = self._MakeJob()
    self._ExpectDescribe(job)
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')

    url = ('http://cloudscheduler.googleapis.com/v1alpha1/projects/{}'
           '/locations/us-central1/jobs/my-job').format(self.Project())
    self.Run('scheduler jobs describe ' + url)

  def testDescribe_RelativeName(self, track):
    self.track = track
    job = self._MakeJob()
    self._ExpectDescribe(job)
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')

    relative_name = ('projects/{}/locations'
                     '/us-central1/jobs/my-job').format(self.Project())
    self.Run('scheduler jobs describe ' + relative_name)


if __name__ == '__main__':
  test_case.main()
