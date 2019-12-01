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
"""Tests for the command_lib.util.binary_operations module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import six


def GetOperationResult(command, stdout, stderr, status, failed):
  return binary_operations.BinaryBackedOperation.OperationResult(
      command_str=command,
      output=stdout,
      errors=stderr,
      status=status,
      failed=failed)


class CheckBinaryTests(parameterized.TestCase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.sdk_root_path = self.CreateTempDir('cloudsdk')
    self.StartObjectPatch(config.Paths, 'sdk_root', self.sdk_root_path)
    self.bin_path = os.path.join(self.sdk_root_path, 'bin')
    self.StartObjectPatch(config.Paths, 'sdk_bin_path', self.bin_path)
    installed = {'foo': 1, 'bar': 1}

    mock_updater = self.StartObjectPatch(
        update_manager, 'UpdateManager', autospec=True)
    mock_updater.return_value = update_manager.UpdateManager(
        sdk_root=self.sdk_root_path,
        url='file://some/path/components.json',
        warn=False)
    (mock_updater.return_value.GetCurrentVersionsInformation.return_value
    ) = installed

  @parameterized.named_parameters(('ComponentFound', 'foo', True),
                                  ('ComponentNotFound', 'baz', False))
  def testCheckBinaryComponentInstalled(self, target, expected):
    self.assertEqual(expected,
                     binary_operations.CheckBinaryComponentInstalled(target))

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
    with self.assertRaises(
        binary_operations.MissingExecutableException):
      binary_operations.CheckForInstalledBinary('myexc')


@test_case.Filters.DoNotRunInDebPackage('packaging does not contain test_data')
@test_case.Filters.DoNotRunInRpmPackage('packaging does not contain test_data')
class BinaryOperationsTests(parameterized.TestCase,
                            sdk_test_base.WithOutputCapture):

  class BasicBinaryOperation(binary_operations.BinaryBackedOperation):
    """Basic implementation. No default args, default IO and status handlers."""

    def _ParseArgsForCommand(self, string_val=None, int_val=None):
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

  def SetUp(self):
    """Configure test binary(ies)."""
    if test_case.Filters.IsOnWindows():
      suffix = 'win_go'
    elif test_case.Filters.IsOnMac():
      suffix = 'darwin_go'
    else:
      suffix = 'ubuntu_go'

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
    operation = self.BasicBinaryOperation(self.basic_binary)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a', 'foo', '-b',
        '1'
    ]
    expected_out = 'GOT value for -a foo\nGOT value for -b 1\n'
    expected_err = ''
    expected_status = 0
    expected_failed = False
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed)
    self.assertEqual(expected_result, operation(string_val='foo', int_val=1))

  def testBasicOperationSuccessResultWithDefaults(self):
    operation = self.BasicBinaryOperation(
        self.basic_binary, default_args={'b': 27})
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
    operation = self.BasicBinaryOperation(
        self.basic_binary,
        failure_func=binary_operations.NonZeroSuccessFailureHandler)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a', 'BAR', '-b',
        '1'
    ]
    expected_out = 'GOT value for -a BAR\nGOT value for -b 1\n'
    expected_err = ''
    expected_status = 1
    expected_failed = False
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed)
    self.assertEqual(expected_result, operation(string_val='BAR', int_val=1))

  def testBasicOperationFailureResult(self):
    operation = self.BasicBinaryOperation(self.basic_binary)
    command = [
        os.path.join(self.scripts_dir, self.basic_binary), '-a', '', '-b', '1'
    ]
    expected_out = ''
    expected_err = 'Parameter -a required.\n'
    expected_status = 1
    expected_failed = True
    expected_result = GetOperationResult(command, expected_out, expected_err,
                                         expected_status, expected_failed)
    self.assertEqual(expected_result, operation(string_val='', int_val=1))

  def testBasicOperationArgumentFailure(self):
    operation = self.BasicBinaryOperation(self.basic_binary)
    with self.assertRaisesRegexp(binary_operations.ArgumentError,
                                 'Invalid int_value bar'):
      operation(string_val='foo', int_val='bar')

  def testBasicOperationExecutionFailure(self):
    exec_patch = self.StartObjectPatch(execution_utils, 'Exec')
    exec_patch.side_effect = execution_utils.PermissionError('Bad Perms')
    operation = self.BasicBinaryOperation(self.basic_binary)
    with self.assertRaisesRegexp(binary_operations.ExecutionError, 'Bad Perms'):
      operation(string_val='foo', int_val=2)

  def testBasicOperationMissingCommand(self):
    with self.assertRaises(binary_operations.MissingExecutableException):
      self.BasicBinaryOperation('no_go')
