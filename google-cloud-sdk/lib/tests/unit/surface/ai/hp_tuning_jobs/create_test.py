# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.ai.hp_tuning_jobs.create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

TEST_CONFIG_YAML = """\
displayName: CreateHpTuningJobUnitTest
maxTrialCount: 1
parallelTrialCount: 1
studySpec:
  metrics:
  - metricId: x
    goal: MINIMIZE
  parameters:
  - parameterId: z
    integerValueSpec:
      minValue: 1
      maxValue: 100
  algorithm: RANDOM_SEARCH
trialJobSpec:
  workerPoolSpecs:
  - machineSpec:
      machineType: n1-standard-4
    replicaCount: 1
    containerSpec:
      imageUri: gcr.io/ucaip-test/ucaip-training-test
"""


class CreateHpTuningJobUnitTestAlpha(cli_test_base.CliTestBase,
                                     sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.region = 'us-central1'
    self.version = 'alpha'
    self.messages = apis.GetMessagesModule('aiplatform', 'v1beta1')
    self.mock_client = mock.Client(
        apis.GetClientClass('aiplatform', 'v1beta1'),
        real_client=apis.GetClientInstance(
            'aiplatform', 'v1beta1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.yaml_file = self.Touch(
        self.temp_path, name='config.yaml', contents=TEST_CONFIG_YAML)

  def RunCommand(self, *command):
    return self.Run([self.version, 'ai', 'hp-tuning-jobs'] + list(command))

  def _buildCreateHpTuningJobRequest(
      self,
      algorithm,
      parent='projects/fake-project/locations/us-central1',
      display_name='CreateHpTuningJobUnitTest',
      max_trial_count=1,
      parallel_trial_count=1):
    # Constructs trial_job_spec in the create request.
    expected_worker_pool_spec = self.messages.GoogleCloudAiplatformV1beta1WorkerPoolSpec(
    )
    expected_worker_pool_spec.replicaCount = 1
    expected_worker_pool_spec.machineSpec = self.messages.GoogleCloudAiplatformV1beta1MachineSpec(
        machineType='n1-standard-4')
    expected_worker_pool_spec.containerSpec = self.messages.GoogleCloudAiplatformV1beta1ContainerSpec(
        imageUri='gcr.io/ucaip-test/ucaip-training-test')
    expected_trial_job_spec = self.messages.GoogleCloudAiplatformV1beta1CustomJobSpec(
    )
    expected_trial_job_spec.workerPoolSpecs = [expected_worker_pool_spec]

    # Constructs study_spec in the create request.
    expected_study_spec = self.messages.GoogleCloudAiplatformV1beta1StudySpec()
    expected_study_spec.algorithm = algorithm
    metric = self.messages.GoogleCloudAiplatformV1beta1StudySpecMetricSpec()
    metric.metricId = 'x'
    metric.goal = self.messages.GoogleCloudAiplatformV1beta1StudySpecMetricSpec.GoalValueValuesEnum.MINIMIZE
    expected_study_spec.metrics = [metric]
    parameter = self.messages.GoogleCloudAiplatformV1beta1StudySpecParameterSpec(
    )
    parameter.parameterId = 'z'
    parameter.integerValueSpec = self.messages.GoogleCloudAiplatformV1beta1StudySpecParameterSpecIntegerValueSpec(
    )
    parameter.integerValueSpec.minValue = 1
    parameter.integerValueSpec.maxValue = 100
    expected_study_spec.parameters = [parameter]

    expected_hptuning_spec = self.messages.GoogleCloudAiplatformV1beta1HyperparameterTuningJob(
    )
    expected_hptuning_spec.displayName = display_name
    expected_hptuning_spec.maxTrialCount = max_trial_count
    expected_hptuning_spec.parallelTrialCount = parallel_trial_count
    expected_hptuning_spec.trialJobSpec = expected_trial_job_spec
    expected_hptuning_spec.studySpec = expected_study_spec

    expected_request = self.messages.AiplatformProjectsLocationsHyperparameterTuningJobsCreateRequest(
    )
    expected_request.parent = parent
    expected_request.googleCloudAiplatformV1beta1HyperparameterTuningJob = expected_hptuning_spec
    return expected_request

  def testCreateValidHpTuningJob(self):
    expected_request = self._buildCreateHpTuningJobRequest(
        self.messages.GoogleCloudAiplatformV1beta1StudySpec
        .AlgorithmValueValuesEnum.RANDOM_SEARCH)
    expected_hptuning_job_spec = expected_request.googleCloudAiplatformV1beta1HyperparameterTuningJob
    expected_response = self.messages.GoogleCloudAiplatformV1beta1HyperparameterTuningJob(
        name='projects/508879632478/locations/us-central1/hyperparameterTuningJobs/1',
        displayName=expected_hptuning_job_spec.displayName,
        maxTrialCount=expected_hptuning_job_spec.maxTrialCount,
        parallelTrialCount=expected_hptuning_job_spec.parallelTrialCount,
        studySpec=expected_hptuning_job_spec.studySpec,
        trialJobSpec=expected_hptuning_job_spec.trialJobSpec)
    self.mock_client.projects_locations_hyperparameterTuningJobs.Create.Expect(
        expected_request, response=expected_response)

    response = self.RunCommand('create', '--region={}'.format(self.region),
                               '--display-name=CreateHpTuningJobUnitTest',
                               '--config={}'.format(self.yaml_file))

    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertErrContains(
        'Your job is still active. You may view the status of your job with the command'
    )
    self.AssertErrContains('gcloud alpha ai hp-tuning-jobs describe 1')
    self.assertEqual(response, expected_response)

  def testCreateHpTuningJobWithMaxTrialCount(self):
    expected_request = self._buildCreateHpTuningJobRequest(
        self.messages.GoogleCloudAiplatformV1beta1StudySpec
        .AlgorithmValueValuesEnum.RANDOM_SEARCH,
        max_trial_count=5)
    expected_hptuning_job_spec = expected_request.googleCloudAiplatformV1beta1HyperparameterTuningJob
    expected_response = self.messages.GoogleCloudAiplatformV1beta1HyperparameterTuningJob(
        name='projects/508879632478/locations/us-central1/hyperparameterTuningJobs/1',
        displayName=expected_hptuning_job_spec.displayName,
        maxTrialCount=expected_hptuning_job_spec.maxTrialCount,
        parallelTrialCount=expected_hptuning_job_spec.parallelTrialCount,
        studySpec=expected_hptuning_job_spec.studySpec,
        trialJobSpec=expected_hptuning_job_spec.trialJobSpec)
    self.mock_client.projects_locations_hyperparameterTuningJobs.Create.Expect(
        expected_request, response=expected_response)

    response = self.RunCommand('create', '--region={}'.format(self.region),
                               '--display-name=CreateHpTuningJobUnitTest',
                               '--max-trial-count=5',
                               '--config={}'.format(self.yaml_file))

    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertErrContains(
        'Your job is still active. You may view the status of your job with the command'
    )
    self.AssertErrContains('gcloud alpha ai hp-tuning-jobs describe 1')
    self.assertEqual(response, expected_response)

  def testCreateHpTuningJobWithParallelTrialCount(self):
    expected_request = self._buildCreateHpTuningJobRequest(
        self.messages.GoogleCloudAiplatformV1beta1StudySpec
        .AlgorithmValueValuesEnum.RANDOM_SEARCH,
        parallel_trial_count=10)
    expected_hptuning_job_spec = expected_request.googleCloudAiplatformV1beta1HyperparameterTuningJob
    expected_response = self.messages.GoogleCloudAiplatformV1beta1HyperparameterTuningJob(
        name='projects/508879632478/locations/us-central1/hyperparameterTuningJobs/1',
        displayName=expected_hptuning_job_spec.displayName,
        maxTrialCount=expected_hptuning_job_spec.maxTrialCount,
        parallelTrialCount=expected_hptuning_job_spec.parallelTrialCount,
        studySpec=expected_hptuning_job_spec.studySpec,
        trialJobSpec=expected_hptuning_job_spec.trialJobSpec)
    self.mock_client.projects_locations_hyperparameterTuningJobs.Create.Expect(
        expected_request, response=expected_response)

    response = self.RunCommand('create', '--region={}'.format(self.region),
                               '--display-name=CreateHpTuningJobUnitTest',
                               '--parallel-trial-count=10',
                               '--config={}'.format(self.yaml_file))

    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertErrContains(
        'Your job is still active. You may view the status of your job with the command'
    )
    self.AssertErrContains('gcloud alpha ai hp-tuning-jobs describe 1')
    self.assertEqual(response, expected_response)

  def testCreateHpTuningJobWithAlgorithm(self):
    expected_request = self._buildCreateHpTuningJobRequest(
        self.messages.GoogleCloudAiplatformV1beta1StudySpec
        .AlgorithmValueValuesEnum.GRID_SEARCH)
    expected_hptuning_job_spec = expected_request.googleCloudAiplatformV1beta1HyperparameterTuningJob
    expected_response = self.messages.GoogleCloudAiplatformV1beta1HyperparameterTuningJob(
        name='projects/508879632478/locations/us-central1/hyperparameterTuningJobs/1',
        displayName=expected_hptuning_job_spec.displayName,
        maxTrialCount=expected_hptuning_job_spec.maxTrialCount,
        parallelTrialCount=expected_hptuning_job_spec.parallelTrialCount,
        studySpec=expected_hptuning_job_spec.studySpec,
        trialJobSpec=expected_hptuning_job_spec.trialJobSpec)
    self.mock_client.projects_locations_hyperparameterTuningJobs.Create.Expect(
        expected_request, response=expected_response)

    response = self.RunCommand('create', '--region={}'.format(self.region),
                               '--display-name=CreateHpTuningJobUnitTest',
                               '--algorithm=grid-search',
                               '--config={}'.format(self.yaml_file))

    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertErrContains(
        'Your job is still active. You may view the status of your job with the command'
    )
    self.AssertErrContains('gcloud alpha ai hp-tuning-jobs describe 1')
    self.assertEqual(response, expected_response)

  def testCreateHpTuningJobWithoutConfig(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --config: Must be specified.'):
      self.RunCommand(
          'create',
          '--region={}'.format(self.region),
          '--display-name=CreateHpTuningJobUnitTest',
      )

  def testCreateHpTuningJobWithoutDisplayName(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --display-name: Must be specified.'):
      self.RunCommand('create', '--region={}'.format(self.region),
                      '--config={}'.format(self.yaml_file))


class CreateHpTuningJobUnitTestBeta(CreateHpTuningJobUnitTestAlpha):

  def SetUp(self):
    self.version = 'beta'


if __name__ == '__main__':
  test_case.main()
