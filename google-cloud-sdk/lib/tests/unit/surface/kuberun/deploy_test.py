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
"""kuberun surface services update tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from tests.lib import parameterized
from tests.lib.surface.kuberun import test_base


class DeployTest(test_base.PackageUnitTestBase, parameterized.TestCase):

  def SetUp(self):
    self.mock_bin_exec = self.StartObjectPatch(
        bin_ops.StreamingBinaryBackedOperation, '_Execute')

  def testDeploy(self):
    command = 'kuberun deploy'
    expected_out = 'Deploying 1 components in application'
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command, output=expected_out))

    result = self.Run(command)

    self.AssertExecuteCalledOnce(command_args=['deploy'])
    self._AssertContains(expected_out, result, 'result')

  def testDeploy_Fail(self):
    command = 'kuberun deploy'
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command, errors='some error text'))

    self.Run(command)

    self.AssertExecuteCalledOnce(command_args=['deploy'])
    self.AssertErrContains('some error text')
