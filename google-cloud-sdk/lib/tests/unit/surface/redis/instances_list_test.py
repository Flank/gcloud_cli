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
"""Unit tests for `gcloud redis instances list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base
from six.moves import range  # pylint: disable=redefined-builtin


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class ListTest(redis_test_base.InstancesUnitTestBase, parameterized.TestCase):

  def testList(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    expected_instances = self._MakeInstances(3)
    self._ExpectList(expected_instances)

    # Disable output so can capture returned lists instead of printing.
    properties.VALUES.core.user_output_enabled.Set(False)
    actual_instances = self.Run('redis instances list --region {}'
                                .format(self.region_id))

    self.assertEqual(actual_instances, expected_instances)

  def testList_UsingRegionProperty(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    expected_instances = self._MakeInstances(3)
    self._ExpectList(expected_instances)

    properties.VALUES.redis.region.Set(self.region_id)
    # Disable output so can capture returned lists instead of printing.
    properties.VALUES.core.user_output_enabled.Set(False)
    actual_instances = self.Run('redis instances list')

    self.assertEqual(actual_instances, expected_instances)

  def testList_Uri(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    expected_instances = self._MakeInstances(3)
    self._ExpectList(expected_instances)

    self.Run('redis instances list --region {} --uri'.format(self.region_id))

    self.AssertOutputEquals(
        """\
        https://redis.googleapis.com/{api_version}/{instance_name}_0
        https://redis.googleapis.com/{api_version}/{instance_name}_1
        https://redis.googleapis.com/{api_version}/{instance_name}_2
        """.format(api_version=self.api_version,
                   instance_name=self.instance_relative_name),
        normalize_space=True)

  def testList_CheckFormat(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    expected_instances = self._MakeInstances(3)
    for instance in expected_instances:
      instance.host = '10.0.0.0'
      instance.port = 6379
      instance.reservedIpRange = '10.0.0.0/29'
      instance.state = self.messages.Instance.StateValueValuesEnum('READY')
      instance.createTime = '2018-01-01T00:00:00'
    self._ExpectList(expected_instances)

    self.Run('redis instances list --region {}'.format(self.region_id))

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        INSTANCE_NAME    REGION       TIER         SIZE_GB  HOST      PORT  NETWORK     RESERVED_IP  STATUS  CREATE_TIME
        {instance_id}_0  us-central1  STANDARD_HA  4        10.0.0.0  6379  my-network  10.0.0.0/29  READY   2018-01-01T00:00:00
        {instance_id}_1  us-central1  STANDARD_HA  4        10.0.0.0  6379  my-network  10.0.0.0/29  READY   2018-01-01T00:00:00
        {instance_id}_2  us-central1  STANDARD_HA  4        10.0.0.0  6379  my-network  10.0.0.0/29  READY   2018-01-01T00:00:00
        """.format(instance_id=self.instance_id), normalize_space=True)
    # pylint: enable=line-too-long

  def _ExpectList(self, expected_instances):
    self.instances_service.List.Expect(
        request=self.messages.RedisProjectsLocationsInstancesListRequest(
            parent=self.region_relative_name),
        response=self.messages.ListInstancesResponse(
            instances=expected_instances))

  def _MakeInstances(self, n):
    instances = []
    for i in range(n):
      instance = self.MakeAllOptionsInstance()
      instance.name = '{}_{}'.format(self.instance_relative_name, i)
      instances.append(instance)
    return instances

if __name__ == '__main__':
  test_case.main()
