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
"""Base classes for anthos tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from googlecloudsdk.core import execution_utils as exec_utils
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import mock
from oauth2client import client

_MOCK_ANTHOS_BINARY = '/usr/bin/anthoscli'
_MOCK_ANTHOS_AUTH_BINARY = '/usr/bin/kubectl-anthos'


def GenerateOperationResponse(command,
                              output=None,
                              status=None,
                              is_error=False):
  """Create test OperationResult output."""
  if status is None:
    status = 1 if is_error else 0

  if is_error:
    return bin_ops.BinaryBackedOperation.OperationResult(
        command, errors=output, status=status, failed=True)
  return bin_ops.BinaryBackedOperation.OperationResult(
      command, output=output, status=status)


def ExecMock(args,
             env=None,
             no_exit=False,
             out_func=None,
             err_func=None,
             in_str=None,
             **extra_popen_kwargs):
  """Stub Implementation of execution_utils.Exec."""
  # We call this function instead of trying to find and invoke an actual binary
  # so that we can isolate and test the surface command interface only e.g.
  # argument parsing and processing up to the point the actual binary would be
  # invoked.
  del args, env, no_exit, err_func, in_str, extra_popen_kwargs
  out_func('Mock Output')
  return 0


class AnthosUnitTestBase(sdk_test_base.WithFakeAuth,
                         cli_test_base.CliTestBase):
  """Base class for all anthos tests."""

  def SetUp(self):
    self.moc_env_setter = self.StartObjectPatch(
        anthoscli_backend, 'GetEnvArgsForCommand',
        return_value={'COBRA_SILENCE_USAGE': 'true',
                      'GCLOUD_AUTH_PLUGIN': 'true'})
    self.mock_bin_exec = self.StartObjectPatch(
        exec_utils, 'ExecWithStreamingOutput',
        autospec=True, side_effect=ExecMock)
    self.mock_bin_check = self.StartObjectPatch(
        bin_ops, 'CheckForInstalledBinary', autospec=True)
    self.mock_athoscli_wrapper = mock.MagicMock(
        anthoscli_backend.AnthosCliWrapper, autospec=True)
    self.home_path = self.CreateTempDir('home')
    self.StartPatch('googlecloudsdk.core.util.files.GetHomeDir',
                    return_value=self.home_path)
    self.StartEnvPatch(
        {'ENV': '', 'HOME': self.home_path, 'SHELL': '/bin/bash'})
    self.refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                              'refresh')

  def AssertValidBinaryCall(self,
                            command_args,
                            std_in=None,
                            env=None,
                            working_dir=None):
    self.mock_bin_exec.assert_called_once_with(
        args=command_args,
        cwd=working_dir or mock.ANY,
        env=env or mock.ANY,
        in_str=std_in or mock.ANY,
        no_exit=True,
        err_func=mock.ANY,
        out_func=mock.ANY)


class PackageUnitTestBase(AnthosUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.mock_bin_check.return_value = _MOCK_ANTHOS_BINARY


class AuthUnitTestBase(AnthosUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.mock_bin_exec = self.StartObjectPatch(
        exec_utils, 'Exec',
        autospec=True, side_effect=ExecMock)
    self.mock_bin_check.return_value = _MOCK_ANTHOS_AUTH_BINARY
