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
"""kuberun surface domain mappings create tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.kuberun import domainmapping
from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from googlecloudsdk.core import exceptions
from tests.lib.surface.kuberun import test_base
from tests.lib.surface.kuberun import testdata
import six


class DomainMappingsCreateTest(test_base.PackageUnitTestBase):

  def testCreate_Succeed(self):
    command = """kuberun core domain-mappings create --service mine
    --domain hello.example.com --cluster foo --cluster-location us-central1"""
    expected_out = testdata.DOMAIN_MAPPING_STRING
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command, output=expected_out))

    result = self.Run(command)

    self.AssertExecuteCalledOnce(command_args=[
        'core', 'domain-mappings', 'create', '--service', 'mine',
        '--domain', 'hello.example.com', '--cluster', 'foo',
        '--cluster-location', 'us-central1'
    ])
    expected_result = domainmapping.DomainMapping(
        json.loads(expected_out)).records
    self.assertEqual(result, expected_result)

  def testCreate_Fail(self):
    command = """kuberun core domain-mappings create --service mine --domain
    hello.example.com --cluster foo --cluster-location us-central1"""
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command,
            status=1,
            errors='Could not map domain [hello.example.com] to service [mine]')
    )

    with self.assertRaises(exceptions.Error) as context:
      self.Run(command)

    self.assertIn('Could not map domain [hello.example.com] to service [mine]',
                  six.text_type(context.exception))
