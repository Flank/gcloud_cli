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
"""Unit tests for `gcloud redis instances update`."""

from __future__ import absolute_import
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers as concepts_handler
from googlecloudsdk.command_lib.redis import instances_update_util
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base


class TestBase(redis_test_base.InstancesUnitTestBase):

  def ExpectUpdate(self, instance_to_update, expected_instance,
                   expected_update_mask, async=False):
    self.instances_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsInstancesGetRequest(
            name=instance_to_update.name),
        response=instance_to_update)

    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    self.instances_service.Patch.Expect(
        request=self.messages.RedisProjectsLocationsInstancesPatchRequest(
            instance=expected_instance, name=expected_instance.name,
            updateMask=expected_update_mask),
        response=operation)

    if async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)
    self.instances_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsInstancesGetRequest(
            name=expected_instance.name),
        response=expected_instance)

  def RedisConfigs(self, configs_dict):
    return encoding.DictToAdditionalPropertyMessage(
        configs_dict, self.messages.Instance.RedisConfigsValue, sort_items=True)

  def Labels(self, labels_dict):
    return encoding.DictToAdditionalPropertyMessage(
        labels_dict, self.messages.Instance.LabelsValue, sort_items=True)


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class UpdateTest(TestBase, parameterized.TestCase):

  def testUpdate(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    self._SetUpExpectations()

    actual_instance = self.Run(
        'redis instances update {instance_id} --region {region_id}'
        ' {update_options}'
        .format(instance_id=self.instance_id, region_id=self.region_id,
                update_options=self.update_options))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdate_UsingRegionProperty(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    self._SetUpExpectations()

    properties.VALUES.redis.region.Set(self.region_id)
    actual_instance = self.Run(
        'redis instances update {instance_id} {update_options}'
        .format(instance_id=self.instance_id,
                update_options=self.update_options))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdate_UsingRelativeInstanceName(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    self._SetUpExpectations()

    actual_instance = self.Run(
        'redis instances update {name} {update_options}'
        .format(name=self.instance_relative_name,
                update_options=self.update_options))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdate_NoRegion(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    with self.assertRaises(concepts_handler.ParseError):
      self.Run(
          'redis instances update {instance_id}'
          .format(instance_id=self.instance_id))

  def testUpdate_Async(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    self._SetUpExpectations(async=True)

    self.Run(
        'redis instances update {instance_id} --region {region_id} --async'
        ' {update_options}'
        .format(instance_id=self.instance_id, region_id=self.region_id,
                update_options=self.update_options))

    self.AssertErrContains('Request issued for: [{}]'.
                           format(self.instance_id))
    self.AssertErrContains('Check operation [{}] for status.'.
                           format(self.wait_operation_id))

  def testUpdate_NoOptions(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    with self.assertRaises(instances_update_util.NoFieldsSpecified):
      self.Run('redis instances update {} --region {}'
               .format(self.instance_id, self.region_id))

  def _SetUpExpectations(self, async=False):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    update_options = (
        ' --display-name new-display-name'
        ' --size 6'
        ' --update-redis-config'
        '     maxmemory-policy=volatile-lru,notify-keyspace-events=kx'
        ' --update-labels a=3,b=4,c=5')
    expected_update_mask = (
        'display_name,memory_size_gb,redis_configs,labels')

    expected_instance = self.messages.Instance(
        name=self.instance_relative_name)
    expected_instance.displayName = 'new-display-name'
    expected_instance.memorySizeGb = 6
    expected_instance.redisConfigs = self.RedisConfigs(
        {'maxmemory-policy': 'volatile-lru', 'notify-keyspace-events': 'kx'})
    expected_instance.labels = self.Labels({'a': '3', 'b': '4', 'c': '5'})

    self.ExpectUpdate(instance_to_update, expected_instance,
                      expected_update_mask, async=async)

    self.expected_instance = expected_instance
    self.update_options = update_options


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class RemoveRedisConfigsTest(TestBase, parameterized.TestCase):

  def testRemoveRedisConfig(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_redis_configs = {'maxmemory-policy': 'noeviction',
                              'notify-keyspace-events': 'El'}
    new_redis_configs = {'maxmemory-policy': 'noeviction'}
    self._SetUpExpectations(original_redis_configs, new_redis_configs)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-redis-config notify-keyspace-events'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemovePreviouslyRemovedRedisConfig(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_redis_configs = {'maxmemory-policy': 'noeviction'}
    # Removing a non-existent Redis config should silently have no effect.
    new_redis_configs = {'maxmemory-policy': 'noeviction'}
    self._SetUpExpectations(original_redis_configs, new_redis_configs)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-redis-config notify-keyspace-events'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveAndUpdateRedisConfig(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_redis_configs = {'maxmemory-policy': 'noeviction',
                              'notify-keyspace-events': 'El'}
    new_redis_configs = {'maxmemory-policy': 'noeviction',
                         'notify-keyspace-events': 'kx'}
    self._SetUpExpectations(original_redis_configs, new_redis_configs)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-redis-config notify-keyspace-events'
        ' --update-redis-config notify-keyspace-events=kx'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveAllRedisConfigs(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_redis_configs = {'maxmemory-policy': 'noeviction',
                              'notify-keyspace-events': 'El'}
    new_redis_configs = {}
    self._SetUpExpectations(original_redis_configs, new_redis_configs)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-redis-config maxmemory-policy,notify-keyspace-events'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def _SetUpExpectations(self, original_redis_configs, new_redis_configs,
                         async=False):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    instance_to_update.redisConfigs = self.RedisConfigs(new_redis_configs)

    expected_instance = self.messages.Instance(
        name=self.instance_relative_name)
    expected_instance.redisConfigs = self.RedisConfigs(new_redis_configs)

    self.ExpectUpdate(instance_to_update, expected_instance, 'redis_configs',
                      async=async)

    self.expected_instance = expected_instance


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class LabelsTest(TestBase, parameterized.TestCase):

  def testUpdateNonExistentLabel(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_labels = {'b': '2'}
    new_labels = {'a': '3', 'b': '2'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {} --update-labels a=3'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveLabel(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {'b': '2'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-labels a'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemovePreviouslyRemovedLabel(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_labels = {'b': '2'}
    # Removing a non-existent label should silently have no effect.
    new_labels = {'b': '2'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-labels a'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveAndUpdateLabel(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {'b': '4', 'c': '5'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-labels a'
        ' --update-labels a=3,b=4,c=5'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveAllLabels(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {} --remove-labels a,b'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testClearLabels(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {} --clear-labels'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testClearAndUpdateLabels(self, track):
    self.SetUpForTrack(track)
    self.SetUpInstancesForTrack()
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {'a': '3', 'b': '4', 'c': '5'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {} --clear-labels'
        ' --update-labels a=3,b=4,c=5'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def _SetUpExpectations(self, original_labels, new_labels, async=False):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    instance_to_update.labels = self.Labels(original_labels)

    expected_instance = self.messages.Instance(
        name=self.instance_relative_name)
    expected_instance.labels = self.Labels(new_labels)

    self.ExpectUpdate(instance_to_update, expected_instance, 'labels',
                      async=async)

    self.expected_instance = expected_instance


if __name__ == '__main__':
  test_case.main()
