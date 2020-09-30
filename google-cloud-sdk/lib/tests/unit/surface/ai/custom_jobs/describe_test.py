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
"""Tests for google3.third_party.py.tests.unit.surface.ai.custom_jobs.describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class DescribeCustomJobUnitTestAlpha(cli_test_base.CliTestBase,
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
    return self.Run([self.version, 'ai', 'custom-jobs'] + list(command))

  def _buildCustomJob(
      self,
      name='projects/fake-project/locations/us-central1/customJobs/1',
      replica_count=1,
      machine_type=u'n1-highmem-2',
      container_uri=u'gcr.io/ucaip-test/ucaip-training-test',
      display_name=u'DescribeCustomJobUnitTest'):
    worker_pool_spec = self.messages.GoogleCloudAiplatformV1beta1WorkerPoolSpec(
    )
    worker_pool_spec.replicaCount = replica_count
    worker_pool_spec.machineSpec = self.messages.GoogleCloudAiplatformV1beta1MachineSpec(
        machineType=machine_type)
    worker_pool_spec.containerSpec = self.messages.GoogleCloudAiplatformV1beta1ContainerSpec(
        imageUri=container_uri)
    job_spec = self.messages.GoogleCloudAiplatformV1beta1CustomJobSpec(
        workerPoolSpecs=[worker_pool_spec])
    return self.messages.GoogleCloudAiplatformV1beta1CustomJob(
        name=name, displayName=display_name, jobSpec=job_spec)

  def testDescribeCustomJobAlpha(self):
    request = self.messages.AiplatformProjectsLocationsCustomJobsGetRequest(
        name='projects/{}/locations/{}/customJobs/{}'.format(
            'fake-project', 'us-central1', '1'))
    expected_response = self._buildCustomJob()
    self.mock_client.projects_locations_customJobs.Get.Expect(
        request, response=expected_response)
    self.RunCommand('describe', '1', '--region={}'.format(self.region))
    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertOutputContains(
        'name: projects/fake-project/locations/us-central1/customJobs/1')
    self.AssertOutputContains('imageUri: gcr.io/ucaip-test/ucaip-training-test')
    self.AssertOutputContains('displayName: DescribeCustomJobUnitTest')


class DescribeCustomJobUnitTestBeta(DescribeCustomJobUnitTestAlpha):

  def SetUp(self):
    self.version = 'beta'
