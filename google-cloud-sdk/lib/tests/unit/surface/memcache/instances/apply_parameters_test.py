# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Unit tests for `gcloud memcache instances apply-parameters`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base


class ApplyParametersTest(memcache_test_base.InstancesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectApplyParameters(self, node_ids=False, is_async=False):
    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    parameters = self.MakeParameters({'a': 'b', 'c': 'd'})
    expected_instance = self.messages.Instance(
        name=self.instance_relative_name,
        parameters=parameters,
        memcacheNodes=[
            self.messages.Node(nodeId='node-1', parameters=parameters),
            self.messages.Node(nodeId='node-2', parameters=parameters)
        ])
    self.expected_instance = expected_instance

    apply_req = self.messages.MemcacheProjectsLocationsInstancesApplyParametersRequest(
        name=self.instance_relative_name,
        applyParametersRequest=self.messages.ApplyParametersRequest())

    if not node_ids:
      apply_req.applyParametersRequest.applyAll = True
    else:
      apply_req.applyParametersRequest.applyAll = False
      apply_req.applyParametersRequest.nodeIds = node_ids
    self.instances_service.ApplyParameters.Expect(
        request=apply_req, response=operation)
    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)

    self.instances_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsInstancesGetRequest(
            name=expected_instance.name),
        response=expected_instance)

  def testApplyParameters_ApplyAll(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectApplyParameters()
    actual_instance = self.Run(
        'memcache instances apply-parameters {} --region {} --apply-all '
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testApplyParameters_NodeIds(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    node_ids = ['node-1', 'node-2']
    self._ExpectApplyParameters(node_ids)
    actual_instance = self.Run(
        'memcache instances apply-parameters {} --region {} --node-ids {}'
        .format(self.instance_id, self.region_id, ','.join(node_ids)))

    self.assertEqual(actual_instance, self.expected_instance)

  def testApplyParameters_UsingRelativeInstanceName(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectApplyParameters()
    actual_instance = self.Run(
        'memcache instances apply-parameters {} --region {} --apply-all '
        .format(self.instance_relative_name, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testApplyParameters_Async(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectApplyParameters(is_async=True)
    self.Run('memcache instances apply-parameters {} --region {} --apply-all '
             '--async -q '.format(self.instance_relative_name, self.region_id))

    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.wait_operation_relative_name))


if __name__ == '__main__':
  test_case.main()
