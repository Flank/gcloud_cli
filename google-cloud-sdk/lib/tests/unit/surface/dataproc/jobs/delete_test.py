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

"""Test of the 'jobs delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsDeleteUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs delete."""

  def ExpectDeleteJob(self,
                      job=None,
                      response=None,
                      exception=None,
                      region=None):
    if region is None:
      region = self.REGION
    if not job:
      job = self.MakeCompletedJob()
    if not (response or exception):
      response = self.messages.Empty()
    self.mock_client.projects_regions_jobs.Delete.Expect(
        self.messages.DataprocProjectsRegionsJobsDeleteRequest(
            region=region, jobId=job.reference.jobId, projectId=self.Project()),
        response=response,
        exception=exception)

  def ExpectDeleteCalls(self, region=None):
    self.ExpectDeleteJob(region=region)
    self.ExpectGetJob(job=self.MakeCompletedJob(), region=region)
    self.ExpectGetJob(job=self.MakeCompletedJob(), region=region)
    self.ExpectGetJob(exception=self.MakeHttpError(404), region=region)

  def _testDeleteJob(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION

    self.ExpectDeleteCalls(region=region)
    self.WriteInput('y\n')
    result = self.RunDataproc('jobs delete {0} {1}'.format(
        self.JOB_ID, region_flag))
    self.assertIsNone(result)
    self.AssertErrContains(
        "The job 'dbf5f287-f332-470b-80b2-c94b49358c45' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeleteJob(self):
    self._testDeleteJob()

  def testDeleteJob_regionProperty(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testDeleteJob(region='global')

  def testDeleteJob_regionFlag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testDeleteJob(
        region='us-central1', region_flag='--region=us-central1')

  def testDeleteJob_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('jobs delete my-awesome-job', set_region=False)

  def testDeleteJobDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        'Deletion aborted by user.'):
      self.RunDataproc('jobs delete ' + self.JOB_ID)
    self.AssertErrContains(
        "The job 'dbf5f287-f332-470b-80b2-c94b49358c45' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeleteJobNotFound(self):
    self.ExpectDeleteJob(exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(' not found.'):
      self.RunDataproc('jobs delete ' + self.JOB_ID)


class JobsDeleteUnitTestBeta(JobsDeleteUnitTest, base.DataprocTestBaseBeta):
  """Tests for dataproc jobs delete."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)


class JobsDeleteUnitTestAlpha(JobsDeleteUnitTestBeta,
                              base.DataprocTestBaseAlpha):
  pass

if __name__ == '__main__':
  sdk_test_base.main()
