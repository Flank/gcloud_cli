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
"""Tests for the apis utility functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import http_wrapper
from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.util import exceptions
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
        request, apis.GetMessagesModule().JobMetrics())
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
    template_args = apis.TemplateArguments(job_name=name, gcs_location=gcs_path,
                                           project_id=self.Project(),
                                           staging_location=staging_path)
    apis.Templates.Create(template_args)

  def testLaunchDynamicTemplate(self):
    name = 'myjob'
    gcs_path = 'gs://dynamic_template_path'
    staging_path = 'gs://my_staging_path'
    parameters = apis.Templates.LAUNCH_TEMPLATE_PARAMETERS(
        jobName=name,
        environment=apis.GetMessagesModule().RuntimeEnvironment(
            tempLocation=staging_path),
        update=False)

    wrapper_req = (
        apis.GetMessagesModule().DataflowProjectsLocationsTemplatesLaunchRequest
    )
    wrapped_request = wrapper_req(
        dynamicTemplate_gcsPath=gcs_path,
        dynamicTemplate_stagingLocation=staging_path,
        launchTemplateParameters=parameters,
        projectId=self.Project(),
        location=base.DEFAULT_REGION,
        validateOnly=False)

    self.mocked_client.projects_locations_templates.Launch.Expect(
        wrapped_request,
        apis.GetMessagesModule().LaunchTemplateResponse())
    template_args = apis.TemplateArguments(
        job_name=name,
        gcs_location=gcs_path,
        project_id=self.Project(),
        staging_location=staging_path)
    apis.Templates.LaunchDynamicTemplate(template_args)

  def testLaunchDynamicTemplate_httpError(self):
    name = 'myjob'
    gcs_path = 'gs://dynamic_template_path'
    staging_path = 'gs://my_staging_path'
    parameters = apis.Templates.LAUNCH_TEMPLATE_PARAMETERS(
        jobName=name,
        environment=apis.GetMessagesModule().RuntimeEnvironment(
            tempLocation=staging_path),
        update=False)

    wrapper_req = (
        apis.GetMessagesModule().DataflowProjectsLocationsTemplatesLaunchRequest
    )
    wrapped_request = wrapper_req(
        dynamicTemplate_gcsPath=gcs_path,
        dynamicTemplate_stagingLocation=staging_path,
        launchTemplateParameters=parameters,
        projectId=self.Project(),
        location=base.DEFAULT_REGION,
        validateOnly=False)

    self.mocked_client.projects_locations_templates.Launch.Expect(
        wrapped_request,
        exception=apitools_exceptions.HttpError.FromResponse(
            http_wrapper.Response(
                info={'status': 400},
                content='{"error": '
                '{"message": "The workflow could not be created."}}',
                request_url='https://dataflow.googleapis.com/v1b3/request-url'))
    )
    template_args = apis.TemplateArguments(
        job_name=name,
        gcs_location=gcs_path,
        project_id=self.Project(),
        staging_location=staging_path)
    with self.AssertRaisesExceptionMatches(
        exceptions.HttpException, 'The workflow could not be created.'):
      apis.Templates.LaunchDynamicTemplate(template_args)

  def testPrivateIPTemplatesCreate(self):
    name = 'job name'
    gcs_path = 'gs://my_gcs_path'
    staging_path = 'gs://my_staging_path'
    ip_configuration_enum = apis.GetMessagesModule(
    ).RuntimeEnvironment.IpConfigurationValueValuesEnum
    ip_private = ip_configuration_enum.WORKER_IP_PRIVATE
    request = apis.Templates.CREATE_REQUEST(
        jobName=name,
        location=base.DEFAULT_REGION,
        gcsPath=gcs_path,
        environment=apis.GetMessagesModule().RuntimeEnvironment(
            tempLocation=staging_path, ipConfiguration=ip_private))

    wrapper_req = (
        apis.GetMessagesModule().DataflowProjectsLocationsTemplatesCreateRequest
    )
    wrapped_request = wrapper_req(
        createJobFromTemplateRequest=request,
        projectId=self.Project(),
        location=base.DEFAULT_REGION)

    self.mocked_client.projects_locations_templates.Create.Expect(
        wrapped_request,
        apis.GetMessagesModule().Job())
    template_args = apis.TemplateArguments(job_name=name, gcs_location=gcs_path,
                                           project_id=self.Project(),
                                           staging_location=staging_path,
                                           disable_public_ips=True)
    apis.Templates.Create(template_args)

  def testFlexTemplatesCreateJob(self):
    name = 'job name'
    gcs_path = 'gs://my_gcs_path'
    template_args = apis.TemplateArguments(job_name=name, gcs_location=gcs_path,
                                           project_id=self.Project())
    launch_params = apis.Templates.FLEX_TEMPLATE_PARAMETER(
        jobName=template_args.job_name,
        containerSpecGcsPath=template_args.gcs_location,
        parameters=None)
    request = apis.Templates.LAUNCH_FLEX_TEMPLATE_REQUEST(
        launchParameter=launch_params)

    wrapper_req = (
        apis.GetMessagesModule()
        .DataflowProjectsLocationsFlexTemplatesLaunchRequest)
    wrapped_request = wrapper_req(
        projectId=self.Project(),
        location=base.DEFAULT_REGION,
        launchFlexTemplateRequest=request)

    self.mocked_client.projects_locations_flexTemplates.Launch.Expect(
        wrapped_request,
        apis.GetMessagesModule().LaunchFlexTemplateResponse())

    apis.Templates.CreateJobFromFlexTemplate(template_args)

  def testBuildAndStoreFlexTemplateFileMalformedMetadata(self):
    metadata = {
        'parameters': [{
            'name': 'input',
            'label': 'input',
            'helpText': 'help text for input param'
        }]
    }
    with self.AssertRaisesExceptionRegexp(
        ValueError,
        'Invalid template metadata. Name field is empty.*'):
      apis.Templates.BuildAndStoreFlexTemplateFile(
          'gs://foo/template-file', 'gcr://foo-image', json.dumps(metadata),
          'JAVA', True)

  def testBuildAndStoreFlexTemplateFileMalformedParameterName(self):
    metadata = {
        'name': 'name',
        'parameters': [{
            'label': 'input',
            'helpText': 'help text for input param'
        }]
    }
    with self.AssertRaisesExceptionRegexp(
        ValueError,
        'Invalid template metadata. Parameter name field is empty.*'):
      apis.Templates.BuildAndStoreFlexTemplateFile(
          'gs://foo/template-file', 'gcr://foo-image', json.dumps(metadata),
          'JAVA', True)

  def testBuildAndStoreFlexTemplateFileMalformedParameterLabel(self):
    metadata = {
        'name': 'name',
        'parameters': [{
            'name': 'name',
            'helpText': 'help text for input param'
        }]
    }
    with self.AssertRaisesExceptionRegexp(
        ValueError,
        'Invalid template metadata. Parameter label field is empty.*'):
      apis.Templates.BuildAndStoreFlexTemplateFile(
          'gs://foo/template-file', 'gcr://foo-image', json.dumps(metadata),
          'JAVA', True)

  def testBuildAndStoreFlexTemplateFileMalformedParameterHelpText(self):
    metadata = {
        'name': 'name',
        'parameters': [{
            'label': 'input',
            'name': 'name'
        }]
    }
    with self.AssertRaisesExceptionRegexp(
        ValueError,
        'Invalid template metadata. Parameter helpText field is empty.*'):
      apis.Templates.BuildAndStoreFlexTemplateFile(
          'gs://foo/template-file', 'gcr://foo-image', json.dumps(metadata),
          'JAVA', True)

  def testBuildAndStoreFlexTemplateFilePrinOnly(self):
    expected_result = {
        'image': 'gcr://foo-image',
        'sdkInfo': {
            'language': 'JAVA'
        },
        'metadata': {
            'name': 'name',
            'parameters': [{
                'name': 'input',
                'label': 'input',
                'helpText': 'help text for input param'
            }]
        }
    }
    metadata_file = self.Resource('tests/unit/surface/dataflow/test_data',
                                  'flex_template_metadata.json')
    with open(metadata_file, 'r') as f:
      result = apis.Templates.BuildAndStoreFlexTemplateFile(
          'gs://foo/template-file', 'gcr://foo-image', f.read(), 'JAVA', True)
      self.assertEqual(json.loads(result), expected_result)

  def testBuildAndStoreFlexTemplateImageMissingRequiredEnv(self):
    with self.AssertRaisesExceptionRegexp(
        ValueError,
        ('FLEX_TEMPLATE_JAVA_MAIN_CLASS environment variable '
         'should be provided for all JAVA jobs.')):
      apis.Templates.BuildAndStoreFlexTemplateImage(
          'gcr://foo-image', 'JAVA11', ['test.jar'],
          {}, 'JAVA')


if __name__ == '__main__':
  test_case.main()
