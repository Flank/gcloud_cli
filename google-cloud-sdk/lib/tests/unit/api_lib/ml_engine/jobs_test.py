# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the ML Engine Jobs library."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class JobsClientTest(base.MlGaPlatformTestBase):

  def _MakeCreateRequest(self, parent, job):
    return self.msgs.MlProjectsJobsCreateRequest(
        parent=parent,
        googleCloudMlV1Job=job
    )

  def SetUp(self):
    self.jobs_client = jobs.JobsClient()

  def testCancel(self):
    response = self.msgs.GoogleProtobufEmpty()
    self.client.projects_jobs.Cancel.Expect(
        request=self.msgs.MlProjectsJobsCancelRequest(
            name='projects/{}/jobs/opId'.format(self.Project())),
        response=response)
    job_ref = resources.REGISTRY.Parse('opId', collection='ml.projects.jobs',
                                       params={'projectsId': self.Project()})
    self.assertEqual(self.jobs_client.Cancel(job_ref), response)

  def testGet(self):
    response = self.short_msgs.Job(jobId='opName')
    self.client.projects_jobs.Get.Expect(
        request=self.msgs.MlProjectsJobsGetRequest(
            name='projects/{}/jobs/opId'.format(self.Project())),
        response=response)
    job_ref = resources.REGISTRY.Parse('opId', collection='ml.projects.jobs',
                                       params={'projectsId': self.Project()})
    self.assertEqual(self.jobs_client.Get(job_ref), response)

  def testList(self):
    response_items = [
        self.short_msgs.Job(jobId='opName1'),
        self.short_msgs.Job(jobId='opName2')
    ]
    self.client.projects_jobs.List.Expect(
        request=self.msgs.MlProjectsJobsListRequest(
            parent='projects/{}'.format(self.Project()), pageSize=100),
        response=self.short_msgs.ListJobsResponse(
            jobs=response_items))
    project_ref = resources.REGISTRY.Parse(self.Project(),
                                           collection='ml.projects')
    self.assertEqual(list(self.jobs_client.List(project_ref)), response_items)

  def testCreate(self):
    job = self.short_msgs.Job(jobId='my_job')
    self.client.projects_jobs.Create.Expect(
        request=self._MakeCreateRequest(
            parent='projects/{}'.format(self.Project()),
            job=job),
        response=job)
    project_ref = resources.REGISTRY.Parse(self.Project(),
                                           collection='ml.projects')
    self.assertEqual(job, self.jobs_client.Create(project_ref, job))

  def testBuildTrainingJobWithYaml(self):
    test_yaml = """
        jobId: job_name_to_override
        trainingInput:
          args:
            - --foo
            - --bar
          scaleTier: CUSTOM
          runtimeVersion: '0.12'
    """

    result = self.jobs_client.BuildTrainingJob(
        path=self.Touch(self.temp_path, 'betaconfigfile.yaml', test_yaml),
        job_name='the_real_job',
        module_name='my_module',
        trainer_uri=['gs://bucket/program.tar.gz'],
        region='us-east1')

    scale_tier_enum = self.short_msgs.TrainingInput.ScaleTierValueValuesEnum
    self.assertEqual(
        result,
        self.short_msgs.Job(
            jobId='the_real_job',
            trainingInput=self.short_msgs.TrainingInput(
                pythonModule='my_module',
                packageUris=['gs://bucket/program.tar.gz'],
                region='us-east1',
                scaleTier=scale_tier_enum.CUSTOM,
                runtimeVersion='0.12',
                args=['--foo', '--bar'])))

  def testBuildTrainingJobWithoutYaml(self):
    scale_tier_enum = self.short_msgs.TrainingInput.ScaleTierValueValuesEnum
    result = self.jobs_client.BuildTrainingJob(
        path=None,
        job_name='the_real_job',
        module_name='my_module',
        trainer_uri=['gs://bucket/program.tar.gz'],
        scale_tier=scale_tier_enum.CUSTOM,
        region='us-east1',
        runtime_version='0.12')

    self.assertEqual(
        result,
        self.short_msgs.Job(
            jobId='the_real_job',
            trainingInput=self.short_msgs.TrainingInput(
                pythonModule='my_module',
                packageUris=['gs://bucket/program.tar.gz'],
                scaleTier=scale_tier_enum.CUSTOM,
                runtimeVersion='0.12',
                region='us-east1')))

  def testBuildTrainingJobWithEmptyYaml(self):

    result = self.jobs_client.BuildTrainingJob(
        path=self.Touch(self.temp_path, 'betaconfigfile.yaml', ''),
        job_name='the_real_job',
        module_name='my_module',
        trainer_uri=['gs://bucket/program.tar.gz'],
        region='us-east1')

    self.assertEqual(
        result,
        self.short_msgs.Job(
            jobId='the_real_job',
            trainingInput=self.short_msgs.TrainingInput(
                pythonModule='my_module',
                packageUris=['gs://bucket/program.tar.gz'],
                region='us-east1')))

  def testBuildBatchPredictionJob(self):
    result = self.jobs_client.BuildBatchPredictionJob(
        job_name='my_job',
        model_name='my_model',
        version_name='v1',
        input_paths=['gs://bucket0/instance', 'gs://bucket1/instance*'],
        data_format='TEXT',
        output_path='gs://bucket/output',
        region='us-central1-c',
        runtime_version='0.12')

    prediction_input_class = self.short_msgs.PredictionInput
    data_formats = prediction_input_class.DataFormatValueValuesEnum
    self.assertEqual(
        result,
        self.short_msgs.Job(
            jobId='my_job',
            predictionInput=self.short_msgs.PredictionInput(
                versionName='projects/fake-project/models/my_model/versions/v1',
                inputPaths=['gs://bucket0/instance', 'gs://bucket1/instance*'],
                dataFormat=data_formats.TEXT,
                outputPath='gs://bucket/output',
                region='us-central1-c',
                runtimeVersion='0.12')))

  def testBuildBatchPredictionJobNoVersion(self):
    result = self.jobs_client.BuildBatchPredictionJob(
        job_name='my_job',
        model_name='my_model',
        input_paths=['gs://bucket0/instance'],
        data_format='TF_RECORD',
        output_path='gs://bucket/output',
        region='us-central1-c')

    prediction_input_class = self.short_msgs.PredictionInput
    data_formats = prediction_input_class.DataFormatValueValuesEnum
    self.assertEqual(
        result,
        self.short_msgs.Job(
            jobId='my_job',
            predictionInput=self.short_msgs.PredictionInput(
                modelName='projects/fake-project/models/my_model',
                inputPaths=['gs://bucket0/instance'],
                dataFormat=data_formats.TF_RECORD,
                outputPath='gs://bucket/output',
                region='us-central1-c')))

  def testBuildBatchPredictionJobModelDir(self):
    result = self.jobs_client.BuildBatchPredictionJob(
        job_name='my_job',
        model_dir='gs://some_bucket/models',
        input_paths=['gs://bucket0/instance'],
        data_format='TF_RECORD',
        output_path='gs://bucket/output',
        region='us-central1')

    data_formats = self.short_msgs.PredictionInput.DataFormatValueValuesEnum
    self.assertEqual(
        result,
        self.short_msgs.Job(
            jobId='my_job',
            predictionInput=self.short_msgs.PredictionInput(
                uri='gs://some_bucket/models',
                inputPaths=['gs://bucket0/instance'],
                dataFormat=data_formats.TF_RECORD,
                outputPath='gs://bucket/output',
                region='us-central1')))

  def testBuildBatchPredictionJobMaxWorkerCount(self):
    result = self.jobs_client.BuildBatchPredictionJob(
        job_name='my_job',
        model_dir='gs://some_bucket/models',
        input_paths=['gs://bucket0/instance'],
        data_format='TF_RECORD',
        output_path='gs://bucket/output',
        region='us-central1',
        max_worker_count=3)

    prediction_input_class = self.short_msgs.PredictionInput
    data_formats = prediction_input_class.DataFormatValueValuesEnum
    self.assertEqual(
        result,
        self.short_msgs.Job(
            jobId='my_job',
            predictionInput=self.short_msgs.PredictionInput(
                uri='gs://some_bucket/models',
                inputPaths=['gs://bucket0/instance'],
                dataFormat=data_formats.TF_RECORD,
                outputPath='gs://bucket/output',
                region='us-central1',
                maxWorkerCount=3)))

  def testBuildBatchPredictionBatchSize(self):
    result = self.jobs_client.BuildBatchPredictionJob(
        job_name='my_job',
        model_dir='gs://some_bucket/models',
        input_paths=['gs://bucket0/instance'],
        data_format='TF_RECORD',
        output_path='gs://bucket/output',
        region='us-central1',
        batch_size=128)

    prediction_input_class = self.short_msgs.PredictionInput
    data_formats = prediction_input_class.DataFormatValueValuesEnum
    self.assertEqual(
        result,
        self.short_msgs.Job(
            jobId='my_job',
            predictionInput=self.short_msgs.PredictionInput(
                uri='gs://some_bucket/models',
                inputPaths=['gs://bucket0/instance'],
                dataFormat=data_formats.TF_RECORD,
                outputPath='gs://bucket/output',
                region='us-central1',
                batchSize=128)))

if __name__ == '__main__':
  test_case.main()
