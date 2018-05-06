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
"""Unit tests for `gcloud redis instances delete`."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers as concepts_handler
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class DeleteTest(redis_test_base.InstancesUnitTestBase, parameterized.TestCase):

  def testDelete(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    self._ExpectDelete()

    self.WriteInput('y')
    self.Run('redis instances delete {} --region {}'
             .format(self.instance_id, self.region_id))

    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.instance_id))
    self.AssertErrContains('Deleted instance [{}].'.format(self.instance_id))

  def testDelete_UsingRegionProperty(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    self._ExpectDelete()

    properties.VALUES.redis.region.Set(self.region_id)
    self.WriteInput('y')
    self.Run('redis instances delete {}'.format(self.instance_id))

    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.instance_id))
    self.AssertErrContains('Deleted instance [{}].'
                           .format(self.instance_id))

  def testDelete_UsingRelativeInstanceName(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    self._ExpectDelete()

    self.WriteInput('y')
    self.Run('redis instances delete {}'.format(self.instance_relative_name))

    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.instance_id))
    self.AssertErrContains('Deleted instance [{}].'
                           .format(self.instance_id))

  def testDelete_Async(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    self._ExpectDelete(async=True)

    self.WriteInput('y')
    self.Run('redis instances delete {} --region {} --async'
             .format(self.instance_id, self.region_id))

    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.instance_id))
    self.AssertErrContains('Check operation [{}] for status.'
                           .format(self.wait_operation_id))

  def testDelete_NoRegion(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('redis instances delete {}'.format(self.instance_id))

  def _ExpectDelete(self, async=False):
    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    self.instances_service.Delete.Expect(
        request=self.messages.RedisProjectsLocationsInstancesDeleteRequest(
            name=self.instance_relative_name),
        response=operation)

    if async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)


if __name__ == '__main__':
  test_case.main()
