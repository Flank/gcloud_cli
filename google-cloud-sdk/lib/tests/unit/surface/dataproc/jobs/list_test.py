# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Test of the 'jobs list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_projector
from surface.dataproc.jobs import list as jobs_list
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsListUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs list."""

  def SetUp(self):
    self.jobs = [
        self.MakeSubmittedJob(jobId=job_id, labels={'k1': 'v1'})
        for job_id in self.JOB_IDS]

  def ExpectListJobs(
      self, request=None, jobs=None, exception=None):
    if not request:
      request = self.messages.DataprocProjectsRegionsJobsListRequest(
          pageSize=100, region=self.REGION, projectId=self.Project())
    response = None
    if not exception:
      response = self.messages.ListJobsResponse(jobs=jobs)
    self.mock_client.projects_regions_jobs.List.Expect(
        request, response=response, exception=exception)

  def testListJobs(self):
    expected = self.jobs
    self.ExpectListJobs(jobs=expected)
    actual = self.RunDataproc('jobs list')
    expected = resource_projector.MakeSerializable(
        [jobs_list.TypedJob(resource) for resource in expected])
    actual = resource_projector.MakeSerializable(actual)
    self.AssertMessagesEqual(expected, actual)

  def testListJobsOutput(self):
    expected = self.jobs
    self.ExpectListJobs(jobs=expected)
    self.RunDataproc('jobs list', output_format='')
    self.AssertOutputContains('JOB_ID TYPE STATUS', normalize_space=True)
    self.AssertOutputContains(
        'dbf2d1b1-c14e-4f78-8d05-cfdb48b51a66 hadoop PENDING',
        normalize_space=True)

  def testFilteredListJobs(self):
    expected = self.jobs
    self.ExpectListJobs(
        request=self.messages.DataprocProjectsRegionsJobsListRequest(
            pageSize=100,
            projectId=self.Project(),
            region=self.REGION,
            clusterName=self.CLUSTER_NAME,
            jobStateMatcher=self.messages.DataprocProjectsRegionsJobsListRequest
            .JobStateMatcherValueValuesEnum.ACTIVE),
        jobs=expected)
    actual = self.RunDataproc(
        'jobs list --state-filter active --cluster {0}'.format(
            self.CLUSTER_NAME))
    expected = resource_projector.MakeSerializable(
        [jobs_list.TypedJob(resource) for resource in expected])
    actual = resource_projector.MakeSerializable(actual)
    self.AssertMessagesEqual(expected, actual)

  def testFilteredListInactiveJobs(self):
    expected = self.jobs
    self.ExpectListJobs(
        request=self.messages.DataprocProjectsRegionsJobsListRequest(
            pageSize=100,
            projectId=self.Project(),
            region=self.REGION,
            clusterName=self.CLUSTER_NAME,
            jobStateMatcher=self.messages.DataprocProjectsRegionsJobsListRequest
            .JobStateMatcherValueValuesEnum.NON_ACTIVE),
        jobs=expected)
    actual = self.RunDataproc(
        'jobs list --state-filter inactive --cluster {0}'.format(
            self.CLUSTER_NAME))
    expected = resource_projector.MakeSerializable(
        [jobs_list.TypedJob(resource) for resource in expected])
    actual = resource_projector.MakeSerializable(actual)
    self.AssertMessagesEqual(expected, actual)

  def testFilteredListJobsUsingNewSyntax(self):
    expected = self.jobs
    request = self.messages.DataprocProjectsRegionsJobsListRequest(
        pageSize=100,
        filter='labels.k1:v1',
        region=self.REGION,
        projectId=self.Project())
    self.ExpectListJobs(request=request, jobs=expected)
    # Since post-filtering is removed we expect to see all jobs
    actual = self.RunDataproc('jobs list --filter="labels.k1:v1"')
    expected = resource_projector.MakeSerializable(
        [jobs_list.TypedJob(job) for job in expected])
    actual = resource_projector.MakeSerializable(actual)
    self.AssertMessagesEqual(expected, actual)

  def testListJobsPagination(self):
    self.mock_client.projects_regions_jobs.List.Expect(
        self.messages.DataprocProjectsRegionsJobsListRequest(
            region=self.REGION,
            projectId=self.Project(),
            pageSize=2),
        response=self.messages.ListJobsResponse(
            jobs=self.jobs[:1],
            nextPageToken='test-token'))
    self.mock_client.projects_regions_jobs.List.Expect(
        self.messages.DataprocProjectsRegionsJobsListRequest(
            region=self.REGION,
            projectId=self.Project(),
            pageSize=2,
            pageToken='test-token'),
        response=self.messages.ListJobsResponse(
            jobs=self.jobs[1:]))

    result = self.RunDataproc('jobs list --page-size=2 --limit=3')
    expected = resource_projector.MakeSerializable(
        [jobs_list.TypedJob(job) for job in self.jobs])
    result = resource_projector.MakeSerializable(
        self.FilterOutPageMarkers(result))
    self.AssertMessagesEqual(expected, result)

  def testListJobsPermissionsError(self):
    self.ExpectListJobs(exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpErrorMatchesAsHttpException(
        'Permission denied API reason: Permission denied.'):
      next(self.RunDataproc('jobs list'))

  def testTypedJob(self):
    typed_job = jobs_list.TypedJob(self.MakeJob(pysparkJob=self.PYSPARK_JOB))
    self.assertEqual('pyspark', typed_job.type)


class JobsListUnitTestBeta(JobsListUnitTest, base.DataprocTestBaseBeta):
  """Tests for dataproc jobs list."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


class JobsListUnitTestAlpha(JobsListUnitTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
