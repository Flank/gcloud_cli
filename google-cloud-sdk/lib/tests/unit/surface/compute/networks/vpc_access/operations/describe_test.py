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
"""Tests of 'gcloud compute networks vpc-access operations describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class OperationsDescribeTest(base.VpcAccessUnitTestBase):

  def _ExpectDescribe(self, expected_operation):
    self.operations_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsOperationsGetRequest(
            name=expected_operation.name),
        response=expected_operation)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.expected_operation = self.messages.Operation(
        name=self.operation_relative_name)
    self._ExpectDescribe(self.expected_operation)

  def testOperationsDescribe(self):
    actual_operation = self.Run(
        'compute networks vpc-access operations describe {} --region={}'.format(
            self.operation_id, self.region_id))
    self.assertEqual(actual_operation, self.expected_operation)

  def testOpertionsDescribe_UsingRelativeOperationName(self):
    actual_operation = self.Run(
        'compute networks vpc-access operations describe {}'.format(
            self.operation_relative_name))
    self.assertEqual(actual_operation, self.expected_operation)


if __name__ == '__main__':
  test_case.main()
