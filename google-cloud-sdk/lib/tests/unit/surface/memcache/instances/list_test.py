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
"""Unit tests for `gcloud memcache instances list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base
from six.moves import range  # pylint: disable=redefined-builtin


class ListTest(
    memcache_test_base.InstancesUnitTestBase,):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectList(self, expected_instances):
    self.instances_service.List.Expect(
        request=self.messages.MemcacheProjectsLocationsInstancesListRequest(
            parent=self.region_relative_name),
        response=self.messages.ListInstancesResponse(
            resources=expected_instances))

  def _MakeInstances(self, n):
    instances = []
    for i in range(n):
      instance = self.MakeInstance()
      instance.name = '{}_{}'.format(self.instance_relative_name, i)
      instances.append(instance)
    return instances

  def testList(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    expected_instances = self._MakeInstances(4)
    self._ExpectList(expected_instances)

    # Disable output so can capture returned lists instead of printing.
    properties.VALUES.core.user_output_enabled.Set(False)
    actual_instances = self.Run('memcache instances list --region {}'.format(
        self.region_id))

    self.assertEqual(actual_instances, expected_instances)

  def testList_Uri(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    expected_instances = self._MakeInstances(3)
    self._ExpectList(expected_instances)

    self.Run('memcache instances list --region {} --uri'.format(self.region_id))

    self.AssertOutputEquals(
        """\
        https://memcache.googleapis.com/{api_version}/{instance_name}_0
        https://memcache.googleapis.com/{api_version}/{instance_name}_1
        https://memcache.googleapis.com/{api_version}/{instance_name}_2
        """.format(
            api_version=self.api_version,
            instance_name=self.instance_relative_name),
        normalize_space=True)

  def testList_CheckFormat(self):
    self.SetUpForTrack()
    self.SetUpInstances()
    expected_instances = self._MakeInstances(3)
    for instance in expected_instances:
      instance.nodeConfig = self.messages.NodeConfig(
          cpuCount=3, memorySizeMb=10)
      instance.memcacheNodes = [
          self.messages.Node(
              host='10.0.0.0',
              nodeId='node1',
              port=1234,
              state=self.messages.Node.StateValueValuesEnum('READY'),
              zone='us-central1-a'),
          self.messages.Node(
              host='10.0.0.1',
              nodeId='node2',
              port=1234,
              state=self.messages.Node.StateValueValuesEnum('READY'),
              zone='us-central1-b')
      ]
      instance.memcacheVersion = (
          self.messages.Instance.MemcacheVersionValueValuesEnum('MEMCACHE_1_5'))
      instance.memcacheFullVersion = 'memcached-1.5.16'
      instance.labels = self.MakeLabels({'a': 'b', 'c': 'd'})
      instance.authorizedNetwork = 'authorizedNetwork'
      instance.displayName = 'Friendly Name'
      instance.nodeCount = 3
      instance.state = self.messages.Instance.StateValueValuesEnum('READY')
      instance.createTime = '2020-01-01T00:00:00'
      instance.updateTime = '2020-01-02T00:00:00'
      instance.zones = ['us-central1-a', 'us-central1-b']
    self._ExpectList(expected_instances)
    self.Run('memcache instances list --region {}'.format(self.region_id))

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        INSTANCE_NAME REGION NETWORK NODE_COUNT NODE_CPU NODE_MB STATUS CREATE_TIME UPDATE_TIME
        test-instance_0 us-central1 authorizedNetwork 3 3 10 READY 2020-01-01T00:00:00 2020-01-02T00:00:00
        test-instance_1 us-central1 authorizedNetwork 3 3 10 READY 2020-01-01T00:00:00 2020-01-02T00:00:00
        test-instance_2 us-central1 authorizedNetwork 3 3 10 READY 2020-01-01T00:00:00 2020-01-02T00:00:00
          """,
        normalize_space=True)
    # pylint: enable=line-too-long


if __name__ == '__main__':
  test_case.main()
