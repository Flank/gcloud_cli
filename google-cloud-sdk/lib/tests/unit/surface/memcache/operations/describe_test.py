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
"""Unit tests for `gcloud memcache operations describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base


class DescribeTest(memcache_test_base.OperationsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectDescribe(self, expected_operation):
    self.operations_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsOperationsGetRequest(
            name=expected_operation.name),
        response=expected_operation)

  def testDescribe(self):
    self.SetUpForTrack()
    self.SetUpOperations()
    expected_operation = self.messages.Operation(
        name=self.operation_relative_name)
    self._ExpectDescribe(expected_operation)

    actual_operation = self.Run('memcache operations describe {} --region {}'
                                .format(self.operation_id, self.region_id))

    self.assertEqual(actual_operation, expected_operation)

  def testDescribe_UsingRelativeOperationName(self):
    self.SetUpForTrack()
    self.SetUpOperations()
    expected_operation = self.messages.Operation(
        name=self.operation_relative_name)
    self._ExpectDescribe(expected_operation)

    actual_operation = self.Run('memcache operations describe {}'
                                .format(self.operation_relative_name))

    self.assertEqual(actual_operation, expected_operation)


if __name__ == '__main__':
  test_case.main()
