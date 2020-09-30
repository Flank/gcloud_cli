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
"""Tests for google3.third_party.py.tests.unit.surface.ai.models.upload."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class UploadModelUnitTestBase(cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('aiplatform', 'v1beta1')

  def RunCommandBeta(self, *command):
    return self.Run(['beta', 'ai', 'models'] + list(command))


class UploadModelUnitTest(UploadModelUnitTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.mock_client = mock.Client(
        apis.GetClientClass('aiplatform', 'v1beta1'),
        real_client=apis.GetClientInstance(
            'aiplatform', 'v1beta1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def _buildUploadModelRequest(
      self,
      parent='projects/fake-project/locations/us-central1',
      display_name=u'UploadModelUnitTest',
      container_image_uri=u'gcr.io/ucaip-test/ucaip-upload-model-test'):
    container_spec = self.messages.GoogleCloudAiplatformV1beta1ModelContainerSpec(
        healthRoute='http://health_route',
        imageUri=container_image_uri,
        predictRoute='http://predict_route')
    container_spec.command = ['COMMAND1', 'COMMAND2']
    container_spec.args = ['ARG1', 'ARG2']
    container_spec.env = [
        self.messages.GoogleCloudAiplatformV1beta1EnvVar(
            name='ENV1', value='VALUE1'),
        self.messages.GoogleCloudAiplatformV1beta1EnvVar(
            name='ENV2', value='VALUE2'),
    ]
    container_spec.ports = [
        self.messages.GoogleCloudAiplatformV1beta1Port(containerPort=8080),
        self.messages.GoogleCloudAiplatformV1beta1Port(containerPort=8000)
    ]
    model = self.messages.GoogleCloudAiplatformV1beta1Model(
        artifactUri='gs://test/1',
        containerSpec=container_spec,
        description=u'description1',
        displayName=display_name)
    return self.messages.AiplatformProjectsLocationsModelsUploadRequest(
        parent=parent,
        googleCloudAiplatformV1beta1UploadModelRequest=self.messages
        .GoogleCloudAiplatformV1beta1UploadModelRequest(model=model))

  def _buildUploadModelResponse(self):
    return self.messages.GoogleLongrunningOperation.ResponseValue(
        additionalProperties=[
            self.messages.GoogleLongrunningOperation.ResponseValue
            .AdditionalProperty(
                key='@type',
                value=extra_types.JsonValue(
                    string_value=('type.googleapis.com/google.cloud.aiplatform'
                                  '.v1beta1.UploadModelResponse'))),
            self.messages.GoogleLongrunningOperation.ResponseValue
            .AdditionalProperty(
                key='model',
                value=extra_types.JsonValue(
                    string_value=(
                        'projects/fake-project/locations/us-central1/models/1'
                    ))),
        ])

  def _expectOperationPolling(self, operation_name):
    self.mock_client.projects_locations_operations.Get.Expect(
        request=self.messages.AiplatformProjectsLocationsOperationsGetRequest(
            name=operation_name),
        response=self.messages.GoogleLongrunningOperation(
            name=operation_name,
            done=True,
            response=self._buildUploadModelResponse()))

  def testUploadValidModelBeta(self):
    expected_request = self._buildUploadModelRequest()
    expected_lro = self.messages.GoogleLongrunningOperation(
        name='projects/fake-project/locations/us-central1/operations/1')
    self.mock_client.projects_locations_models.Upload.Expect(
        expected_request, response=expected_lro)
    self._expectOperationPolling(
        operation_name='projects/fake-project/locations/us-central1/operations/1'
    )
    response = self.RunCommandBeta(
        'upload', '--region=us-central1',
        '--container-image-uri=gcr.io/ucaip-test/ucaip-upload-model-test',
        '--description=description1', '--display-name=UploadModelUnitTest',
        '--artifact-uri=gs://test/1', '--container-args=ARG1,ARG2',
        '--container-command=COMMAND1,COMMAND2',
        '--container-env-vars=ENV1=VALUE1,ENV2=VALUE2',
        '--container-health-route=http://health_route',
        '--container-predict-route=http://predict_route',
        '--container-ports=8080,8000')
    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.assertEqual(response, self._buildUploadModelResponse())

  def testUploadValidModelNewOperationNameBeta(self):
    expected_request = self._buildUploadModelRequest()
    expected_lro = self.messages.GoogleLongrunningOperation(
        name='projects/fake-project/locations/us-central1/models/123/operations/1'
    )
    self.mock_client.projects_locations_models.Upload.Expect(
        expected_request, response=expected_lro)
    self._expectOperationPolling(
        operation_name='projects/fake-project/locations/us-central1/models/123/operations/1'
    )
    response = self.RunCommandBeta(
        'upload', '--region=us-central1',
        '--container-image-uri=gcr.io/ucaip-test/ucaip-upload-model-test',
        '--description=description1', '--display-name=UploadModelUnitTest',
        '--artifact-uri=gs://test/1', '--container-args=ARG1,ARG2',
        '--container-command=COMMAND1,COMMAND2',
        '--container-env-vars=ENV1=VALUE1,ENV2=VALUE2',
        '--container-health-route=http://health_route',
        '--container-predict-route=http://predict_route',
        '--container-ports=8080,8000')
    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.assertEqual(response, self._buildUploadModelResponse())
