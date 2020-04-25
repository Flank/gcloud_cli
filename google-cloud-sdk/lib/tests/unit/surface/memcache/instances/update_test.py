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
"""Unit tests for `gcloud memcache instances update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base


class UpdateTest(memcache_test_base.InstancesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectUpdate(self, is_async=False):
    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    expected_update_mask = u'displayName,nodeCount,labels'
    expected_instance = self.messages.Instance(
        displayName=u'new-display-name',
        labels=self.MakeLabels({
            u'a': u'b',
            u'c': u'd'
        }),
        nodeCount=2)
    self.expected_instance = expected_instance

    update_req = self.messages.MemcacheProjectsLocationsInstancesPatchRequest(
        instance=expected_instance,
        name=self.instance_relative_name,
        updateMask=expected_update_mask)
    self.instances_service.Patch.Expect(request=update_req, response=operation)
    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)

    self.instances_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsInstancesGetRequest(
            name=self.instance_relative_name),
        response=expected_instance)

  def testUpdate(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectUpdate()
    actual_instance = self.Run('memcache instances update {} --region {} '
                               '--display-name \'{}\' '
                               '--labels a=b,c=d '
                               '--node-count {} '.format(
                                   self.instance_id, self.region_id,
                                   self.expected_instance.displayName,
                                   self.expected_instance.nodeCount))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdate_UsingRelativeInstanceName(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectUpdate()
    actual_instance = self.Run('memcache instances update {} --region {} '
                               '--display-name \'{}\' '
                               '--labels a=b,c=d '
                               '--node-count {} '.format(
                                   self.instance_relative_name, self.region_id,
                                   self.expected_instance.displayName,
                                   self.expected_instance.nodeCount))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdate_Async(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectUpdate(is_async=True)
    self.Run('memcache instances update {} --region {} '
             '--display-name \'{}\' '
             '--labels a=b,c=d '
             '--node-count {} '
             '--async -q '.format(self.instance_id, self.region_id,
                                  self.expected_instance.displayName,
                                  self.expected_instance.nodeCount))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.wait_operation_relative_name))


class UpdateParametersTest(memcache_test_base.InstancesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectUpdateParameters(self, is_async=False):
    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    expected_instance = self.messages.Instance(
        name=self.instance_relative_name,
        parameters=self.MakeParameters({'idle_timeout': '1'}))
    self.expected_instance = expected_instance

    param_req = self.messages.UpdateParametersRequest(
        updateMask=u'params', parameters=expected_instance.parameters)
    update_req = self.messages.MemcacheProjectsLocationsInstancesUpdateParametersRequest(
        name=expected_instance.name, updateParametersRequest=param_req)

    self.instances_service.UpdateParameters.Expect(
        request=update_req, response=operation)
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

  def testUpdateParameters(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectUpdateParameters()
    actual_instance = self.Run('memcache instances update {} --region {} '
                               '--parameters idle-timeout=1 '.format(
                                   self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdateParameters_UsingRelativeInstanceName(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectUpdateParameters()
    actual_instance = self.Run('memcache instances update {} --region {} '
                               '--parameters idle-timeout=1 '.format(
                                   self.instance_relative_name, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdateParameters_Async(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectUpdateParameters(is_async=True)
    self.Run('memcache instances update {} --region {} '
             '--parameters idle-timeout=1 '
             '--async -q '.format(self.instance_id, self.region_id))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.wait_operation_relative_name))


if __name__ == '__main__':
  test_case.main()
