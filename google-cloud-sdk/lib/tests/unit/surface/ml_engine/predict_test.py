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
"""ml-engine predict tests."""
from googlecloudsdk.api_lib.ml_engine import predict
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.ml_engine import base
from tests.lib.surface.ml_engine import predict_format_test_lib as format_test_data


class PredictTestBase(object):

  def SetUp(self):
    self.mock_predict = self.StartObjectPatch(predict, 'Predict')
    self.command = 'ml-engine predict --model my_model'

  def _RunWithInstances(self, contents, type_, version='v1'):
    command = self.command

    if version:
      command += ' --version ' + version

    path = self.Touch(self.temp_path, 'instances.txt', contents=contents)
    command += ' --{}-instances '.format(type_) + path

    return self.Run(command)


class PredictArgumentsTest(PredictTestBase):

  def testPredictModelRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --model: Must be specified.'):
      self.Run('ml-engine predict --text-instances=file.txt')

  def testPredictInstancesRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--json-instances | --text-instances) must be '
        'specified.'):
      self.Run('ml-engine predict --model my_model')

  def testPredictInstancesCannotSpecifyBoth(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --json-instances: Exactly one of (--json-instances | '
        '--text-instances) must be specified.'):
      self.Run('ml-engine predict --model my_model '
               '--text-instances=instances.txt '
               '--json-instances=instances.json')


class PredictTest(PredictTestBase):

  _PREDICTIONS = {'predictions': [{'x': 1, 'y': 2}]}
  _PREDICTIONS_LIST = {'predictions': [1, 2, 3]}

  def SetUp(self):
    super(PredictTest, self).SetUp()
    self.version_ref = resources.REGISTRY.Create('ml.projects.models.versions',
                                                 versionsId='v1',
                                                 modelsId='my_model',
                                                 projectsId=self.Project())

  def testPredictJsonInstances(self):
    self.mock_predict.return_value = self._PREDICTIONS
    test_instances = '{"images": [0, 1], "key": 3}'
    self._RunWithInstances(test_instances, 'json')

    self.mock_predict.assert_called_once_with(self.version_ref,
                                              [{'images': [0, 1], 'key': 3}])

  def testPredictMultipleJsonInstances(self):
    self.mock_predict.return_value = self._PREDICTIONS_LIST

    test_instances = ('{"images": [0, 1], "key": 3}\n'
                      '{"images": [3, 2], "key": 2}\n'
                      '{"images": [2, 1], "key": 1}')
    self._RunWithInstances(test_instances, 'json')

    self.mock_predict.assert_called_once_with(
        self.version_ref,
        [{'images': [0, 1], 'key': 3},
         {'images': [3, 2], 'key': 2},
         {'images': [2, 1], 'key': 1}])

  def testPredictNoVersion(self):
    self.mock_predict.return_value = self._PREDICTIONS

    test_instances = '{"images": [0, 1], "key": 3}'
    self._RunWithInstances(test_instances, 'json', version=None)

    model_ref = resources.REGISTRY.Create('ml.projects.models',
                                          modelsId='my_model',
                                          projectsId=self.Project())
    self.mock_predict.assert_called_once_with(
        model_ref, [{'images': [0, 1], 'key': 3}])

  def testPredictEmptyFile(self):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'No valid instance was found.'):
      self._RunWithInstances('', 'json')

  def testPredictTooManyInstances(self):
    test_instances = '\n'.join(['{"images": [0, 1], "key": 3}'] * 101)
    with self.assertRaisesRegex(core_exceptions.Error, 'no more than 100'):
      self._RunWithInstances(test_instances, 'json')

  def testPredictNonJSON(self):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Input instances are not in JSON format.'):
      self._RunWithInstances('abcd', 'json')

  def testPredictTextFile(self):
    self.mock_predict.return_value = self._PREDICTIONS

    self._RunWithInstances('2, 3', 'text')

    self.mock_predict.assert_called_once_with(self.version_ref, ['2, 3'])

  def testPredictTextFileMultipleInstances(self):
    self.mock_predict.return_value = self._PREDICTIONS_LIST

    self._RunWithInstances('2, 3\n4, 5\n6, 7', 'text')

    self.mock_predict.assert_called_once_with(self.version_ref,
                                              ['2, 3', '4, 5', '6, 7'])

  def testPredictTextFileWithJson(self):
    self.mock_predict.return_value = self._PREDICTIONS_LIST
    test_instances = ('{"images": [0, 1], "key": 3}\n'
                      '{"images": [3, 2], "key": 2}\n'
                      '{"images": [2, 1], "key": 1}')

    self._RunWithInstances(test_instances, 'text')

    self.mock_predict.assert_called_once_with(
        self.version_ref,
        ['{"images": [0, 1], "key": 3}',
         '{"images": [3, 2], "key": 2}',
         '{"images": [2, 1], "key": 1}'])

  def testPredictNewlineOnlyJson(self):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('\n', 'json')

  def testPredictNewlineOnlyText(self):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('\n', 'text')

  def testPredictEmptyLineJson(self):
    test_instances = '{"images": [0, 1], "key": 3}\n\n'
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances(test_instances, 'text')

  def testPredictEmptyLineText(self):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('2, 3\n\n', 'text')


class PredictFormattingTestBase(PredictTestBase):

  def _RunWithResult(self, result, version='v1'):
    self.mock_predict.return_value = {'predictions': result}
    self._RunWithInstances('{}', 'json', version=version)
    version_ref = resources.REGISTRY.Create('ml.projects.models.versions',
                                            versionsId='v1',
                                            modelsId='my_model',
                                            projectsId=self.Project())
    self.mock_predict.assert_called_once_with(version_ref, [{}])

  def testNoPredictions(self):
    self._RunWithResult([])

    self.AssertOutputEquals('predictions: []\n')

  def testInvalidFormat(self):
    self.mock_predict.return_value = {'bad-key': []}

    self._RunWithInstances('{}', 'json')

    self.AssertOutputEquals('{\n"bad-key": []\n}\n', normalize_space=True)

  def testInvalidFormat2(self):
    result, testdata = format_test_data.PREDICT_SINGLE_VALUE_FORMAT_RESULT
    self._RunWithResult(testdata)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionDict(self):
    result, testdata = format_test_data.PREDICT_DICT_FORMAT_RESULT
    self._RunWithResult(testdata)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionDictOfLists(self):
    result, testdata = format_test_data.PREDICT_DICT_LIST_FORMAT_RESULT
    self._RunWithResult(testdata)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionDictOfListsOfFloats(self):
    result, testdata = format_test_data.PREDICT_DICT_LIST_FLOAT_FORMAT_RESULT
    self._RunWithResult(testdata)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionInts(self):
    result, testdata = format_test_data.PREDICT_LIST_INT_FORMAT_RESULT
    self._RunWithResult(testdata)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionFloats(self):
    result, testdata = format_test_data.PREDICT_LIST_FLOAT_FORMAT_RESULT
    self._RunWithResult(testdata)
    self.AssertOutputEquals(result, normalize_space=True)

  def testPredictionPredictionsInKeyName(self):
    result, testdata = format_test_data.PREDICT_IN_KEY_FORMAT_RESULT
    self._RunWithResult(testdata)
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
