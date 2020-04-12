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
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base
from tests.lib.surface.ml_engine import predict_format_test_lib as format_test_data

import mock
import six


@parameterized.parameters('ml-engine', 'ai-platform')
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

  JSON_REQUEST = textwrap.dedent("""\
      {
        "instances": [
          {"a": "b"},
          {"a": "c"}
        ]
      }
      """)
  JSON_REQUEST_INSTANCES = '{"a": "b"}\n{"a": "c"}\n'

  def SetUp(self):
    self.StartObjectPatch(
        files, 'SearchForExecutableOnPath', return_value=['/tmp/python'])
    self.StartPropertyPatch(
        config.Paths, 'sdk_root', return_value='fake-sdk-root')
    self.StartPatch('googlecloudsdk.command_lib.ml_engine.'
                    'predict_utilities.CheckRuntimeVersion',
                    return_value=False)

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

  def testLocalPredict_NoSdkRoot(self, module_name):
    self.StartObjectPatch(config.Paths, 'sdk_root',
                          mock.PropertyMock(return_value=None))
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)
    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'You must be running an installed Cloud SDK to perform local '
        'prediction.'):
      self.Run(('{} local predict '
                '--model-dir {} '
                '--json-instances {}').format(module_name, self.temp_path,
                                              instances_file))

  def testLocalPredict_NoPython(self, module_name):
    self.StartObjectPatch(files, 'SearchForExecutableOnPath', return_value=[])
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)
    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'Something has gone really wrong; we can\'t find a valid Python '
        'executable on your PATH.'):
      self.Run(('{} local predict '
                '--model-dir {} '
                '--json-instances {}').format(module_name, self.temp_path,
                                              instances_file))

  def testLocalPredict(self, module_name):
    popen_mock = self._MockPopen()
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    results = self.Run('{} local predict '
                       '--model-dir {} '
                       '--json-instances {}'.format(module_name, self.temp_path,
                                                    instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_WindowsLineBreaks(self, module_name):
    popen_mock = self._MockPopen()
    json_instances = '\r\n'.join(self.JSON_INSTANCES_UNNORMALIZED.split('\n'))
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=json_instances)

    results = self.Run('{} local predict '
                       '--model-dir {} '
                       '--json-instances {}'.format(module_name, self.temp_path,
                                                    instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_TextInstances(self, module_name):
    popen_mock = self._MockPopen()
    instances_file = self.Touch(self.temp_path, 'instances.txt',
                                contents=self.TEXT_INSTANCES_UNNORMALIZED)

    results = self.Run('{} local predict '
                       '--model-dir {} '
                       '--text-instances {}'.format(module_name, self.temp_path,
                                                    instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.TEXT_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_JsonRequest(self, module_name):
    popen_mock = self._MockPopen()
    request_file = self.Touch(self.temp_path, 'request.json',
                              contents=self.JSON_REQUEST)

    results = self.Run(
        '{} local predict '
        '--model-dir {} '
        '--json-request {}'.format(module_name, self.temp_path, request_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_REQUEST_INSTANCES)
    self.AssertErrNotContains('WARNING: warning!\n')

  def _RunFrameworkTest(self, framework, module_name):
    framework = framework.replace('-', '_')
    popen_mock = self._MockPopen()
    instances_file = self.Touch(self.temp_path, 'instances.txt',
                                contents=self.TEXT_INSTANCES_UNNORMALIZED)
    results = self.Run('{} local predict '
                       '--model-dir {} '
                       '--framework {} '
                       '--text-instances {}'.format(module_name, self.temp_path,
                                                    framework, instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.TEXT_INSTANCES_NORMALIZED,
                                     framework=framework)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_TensorFlowFramework(self, module_name):
    self._RunFrameworkTest('tensorflow', module_name)

  def testLocalPredict_XgboostFramework(self, module_name):
    self._RunFrameworkTest('xgboost', module_name)

  def testLocalPredict_ScikitLearnFramework(self, module_name):
    self._RunFrameworkTest('scikit-learn', module_name)

  def testLocalPredict_TextInstancesWindowsLineBreaks(self, module_name):
    popen_mock = self._MockPopen()
    text_instances = '\r\n'.join(self.TEXT_INSTANCES_UNNORMALIZED.split('\n'))
    instances_file = self.Touch(self.temp_path, 'instances.txt',
                                contents=text_instances)

    results = self.Run('{} local predict '
                       '--model-dir {} '
                       '--text-instances {}'.format(module_name, self.temp_path,
                                                    instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.TEXT_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_Error(self, module_name):
    popen_mock = self._MockPopen(returncode=1, stderr='error!')
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    with self.AssertRaisesExceptionMatches(core_exceptions.Error, 'error!'):
      self.Run('{} local predict '
               '--model-dir {} '
               '--json-instances {}'.format(module_name, self.temp_path,
                                            instances_file))

    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_Warning(self, module_name):
    popen_mock = self._MockPopen(returncode=0, stderr='warning!')
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    results = self.Run('{} local predict '
                       '--model-dir {} '
                       '--json-instances {}'.format(module_name, self.temp_path,
                                                    instances_file))

    self.assertEqual(results, [])
    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrContains('WARNING: warning!\n')

  def testLocalPredict_InvalidFormat(self, module_name):
    popen_mock = self._MockPopen(returncode=0, stdout='not json!')
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'The output for prediction is not in JSON format: not json!'):
      self.Run('{} local predict '
               '--model-dir {} '
               '--json-instances {}'.format(module_name, self.temp_path,
                                            instances_file))

    self._AssertPopenCalledCorrectly(popen_mock, self.JSON_INSTANCES_NORMALIZED)
    self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_InheritsEnvironment(self, module_name):
    with mock.patch.object(os, 'environ', new={'test_key': 'test_value'}):
      popen_mock = self._MockPopen()
      instances_file = self.Touch(self.temp_path, 'instances.json',
                                  contents=self.JSON_INSTANCES_UNNORMALIZED)

      results = self.Run('{} local predict '
                         '--model-dir {} '
                         '--json-instances {}'.format(
                             module_name, self.temp_path, instances_file))

      self.assertEqual(results, [])
      self._AssertPopenCalledCorrectly(popen_mock,
                                       self.JSON_INSTANCES_NORMALIZED,
                                       {'test_key': 'test_value'})
      self.AssertErrNotContains('WARNING: warning!\n')

  def testLocalPredict_SignatureName(self, module_name):
    popen_mock = self._MockPopen()
    instances_file = self.Touch(self.temp_path, 'instances.json',
                                contents=self.JSON_INSTANCES_UNNORMALIZED)

    results = self.Run('{} local predict '
                       '--model-dir {} '
                       '--json-instances {} '
                       '--framework tensorflow '
                       '--signature-name signature'.format(
                           module_name, self.temp_path, instances_file))

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


@parameterized.parameters('ml-engine', 'ai-platform')
class LocalPredictFormatTestBase(object):

  def _RunWithInstances(self, contents, type_, module_name):
    command = self.command.format(module_name)
    path = self.Touch(self.temp_path, 'instances.txt', contents=contents)
    command += ' --{}-instances '.format(type_) + path

    return self.Run(command)

  def _RunWithResult(self, result, module_name):
    self.mock_predict.return_value = {'predictions': result}
    self._RunWithInstances('{}', 'json', module_name)
    self.mock_predict.assert_called_once()

  def SetUp(self):
    self.mock_predict = self.StartObjectPatch(local_utils, 'RunPredict')
    self.command = '{} local predict --model-dir //fake/path '

  def testNoPredictions(self, module_name):
    self._RunWithResult([], module_name)

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
