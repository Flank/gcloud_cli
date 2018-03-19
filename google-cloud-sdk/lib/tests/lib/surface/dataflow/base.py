# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Base classes for all dataflow tests."""

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.dataflow import job_utils
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error

MESSAGE_MODULE = core_apis.GetMessagesModule('dataflow', 'v1b3')

# Must match job ID in test_data/WordCountJob.json
JOB_1_ID = '2016-01-01_13_11_11-11111'
JOB_2_ID = '2016-02-02_14_22_22-22222'
JOB_3_ID = '2016-03-03_15_33_33-33333'
JOB_4_ID = '2016-04-04_16_44_44-44444'
JOB_5_ID = '2016-05-05_17_55_55-55555'
JOB_6_ID = '2016-06-06_18_66_66-66666'

DEFAULT_PAGE_SIZE = 20

DEFAULT_REGION = job_utils.DATAFLOW_API_DEFAULT_REGION


class DataflowTestBase(cli_test_base.CliTestBase):
  """Base class for Dataflow Tests that registers the dataflow commands."""

  def SetUp(self):
    pass


class DataflowMockingTestBase(sdk_test_base.WithFakeAuth, DataflowTestBase):
  """Base class for Dataflow Tests that sets up a Mock API client."""

  def SetUp(self):
    self.mocked_client = mock.Client(
        client_class=core_apis.GetClientClass('dataflow', 'v1b3'),
        real_client=core_apis.GetClientInstance(
            'dataflow', 'v1b3', no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

  # the API argument "filter" is set in stone. Ignore this warning.
  # pylint: disable=redefined-builtin
  def MockListJobs(self,
                   jobs,
                   filter=None,
                   page_token=None,
                   next_page_token=None,
                   location=None):
    req_class = (MESSAGE_MODULE.DataflowProjectsLocationsJobsListRequest)

    location = location or DEFAULT_REGION

    self.mocked_client.projects_locations_jobs.List.Expect(
        request=req_class(
            projectId=self.Project(),
            location=location,
            pageToken=page_token,
            filter=filter or req_class.FilterValueValuesEnum.ALL,
            pageSize=DEFAULT_PAGE_SIZE,
            view=None),
        response=MESSAGE_MODULE.ListJobsResponse(
            jobs=jobs, nextPageToken=next_page_token))

  # the API argument "filter" is set in stone. Ignore this warning.
  # pylint: disable=redefined-builtin
  def MockAggregatedListJobs(self,
                             jobs,
                             filter=None,
                             page_token=None,
                             next_page_token=None):
    req_class = (MESSAGE_MODULE.DataflowProjectsJobsAggregatedRequest)

    self.mocked_client.projects_jobs.Aggregated.Expect(
        request=req_class(
            projectId=self.Project(),
            pageToken=page_token,
            filter=filter or req_class.FilterValueValuesEnum.ALL,
            pageSize=DEFAULT_PAGE_SIZE,
            view=None),
        response=MESSAGE_MODULE.ListJobsResponse(
            jobs=jobs, nextPageToken=next_page_token))

  def MockGetJob(self, job, location=None, view=None):
    get_job_req_class = MESSAGE_MODULE.DataflowProjectsLocationsJobsGetRequest

    view = view or get_job_req_class.ViewValueValuesEnum.JOB_VIEW_SUMMARY
    location = location or DEFAULT_REGION

    self.mocked_client.projects_locations_jobs.Get.Expect(
        request=get_job_req_class(
            projectId=self.Project(),
            jobId=job.id,
            location=location,
            view=view),
        response=job)

  def MockRunJob(self,
                 job=None,
                 location=None,
                 gcs_location=None,
                 parameters=None,
                 job_name=None,
                 service_account_email=None,
                 zone=None,
                 max_workers=None):
    run_job_req_body = MESSAGE_MODULE.CreateJobFromTemplateRequest
    run_job_req_class = (
        MESSAGE_MODULE.DataflowProjectsLocationsTemplatesCreateRequest)
    params_value = run_job_req_body.ParametersValue

    location = location or DEFAULT_REGION

    params_list = []
    for k, v in parameters.iteritems() if parameters else {}:
      params_list.append(params_value.AdditionalProperty(key=k, value=v))

    body = run_job_req_body(
        gcsPath=gcs_location,
        jobName=job_name,
        location=location,
        environment=MESSAGE_MODULE.RuntimeEnvironment(
            serviceAccountEmail=service_account_email,
            zone=zone,
            maxWorkers=max_workers,
        ),
        parameters=params_value(additionalProperties=params_list)
        if parameters else None)

    self.mocked_client.projects_locations_templates.Create.Expect(
        request=run_job_req_class(
            projectId=self.Project(),
            createJobFromTemplateRequest=body,
            location=location),
        response=job)

  def MockGetJobFailure(self, job_id, location=None, view=None):
    get_job_req_class = MESSAGE_MODULE.DataflowProjectsLocationsJobsGetRequest

    view = view or get_job_req_class.ViewValueValuesEnum.JOB_VIEW_SUMMARY
    location = location or DEFAULT_REGION

    self.mocked_client.projects_locations_jobs.Get.Expect(
        request=get_job_req_class(
            projectId=self.Project(),
            jobId=job_id,
            location=location,
            view=view),
        exception=http_error.MakeHttpError(
            404, 'Requested entity was not found.', url='FakeUrl'))

  def SampleJob(
      self,
      job_id,
      job_name=None,
      project_id=None,
      creation_time=None,
      job_type=MESSAGE_MODULE.Job.TypeValueValuesEnum.JOB_TYPE_BATCH,
      job_status=MESSAGE_MODULE.Job.CurrentStateValueValuesEnum.JOB_STATE_DONE,
      environment=None,
      region=None):
    """Returns a Job message object for use in tests.

    Args:
      job_id: The job ID for the Job.
      job_name: The name for the job. Defaults to '<job_id>_name'.
      project_id: The project ID for the job.
      creation_time: The creation time, in 'yyyy-mm-dd hh-mm-ss' format, if not
        specified defaults to 2013-09-06 17:54:10.
      job_type: The job type, defaults to JOB_TYPE_BATCH.
      job_status: The job status, defaults to JOB_STATE_DONE.
      environment: The environment, defaults to None.
      region: The regional endpoint, defaults to 'us-central1'.

    Returns:
      Job message for use in tests.
    """
    region = region or DEFAULT_REGION
    if not creation_time:
      creation_time = '2013-09-06 17:54:10'
    creation_time_str = times.FormatDateTime(times.ParseDateTime(creation_time))

    return MESSAGE_MODULE.Job(
        projectId=project_id or self.Project(),
        id=job_id,
        name=job_name or ('%s_name' % job_id),
        type=job_type,
        currentState=job_status,
        currentStateTime='2013-09-06T17:54:10.636-07:00',
        createTime=creation_time_str,
        environment=environment,
        location=region)
