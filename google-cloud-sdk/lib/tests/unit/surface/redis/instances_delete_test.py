# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers as concepts_handler
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import redis_test_base


class DeleteTestGA(redis_test_base.InstancesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testDelete(self):
    self._ExpectDelete()

    self.WriteInput('y')
    self.Run('redis instances delete {} --region {}'
             .format(self.instance_id, self.region_id))

    self.AssertErrContains('You are about to delete instance [{}] in [{}].'
                           .format(self.instance_id, self.region_id))
    self.AssertErrContains('Any associated data will be lost.')
    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.instance_id))
    self.AssertErrContains('Deleted instance [{}].'.format(self.instance_id))

  def testDelete_UsingRegionProperty(self):
    self._ExpectDelete()

    properties.VALUES.redis.region.Set(self.region_id)
    self.WriteInput('y')
    self.Run('redis instances delete {}'.format(self.instance_id))

    self.AssertErrContains('You are about to delete instance [{}] in [{}].'
                           .format(self.instance_id, self.region_id))
    self.AssertErrContains('Any associated data will be lost.')
    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.instance_id))
    self.AssertErrContains('Deleted instance [{}].'
                           .format(self.instance_id))

  def testDelete_UsingRelativeInstanceName(self):
    self._ExpectDelete()

    self.WriteInput('y')
    self.Run('redis instances delete {}'.format(self.instance_relative_name))

    self.AssertErrContains('You are about to delete instance [{}] in [{}].'
                           .format(self.instance_id, self.region_id))
    self.AssertErrContains('Any associated data will be lost.')
    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.instance_id))
    self.AssertErrContains('Deleted instance [{}].'
                           .format(self.instance_id))

  def testDelete_Async(self):
    self._ExpectDelete(is_async=True)

    self.WriteInput('y')
    self.Run('redis instances delete {} --region {} --async'
             .format(self.instance_id, self.region_id))

    self.AssertErrContains('You are about to delete instance [{}] in [{}].'
                           .format(self.instance_id, self.region_id))
    self.AssertErrContains('Any associated data will be lost.')
    self.AssertErrContains('Delete request issued for: [{}]'
                           .format(self.instance_id))
    self.AssertErrContains('Check operation [{}] for status.'
                           .format(self.wait_operation_id))

  def testDelete_NoRegion(self):
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('redis instances delete {}'.format(self.instance_id))

  def _ExpectDelete(self, is_async=False):
    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    self.instances_service.Delete.Expect(
        request=self.messages.RedisProjectsLocationsInstancesDeleteRequest(
            name=self.instance_relative_name),
        response=operation)

    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)


class DeleteTestBeta(DeleteTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DeleteTestAlpha(DeleteTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
