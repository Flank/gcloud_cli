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
"""Base classes for kuberun tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import domainmapping
from googlecloudsdk.api_lib.kuberun import revision
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.kuberun import kuberuncli
from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from googlecloudsdk.core import execution_utils as exec_utils
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import mock
from oauth2client import client

_MOCK_BINARY = '/usr/bin/kuberun'


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


class KubeRunUnitTestBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):
  """Base class for all kuberun tests."""

  def SetUp(self):
    self.moc_env_setter = self.StartObjectPatch(
        kuberuncli, 'GetEnvArgsForCommand',
        return_value={'CLOUDSDK_PROJECT': 'true',
                      'CLOUDSDK_AUTH_TOKEN': 'true'})
    self.mock_bin_exec = self.StartObjectPatch(
        exec_utils, 'Exec',
        autospec=True, side_effect=ExecMock)
    self.mock_bin_check = self.StartObjectPatch(
        bin_ops, 'CheckForInstalledBinary', autospec=True)
    self.home_path = self.CreateTempDir('home')
    self.refresh_mock = self.StartObjectPatch(client.OAuth2Credentials,
                                              'refresh')
    self.mock_bin_exec = self.StartObjectPatch(bin_ops.BinaryBackedOperation,
                                               '_Execute')
    self.addTypeEqualityFunc(revision.Revision, self.props_compare)
    self.addTypeEqualityFunc(domainmapping.DomainMapping, self.props_compare)

  def AssertExecuteCalledOnce(self, command_args):
    """Assert one call to bin_ops.BinaryBackedOperation._Execute."""
    self.mock_bin_exec.assert_called_once_with(
        [_MOCK_BINARY] + command_args,
        command=mock.ANY,
        env={
            'CLOUDSDK_PROJECT': 'true',
            'CLOUDSDK_AUTH_TOKEN': 'true'
        },
        show_exec_error=False)

  def props_compare(self, obj1, obj2, msg=None):
    return self.assertEqual(obj1.props, obj2.props)


class PackageUnitTestBase(KubeRunUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.Run('config set kuberun/enable_experimental_commands true')
    self.mock_bin_check.return_value = _MOCK_BINARY
