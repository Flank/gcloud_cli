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
"""kuberun surface services deploy tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from tests.lib import parameterized
from tests.lib.surface.kuberun import test_base


class ServicesDeployTest(test_base.PackageUnitTestBase, parameterized.TestCase):

  def SetUp(self):
    self.mock_bin_exec = self.StartObjectPatch(
        bin_ops.StreamingBinaryBackedOperation, '_Execute')

  def testDeploy_Succeed(self):
    svc_name = 'bar'
    command = """kuberun core services deploy {} --cluster foo
    --cluster-location us-central1 --image newImage""".format(svc_name)
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command, output='Service [{}] has been deployed.'.format(svc_name)))

    result = self.Run(command)

    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'deploy', svc_name, '--cluster', 'foo',
        '--cluster-location', 'us-central1', '--image', 'newImage',
    ])
    self._AssertContains('Service [{}] has been deployed.'.format(svc_name),
                         result, 'result')

  def testDeploy_Fail(self):
    svc_name = 'bar'
    command = """kuberun core services deploy {} --cluster foo
    --cluster-location us-central1 --image newImage""".format(svc_name)
    self.mock_bin_exec.return_value = (
        bin_ops.BinaryBackedOperation.OperationResult(
            command, errors='service [{}] not found'.format(svc_name)))

    self.Run(command)

    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'deploy', svc_name, '--cluster', 'foo',
        '--cluster-location', 'us-central1', '--image', 'newImage'
    ])
    self.AssertErrContains('service [{}] not found'.format(svc_name))

  @parameterized.parameters(
      ('--concurrency 1', ['--concurrency', '1']),
      ('--cpu 2', ['--cpu', '2']),
      ('--memory 3G', ['--memory', '3G']),
      ('--port 8888', ['--port', '8888']),
      ('--args test,arg', ['--args', 'test,arg']),
      ('--command testcommand', ['--command', 'testcommand']),
      ('--min-instances 4', ['--min-instances', '4']),
      ('--max-instances 5', ['--max-instances', '5']),
      ('--clear-labels', ['--clear-labels']),
      ('--remove-labels label1', ['--remove-labels', 'label1']),
      ('--update-labels label2=value2', ['--update-labels', 'label2=value2']),
      ('--labels label3=value3', ['--labels', 'label3=value3']),
      ('--clear-config-maps', ['--clear-config-maps']),
      ('--remove-config-maps /cm1', ['--remove-config-maps', '/cm1']),
      ('--update-config-maps /cm2=cf2', ['--update-config-maps', '/cm2=cf2']),
      ('--set-config-maps /cm3=config3', ['--set-config-maps', '/cm3=config3']),
      ('--clear-secrets', ['--clear-secrets']),
      ('--remove-secrets /s1', ['--remove-secrets', '/s1']),
      ('--update-secrets /s2=secret2', ['--update-secrets', '/s2=secret2']),
      ('--set-secrets /s3=secret3', ['--set-secrets', '/s3=secret3']),
      ('--clear-env-vars', ['--clear-env-vars']),
      ('--remove-env-vars ev1', ['--remove-env-vars', 'ev1']),
      ('--update-env-vars ev2=value2', ['--update-env-vars', 'ev2=value2']),
      ('--set-env-vars ev3=testvalue3', ['--set-env-vars', 'ev3=testvalue3']),
      ('--connectivity external', ['--connectivity', 'external']),
      ('--service-account testaccount', ['--service-account', 'testaccount']),
      ('--revision-suffix test-suffix', ['--revision-suffix', 'test-suffix']),
      ('--timeout 1m', ['--timeout', '60']),
      ('--use-http2', ['--use-http2']),
      ('--no-use-http2', ['--no-use-http2']),
      ('--async', ['--async']),
  )
  def testDeployWithFlags(self, cmd_args, exe_args):
    svc_name = 'bar'
    command = """kuberun core services deploy {} --cluster foo
    --cluster-location us-central1 --image testimage {}""".format(
        svc_name, cmd_args)

    self.Run(command)

    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'deploy', svc_name, '--cluster', 'foo',
        '--cluster-location', 'us-central1', '--image', 'testimage',
    ] + exe_args)
