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
"""e2e tests for ml local predict command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import subprocess

from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


def _VerifyLibIsInstalled(lib_name):
  """Checks whether a python library (module) needed for a test is installed.

  Args:
    lib_name: name of the library, e.g. `tensorflow`.

  Returns:
    A tuple for test skip decorators, consisting of two elements:
     - a boolean value to indicate whether the test should be skipped
     - a string with the reason for the skip, if any
  """

  python_executables = files.SearchForExecutableOnPath('python')
  if not python_executables:
    return False, 'No python executable available'
  python_executable = python_executables[0]
  command = [python_executable, '-c', 'import {}'.format(lib_name)]
  proc = subprocess.Popen(command,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = proc.communicate()
  if proc.returncode:
    # Something went wrong during module import
    return (
        False,
        (
            'Could not verify {lib} install.\n'
            'Python location: {python}\n'
            'Command to test: {command}\n'
            '----------------stdout----------------\n'
            '{stdout}'
            '----------------stderr----------------'
            '{stderr}'.format(lib=lib_name,
                              python=python_executable,
                              command=command,
                              stdout=stdout,
                              stderr=stderr)
        )
    )

  return True, ''


tensorflow_available, tensorflow_reason = _VerifyLibIsInstalled('tensorflow')
sklearn_available, sklearn_reason = _VerifyLibIsInstalled('sklearn')
xgboost_available, xgboost_reason = _VerifyLibIsInstalled('xgboost')


# If this test is skipped, we have very little effective coverage of this code
# path and it should be treated as a high-priority issue.
@sdk_test_base.Filters.RunOnlyInBundle
@test_case.Filters.RunOnlyIf(tensorflow_available, tensorflow_reason)
@parameterized.parameters('ml-engine', 'ai-platform')
class TensorflowPredictTest(base.MlGaPlatformTestBase):
  """e2e tests for ai-platform local predict command using tensorflow."""

  @property
  def model_path(self):
    return self.Resource('tests', 'e2e', 'surface', 'ai_platform', 'testdata',
                         'savedmodel')

  def testLocalPredict(self, module_name):
    json_instances = self.Resource('tests', 'e2e', 'surface', 'ai_platform',
                                   'testdata', 'predict_sample.tensor.json')

    results = self.Run('{} local predict '
                       '    --model-dir={} '
                       '    --json-instances={}'.format(
                           module_name, self.model_path, json_instances))
    self.assertEqual(list(results.keys()), ['predictions'])
    predictions = results['predictions']
    self.assertEqual(len(predictions), 10)
    expected_keys = set(['prediction', 'key', 'scores'])
    for prediction in predictions:
      self.assertSetEqual(set(prediction.keys()), expected_keys)


# If this test is skipped, we have very little effective coverage of this code
# path and it should be treated as a high-priority issue.
@sdk_test_base.Filters.RunOnlyInBundle
@test_case.Filters.RunOnlyIf(sklearn_available, sklearn_reason)
@parameterized.parameters('ml-engine', 'ai-platform')
class ScikitLearnPredictTest(base.MlGaPlatformTestBase):
  """e2e tests for ai-platform local predict command using scikit-learn."""

  @property
  def model_path(self):
    return self.Resource('tests', 'e2e', 'surface', 'ai_platform', 'testdata',
                         'scikit_learn_iris_model')

  def testLocalPredict(self, module_name):
    json_instances = self.Resource('tests', 'e2e', 'surface', 'ai_platform',
                                   'testdata', 'iris_model_input.json')

    results = self.Run('{} local predict '
                       '    --model-dir={} '
                       '    --framework=scikit-learn'
                       '    --json-instances={}'.format(
                           module_name, self.model_path, json_instances))

    # Prediction output should look something like the following:
    # {'predictions' : [2,2]}
    self.AssertOutputMatches('[2,2]')
    self.assertEqual(list(results.keys()), ['predictions'])
    predictions = results['predictions']
    self.assertEqual(len(predictions), 2)


# If this test is skipped, we have very little effective coverage of this code
# path and it should be treated as a high-priority issue.
@sdk_test_base.Filters.RunOnlyInBundle
@test_case.Filters.RunOnlyIf(xgboost_available, xgboost_reason)
@parameterized.parameters('ml-engine', 'ai-platform')
class XgboostPredictTest(base.MlGaPlatformTestBase):
  """e2e tests for ai-platform local predict command using xgboost."""

  @property
  def model_path(self):
    return self.Resource('tests', 'e2e', 'surface', 'ai_platform', 'testdata',
                         'xgboost_iris_model')

  def testLocalPredict(self, module_name):
    json_instances = self.Resource('tests', 'e2e', 'surface', 'ai_platform',
                                   'testdata', 'iris_model_input.json')

    results = self.Run('{} local predict '
                       '    --model-dir={} '
                       '    --framework=xgboost'
                       '    --json-instances={}'.format(
                           module_name, self.model_path, json_instances))

    self.AssertOutputMatches(
        r"""\[\[0.989785[e0-9-]+, 0.005485[e0-9-]+, 0.004728[e0-9-]+\],
        \[0.989785[e0-9-]+, 0.005485[e0-9-]+, 0.004728[e0-9-]+\]\]""",
        normalize_space=' \t\v\n')
    self.assertEqual(list(results.keys()), ['predictions'])
    predictions = results['predictions']
    self.assertEqual(len(predictions), 2)


if __name__ == '__main__':
  test_case.main()
