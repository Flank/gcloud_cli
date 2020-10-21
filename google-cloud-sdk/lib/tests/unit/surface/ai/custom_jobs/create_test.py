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
"""Tests for google3.third_party.py.tests.unit.surface.ai.custom_jobs.create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

_TEST_CONFIG_YAML = """\
workerPoolSpecs:
  machineSpec:
    machineType: n1-highmem-2
  replicaCount: 1
  containerSpec:
    imageUri: gcr.io/ucaip-test/ucaip-training-test
"""


class CreateCustomJobUnitTestAlpha(cli_test_base.CliTestBase,
                                   sdk_test_base.WithFakeAuth):

  def PreSetUp(self):
    self.version = 'alpha'

  def SetUp(self):
    self.messages = apis.GetMessagesModule('aiplatform', 'v1beta1')
    self.region = 'us-central1'
    self.mock_client = mock.Client(
        apis.GetClientClass('aiplatform', 'v1beta1'),
        real_client=apis.GetClientInstance(
            'aiplatform', 'v1beta1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.yaml_file = self.Touch(
        self.temp_path, name='config.yaml', contents=_TEST_CONFIG_YAML)

  def RunCommand(self, *command):
    return self.Run([self.version, 'ai', 'custom-jobs'] + list(command))

  def _buildCreateCustomJobRequest(
      self,
      parent='projects/fake-project/locations/us-central1',
      replica_count=1,
      machine_type=u'n1-highmem-2',
      container_uri=u'gcr.io/ucaip-test/ucaip-training-test',
      display_name=u'CreateCustomJobUnitTest'):
    expected_request = self.messages.AiplatformProjectsLocationsCustomJobsCreateRequest(
    )
    expected_request.parent = parent
    expected_worker_pool_spec = self.messages.GoogleCloudAiplatformV1beta1WorkerPoolSpec(
    )
    expected_worker_pool_spec.replicaCount = replica_count
    expected_worker_pool_spec.machineSpec = self.messages.GoogleCloudAiplatformV1beta1MachineSpec(
        machineType=machine_type)
    expected_worker_pool_spec.containerSpec = self.messages.GoogleCloudAiplatformV1beta1ContainerSpec(
        imageUri=container_uri)
    expected_job_spec = self.messages.GoogleCloudAiplatformV1beta1CustomJobSpec(
        workerPoolSpecs=[expected_worker_pool_spec])
    expected_request.googleCloudAiplatformV1beta1CustomJob = self.messages.GoogleCloudAiplatformV1beta1CustomJob(
        displayName=display_name, jobSpec=expected_job_spec)
    return expected_request

  def testCreateValidCustomJobAlpha(self):
    expected_request = self._buildCreateCustomJobRequest()
    expected_response = self.messages.GoogleCloudAiplatformV1beta1CustomJob(
        name='projects/508879632478/locations/us-central1/customJobs/1',
        jobSpec=expected_request.googleCloudAiplatformV1beta1CustomJob.jobSpec)
    self.mock_client.projects_locations_customJobs.Create.Expect(
        expected_request, response=expected_response)
    response = self.RunCommand(
        'create', '--region={}'.format(self.region),
        '--display-name=CreateCustomJobUnitTest',
        '--worker-pool-spec=replica-count=1,machine-type=n1-highmem-2,container-image-uri=gcr.io/ucaip-test/ucaip-training-test'
    )
    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertErrContains(
        'Your job is still active. You may view the status of your job with the command'
    )
    self.AssertErrContains('gcloud alpha ai custom-jobs describe 1')
    self.assertEqual(response, expected_response)

  def testCreateValidCustomJobWithConfig(self):
    expected_request = self._buildCreateCustomJobRequest()
    expected_response = self.messages.GoogleCloudAiplatformV1beta1CustomJob(
        name='projects/508879632478/locations/us-central1/customJobs/1',
        jobSpec=expected_request.googleCloudAiplatformV1beta1CustomJob.jobSpec)
    self.mock_client.projects_locations_customJobs.Create.Expect(
        expected_request, response=expected_response)

    response = self.RunCommand('create', '--region={}'.format(self.region),
                               '--display-name=CreateCustomJobUnitTest',
                               '--config={}'.format(self.yaml_file))

    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertErrContains('Your job is still active. You may view the status '
                           'of your job with the command')
    self.AssertErrContains('gcloud alpha ai custom-jobs describe 1')
    self.assertEqual(response, expected_response)

  def testCreateCustomJobWithPropertyRegionAlpha(self):
    properties.VALUES.ai.region.Set('us-central1')
    expected_request = self._buildCreateCustomJobRequest()
    expected_response = self.messages.GoogleCloudAiplatformV1beta1CustomJob(
        name='projects/508879632478/locations/us-central1/customJobs/1',
        jobSpec=expected_request.googleCloudAiplatformV1beta1CustomJob.jobSpec)
    self.mock_client.projects_locations_customJobs.Create.Expect(
        expected_request, response=expected_response)
    response = self.RunCommand(
        'create', '--display-name=CreateCustomJobUnitTest',
        '--worker-pool-spec=replica-count=1,machine-type=n1-highmem-2,container-image-uri=gcr.io/ucaip-test/ucaip-training-test'
    )
    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertErrContains(
        'Your job is still active. You may view the status of your job with the command'
    )
    self.AssertErrContains('gcloud alpha ai custom-jobs describe 1')
    self.assertEqual(response, expected_response)

  def testCreateCustomJobWithNoWorkerPoolAlpha(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument (--config --worker-pool-spec): Must be specified.'):
      self.RunCommand(
          'create',
          '--region={}'.format(self.region),
          '--display-name=CreateCustomJobUnitTest',
      )
    self.AssertErrContains(
        'argument (--config --worker-pool-spec): Must be specified.')

  def testCreateCustomJobWithBothContainerAndPythonAlpha(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Either container or python package must be set.'):
      self.RunCommand(
          'create', '--region={}'.format(self.region),
          '--display-name=CreateCustomJobUnitTest',
          '--worker-pool-spec=replica-count=1,machine-type=n1-highmem-2,container-image-uri=gcr.io/ucaip-test/ucaip-training-test,python-image-uri=gcr.io/ucaip-test/ucaip-training-test'
      )
    self.AssertErrContains('Either container or python package must be set.')

  def testCreateCustomJobWithNoContainerAndPythonAlpha(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Either container or python package must be set.'):
      self.RunCommand(
          'create', '--region={}'.format(self.region),
          '--display-name=CreateCustomJobUnitTest',
          '--worker-pool-spec=replica-count=1,machine-type=n1-highmem-2')
    self.AssertErrContains('Either container or python package must be set.')


class CreateCustomJobUnitTestBeta(CreateCustomJobUnitTestAlpha):

  def PreSetUp(self):
    self.version = 'beta'


if __name__ == '__main__':
  test_case.main()
