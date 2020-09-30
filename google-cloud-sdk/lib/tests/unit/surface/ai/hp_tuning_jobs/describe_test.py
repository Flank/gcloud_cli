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
"""Tests for google3.third_party.py.tests.unit.surface.ai.hp_tuning_jobs.describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class DescribeHptuningJobUnitTestAlpha(cli_test_base.CliTestBase,
                                       sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('aiplatform', 'v1beta1')
    self.version = 'alpha'
    self.region = 'us-central1'
    self.mock_client = mock.Client(
        apis.GetClientClass('aiplatform', 'v1beta1'),
        real_client=apis.GetClientInstance(
            'aiplatform', 'v1beta1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def RunCommand(self, *command):
    return self.Run([self.version, 'ai', 'hp-tuning-jobs'] + list(command))

  def _buildHptuningJobRequest(
      self,
      algorithm,
      parent='projects/fake-project/locations/us-central1',
      display_name='DescribeHptuningJobUnitTest',
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

    return expected_hptuning_spec

  def testDescribeHptuningJobAlpha(self):
    request = self.messages.AiplatformProjectsLocationsHyperparameterTuningJobsGetRequest(
        name='projects/{}/locations/{}/hyperparameterTuningJobs/{}'.format(
            'fake-project', 'us-central1', '1'))
    expected_response = self._buildHptuningJobRequest(
        self.messages.GoogleCloudAiplatformV1beta1StudySpec
        .AlgorithmValueValuesEnum.RANDOM_SEARCH)
    expected_response.name = 'projects/fake-project/locations/us-central1/hyperparameterTuningJobs/1'
    self.mock_client.projects_locations_hyperparameterTuningJobs.Get.Expect(
        request, response=expected_response)
    self.RunCommand('describe', '1', '--region={}'.format(self.region))
    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertOutputContains(
        'name: projects/fake-project/locations/us-central1/hyperparameterTuningJobs/1'
    )
    self.AssertOutputContains('imageUri: gcr.io/ucaip-test/ucaip-training-test')
    self.AssertOutputContains('displayName: DescribeHptuningJobUnitTest')


class DescribeHptuningJobUnitTestBeta(DescribeHptuningJobUnitTestAlpha):

  def SetUp(self):
    self.version = 'beta'
