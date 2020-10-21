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
"""kuberun surface services delete tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from googlecloudsdk.core.console import console_io
from tests.lib.surface.kuberun import test_base


class ServicesDeleteTest(test_base.PackageUnitTestBase):

  def SetUp(self):
    self.test_package = self.Touch(
        os.path.join(self.home_path, 'my-package-dir'),
        name='temp',
        makedirs=True)

  def testDelete(self):
    """Tests successful delete with default output format."""
    command = '''kuberun core services delete bar --cluster foo
    --cluster-location us-central1'''
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(command, output=None))
    self.WriteInput('Y\n')

    self.Run(command)

    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'delete', 'bar', '--cluster', 'foo',
        '--cluster-location', 'us-central1'
    ])
    self.AssertErrContains('Service is successfully deleted.')

  def testDeleteAbortsIfReplyNo(self):
    """Tests that delete fails if console is unattended."""
    command = '''kuberun core services delete bar --cluster foo
    --cluster-location us-central1'''
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(command)

  def testDeleteFailsIfUnattended(self):
    """Tests that delete fails if console is unattended."""
    command = '''kuberun core services delete bar --cluster foo
    --cluster-location us-central1'''
    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run(command)

  def testDeleteWithError(self):
    """Tests successful delete with default output format."""
    command = '''kuberun core services delete bar --cluster foo
    --cluster-location us-central1'''
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command,
            errors='services.serving.knative.dev "bar" not found',
            status=1))
    self.WriteInput('Y\n')

    self.Run(command)

    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'delete', 'bar', '--cluster', 'foo',
        '--cluster-location', 'us-central1'
    ])
    self.AssertErrContains('services.serving.knative.dev "bar" not found')
