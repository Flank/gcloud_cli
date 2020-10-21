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
"""kuberun surface services update traffic tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import traffic
from googlecloudsdk.command_lib.kuberun import traffic_pair
from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib.surface.kuberun import test_base
from tests.lib.surface.kuberun import testdata

import six


class ServicesUpdateTrafficTest(test_base.PackageUnitTestBase,
                                parameterized.TestCase):

  def _traffic_target_equal(self, target, other_target, msg=None):
    self.assertEqual(target.latestRevision, other_target.latestRevision,
                     'latestRevision')
    self.assertEqual(target.revisionName, other_target.revisionName,
                     'revisionName')
    self.assertEqual(target.specPercent, other_target.specPercent,
                     'specPercent')
    self.assertEqual(target.statusPercent, other_target.statusPercent,
                     'statusPercent')
    self.assertEqual(target.specTags, other_target.specTags, 'specTags')
    self.assertEqual(target.statusTags, other_target.statusTags, 'statusTags')
    self.assertEqual(target.urls, other_target.urls, 'urls')
    self.assertEqual(target.serviceUrl, other_target.serviceUrl, 'serviceUrl')

  def SetUp(self):
    self.addTypeEqualityFunc(traffic_pair.TrafficTargetPair,
                             self._traffic_target_equal)
    self.mock_bin_exec = self.StartObjectPatch(bin_ops.BinaryBackedOperation,
                                               '_Execute')

  def testUpdateTraffic_Succeed(self):
    mock_output = testdata.SERVICE_STRING
    svc_name = 'bar'
    command = """kuberun core services update-traffic {} --cluster foo
    --cluster-location us-central1 --to-latest""".format(svc_name)
    self.mock_bin_exec.return_value = bin_ops.BinaryBackedOperation.OperationResult(
        command, output=mock_output)

    result = self.Run(command)

    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'update-traffic', svc_name, '--cluster', 'foo',
        '--cluster-location', 'us-central1', '--to-latest'
    ])
    expected_result = traffic_pair.GetTrafficTargetPairs(
        spec_traffic={
            'hello-00001-loq': [
                traffic.TrafficTarget({
                    'revisionName': 'hello-00001-loq',
                    'percent': 100,
                    'latestRevision': False,
                    'tag': 'tag1',
                    'url': 'hello-00001-loq.service.example.com'
                })
            ]
        },
        status_traffic={
            'hello-00001-loq': [
                traffic.TrafficTarget({
                    'revisionName': 'hello-00001-loq',
                    'percent': 100,
                    'latestRevision': False,
                    'tag': 'tag1',
                    'url': 'hello-00001-loq.service.example.com'
                })
            ]
        },
        latest_ready_revision_name='hello-00001-loq',
        service_url='http://hello.default.example.com')
    self.assertEqual(1, len(result))
    self.assertEqual(expected_result[0], result[0])

  def testUpdateTraffic_Fail(self):
    svc_name = 'bar'
    command = """kuberun core services update-traffic {} --cluster foo
    --cluster-location us-central1 --to-latest""".format(svc_name)
    self.mock_bin_exec.return_value = bin_ops.BinaryBackedOperation.OperationResult(
        command, errors='Error occurred', failed=True)

    with self.assertRaises(exceptions.Error) as context:
      self.Run(command)

    self.assertIn('Command execution failed', six.text_type(context.exception))
    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'update-traffic', svc_name, '--cluster', 'foo',
        '--cluster-location', 'us-central1', '--to-latest'
    ])

  @parameterized.parameters(
      ('--to-latest', ['--to-latest']),
      ('--to-revisions=rev1=1,rev2=2', ['--to-revisions', 'rev1=1,rev2=2']),
  )
  def testUpdateTrafficWithFlags(self, cmd_args, exe_args):
    svc_name = 'bar'
    command = """kuberun core services update-traffic {} --cluster foo
    --cluster-location us-central1 {}""".format(svc_name, cmd_args)

    with self.assertRaises(exceptions.Error):
      self.Run(command)

    self.AssertExecuteCalledOnce(command_args=[
        'core', 'services', 'update-traffic', svc_name, '--cluster', 'foo',
        '--cluster-location', 'us-central1'
    ] + exe_args)
