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
"""Tests for the command_lib.util.anthos.binary_operations module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import os

from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import six


def GetOperationResult(command, stdout, stderr, status, failed, context=None):
  if not context:
    context = {'env': None, 'exec_dir': None, 'stdin': None}
  return binary_operations.BinaryBackedOperation.OperationResult(
      command_str=command,
      output=stdout,
      errors=stderr,
      status=status,
      failed=failed,
      execution_context=context)


class CheckBinaryTests(parameterized.TestCase, sdk_test_base.WithLogCapture):

  def SetUp(self):
    self.sdk_root_path = self.CreateTempDir('cloudsdk')
    self.StartObjectPatch(config.Paths, 'sdk_root', self.sdk_root_path)
    self.bin_path = os.path.join(self.sdk_root_path, 'bin')
    self.StartObjectPatch(config.Paths, 'sdk_bin_path', self.bin_path)
    installed = {'foo': 1, 'bar': 1}

    self.mock_updater = self.StartObjectPatch(
        update_manager, 'UpdateManager', autospec=True)
    self.mock_updater.return_value = update_manager.UpdateManager(
        sdk_root=self.sdk_root_path,
        url='file://some/path/components.json',
        warn=False)
    (self.mock_updater.return_value.GetCurrentVersionsInformation.return_value
    ) = installed

  @parameterized.named_parameters(('ComponentFound', 'foo', True),
                                  ('ComponentNotFound', 'baz', False))
  def testCheckBinaryComponentInstalled(self, target, expected):
    self.assertEqual(expected,
                     binary_operations.CheckBinaryComponentInstalled(target))

  def testCheckBinaryComponentInstalledLocalError(self):
    self.mock_updater.side_effect = local_state.InvalidSDKRootError()

    self.assertIsNone(binary_operations.CheckBinaryComponentInstalled('foo'))
    self.AssertErrContains('Could not verify SDK install path.')

  def testCheckForInstalledBinaryAsComponent(self):
    component = binary_operations.CheckForInstalledBinary('foo')
    expected = os.path.join(self.bin_path, component)
    self.assertEqual(expected, component)

  def testCheckForInstalledBinaryOnPath(self):
    expected_path = os.path.join('/usr', 'bin', 'myexc')
    self.StartObjectPatch(
        files, 'FindExecutableOnPath', return_value=expected_path)
    self.assertEqual(expected_path,
                     binary_operations.CheckForInstalledBinary('myexc'))

  def testCheckForInstalledBinaryMissing(self):
    self.StartObjectPatch(files, 'FindExecutableOnPath', return_value=None)
    with self.assertRaisesRegex(
        binary_operations.MissingExecutableException, r'Not Found!!'):
      binary_operations.CheckForInstalledBinary('myexc', 'Not Found!!')


class BasicBinaryOperation(binary_operations.BinaryBackedOperation):
  """Basic implementation. No default args, default IO and status handlers."""

  def _ParseArgsForCommand(self, string_val=None, int_val=None, **kwargs):
    del kwargs  # Not used here, passed through.
    if int_val:
      try:
        int(int_val)
      except ValueError:
        raise binary_operations.ArgumentError(
            'Invalid int_value {}'.format(int_val))
    if self.defaults:
      arg1_val = self.defaults.get('a', string_val)
      arg2_val = self.defaults.get('b', int_val)
    else:
      arg1_val = string_val
      arg2_val = int_val

    return ['-a', arg1_val, '-b', six.text_type(arg2_val)]


class StreamingBinaryOperation(
    binary_operations.StreamingBinaryBackedOperation):
  """Simple Streaming implementation."""

  def _ParseArgsForCommand(self, string_val=None, int_val=None, **kwargs):
    del kwargs  # Not used here, passed through.
    if int_val:
      try:
        int(int_val)
      except ValueError:
        raise binary_operations.ArgumentError(
            'Invalid int_value {}'.format(int_val))
    if self.defaults:
      arg1_val = self.defaults.get('a', string_val)
      arg2_val = self.defaults.get('b', int_val)
    else:
      arg1_val = string_val
      arg2_val = int_val

    return ['-a', arg1_val, '-b', six.text_type(arg2_val)]


@test_case.Filters.DoNotRunInDebPackage('Given test binaries are grte which do '
                                        'not work on non google machines')
@test_case.Filters.DoNotRunInRpmPackage('Given test binaries are grte which do '
                                        'not work on non google machines')
class BinaryOperationsTests(parameterized.TestCase,
                            sdk_test_base.WithLogCapture):

  def SetUp(self):
    """Configure test binary(ies)."""
    if test_case.Filters.IsOnWindows():
      suffix = 'windows_go'
    elif test_case.Filters.IsOnMac():
      suffix = 'darwin_go'
    else:
      suffix = 'linux_go'

    self.basic_binary = 'basic_' + suffix
    self.sdk_root_path = self.CreateTempDir('cloudsdk')
    self.StartObjectPatch(config.Paths, 'sdk_root', self.sdk_root_path)
    self.scripts_dir = self.Resource('tests', 'unit', 'command_lib',
                                     'test_data', 'util', 'anthos')
    self.StartObjectPatch(config.Paths, 'sdk_bin_path', self.scripts_dir)
    installed = {self.basic_binary: 1}

    mock_updater = self.StartObjectPatch(
        update_manager, 'UpdateManager', autospec=True)
    mock_updater.return_value = update_manager.UpdateManager(
        sdk_root=self.sdk_root_path,
        url='file://some/path/components.json',
        warn=False)
    (mock_updater.return_value.GetCurrentVersionsInformation.return_value
    ) = installed

  def testBasicOperationSuccessResult(self):
    operation = BasicBinaryOperation(self.basic_binary)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a', 'foo', '-b',
        '1'
    ]
    context = {'env': {'FOO': 'bar'}, 'exec_dir': '.', 'stdin': 'input'}
    expected_out = 'GOT value for -a foo\nGOT value for -b 1\n'
    expected_err = ''
    expected_status = 0
    expected_failed = False
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed,
                                         context=context)
    actual_result = operation(string_val='foo',
                              int_val=1,
                              env={'FOO': 'bar'},
                              stdin='input',
                              execution_dir='.')
    self.assertEqual(expected_result, actual_result)

  def testBasicOperationSuccessResultWithDefaults(self):
    operation = BasicBinaryOperation(self.basic_binary, default_args={'b': 27})
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a', 'foo', '-b',
        '27'
    ]
    expected_out = 'GOT value for -a foo\nGOT value for -b 27\n'
    expected_err = ''
    expected_status = 0
    expected_failed = False
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed)
    self.assertEqual(expected_result, operation(string_val='foo'))

  def testBasicOperationSuccessResultWithNonZeroExit(self):
    operation = BasicBinaryOperation(
        self.basic_binary,
        failure_func=binary_operations.NonZeroSuccessFailureHandler)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary),
        '-a', 'EXIT_WITH_ERROR', '-b', '1'
    ]
    expected_out = 'GOT value for -a EXIT_WITH_ERROR\nGOT value for -b 1\n'
    expected_err = ''
    expected_status = 1
    expected_failed = False
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed)
    actual_result = operation(string_val='EXIT_WITH_ERROR', int_val=1)
    self.assertEqual(expected_result, actual_result)

  def testBasicOperationFailureResult(self):
    operation = BasicBinaryOperation(self.basic_binary)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a', '', '-b', '1'
    ]
    context = {'env': {'FOO': 'bar'}, 'exec_dir': '.', 'stdin': 'input'}
    expected_out = ''
    expected_err = 'Parameter -a required.\n'
    expected_status = 1
    expected_failed = True
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed,
                                         context=context)
    self.assertEqual(expected_result, operation(string_val='', int_val=1,
                                                show_exec_error=True,
                                                env={'FOO': 'bar'},
                                                stdin='input',
                                                execution_dir='.'))
    self.AssertLogContains('Error executing command')

  def testBasicOperationArgumentFailure(self):
    operation = BasicBinaryOperation(self.basic_binary)
    with self.assertRaisesRegexp(binary_operations.ArgumentError,
                                 'Invalid int_value bar'):
      operation(string_val='foo', int_val='bar')

  def testBasicOperationExecutionFailure(self):
    exec_patch = self.StartObjectPatch(execution_utils, 'Exec')
    exec_patch.side_effect = execution_utils.PermissionError('Bad Perms')
    operation = BasicBinaryOperation(self.basic_binary)
    with self.assertRaisesRegexp(binary_operations.ExecutionError, 'Bad Perms'):
      operation(string_val='foo', int_val=2)

  def testBasicOperationMissingExecutable(self):
    error_msgs = {
        'MISSING_EXEC': 'My Custom Message: [{}] not found'.format('no_go')
    }
    with self.assertRaisesRegex(binary_operations.MissingExecutableException,
                                r'My Custom Message: \[no_go\] not found'):
      BasicBinaryOperation('no_go', custom_errors=error_msgs)

  def testBasicOperationWorkingDirExecutable(self):
    operation = BasicBinaryOperation(self.basic_binary)
    with self.assertRaisesRegex(
        binary_operations.InvalidWorkingDirectoryError,
        r'Error executing command on \[.+\]. '
        r'Invalid Path \[NOT_REAL\]'):
      operation(string_val='foo', int_val=1, execution_dir='NOT_REAL')


@test_case.Filters.DoNotRunInDebPackage('packaging does not contain test_data')
@test_case.Filters.DoNotRunInRpmPackage('packaging does not contain test_data')
class StreamingBinaryOperationsTests(sdk_test_base.WithLogCapture,
                                     sdk_test_base.WithOutputCapture):

  def SetUp(self):
    """Configure test binary(ies)."""
    if test_case.Filters.IsOnWindows():
      suffix = 'windows_go'
    elif test_case.Filters.IsOnMac():
      suffix = 'darwin_go'
    else:
      suffix = 'linux_go'

    self.basic_binary = 'basic_' + suffix
    self.sdk_root_path = self.CreateTempDir('cloudsdk')
    self.StartObjectPatch(config.Paths, 'sdk_root', self.sdk_root_path)
    self.scripts_dir = self.Resource('tests', 'unit', 'command_lib',
                                     'test_data', 'util', 'anthos')
    self.StartObjectPatch(config.Paths, 'sdk_bin_path', self.scripts_dir)
    installed = {self.basic_binary: 1}

    mock_updater = self.StartObjectPatch(
        update_manager, 'UpdateManager', autospec=True)
    mock_updater.return_value = update_manager.UpdateManager(
        sdk_root=self.sdk_root_path,
        url='file://some/path/components.json',
        warn=False)
    (mock_updater.return_value.
     GetCurrentVersionsInformation.return_value) = installed

  def testStreamOperationResult_WithCapture(self):
    operation = StreamingBinaryOperation(self.basic_binary, capture_output=True)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a', 'LONG_OUTPUT',
        '-b', '10'
    ]
    context = {'env': {'FOO': 'bar'}, 'exec_dir': '.', 'stdin': 'input'}
    long_output = ['Output value {}'.format(x) for x in range(10)]
    expected_out = (['GOT value for -a LONG_OUTPUT', 'GOT value for -b 10'] +
                    long_output)
    expected_err = None
    expected_status = 0
    expected_failed = False
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed,
                                         context=context)
    actual_result = operation(string_val='LONG_OUTPUT',
                              int_val=10,
                              env={'FOO': 'bar'},
                              stdin='input',
                              execution_dir='.')
    for line in expected_out:
      self.AssertLogContains(line)
    self.AssertErrEquals('')
    self.assertEqual(expected_result, actual_result)

  def testStreamOperationResult_NoCapture(self):
    operation = StreamingBinaryOperation(self.basic_binary,
                                         capture_output=False)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a',
        'LONG_OUTPUT_W_ERRORS',
        '-b', '100'
    ]
    context = {'env': {'FOO': 'bar'}, 'exec_dir': '.', 'stdin': 'input'}
    expected_out = None
    expected_err = None
    expected_status = 0
    expected_failed = False
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed,
                                         context=context)
    actual_result = operation(string_val='LONG_OUTPUT_W_ERRORS',
                              int_val=100,
                              env={'FOO': 'bar'},
                              stdin='input',
                              execution_dir='.')
    self.assertEqual(expected_result, actual_result)
    long_output = ['Output value {}'.format(x) for x in range(10)]
    expected_log = (['GOT value for -a LONG_OUTPUT_W_ERRORS',
                     'GOT value for -b 100'] +
                    long_output)
    for line in expected_log:
      self.AssertLogContains(line)
    self.AssertErrContains(
        '\n'.join(('StdErr value {}'.format(x) for x in range(100))))

  def testStreamingOperationResult_WithNonZeroExit(self):
    # NOTE: MUST USE capture_output=True OR THIS WILL LOG AS A FAILURE
    operation = StreamingBinaryOperation(
        self.basic_binary,
        failure_func=binary_operations.NonZeroSuccessFailureHandler,
        capture_output=True)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a',
        'EXIT_WITH_ERROR', '-b', '1'
    ]
    expected_out = ['GOT value for -a EXIT_WITH_ERROR', 'GOT value for -b 1']
    expected_err = None
    expected_status = 1
    expected_failed = False
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed)
    actual_result = operation(string_val='EXIT_WITH_ERROR', int_val=1)
    self.assertEqual(expected_result, actual_result)
    self.AssertLogContains('GOT value for -a EXIT_WITH_ERROR')
    self.AssertLogContains('GOT value for -b 1')
    self.AssertErrEquals('')

  def testStreamingOperationFailureResult(self):
    operation = StreamingBinaryOperation(self.basic_binary)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a', '', '-b', '1'
    ]
    context = {'env': {'FOO': 'bar'}, 'exec_dir': '.', 'stdin': 'input'}
    expected_out = None
    expected_err = None
    expected_status = 1
    expected_failed = True
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed,
                                         context=context)
    self.assertEqual(expected_result, operation(string_val='', int_val=1,
                                                show_exec_error=True,
                                                env={'FOO': 'bar'},
                                                stdin='input',
                                                execution_dir='.'))
    self.AssertLogContains('Error executing command')
    self.AssertErrContains('Parameter -a required.')


if __name__ == '__main__':
  test_case.main()
