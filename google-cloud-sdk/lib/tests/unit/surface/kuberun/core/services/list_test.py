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
"""kuberun surface revisions list tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import exceptions
from tests.lib.surface.kuberun import test_base
from tests.lib.surface.kuberun import testdata


class ServicesListTest(test_base.PackageUnitTestBase):

  def testList(self):
    command = ('kuberun core services list --cluster foo '
               '--cluster-location us-central1')
    mock_out = '[' + testdata.SERVICE_STRING + ']'
    self.mock_bin_exec.return_value = (
        binary_operations.BinaryBackedOperation.OperationResult(
            command, output=mock_out))

    result = self.Run(command)
    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'list', '--cluster', 'foo',
        '--cluster-location', 'us-central1'
    ])
    expected_result = testdata.SERVICE
    self.assertEqual(result[0], expected_result)

  def testList_emptyListReturnedOnEmptyInput(self):
    command = ('kuberun core services list --cluster foo '
               '--cluster-location us-central1')
    mock_out = '[]'
    self.mock_bin_exec.return_value = (
        binary_operations.BinaryBackedOperation.OperationResult(
            command, output=mock_out))

    result = self.Run(command)
    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'list', '--cluster', 'foo',
        '--cluster-location', 'us-central1'
    ])
    self.assertEqual(result, [])

  def testList_failure(self):
    command = ('kuberun core services list --cluster foo '
               '--cluster-location us-central1')
    self.mock_bin_exec.return_value = (
        binary_operations.BinaryBackedOperation.OperationResult(
            command, output='', errors='error', failed=True))

    with self.assertRaises(exceptions.Error):
      self.Run(command)
    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'list', '--cluster', 'foo',
        '--cluster-location', 'us-central1'
    ])

