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
"""Tests for tests.unit.command_lib.iot.edge.ml.util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import json

from apitools.base.py import encoding_helper

from googlecloudsdk.api_lib.edgeml import edgeml
from googlecloudsdk.command_lib.iot.edge.ml import util

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.edge import base

import mock


class MlUtilTest(base.CloudIotEdgeBase, parameterized.TestCase):

  def SetUp(self):
    """Sets up tensor info and other predefined values for testing."""
    self.input_tensor_refs = self._DictToTensorRef([
        {
            'index': 1,
            'tensorInfo': {
                'dimensions': [1, 224, 224, 3],
                'inferenceType': 'QUANTIZED_UINT_8',
                'tensorName': 'input_1'
            }
        },
        {
            'index': 0,
            'tensorInfo': {
                'dimensions': [1, 100],
                'inferenceType': 'FLOAT_32',
                'tensorName': 'input_2'
            }
        },
    ])
    self.output_tensor_refs = self._DictToTensorRef([
        {
            'index': 0,
            'tensorInfo': {
                'dimensions': [1, 1001],
                'inferenceType': 'QUANTIZED_UINT_8',
                'tensorName': 'softmax'
            }
        },
    ])

    self.model_signature = self.edgeml_messages.ModelSignature(
        inputTensors=self.input_tensor_refs,
        outputTensors=self.output_tensor_refs)

    self.expected_input_tensor_infos = [
        {
            'index': 1,
            'dimensions': [1, 224, 224, 3],
            'inferenceType': 'QUANTIZED_UINT_8',
            'tensorName': 'input_1'
        },
        {
            'index': 0,
            'dimensions': [1, 100],
            'inferenceType': 'FLOAT_32',
            'tensorName': 'input_2'
        },
    ]
    self.expected_output_tensor_infos = [
        {
            'index': 0,
            'dimensions': [1, 1001],
            'inferenceType': 'QUANTIZED_UINT_8',
            'tensorName': 'softmax'
        },
    ]
    self.sklearn_model_path = 'gs://my-bucket/my/sklearn_model.tar.gz'
    self.saved_model_path = 'gs://my-bucket/my/model/saved_model.pbtxt'
    self.tflite_model_path = 'gs://my-bucket/my/model.tflite'
    self.tflite_edgetpu_model_path = 'gs://my-bucket/my/model_edgetpu.tflite'

    self.parent = ('projects/fake-project/locations/asia-east1/'
                   'registries/my-registry/devices/my-device')
    self.ml_model_name = 'foo'
    self.full_ml_model_name = (
        'projects/fake-project/locations/asia-east1/'
        'registries/my-registry/devices/my-device/mlModels/foo')
    self.ml_model_ref = self.resources.Parse(
        self.full_ml_model_name,
        collection='edge.projects.locations.registries.devices.mlModels')

    self.project = 'projects/fake-project'

    self.model_type = (
        self.edgeml_messages.AnalyzeModelResponse.ModelTypeValueValuesEnum)
    self.framework_type = self.messages.MlModel.FrameworkValueValuesEnum
    self.accelerator_type = self.messages.MlModel.AcceleratorTypeValueValuesEnum

    self.edgetpu_compilable = self.edgeml_messages.EdgeTpuCompilability(
        compilableReason=self.edgeml_messages.
        EdgeTpuCompilability.CompilableReasonValueValuesEnum.COMPILABLE)

  def _GcsSource(self, uri):
    """Makes GcsSource message from a single URI."""
    return self.edgeml_messages.GcsSource(inputUris=[uri])

  def _CreateRequestWithUri(self, uri):
    """Makes MlModelCreateRequest with pre-filled modelUri field."""
    req_type = (
        self.messages
        .EdgeProjectsLocationsRegistriesDevicesMlModelsCreateRequest)
    req = req_type(
        mlModel=self.messages.MlModel(
            name=self.full_ml_model_name, modelUri=uri),
        parent=self.parent)
    return req

  @mock.patch('googlecloudsdk.api_lib.edgeml.util.GetClientInstance')
  def testProcessModelHookSklearn(self, unused_mock_client):
    """For Scikit-learn model, only analyze method is expected to be called."""
    analyze_response = self.edgeml_messages.AnalyzeModelResponse(
        modelType=self.model_type.NON_TENSORFLOW_MODEL)

    request = self._CreateRequestWithUri(self.sklearn_model_path)
    request.mlModel.framework = self.framework_type.SCIKIT_LEARN

    with mock.patch.object(edgeml.EdgeMlClient, 'Analyze') as mock_analyze:
      mock_analyze.return_value = analyze_response
      result_req = util.ProcessModelHook(self.ml_model_ref,
                                         argparse.Namespace(), request)
      mock_analyze.assert_called_once_with(self.sklearn_model_path)
      self.assertEqual(result_req.mlModel.modelUri, self.sklearn_model_path)

  @mock.patch('googlecloudsdk.api_lib.edgeml.util.GetClientInstance')
  @mock.patch('googlecloudsdk.api_lib.edgeml.util.GetMessagesModule')
  def testProcessModelHookTfLiteCompile(
      self, mock_edgeml_messages, unused_mock_client):
    """For Tflite model and tpu provided, analyze and compile are called."""
    mock_edgeml_messages.return_value = self.edgeml_messages
    analyze_response = self.edgeml_messages.AnalyzeModelResponse(
        modelType=self.model_type.TENSORFLOW_LITE,
        edgeTpuCompilability=self.edgetpu_compilable,
        modelSignature=self.model_signature)

    compile_response = self.edgeml_messages.CompileModelResponse(
        modelSignature=self.model_signature)

    request = self._CreateRequestWithUri(self.tflite_model_path)
    request.mlModel.framework = self.framework_type.TFLITE

    with mock.patch.object(edgeml.EdgeMlClient, 'Analyze') as mock_analyze:
      with mock.patch.object(edgeml.EdgeMlClient, 'Compile') as mock_compile:
        mock_analyze.return_value = analyze_response
        mock_compile.return_value = (
            compile_response, self.tflite_edgetpu_model_path)

        args = argparse.Namespace(accelerator='tpu')
        args.IsSpecified = lambda arg_name: arg_name == '--accelerator'
        result_req = util.ProcessModelHook(self.ml_model_ref, args, request)

        mock_analyze.assert_called_once_with(self.tflite_model_path)
        mock_compile.assert_called_once_with(self.tflite_model_path)
        self.assertEqual(result_req.mlModel.modelUri,
                         self.tflite_edgetpu_model_path)
        self.assertEqual(
            self._TensorInfoToDict(result_req.mlModel.inputTensors),
            self.expected_input_tensor_infos)
        self.assertEqual(
            self._TensorInfoToDict(result_req.mlModel.outputTensors),
            self.expected_output_tensor_infos)

  @mock.patch('googlecloudsdk.api_lib.edgeml.util.GetClientInstance')
  @mock.patch('googlecloudsdk.api_lib.edgeml.util.GetMessagesModule')
  def testProcessModelHookTensorflowSavedModel(
      self, mock_edgeml_messages, unused_mock_client):
    """For Tensorflow SavedModel, analyze and convert are called."""
    mock_edgeml_messages.return_value = self.edgeml_messages
    analyze_response = self.edgeml_messages.AnalyzeModelResponse(
        modelType=self.model_type.TENSORFLOW_SAVED_MODEL)

    convert_response = self.edgeml_messages.ConvertModelResponse(
        edgeTpuCompilability=self.edgetpu_compilable,
        modelSignature=self.model_signature)

    request = self._CreateRequestWithUri(self.saved_model_path)
    request.mlModel.framework = self.framework_type.TFLITE

    with mock.patch.object(edgeml.EdgeMlClient, 'Analyze') as mock_analyze:
      with mock.patch.object(edgeml.EdgeMlClient, 'Convert') as mock_convert:
        mock_analyze.return_value = analyze_response
        mock_convert.return_value = (convert_response, self.tflite_model_path)

        args = argparse.Namespace(accelerator='cpu')
        result_req = util.ProcessModelHook(self.ml_model_ref, args, request)

        mock_analyze.assert_called_once_with(self.saved_model_path)
        mock_convert.assert_called_once_with(self.saved_model_path)
        self.assertEqual(result_req.mlModel.modelUri, self.tflite_model_path)
        self.assertEqual(
            self._TensorInfoToDict(result_req.mlModel.inputTensors),
            self.expected_input_tensor_infos)
        self.assertEqual(
            self._TensorInfoToDict(result_req.mlModel.outputTensors),
            self.expected_output_tensor_infos)

  def _DictToTensorRef(self, dicts):
    """Converts list of dictionaries to list of edgeml.TensorRef[]."""
    tensor_ref_type = self.edgeml_messages.TensorRef
    return [
        encoding_helper.JsonToMessage(tensor_ref_type, json.dumps(dic))
        for dic in dicts
    ]

  def _TensorInfoToDict(self, messages):
    """Converts edge.TensorInfo[] to list of dictionaries."""
    return [json.loads(encoding_helper.MessageToJson(m)) for m in messages]

  def testConvertTensorRef(self):
    """Tests converting edgeml.TensorRef[] to edge.TensorInfo[]."""

    actual_tensor_infos = util._ConvertTensorRef(self.input_tensor_refs)
    self.assertEqual(
        self._TensorInfoToDict(actual_tensor_infos),
        self.expected_input_tensor_infos)

  def testFillModelSignature(self):
    """Tests filling model with modelSignature."""
    model = self.messages.MlModel()
    util._FillModelSignature(model, self.model_signature)
    self.assertEqual(
        self._TensorInfoToDict(model.inputTensors),
        self.expected_input_tensor_infos)
    self.assertEqual(
        self._TensorInfoToDict(model.outputTensors),
        self.expected_output_tensor_infos)

if __name__ == '__main__':
  test_case.main()
