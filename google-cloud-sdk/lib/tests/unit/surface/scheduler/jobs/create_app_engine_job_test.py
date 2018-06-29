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
"""Tests for `gcloud scheduler jobs create-app-engine-job`."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.scheduler import base


@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,))
class JobsCreateTest(base.SchedulerTestBase):

  def _MakeJob(self):
    method = self.messages.AppEngineHttpTarget.HttpMethodValueValuesEnum.POST
    name = 'projects/{}/locations/us-central1/jobs/my-job'.format(
        self.Project())
    return self.messages.Job(
        name=name,
        schedule=self.messages.Schedule(
            schedule='every tuesday',
            timeZone='Etc/UTC'),
        appEngineHttpTarget=self.messages.AppEngineHttpTarget(
            httpMethod=method,
            relativeUrl='/',
            body=b'my-payload',
        ),
        retryConfig=self.messages.RetryConfig(
            maxBackoffDuration='3600s',
            minBackoffDuration='5s',
            maxDoublings=16,
            retryCount=0
        )
    )

  def _ExpectCreate(self, location_name, job):
    self.client.projects_locations_jobs.Create.Expect(
        self.messages.CloudschedulerProjectsLocationsJobsCreateRequest(
            parent=location_name,
            job=job),
        job)

  def testCreate_MissingSchedule(self, track):
    self.track = track

    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB --schedule: Must be specified.'):
      self.Run('scheduler jobs create-app-engine-job')

  def testCreate(self, track):
    self.track = track
    job = self._MakeJob()
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run('scheduler jobs create-app-engine-job my-job '
             '    --schedule "every tuesday" '
             '    --message-body my-payload')

  def testCreate_PayloadMutuallyExclusive(self, track):
    self.track = track

    payload_file = self.Touch(self.temp_path, 'payload_file', 'my-payload-2')

    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(('scheduler jobs create-app-engine-job my-job '
                '    --schedule "every tuesday" '
                '    --message-body my-payload '
                '    --message-body-from-file {}').format(payload_file))
    self.AssertErrContains(
        'At most one of --message-body | --message-body-from-file '
        'may be specified')

  def testCreate_AllArguments(self, track):
    self.track = track
    payload_file = self.Touch(self.temp_path, 'payload_file', 'my-payload-2')
    job = self._MakeJob()
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    job.description = 'my super cool job'
    job.retryConfig.retryCount = 5
    job.retryConfig.maxRetryDuration = '7200s'
    job.retryConfig.minBackoffDuration = '0.2s'
    job.retryConfig.maxBackoffDuration = '10s'
    job.retryConfig.maxDoublings = 2
    job.appEngineHttpTarget.relativeUrl = '/foo/bar'
    job.appEngineHttpTarget.body = b'my-payload-2'
    headers_value = self.messages.AppEngineHttpTarget.HeadersValue(
        additionalProperties=[
            self.messages.AppEngineHttpTarget.HeadersValue.AdditionalProperty(
                key='Header1',
                value='Value1,comma'
            ),
            self.messages.AppEngineHttpTarget.HeadersValue.AdditionalProperty(
                key='Header2',
                value='Value2')])
    job.appEngineHttpTarget.headers = headers_value
    job.appEngineHttpTarget.httpMethod = job.appEngineHttpTarget.httpMethod.GET
    job.appEngineHttpTarget.appEngineRouting = self.messages.AppEngineRouting(
        service='service',
        version='version'
    )
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run(('scheduler jobs create-app-engine-job my-job '
              '    --schedule "every tuesday" '
              '    --description "my super cool job" '
              '    --max-attempts 5 '
              '    --max-retry-duration 2h '
              '    --min-backoff 0.2s '
              '    --max-backoff 10s '
              '    --relative-url /foo/bar '
              '    --max-doublings 2 '
              '    --http-method gEt '
              '    --header "Header1: Value1,comma" '
              '    --header "Header2:  Value2" '
              '    --message-body-from-file {} '
              '    --version version '
              '    --service service ').format(payload_file))


if __name__ == '__main__':
  test_case.main()
