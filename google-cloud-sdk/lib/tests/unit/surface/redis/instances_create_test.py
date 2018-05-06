# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for `gcloud redis instances create`."""

from __future__ import absolute_import
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers as concepts_handler
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class CreateTest(redis_test_base.InstancesUnitTestBase, parameterized.TestCase):

  def testCreate_NoOptions(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    instance_to_create = self.MakeDefaultInstance()
    expected_instance = self._ExpectCreate(instance_to_create, self.instance_id,
                                           self.instance_relative_name)

    actual_instance = self.Run('redis instances create {} --region {}'
                               .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, expected_instance)

  def testCreate_AllOptions(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    instance_to_create = self.MakeAllOptionsInstance()
    expected_instance = self._ExpectCreate(instance_to_create, self.instance_id,
                                           self.instance_relative_name)

    actual_instance = self.Run(
        'redis instances create {} --region {}'
        ' --alternative-zone zone2'
        ' --display-name my-display-name'
        ' --labels a=1,b=2'
        ' --network my-network'
        ' --redis-config maxmemory-policy=noeviction,notify-keyspace-events=El'
        ' --redis-version redis_3_2'
        ' --reserved-ip-range 10.0.0.0/29'
        ' --size 4'
        ' --tier standard'
        ' --zone zone1'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, expected_instance)

  def testCreate_UsingRegionProperty(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    instance_to_create = self.MakeDefaultInstance()
    expected_instance = self._ExpectCreate(instance_to_create, self.instance_id,
                                           self.instance_relative_name)

    properties.VALUES.redis.region.Set(self.region_id)
    actual_instance = self.Run('redis instances create {}'
                               .format(self.instance_id))

    self.assertEqual(actual_instance, expected_instance)

  def testCreate_UsingRelativeInstanceName(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    instance_to_create = self.MakeDefaultInstance()
    expected_instance = self._ExpectCreate(instance_to_create, self.instance_id,
                                           self.instance_relative_name)

    actual_instance = self.Run('redis instances create {}'
                               .format(self.instance_relative_name))

    self.assertEqual(actual_instance, expected_instance)

  def testCreate_NoRegion(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('redis instances create {}'.format(self.instance_id))

  def testCreate_Async(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    instance_to_create = self.MakeDefaultInstance()
    self._ExpectCreate(instance_to_create, self.instance_id,
                       self.instance_relative_name, async=True)

    self.Run('redis instances create {} --region {} --async'
             .format(self.instance_id, self.region_id))

    self.AssertErrContains('Create request issued for: [{}]'.
                           format(self.instance_id))
    self.AssertErrContains('Check operation [{}] for status.'.
                           format(self.wait_operation_id))

  def _ExpectCreate(self, instance_to_create, instance_to_create_id,
                    instance_to_create_name, async=False):
    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    self.instances_service.Create.Expect(
        request=self.messages.RedisProjectsLocationsInstancesCreateRequest(
            instance=instance_to_create, instanceId=instance_to_create_id,
            parent=self.region_relative_name),
        response=operation)

    if async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)

    # The Get request to fetch the created instance needs an instance name.
    expected_created_instance = copy.deepcopy(instance_to_create)
    expected_created_instance.name = instance_to_create_name
    self.instances_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsInstancesGetRequest(
            name=expected_created_instance.name),
        response=expected_created_instance)

    return expected_created_instance


if __name__ == '__main__':
  test_case.main()
