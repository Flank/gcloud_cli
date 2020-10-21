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
"""kuberun devkits list tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import devkit
from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from tests.lib.surface.kuberun import test_base
from tests.lib.surface.kuberun import testdata


class DevkitsListTest(test_base.PackageUnitTestBase):

  def _DevKitsEqual(self, a, b, msg=None):
    self.assertEqual(a.id, b.id, msg + ", field 'id'")
    self.assertEqual(a.name, b.name, msg + ", field 'name'")
    self.assertEqual(a.description, b.description,
                     msg + ", field 'description'")
    self.assertEqual(a.version, b.version, msg + ", field 'version'")

  def SetUp(self):
    self.addTypeEqualityFunc(devkit.DevKit, self._DevKitsEqual)

  def testList(self):
    command = 'kuberun devkits list'
    expected_out = testdata.DEVKITS_LIST_JSON
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command, output=expected_out))

    result = self.Run(command)

    self.AssertExecuteCalledOnce(
        command_args=['devkits', 'list'])
    self.assertEqual(len(result), len(testdata.DEVKITS_LIST))
    for i in range(len(testdata.DEVKITS_LIST)):
      want = testdata.DEVKITS_LIST[i]
      got = result[i]
      self.assertEqual(got, want, 'Got {}, want {}'.format(got, want))

  def testList_error(self):
    command = 'kuberun devkits list'
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command, errors='error from the binary'))

    result = self.Run(command)

    self.AssertExecuteCalledOnce(command_args=['devkits', 'list'])
    self.assertEqual(result, [])
    self.AssertErrContains('error from the binary')
