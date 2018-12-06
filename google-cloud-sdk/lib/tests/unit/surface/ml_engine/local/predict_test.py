# -*- coding: utf-8 -*- #
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
"""Unit tests for local prediction.

Mocks subprocess; everything else is an integration test.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import subprocess
import textwrap

from googlecloudsdk.command_lib.ml_engine import local_predict
from googlecloudsdk.command_lib.ml_engine import local_utils
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.ml_engine import base
from tests.lib.surface.ml_engine import predict_format_test_lib as format_test_data

import mock
import six


class LocalPredictTestBase(object):

  JSON_INSTANCES_UNNORMALIZED = textwrap.dedent("""\
      {"a": "b"}
      {"a":    "c"}
      """)
  # Normalized spacing/printing
  JSON_INSTANCES_NORMALIZED = '{"a": "b"}\n{"a": "c"}\n'

  TEXT_INSTANCES_UNNORMALIZED = textwrap.dedent("""\
      foo
      bar
      baz
      """)
  TEXT_INSTANCES_NORMALIZED = '"foo"\n"bar"\n"baz"\n'

  def SetUp(self):
    self.StartObjectPatch(
        files, 'SearchForExecutableOnPath', return_value=['/tmp/python'])
    self.StartPropertyPatch(
        config.Paths, 'sdk_root', return_value='fake-sdk-root')

  def _MockPopen(self, returncode=0, stdout='[]\n', stderr=''):
    popen_mock = mock.MagicMock()
    popen_mock.stdin = io.BytesIO()
    popen_mock.communicate.return_value = (stdout, stderr)
    popen_mock.returncode = returncode
    return self.StartObjectPatch(
        subprocess, 'Popen', return_value=popen_mock, autospec=True)

  def _AssertPopenCalledCorrectly(self, popen_mock, instances,
                                  additional_env=None,
                                  framework='tensorflow',
                                  additional_python_args=None):
    expected_env = {'CLOUDSDK_ROOT': 'fake-sdk-root'}
    if additional_env:
      expected_env.update(additional_env)
    expected_command = ['/tmp/python', local_predict.__file__,
                        '--model-dir', self.temp_path,
                        '--framework', framework]
    if additional_python_args:
      expected_command += additional_python_args

    # On py3, some core library uses popen to call uname which throws off the
    # assertion.
    calls = [args for args in popen_mock.call_args_list
             if isinstance(args[0][0], list)
             or not args[0][0].startswith('uname')]
    self.assertEqual(len(calls), 1)
    args, kwargs = calls[0]
    self.assertEqual(args[0], expected_command)
    self.assertEqual(set(kwargs.keys()), {'stdout', 'stderr', 'stdin', 'env'})
    self.assertEqual(kwargs['stdout'], subprocess.PIPE)
    self.assertEqual(kwargs['stderr'], subprocess.PIPE)
    self.assertEqual(kwargs['stdin'], subprocess.PIPE)
    self.assertDictContainsSubset(expected_env, kwargs['env'])

    stdin_value = popen_mock.return_value.stdin.getvalue()
    if isinstance(stdin_value, six.binary_type):
      # In Python 3, getvalue() returns bytes, while in Python 2, it returns
      # text.
      stdin_value = stdin_value.decode('utf-8')
    self.assertEqual(stdin_value, instances)

  def testLocalPredict_NoSdkRoot(self):
    self.StartObjectPatch(config.Paths, 'sdk_root',
                          mock.PropertyMock(return_value=None))
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)
    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'You must be running an installed Cloud SDK to perform local '
        'prediction.'):
      self.Run(
          ('ml-engine local predict '
           '--model-dir {} '
           '--json-instances {}').format(self.temp_path, instances_file))

  def testLocalPredict_NoPython(self):
    self.StartObjectPatch(files, 'SearchForExecutableOnPath', return_value=[])
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)
    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'Something has gone really wrong; we can\'t find a valid Python '
        'executable on your PATH.'):
      self.Run(
          ('ml-engine local predict '
           '--model-dir {} '
           '--json-instances {}').format(self.temp_path, instances_file))

  def testLocalPredict(self):
    popen_mock = self._MockPopen()
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    results = self.Run(
        'ml-engine local predict '
        '--model-dir {} '
        '--json-instances {}'.format(self.temp_path, instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_WindowsLineBreaks(self):
    popen_mock = self._MockPopen()
    json_instances = '\r\n'.join(self.JSON_INSTANCES_UNNORMALIZED.split('\n'))
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=json_instances)

    results = self.Run(
        'ml-engine local predict '
        '--model-dir {} '
        '--json-instances {}'.format(self.temp_path, instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_TextInstances(self):
    popen_mock = self._MockPopen()
    instances_file = self.Touch(self.temp_path, 'instances.txt',
                                contents=self.TEXT_INSTANCES_UNNORMALIZED)

    results = self.Run(
        'ml-engine local predict '
        '--model-dir {} '
        '--text-instances {}'.format(self.temp_path, instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.TEXT_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def _RunFrameworkTest(self, framework):
    framework = framework.replace('-', '_')
    popen_mock = self._MockPopen()
    instances_file = self.Touch(self.temp_path, 'instances.txt',
                                contents=self.TEXT_INSTANCES_UNNORMALIZED)
    results = self.Run(
        'ml-engine local predict '
        '--model-dir {} '
        '--framework {} '
        '--text-instances {}'.format(self.temp_path, framework, instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.TEXT_INSTANCES_NORMALIZED,
                                     framework=framework)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_TensorFlowFramework(self):
    self._RunFrameworkTest('tensorflow')

  def testLocalPredict_XgboostFramework(self):
    self._RunFrameworkTest('xgboost')

  def testLocalPredict_ScikitLearnFramework(self):
    self._RunFrameworkTest('scikit-learn')

  def testLocalPredict_TextInstancesWindowsLineBreaks(self):
    popen_mock = self._MockPopen()
    text_instances = '\r\n'.join(self.TEXT_INSTANCES_UNNORMALIZED.split('\n'))
    instances_file = self.Touch(self.temp_path, 'instances.txt',
                                contents=text_instances)

    results = self.Run(
        'ml-engine local predict '
        '--model-dir {} '
        '--text-instances {}'.format(self.temp_path, instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.TEXT_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_Error(self):
    popen_mock = self._MockPopen(returncode=1, stderr='error!')
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    with self.AssertRaisesExceptionMatches(core_exceptions.Error, 'error!'):
      self.Run(
          'ml-engine local predict '
          '--model-dir {} '
          '--json-instances {}'.format(self.temp_path, instances_file))

    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_Warning(self):
    popen_mock = self._MockPopen(returncode=0, stderr='warning!')
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    results = self.Run(
        'ml-engine local predict '
        '--model-dir {} '
        '--json-instances {}'.format(self.temp_path, instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrContains('WARNING: warning!\n')

  def testLocalPredict_InvalidFormat(self):
    popen_mock = self._MockPopen(returncode=0, stdout='not json!')
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'The output for prediction is not in JSON format: not json!'):
      self.Run(
          'ml-engine local predict '
          '--model-dir {} '
          '--json-instances {}'.format(self.temp_path, instances_file))

    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_InheritsEnvironment(self):
    with mock.patch.object(os, 'environ', new={'test_key': 'test_value'}):
      popen_mock = self._MockPopen()
      instances_file = self.Touch(self.temp_path, 'instances.json',
                                  contents=self.JSON_INSTANCES_UNNORMALIZED)

      results = self.Run(
          'ml-engine local predict '
          '--model-dir {} '
          '--json-instances {}'.format(self.temp_path, instances_file))

      self.assertEqual(results, [])
      self._AssertPopenCalledCorrectly(popen_mock,
                                       self.JSON_INSTANCES_NORMALIZED,
                                       {'test_key': 'test_value'})
      self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_SignatureName(self):
    popen_mock = self._MockPopen()
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    results = self.Run(
        'ml-engine local predict '
        '--model-dir {} '
        '--json-instances {} '
        '--framework tensorflow '
        '--signature-name signature'.format(self.temp_path, instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED,
                                     additional_python_args=['--signature-name',
                                                             'signature'])
    self.AssertErrNotContains('WARNING: warning!\n')


class LocalPredictGaTest(LocalPredictTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(LocalPredictGaTest, self).SetUp()


class LocalPredictBetaTest(LocalPredictTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(LocalPredictBetaTest, self).SetUp()


class LocalPredictFormatTestBase(object):

  def _RunWithInstances(self, contents, type_):
    command = self.command
    path = self.Touch(self.temp_path, 'instances.txt', contents=contents)
    command += ' --{}-instances '.format(type_) + path

    return self.Run(command)

  def _RunWithResult(self, result):
    self.mock_predict.return_value = {'predictions': result}
    self._RunWithInstances('{}', 'json')
    self.mock_predict.assert_called_once()

  def SetUp(self):
    self.mock_predict = self.StartObjectPatch(local_utils, 'RunPredict')
    self.command = 'ml-engine local predict --model-dir //fake/path '

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


class LocalPredictGaFormatTest(LocalPredictFormatTestBase,
                               base.MlGaPlatformTestBase):

  def SetUp(self):
    super(LocalPredictGaFormatTest, self).SetUp()


class LocalPredictBetaFormatTest(LocalPredictFormatTestBase,
                                 base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(LocalPredictBetaFormatTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()

