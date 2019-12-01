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
"""ai-platform explain tests."""

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


class ExplainTestBase(object):

  def SetUp(self):
    self.mock_explain = self.StartObjectPatch(predict, 'Explain')
    self.command = '{} explain --model my_model'
    self.StartPatch('googlecloudsdk.command_lib.ml_engine.'
                    'predict_utilities.CheckRuntimeVersion',
                    return_value=False)

  def _RunWithInstances(self, contents, type_, module_name, version='v1'):
    command = self.command.format(module_name)

    if version:
      command += ' --version ' + version

    path = self.Touch(self.temp_path, 'instances.txt', contents=contents)
    command += ' --{}-instances '.format(type_) + path

    return self.Run(command)


@parameterized.parameters('ml-engine', 'ai-platform')
class ExplainArgumentsTest(ExplainTestBase):

  def testExplainModelRequired(self, module_name):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --model: Must be specified.'):
      self.Run('{} explain --text-instances=file.txt'.format(module_name))

  def testExplainInstancesRequired(self, module_name):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--json-instances | --text-instances) must be '
        'specified.'):
      self.Run('{} explain --model my_model'.format(module_name))

  def testExplainInstancesCannotSpecifyBoth(self, module_name):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --json-instances: Exactly one of (--json-instances | '
        '--text-instances) must be specified.'):
      self.Run('{} explain --model my_model '
               '--text-instances=instances.txt '
               '--json-instances=instances.json'.format(module_name))


@parameterized.parameters('ml-engine', 'ai-platform')
class ExplainTest(ExplainTestBase):

  _EXPLANATIONS = {
      'explanations': [
          {
              'attributions_by_label': [
                  {
                      'attributions': {
                          'x': [
                              -6.247829719784316,
                              -22.138859361882364,
                              56.97569988000004,
                              73.96156920619606
                          ]
                      },
                      'baseline_score': -10.312005,
                      'example_score': 93.5008316,
                      'label_index': 2,
                      'output_name': 'logit'
                  }
              ]
          }
      ]
  }
  _EXPLANATIONS_LIST = {
      'explanations': [
          {
              'attributions_by_label': [
                  {
                      'attributions': {
                          'x': [
                              -6.247829719784316,
                              -22.138859361882364,
                              56.97569988000004,
                              73.96156920619606
                          ]
                      },
                      'baseline_score': -10.312005,
                      'example_score': 93.5008316,
                      'label_index': 2,
                      'output_name': 'logit'
                  }
              ]
          },
          {
              'attributions_by_label': [
                  {
                      'attributions': {
                          'x': [
                              -6.247829719784316,
                              -22.138859361882364,
                              56.97569988000004,
                              73.96156920619606
                          ]
                      },
                      'baseline_score': -10.312005,
                      'example_score': 93.5008316,
                      'label_index': 2,
                      'output_name': 'logit'
                  }
              ]
          }
      ]
  }

  def SetUp(self):
    super(ExplainTest, self).SetUp()
    self.version_ref = resources.REGISTRY.Create('ml.projects.models.versions',
                                                 versionsId='v1',
                                                 modelsId='my_model',
                                                 projectsId=self.Project())

  def testExplainJsonInstances(self, module_name):
    self.mock_explain.return_value = self._EXPLANATIONS
    test_instances = '{"images": [0, 1], "key": 3}'
    self._RunWithInstances(test_instances, 'json', module_name)

    self.mock_explain.assert_called_once_with(self.version_ref,
                                              [{'images': [0, 1], 'key': 3}])

  def testExplainMultipleJsonInstances(self, module_name):
    self.mock_explain.return_value = self._EXPLANATIONS_LIST

    test_instances = ('{"images": [0, 1], "key": 3}\n'
                      '{"images": [3, 2], "key": 2}\n'
                      '{"images": [2, 1], "key": 1}')
    self._RunWithInstances(test_instances, 'json', module_name)

    self.mock_explain.assert_called_once_with(
        self.version_ref,
        [{'images': [0, 1], 'key': 3},
         {'images': [3, 2], 'key': 2},
         {'images': [2, 1], 'key': 1}])

  def testExplainNoVersion(self, module_name):
    self.mock_explain.return_value = self._EXPLANATIONS

    test_instances = '{"images": [0, 1], "key": 3}'
    self._RunWithInstances(test_instances, 'json', module_name, version=None)

    model_ref = resources.REGISTRY.Create('ml.projects.models',
                                          modelsId='my_model',
                                          projectsId=self.Project())
    self.mock_explain.assert_called_once_with(
        model_ref, [{'images': [0, 1], 'key': 3}])

  def testExplainEmptyFile(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'No valid instance was found.'):
      self._RunWithInstances('', 'json', module_name)

  def testExplainTooManyInstances(self, module_name):
    test_instances = '\n'.join(['{"images": [0, 1], "key": 3}'] * 101)
    with self.assertRaisesRegex(core_exceptions.Error, 'no more than 100'):
      self._RunWithInstances(test_instances, 'json', module_name)

  def testExplainNonJSON(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Input instances are not in JSON format.'):
      self._RunWithInstances('abcd', 'json', module_name)

  def testExplainTextFile(self, module_name):
    self.mock_explain.return_value = self._EXPLANATIONS

    self._RunWithInstances('2, 3', 'text', module_name)

    self.mock_explain.assert_called_once_with(self.version_ref, ['2, 3'])

  def testExplainTextFileMultipleInstances(self, module_name):
    self.mock_explain.return_value = self._EXPLANATIONS_LIST

    self._RunWithInstances('2, 3\n4, 5\n6, 7', 'text', module_name)

    self.mock_explain.assert_called_once_with(self.version_ref,
                                              ['2, 3', '4, 5', '6, 7'])

  def testExplainTextFileWithJson(self, module_name):
    self.mock_explain.return_value = self._EXPLANATIONS_LIST
    test_instances = ('{"images": [0, 1], "key": 3}\n'
                      '{"images": [3, 2], "key": 2}\n'
                      '{"images": [2, 1], "key": 1}')

    self._RunWithInstances(test_instances, 'text', module_name)

    self.mock_explain.assert_called_once_with(
        self.version_ref,
        ['{"images": [0, 1], "key": 3}',
         '{"images": [3, 2], "key": 2}',
         '{"images": [2, 1], "key": 1}'])

  def testExplainNewlineOnlyJson(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('\n', 'json', module_name)

  def testExplainNewlineOnlyText(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('\n', 'text', module_name)

  def testExplainEmptyLineJson(self, module_name):
    test_instances = '{"images": [0, 1], "key": 3}\n\n'
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances(test_instances, 'text', module_name)

  def testExplainEmptyLineText(self, module_name):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Empty line is not allowed'):
      self._RunWithInstances('2, 3\n\n', 'text', module_name)


@parameterized.parameters('ml-engine', 'ai-platform')
class ExplainFormattingTestBase(ExplainTestBase):

  def _RunWithResult(self, result, module_name, version='v1'):
    self.mock_explain.return_value = {'explanations': result}
    self._RunWithInstances('{}', 'json', module_name, version=version)
    version_ref = resources.REGISTRY.Create('ml.projects.models.versions',
                                            versionsId='v1',
                                            modelsId='my_model',
                                            projectsId=self.Project())
    self.mock_explain.assert_called_once_with(version_ref, [{}])

  def testNoExplanations(self, module_name):
    self._RunWithResult([], module_name=module_name)

    self.AssertOutputEquals('{\n  \"explanations\": []\n}\n')

  def testInvalidFormat(self, module_name):
    self.mock_explain.return_value = {'bad-key': []}

    self._RunWithInstances('{}', 'json', module_name)

    self.AssertOutputEquals('{\n"bad-key": []\n}\n', normalize_space=True)


class ExplainArgumentsBetaTest(ExplainArgumentsTest,
                               base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(ExplainArgumentsBetaTest, self).SetUp()


class ExplainBetaTest(ExplainTest, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(ExplainBetaTest, self).SetUp()


class ExplainFormattingBetaTest(ExplainFormattingTestBase,
                                base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(ExplainFormattingBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
