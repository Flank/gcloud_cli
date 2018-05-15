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
"""Tests for `gcloud scheduler jobs list`."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.scheduler import base


@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,))
class JobsListTest(base.SchedulerTestBase):

  def _MakeJobs(self, n=10):
    jobs = []
    for i in range(n):
      app_engine_http_target = None
      pubsub_target = None
      if i % 2 == 0:
        app_engine_http_target = self.messages.AppEngineHttpTarget(
            relativeUrl='/')
      else:
        pubsub_target = self.messages.PubsubTarget(
            topicName='projects/other-project/topic/my-topic')
      job_name = ('projects/{}/'
                  'locations/us-central1/'
                  'jobs/j{}').format(self.Project(), i)
      job = self.messages.Job(
          name=job_name,
          schedule=self.messages.Schedule(schedule='every tuesday',
                                          timeZone='utc'),
          pubsubTarget=pubsub_target,
          appEngineHttpTarget=app_engine_http_target,
          state=self.messages.Job.StateValueValuesEnum.ENABLED,
          userUpdateTime='2017-01-01T00:00:00Z'
      )
      jobs.append(job)
    return jobs

  def _ExpectList(self, jobs, page_size=None, page_token=None,
                  next_page_token=None):
    location_name = ('projects/{}/'
                     'locations/us-central1').format(self.Project())
    self.client.projects_locations_jobs.List.Expect(
        self.messages.CloudschedulerProjectsLocationsJobsListRequest(
            parent=location_name,
            pageSize=page_size,
            pageToken=page_token
        ),
        self.messages.ListJobsResponse(jobs=jobs,
                                       nextPageToken=next_page_token))

  def testList(self, track):
    self.track = track
    jobs = self._MakeJobs()
    self._ExpectGetApp()
    self._ExpectList(jobs)

    results = self.Run('scheduler jobs list')

    self.assertEqual(results, jobs)

  def testList_CheckFormat(self, track):
    self.track = track
    jobs = self._MakeJobs(n=3)
    self._ExpectGetApp()
    self._ExpectList(jobs)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('scheduler jobs list')

    self.AssertOutputEquals("""\
        ID  LOCATION     SCHEDULE (TZ)        TARGET_TYPE  STATE
        j0  us-central1  every tuesday (utc)  App Engine   ENABLED
        j1  us-central1  every tuesday (utc)  Pub/Sub      ENABLED
        j2  us-central1  every tuesday (utc)  App Engine   ENABLED
        """, normalize_space=True)

  def testList_Uri(self, track):
    self.track = track
    jobs = self._MakeJobs(n=3)
    self._ExpectGetApp()
    self._ExpectList(jobs)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('scheduler jobs list --uri')

    self.AssertOutputEquals(
        """\
        https://cloudscheduler.googleapis.com/v1alpha1/projects/{project}/locations/us-central1/jobs/j0
        https://cloudscheduler.googleapis.com/v1alpha1/projects/{project}/locations/us-central1/jobs/j1
        https://cloudscheduler.googleapis.com/v1alpha1/projects/{project}/locations/us-central1/jobs/j2
        """.format(project=self.Project()), normalize_space=True)

  def testList_MultiplePages(self, track):
    self.track = track
    jobs = self._MakeJobs(n=10)
    self._ExpectGetApp()
    self._ExpectList(jobs[:5], page_size=5, next_page_token='token')
    self._ExpectList(jobs[5:], page_size=5, page_token='token')

    results = self.Run('scheduler jobs list --page-size 5')

    self.assertEqual(results, jobs)


if __name__ == '__main__':
  test_case.main()
