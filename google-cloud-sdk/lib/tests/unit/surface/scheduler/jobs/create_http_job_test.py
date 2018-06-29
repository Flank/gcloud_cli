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
"""Tests for `gcloud scheduler jobs create-http-job`."""

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
    method = self.messages.HttpTarget.HttpMethodValueValuesEnum.POST
    name = 'projects/{}/locations/us-central1/jobs/my-job'.format(
        self.Project())
    return self.messages.Job(
        name=name,
        schedule=self.messages.Schedule(
            schedule='every tuesday',
            timeZone='Etc/UTC'),
        httpTarget=self.messages.HttpTarget(
            httpMethod=method,
            url='http://www.example.com/endpoint',
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

  def testCreate_MissingRequired(self, track):
    self.track = track

    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB --schedule --url: Must be specified.'):
      self.Run('scheduler jobs create-http-job')

  def testCreate(self, track):
    self.track = track
    job = self._MakeJob()
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run('scheduler jobs create-http-job my-job '
             '    --schedule "every tuesday" '
             '    --url http://www.example.com/endpoint'
             '    --message-body my-payload')

  def testCreate_OtherValidUrl(self, track):
    self.track = track
    job = self._MakeJob()
    job.httpTarget.url = 'https://www.example.com:8000/'
    location_name = 'projects/{}/locations/us-central1'.format(self.Project())
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run('scheduler jobs create-http-job my-job '
             '    --schedule "every tuesday" '
             '    --url https://www.example.com:8000/'
             '    --message-body my-payload')

  def testCreate_InalidUrls(self, track):
    self.track = track

    for bad_url in ('/', 'ftp://foo.com/bar', 'baz'):
      with self.AssertRaisesArgumentErrorMatches(
          'Must be a valid HTTP or HTTPS URL'):
        self.Run(('scheduler jobs create-http-job my-job '
                  '    --schedule "every tuesday" '
                  '    --url {}'
                  '    --message-body my-payload').format(bad_url))

  def testCreate_PayloadMutuallyExclusive(self, track):
    self.track = track

    payload_file = self.Touch(self.temp_path, 'payload_file', 'my-payload-2')

    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(('scheduler jobs create-http-job my-job '
                '    --schedule "every tuesday" '
                '    --url http://www.example.com/endpoint'
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
    job.schedule.timeZone = 'US/Eastern'
    job.description = 'my super cool job'
    job.retryConfig.retryCount = 5
    job.retryConfig.maxRetryDuration = '7200s'
    job.retryConfig.minBackoffDuration = '0.2s'
    job.retryConfig.maxBackoffDuration = '10s'
    job.retryConfig.maxDoublings = 2
    job.httpTarget.body = b'my-payload-2'
    headers_value = self.messages.HttpTarget.HeadersValue(
        additionalProperties=[
            self.messages.HttpTarget.HeadersValue.AdditionalProperty(
                key='Header1',
                value='Value1,comma'
            ),
            self.messages.HttpTarget.HeadersValue.AdditionalProperty(
                key='Header2',
                value='Value2')])
    job.httpTarget.headers = headers_value
    job.httpTarget.httpMethod = job.httpTarget.httpMethod.GET
    self._ExpectCreate(location_name, job)
    self._ExpectGetApp()

    self.Run(('scheduler jobs create-http-job my-job '
              '    --schedule "every tuesday" '
              '    --time-zone US/Eastern '
              '    --description "my super cool job" '
              '    --max-attempts 5 '
              '    --max-retry-duration 2h '
              '    --min-backoff 0.2s '
              '    --max-backoff 10s '
              '    --url http://www.example.com/endpoint'
              '    --max-doublings 2 '
              '    --http-method gEt '
              '    --header "Header1: Value1,comma" '
              '    --header "Header2:  Value2" '
              '    --message-body-from-file {} ').format(payload_file))


if __name__ == '__main__':
  test_case.main()
