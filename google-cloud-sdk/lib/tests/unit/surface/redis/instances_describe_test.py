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
"""Unit tests for `gcloud redis instances describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA,
                           calliope_base.ReleaseTrack.GA])
class DescribeTest(redis_test_base.InstancesUnitTestBase,
                   parameterized.TestCase):

  def testDescribe(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    expected_instance = self.messages.Instance(name=self.instance_relative_name)
    self._ExpectDescribe(expected_instance)

    actual_instance = self.Run('redis instances describe {} --region {}'
                               .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, expected_instance)

  def testDescribe_UsingRegionProperty(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    expected_instance = self.messages.Instance(name=self.instance_relative_name)
    self._ExpectDescribe(expected_instance)

    properties.VALUES.redis.region.Set(self.region_id)
    actual_instance = self.Run('redis instances describe {}'
                               .format(self.instance_id))

    self.assertEqual(actual_instance, expected_instance)

  def testDescribe_UsingRelativeInstanceName(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    expected_instance = self.messages.Instance(name=self.instance_relative_name)
    self._ExpectDescribe(expected_instance)

    actual_instance = self.Run('redis instances describe {}'
                               .format(self.instance_relative_name))

    self.assertEqual(actual_instance, expected_instance)

  def _ExpectDescribe(self, expected_instance):
    self.instances_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsInstancesGetRequest(
            name=expected_instance.name),
        response=expected_instance)


if __name__ == '__main__':
  test_case.main()
