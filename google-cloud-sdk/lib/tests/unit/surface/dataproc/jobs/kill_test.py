# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Test of the 'jobs kill' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsKillUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs kill."""

  def ExpectCancelJob(
      self, job=None, response=None, exception=None, region=None):
    if region is None:
      region = self.REGION
    if not job:
      job = self.MakeRunningJob()
    if not (response or exception):
      response = copy.deepcopy(job)
      response.status.state = self.STATE_ENUM.CANCEL_PENDING
    self.mock_client.projects_regions_jobs.Cancel.Expect(
        self.messages.DataprocProjectsRegionsJobsCancelRequest(
            jobId=job.reference.jobId,
            region=region,
            projectId=self.Project(),
            cancelJobRequest=self.messages.CancelJobRequest()),
        response=response,
        exception=exception)
    return response

  def ExpectKillCalls(self, job=None, final_state=None, region=None):
    if region is None:
      region = self.REGION
    if not final_state:
      final_state = self.STATE_ENUM.CANCELLED
    job = self.ExpectCancelJob(job, region=region)
    self.ExpectGetJob(job, region=region)
    job = copy.deepcopy(job)
    job.status.state = self.STATE_ENUM.CANCEL_STARTED
    self.ExpectGetJob(job, region=region)
    self.ExpectGetJob(job, region=region)
    job = copy.deepcopy(job)
    job.status.state = final_state
    self.ExpectGetJob(job, region=region)
    return job

  def _testKillJob(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    expected = self.ExpectKillCalls(region=region)
    self.WriteInput('y\n')
    result = self.RunDataproc('jobs kill {0} {1}'.format(
        self.JOB_ID, region_flag))
    self.AssertErrContains(
        "The job 'dbf5f287-f332-470b-80b2-c94b49358c45' will be killed.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains('Job cancellation initiated')
    self.AssertErrContains('Waiting for job cancellation')

  def testKillJob(self):
    self._testKillJob()

  def testKillJob_regionProperty(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testKillJob(region='us-central1')

  def testKillJob_regionFlag(self):
    properties.VALUES.dataproc.region.Set('other-default-region')
    self._testKillJob(region='us-central1', region_flag='--region=us-central1')

  def testKillJob_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('jobs kill foo-job', set_region=False)

  def testKillJobFailure(self):
    self.ExpectKillCalls(final_state=self.STATE_ENUM.ERROR)
    with self.AssertRaisesExceptionMatches(
        exceptions.JobError,
        'Job [{0}] entered state [ERROR] while waiting for [CANCELLED].'.format(
            self.JOB_ID)):
      self.RunDataproc('jobs kill ' + self.JOB_ID)
    self.AssertErrContains('Job cancellation initiated')
    self.AssertErrContains('Waiting for job cancellation')

  def testKillJobDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        'Cancellation aborted by user.'):
      self.RunDataproc('jobs kill ' + self.JOB_ID)
    self.AssertErrContains(
        "The job 'dbf5f287-f332-470b-80b2-c94b49358c45' will be killed.")
    self.AssertErrContains('PROMPT_CONTINUE')

  def testKillJobNotFound(self):
    self.ExpectCancelJob(
        exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(' not found.'):
      self.RunDataproc('jobs kill ' + self.JOB_ID)


class JobsKillUnitTestBeta(JobsKillUnitTest, base.DataprocTestBaseBeta):
  """Tests for dataproc jobs kill."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


class JobsKillUnitTestAlpha(JobsKillUnitTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
