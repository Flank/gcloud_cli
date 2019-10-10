# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the Cloud IoT Devices library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.edgeml import edgeml
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class EdgeMlTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                 sdk_test_base.WithLogCapture):

  def SetUp(self):
    self.client = mock.Client(
        client_class=apis.GetClientClass('edgeml', 'v1beta1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule('edgeml', 'v1beta1')
    self.edgeml_client = edgeml.EdgeMlClient(self.client, self.messages)

    self.saved_model_path = 'gs://my-bucket/my/model/saved_model.pbtxt'
    self.saved_model_path_dir = 'gs://my-bucket/my/model'
    self.tflite_model_path = 'gs://my-bucket/my/model.tflite'
    self.tflite_edgetpu_model_path = 'gs://my-bucket/my/model_edgetpu.tflite'

    self.project = 'projects/fake-project'

  def _InputConfig(self, uri):
    return self.messages.InputConfig(
        gcsSource=self.messages.GcsSource(inputUris=[uri]))

  def _OutputConfig(self, uri):
    return self.messages.OutputConfig(
        gcsDestination=self.messages.GcsDestination(outputUri=uri))

  def testCompileDestination(self):
    self.assertEqual(
        edgeml._CompileDestination(self.tflite_model_path),
        self.tflite_edgetpu_model_path)

  def testConvertDestination(self):
    self.assertEqual(
        edgeml._ConvertDestination(self.saved_model_path),
        self.tflite_model_path)
    self.assertEqual(
        edgeml._ConvertDestination(self.saved_model_path_dir),
        self.tflite_model_path)

  def testAnalyze(self):
    analyze_request = self.messages.EdgemlProjectsModelsAnalyzeRequest(
        analyzeModelRequest=self.messages.AnalyzeModelRequest(
            gcsSource=self.messages.GcsSource(
                inputUris=[self.tflite_model_path])),
        project=self.project)
    operation_id = 'analyze/100'
    operation_name = 'operations/analyze/100'
    analyze_operation = self.messages.Operation(name=operation_id)

    operation_request = self.messages.EdgemlOperationsGetRequest(
        name=operation_name)

    running_operation = self.messages.Operation(name=operation_name)

    finished_operation = self.messages.Operation(
        name=operation_name,
        done=True,
        response=self.messages.Operation.ResponseValue())

    self.client.projects_models.Analyze.Expect(analyze_request,
                                               analyze_operation)
    self.client.operations.Get.Expect(operation_request, running_operation)
    self.client.operations.Get.Expect(operation_request, finished_operation)
    result = self.edgeml_client.Analyze(self.tflite_model_path)

    self.assertIsInstance(result, self.messages.AnalyzeModelResponse)

  def testCompile(self):
    compile_req_type = self.messages.CompileModelRequest
    edgetpu_chiptype = compile_req_type.ChipTypeValueValuesEnum.EDGE_TPU_V1

    compile_request = self.messages.EdgemlProjectsModelsCompileRequest(
        compileModelRequest=compile_req_type(
            chipType=edgetpu_chiptype,
            inputConfig=self._InputConfig(self.tflite_model_path),
            outputConfig=self._OutputConfig(self.tflite_edgetpu_model_path)),
        project=self.project)
    operation_id = 'compile/100'
    operation_name = 'operations/compile/100'
    compile_operation = self.messages.Operation(name=operation_id)

    operation_request = self.messages.EdgemlOperationsGetRequest(
        name=operation_name)

    running_operation = self.messages.Operation(name=operation_name)

    finished_operation = self.messages.Operation(
        name=operation_name,
        done=True,
        response=self.messages.Operation.ResponseValue())

    self.client.projects_models.Compile.Expect(compile_request,
                                               compile_operation)
    self.client.operations.Get.Expect(operation_request, running_operation)
    self.client.operations.Get.Expect(operation_request, finished_operation)
    result, dest_uri = self.edgeml_client.Compile(self.tflite_model_path)

    self.assertIsInstance(result, self.messages.CompileModelResponse)
    self.assertEqual(dest_uri, self.tflite_edgetpu_model_path)

  def testConvert(self):
    convert_req_type = self.messages.ConvertModelRequest

    convert_request = self.messages.EdgemlProjectsModelsConvertRequest(
        convertModelRequest=convert_req_type(
            inputConfig=self._InputConfig(self.saved_model_path),
            outputConfig=self._OutputConfig(self.tflite_model_path)),
        project=self.project)
    operation_id = 'convert/100'
    operation_name = 'operations/convert/100'
    convert_operation = self.messages.Operation(name=operation_id)

    operation_request = self.messages.EdgemlOperationsGetRequest(
        name=operation_name)

    running_operation = self.messages.Operation(name=operation_name)

    finished_operation = self.messages.Operation(
        name=operation_name,
        done=True,
        response=self.messages.Operation.ResponseValue())

    self.client.projects_models.Convert.Expect(convert_request,
                                               convert_operation)
    self.client.operations.Get.Expect(operation_request, running_operation)
    self.client.operations.Get.Expect(operation_request, finished_operation)
    result, dest_uri = self.edgeml_client.Convert(self.saved_model_path)

    self.assertIsInstance(result, self.messages.ConvertModelResponse)
    self.assertEqual(dest_uri, self.tflite_model_path)

if __name__ == '__main__':
  test_case.main()
