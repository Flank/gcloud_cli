# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Unit tests for `gcloud redis instances failover`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers as concepts_handler
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import redis_test_base


class FailoverTestGA(redis_test_base.InstancesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testFailover(self):
    self._TestFailover('redis instances failover {} --region {}'.format(
        self.instance_id, self.region_id))

  def testFailover_UsingRegionProperty(self):
    properties.VALUES.redis.region.Set(self.region_id)
    self._TestFailover('redis instances failover {}'.format(self.instance_id))

  def testFailover_UsingRelativeInstanceName(self):
    self._TestFailover('redis instances failover {}'.format(
        self.instance_relative_name))

  def testFailover_ForceDataLoss(self):
    self._TestFailover(
        'redis instances failover {} --region {} '.format(
            self.instance_id, self.region_id),
        force_loss=True)

  def testFailover_Async(self):
    self._TestFailover(
        'redis instances failover {} --region {}'.format(
            self.instance_id, self.region_id),
        is_async=True)

  def testFailover_NoRegion(self):
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('redis instances failover {}'.format(self.instance_id))

  def _TestFailover(self, failover_command, is_async=False, force_loss=False):
    # Construct and register expected requests & responses.
    request = self.messages.RedisProjectsLocationsInstancesFailoverRequest(
        name=self.instance_relative_name,)

    if force_loss:
      failover_request_class = self.messages.FailoverInstanceRequest
      loss_enum = failover_request_class.DataProtectionModeValueValuesEnum
      request.failoverInstanceRequest = failover_request_class(
          dataProtectionMode=loss_enum.FORCE_DATA_LOSS)
      failover_command += ' --data-protection-mode=force-data-loss'

    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    self.instances_service.Failover.Expect(request=request, response=operation)

    if is_async:
      failover_command += ' --async'
    else:
      operation.done = True  # Simulate immediate success.
      self.operations_service.Get.Expect(
          request=self.messages.RedisProjectsLocationsOperationsGetRequest(
              name=operation.name),
          response=operation)
      expected_instance = self.messages.Instance(
          name=self.instance_relative_name)
      self.instances_service.Get.Expect(
          request=self.messages.RedisProjectsLocationsInstancesGetRequest(
              name=expected_instance.name),
          response=expected_instance)

    # Run the command to be tested.
    self.WriteInput('y')
    self.Run(failover_command)

    # Perform assertions on the command output.
    self.AssertErrContains('can result in the loss of unreplicated data')
    self.AssertErrContains('Request issued for: [{}]'.format(self.instance_id))

    if is_async:
      self.AssertErrContains('Check operation [{}] for status.'.format(
          self.wait_operation_relative_name))
    else:
      self.AssertErrContains('Waiting for operation [{}] to complete'.format(
          self.wait_operation_relative_name))


class FailoverTestBeta(FailoverTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class FailoverTestAlpha(FailoverTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
