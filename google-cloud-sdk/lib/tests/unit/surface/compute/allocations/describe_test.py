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
"""compute allocations describe tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import allocations_test_base as base


@parameterized.parameters(
    (calliope_base.ReleaseTrack.ALPHA, 'alpha'),)
class DescribeTest(base.AllocationTestBase):

  def testDescribe(self, track, api_version):
    self._SetUp(track, api_version)

    self.mock_client.allocations.Get.Expect(
        request=self.messages.ComputeAllocationsGetRequest(
            allocation='alloc', project='fake-project', zone='fake-zone'),
        response=self.messages.Allocation(name='alloc'))

    self.Run('compute allocations describe alloc --zone=fake-zone')


if __name__ == '__main__':
  test_case.main()
