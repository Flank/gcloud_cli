# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for kuberun_command module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.command_lib.kuberun import kuberuncli
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
import mock


# The base class can't be instantiated on it's own because it is abstract,
# so testing is done against this class.
class TestCommand(kuberun_command.KubeRunCommand):
  flags = []

  def Command(self):
    return ['test']


class KubeRunCommandTest(sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.prompt_continue = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self.context = mock.Mock()
    self.cli = mock.Mock()
    self.executor = mock.Mock()
    self.get_env_args = self.StartObjectPatch(
        kuberuncli, 'GetEnvArgsForCommand')

    self.StartObjectPatch(
        TestCommand, 'CommandExecutor', return_value=self.executor)
    self.StartObjectPatch(TestCommand, 'flags', [MockFlag(['--foo', 'bar'])])
    self.command = TestCommand(self.cli, self.context)

  def testArgsWithOneFlag(self):
    # The default flags are configured in SetUp().
    parser = mock.Mock()
    self.command.Args(parser)
    TestCommand.flags[0].AddToParser.assert_called_once_with(parser)

  def testArgsWithMultipleFlags(self):
    TestCommand.flags = [MockFlag(['--one', '1']), MockFlag(['--two', '2'])]
    parser = mock.Mock()
    self.command.Args(parser)
    TestCommand.flags[0].AddToParser.assert_called_once_with(parser)
    TestCommand.flags[1].AddToParser.assert_called_once_with(parser)

  def testUserPromptedRegardingExperimental(self):
    args = mock.Mock()
    self.prompt_continue.side_effect = console_io.UnattendedPromptError

    with self.assertRaises(console_io.UnattendedPromptError):
      self.command.Run(args)

  def testSuccessfulExecution(self):
    args = mock.Mock()
    args.show_exec_error = True
    self.executor.return_value = (
        binary_operations.BinaryBackedOperation.OperationResult(
            'command', output='output'))
    result = self.command.Run(args)

    self.assertEqual(result, 'output')
    self.executor.assert_called_once_with(
        command=['test', '--foo', 'bar'],
        env=self.get_env_args.return_value,
        show_exec_error=True,
    )

  def testFailedExecution(self):
    args = mock.Mock()
    args.show_exec_error = True
    self.executor.return_value = (
        binary_operations.BinaryBackedOperation.OperationResult(
            'command', failed=True, status=1, output='output'))
    result = self.command.Run(args)

    self.assertIsNone(result)
    self.executor.assert_called_once_with(
        command=['test', '--foo', 'bar'],
        env=self.get_env_args.return_value,
        show_exec_error=True,
    )


class TestCommandWithOutput(kuberun_command.KubeRunCommandWithOutput):
  flags = []

  def Command(self):
    return ['test']

  def FormatOutput(self, out, args):
    return out


class KubeRunCommandWithOutputTest(sdk_test_base.WithFakeAuth):

  def testOperationResponseHandlerSuccess(self):
    command = TestCommandWithOutput(mock.Mock(), mock.Mock())
    self.StartObjectPatch(command, 'FormatOutput')
    response = binary_operations.BinaryBackedOperation.OperationResult(
        'command', output='stdout', errors='stderr')
    args = mock.Mock()

    result = command.OperationResponseHandler(response, args)
    self.assertEqual(result, command.FormatOutput.return_value)
    command.FormatOutput.assert_called_once_with('stdout', args)

  def testOperationResponseHandlerError(self):
    command = TestCommandWithOutput(mock.Mock(), mock.Mock())
    self.StartObjectPatch(command, 'FormatOutput')
    response = binary_operations.BinaryBackedOperation.OperationResult(
        'command', output='stdout', errors='stderr', failed=True)
    args = mock.Mock()

    with self.assertRaises(exceptions.Error):
      command.OperationResponseHandler(response, args)
    self.assertFalse(command.FormatOutput.called)


def MockFlag(format_flags_result):
  flag = mock.Mock(spec=flags.BinaryCommandFlag)
  flag.FormatFlags.return_value = format_flags_result
  return flag
