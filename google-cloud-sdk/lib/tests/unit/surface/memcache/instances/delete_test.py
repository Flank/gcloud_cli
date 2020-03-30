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
"""Unit tests for `gcloud memcache instances delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base


class DeleteTest(memcache_test_base.InstancesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectDelete(self, is_async=False):
    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    self.instances_service.Delete.Expect(
        request=self.messages.MemcacheProjectsLocationsInstancesDeleteRequest(
            name=self.instance_relative_name),
        response=operation)

    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)

  def testDelete(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectDelete()

    self.Run('memcache instances delete {} --region {} -q'.format(
        self.instance_id, self.region_id))

    self.AssertErrContains('Deleted instance [{}].'.format(self.instance_id))

  def testDelete_UsingRelativeInstanceName(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectDelete()

    self.Run('memcache instances delete {} -q'.format(
        self.instance_relative_name))
    self.AssertErrContains('Deleted instance [{}].'.format(self.instance_id))

  def testDelete_Async(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    self._ExpectDelete(is_async=True)

    self.Run('memcache instances delete {} --region {} --async -q'.format(
        self.instance_id, self.region_id))

    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.wait_operation_relative_name))


if __name__ == '__main__':
  test_case.main()
