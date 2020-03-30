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
"""Unit tests for `gcloud memcache instances describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base


class DescribeTest(memcache_test_base.InstancesUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectDescribe(self, expected_instance):
    self.instances_service.Get.Expect(
        request=self.messages.MemcacheProjectsLocationsInstancesGetRequest(
            name=expected_instance.name),
        response=expected_instance)

  def testDescribe(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    expected_instance = self.messages.Instance(name=self.instance_relative_name)
    self._ExpectDescribe(expected_instance)

    actual_instance = self.Run('memcache instances describe {} --region {}'
                               .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, expected_instance)

  def testDescribe_UsingRelativeInstanceName(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    expected_instance = self.messages.Instance(name=self.instance_relative_name)
    self._ExpectDescribe(expected_instance)

    actual_instance = self.Run('memcache instances describe {}'
                               .format(self.instance_relative_name))

    self.assertEqual(actual_instance, expected_instance)

if __name__ == '__main__':
  test_case.main()
