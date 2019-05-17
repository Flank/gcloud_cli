# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""ai-platform predict tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import predict
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base
from tests.lib.surface.ml_engine import predict_format_test_lib as format_test_data


class PredictTestBase(object):

  def SetUp(self):
    self.mock_predict = self.StartObjectPatch(predict, 'Predict')
    self.command = '{} predict --model my_model'

  def _RunWithInstances(self, contents, type_, module_name, version='v1'):
    command = self.command.format(module_name)

    if version:
      command += ' --version ' + version

    path = self.Touch(self.temp_path, 'instances.txt', contents=contents)
    command += ' --{}-instances '.format(type_) + path

    return self.Run(command)


@parameterized.parameters('ml-engine', 'ai-platform')
class PredictArgumentsTest(PredictTestBase):

  def testPredictModelRequired(self, module_name):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --model: Must be specified.'):
      self.Run('{} predict --text-instances=file.txt'.format(module_name))

  def testPredictInstancesRequired(self, module_name):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--json-instances | --text-instances) must be '
        'specified.'):
      self.Run('{} predict --model my_model'.format(module_name))

  def testPredictInstancesCannotSpecifyBoth(self, module_name):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --json-instances: Exactly one of (--json-instances | '
        '--text-instances) must be specified.'):
      self.Run('{} predict --model my_model '
               '--text-instances=instances.txt '
               '--json-instances=instances.json'.format(module_name))


@parameterized.parameters('ml-engine', 'ai-platform')
class PredictTest(PredictTestBase):

  _PREDICTIONS = {'predictions': [{'x': 1, 'y': 2}]}
  _PREDICTIONS_LIST = {'predictions': [1, 2, 3]}

  def SetUp(self):
    super(PredictTest, self).SetUp()
    self.version_ref = resources.REGISTRY.Create('ml.projects.models.versions',
                                                 versionsId='v1',
                                                 modelsId='my_model',
                                                 projectsId=self.Project())

  def testPredictJsonInstances(self, module_name):
    self.mock_predict.return_value = self._PREDICTIONS
    test_instances = '{"images": [0, 1], "key": 3}'
    self._RunWithInstances(test_instances, 'json', module_name)

    self.mock_predict.assert_called_once_with(self.version_ref,
                                              [{'images': [0, 1], 'key': 3}],
                                              signature_name=None)

  def testPredictMultipleJsonInstances(self, module_name):
    self.mock_predict.return_value = self._PREDICTIONS_LIST

    test_instances = ('{"images": [0, 1], "key": 3}\n'
                      '{"images": [3, 2], "key": 2}\n'
                      '{"images": [2, 1], "key": 1}')
    self._RunWithInstances(test_instances, 'json', module_name)

    self.mock_predict.assert_called_once_with(
        self.version_ref,
        [{'images': [0, 1], 'key': 3},
         {'images': [3, 2], 'key': 2},
         {'images': [2, 1], 'key': 1}],
        signature_name=None)

  def testPredictNoVersion(self, module_name):
    self.mock_predict.return_value = self._PREDICTIONS

    test_instances = '{"images": [0, 1], "key": 3}'
    self._RunWithInstances(test_instances, 'json', module_name, version=None)

    model_ref = resources.REGISTRY.Create('ml.projects.models',
                                          modelsId='my_model',
                                          projectsId=self.Project())
    self.mock_predict.assert_called_once_with(
        model_ref, [{'images': [0, 1], 'key': 3}], signature_name=None)

  def testPredictEmptyFile(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'No valid instance was found.'):
      self._RunWithInstances('', 'json', module_name)

  def testPredictTooManyInstances(self, module_name):
    test_instances = '\n'.join(['{"images": [0, 1], "key": 3}'] * 101)
    with self.assertRaisesRegex(core_exceptions.Error, 'no more than 100'):
      self._RunWithInstances(test_instances, 'json', module_name)

  def testPredictNonJSON(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Input instances are not in JSON format.'):
      self._RunWithInstances('abcd', 'json', module_name)

  def testPredictTextFile(self, module_name):
    self.mock_predict.return_value = self._PREDICTIONS

    self._RunWithInstances('2, 3', 'text', module_name)

    self.mock_predict.assert_called_once_with(self.version_ref, ['2, 3'],
                                              signature_name=None)

  def testPredictTextFileMultipleInstances(self, module_name):
    self.mock_predict.return_value = self._PREDICTIONS_LIST

    self._RunWithInstances('2, 3\n4, 5\n6, 7', 'text', module_name)

    self.mock_predict.assert_called_once_with(self.version_ref,
                                              ['2, 3', '4, 5', '6, 7'],
                                              signature_name=None)

  def testPredictTextFileWithJson(self, module_name):
    self.mock_predict.return_value = self._PREDICTIONS_LIST
    test_instances = ('{"images": [0, 1], "key": 3}\n'
                      '{"images": [3, 2], "key": 2}\n'
                      '{"images": [2, 1], "key": 1}')

    self._RunWithInstances(test_instances, 'text', module_name)

    self.mock_predict.assert_called_once_with(
        self.version_ref,
        ['{"images": [0, 1], "key": 3}',
         '{"images": [3, 2], "key": 2}',
         '{"images": [2, 1], "key": 1}'],
        signature_name=None)

  def testPredictSignatureName(self, module_name):
    self.command = ('{} predict --model my_model '
                    '--signature-name my-custom-signature')
    self.mock_predict.return_value = self._PREDICTIONS
    test_instances = '{"images": [0, 1], "key": 3}'
    self._RunWithInstances(test_instances, 'json', module_name)

    self.mock_predict.assert_called_once_with(
        self.version_ref,
        [{'images': [0, 1], 'key': 3}],
        signature_name='my-custom-signature')

  def testPredictNewlineOnlyJson(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('\n', 'json', module_name)

  def testPredictNewlineOnlyText(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('\n', 'text', module_name)

  def testPredictEmptyLineJson(self, module_name):
    test_instances = '{"images": [0, 1], "key": 3}\n\n'
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances(test_instances, 'text', module_name)

  def testPredictEmptyLineText(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('2, 3\n\n', 'text', module_name)


@parameterized.parameters('ml-engine', 'ai-platform')
class PredictFormattingTestBase(PredictTestBase):

  def _RunWithResult(self, result, module_name, version='v1'):
    self.mock_predict.return_value = {'predictions': result}
    self._RunWithInstances('{}', 'json', module_name, version=version)
    version_ref = resources.REGISTRY.Create('ml.projects.models.versions',
                                            versionsId='v1',
                                            modelsId='my_model',
                                            projectsId=self.Project())
    self.mock_predict.assert_called_once_with(version_ref, [{}],
                                              signature_name=None)

  def testNoPredictions(self, module_name):
    self._RunWithResult([], module_name=module_name)

    self.AssertOutputEquals('predictions: []\n')

  def testInvalidFormat(self, module_name):
    self.mock_predict.return_value = {'bad-key': []}

    self._RunWithInstances('{}', 'json', module_name)

    self.AssertOutputEquals('{\n"bad-key": []\n}\n', normalize_space=True)

  def testInvalidFormat2(self, module_name):
    result, testdata = format_test_data.PREDICT_SINGLE_VALUE_FORMAT_RESULT
    self._RunWithResult(testdata, module_name)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionDict(self, module_name):
    result, testdata = format_test_data.PREDICT_DICT_FORMAT_RESULT
    self._RunWithResult(testdata, module_name)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionDictOfLists(self, module_name):
    result, testdata = format_test_data.PREDICT_DICT_LIST_FORMAT_RESULT
    self._RunWithResult(testdata, module_name)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionDictOfListsOfFloats(self, module_name):
    result, testdata = format_test_data.PREDICT_DICT_LIST_FLOAT_FORMAT_RESULT
    self._RunWithResult(testdata, module_name)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionInts(self, module_name):
    result, testdata = format_test_data.PREDICT_LIST_INT_FORMAT_RESULT
    self._RunWithResult(testdata, module_name)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionFloats(self, module_name):
    result, testdata = format_test_data.PREDICT_LIST_FLOAT_FORMAT_RESULT
    self._RunWithResult(testdata, module_name)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionPredictionsInKeyName(self, module_name):
    result, testdata = format_test_data.PREDICT_IN_KEY_FORMAT_RESULT
    self._RunWithResult(testdata, module_name)
    self.AssertOutputEquals(result, normalize_space=True)


class PredictArgumentsGaTest(PredictArgumentsTest, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(PredictArgumentsGaTest, self).SetUp()


class PredictArgumentsBetaTest(PredictArgumentsTest,
                               base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(PredictArgumentsBetaTest, self).SetUp()


class PredictGaTest(PredictTest, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(PredictGaTest, self).SetUp()


class PredictBetaTest(PredictTest, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(PredictBetaTest, self).SetUp()


class PredictFormattingGaTest(PredictFormattingTestBase,
                              base.MlGaPlatformTestBase):

  def SetUp(self):
    super(PredictFormattingGaTest, self).SetUp()


class PredictFormattingBetaTest(PredictFormattingTestBase,
                                base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(PredictFormattingBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
