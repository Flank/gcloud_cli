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
"""Tests for the apis utility functions."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.dataflow import apis
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base


class ApisUnitTest(base.DataflowMockingTestBase,
                   sdk_test_base.WithOutputCapture):

  def SetUp(self):
    super(base.DataflowMockingTestBase, self).SetUp()

  def testJobsGet(self):
    request = apis.Jobs.GET_REQUEST(
        jobId=base.JOB_1_ID,
        projectId=self.Project(),
        location=base.DEFAULT_REGION,
        view=apis.Jobs.GET_REQUEST.ViewValueValuesEnum.JOB_VIEW_ALL)
    self.mocked_client.projects_locations_jobs.Get.Expect(
        request, apis.GetMessagesModule().Job())
    apis.Jobs.Get(job_id=base.JOB_1_ID,
                  project_id=self.Project(),
                  view=apis.Jobs.GET_REQUEST.ViewValueValuesEnum.JOB_VIEW_ALL)

  def testJobsCancel(self):
    job_id = base.JOB_1_ID
    project_id = self.Project()

    state = (apis.GetMessagesModule(
    ).Job.RequestedStateValueValuesEnum.JOB_STATE_CANCELLED)
    job = apis.GetMessagesModule().Job(requestedState=state)

    request = apis.Jobs.UPDATE_REQUEST(
        jobId=job_id,
        projectId=project_id,
        location=base.DEFAULT_REGION,
        job=job)
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request, apis.GetMessagesModule().Job())
    apis.Jobs.Cancel(job_id=job_id, project_id=project_id)

  def testJobsDrain(self):
    job_id = base.JOB_1_ID
    project_id = self.Project()

    state = (apis.GetMessagesModule(
    ).Job.RequestedStateValueValuesEnum.JOB_STATE_DRAINED)
    job = apis.GetMessagesModule().Job(requestedState=state)

    request = apis.Jobs.UPDATE_REQUEST(
        jobId=job_id,
        projectId=project_id,
        location=base.DEFAULT_REGION,
        job=job)
    self.mocked_client.projects_locations_jobs.Update.Expect(
        request, apis.GetMessagesModule().Job())
    apis.Jobs.Drain(job_id=job_id, project_id=project_id)

  def testMetricsGet(self):
    request = apis.Metrics.GET_REQUEST(
        jobId=base.JOB_1_ID,
        projectId=self.Project(),
        location=base.DEFAULT_REGION,
        startTime='start_time')
    self.mocked_client.projects_locations_jobs.GetMetrics.Expect(
        request, apis.GetMessagesModule().MetricUpdate())
    apis.Metrics.Get(job_id=base.JOB_1_ID,
                     project_id=self.Project(),
                     start_time='start_time')

  def testMessagesList(self):
    start_time = 'start_time'
    end_time = 'end_time'
    page_size = 1337
    page_token = 'page_token'
    minimum_importance = (
        apis.Messages.LIST_REQUEST.MinimumImportanceValueValuesEnum.
        JOB_MESSAGE_DETAILED)
    request = apis.Messages.LIST_REQUEST(
        jobId=base.JOB_1_ID,
        projectId=self.Project(),
        location=base.DEFAULT_REGION,
        minimumImportance=minimum_importance,
        startTime=start_time,
        endTime=end_time,
        pageSize=page_size,
        pageToken=page_token)
    self.mocked_client.projects_locations_jobs_messages.List.Expect(
        request, apis.GetMessagesModule().ListJobMessagesResponse())
    apis.Messages.List(
        job_id=base.JOB_1_ID,
        project_id=self.Project(),
        minimum_importance=minimum_importance,
        start_time=start_time,
        end_time=end_time,
        page_size=page_size,
        page_token=page_token)

  def testTemplatesCreate(self):
    name = 'job name'
    gcs_path = 'gs://my_gcs_path'
    staging_path = 'gs://my_staging_path'
    request = apis.Templates.CREATE_REQUEST(
        jobName=name,
        location=base.DEFAULT_REGION,
        gcsPath=gcs_path,
        environment=apis.GetMessagesModule().RuntimeEnvironment(
            tempLocation=staging_path))

    wrapper_req = (
        apis.GetMessagesModule()
        .DataflowProjectsLocationsTemplatesCreateRequest)
    wrapped_request = wrapper_req(
        createJobFromTemplateRequest=request,
        projectId=self.Project(),
        location=base.DEFAULT_REGION)

    self.mocked_client.projects_locations_templates.Create.Expect(
        wrapped_request, apis.GetMessagesModule().Job())

    apis.Templates.Create(
        job_name=name,
        project_id=self.Project(),
        gcs_location=gcs_path,
        staging_location=staging_path)


if __name__ == '__main__':
  test_case.main()
