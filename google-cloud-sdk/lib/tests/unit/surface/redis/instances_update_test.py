# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers as concepts_handler
from googlecloudsdk.command_lib.redis import instances_update_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import redis_test_base


class InstancesUpdateUnitTestBase(redis_test_base.InstancesUnitTestBase,
                                  parameterized.TestCase):

  def ExpectGet(self, instance_to_get):
    self.instances_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsInstancesGetRequest(
            name=instance_to_get.name),
        response=instance_to_get)

  def ExpectUpdate(self,
                   instance_to_update,
                   expected_instance,
                   expected_update_mask,
                   is_async=False):
    self.instances_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsInstancesGetRequest(
            name=instance_to_update.name),
        response=instance_to_update)

    operation = self.messages.Operation(name=self.wait_operation_relative_name)
    self.instances_service.Patch.Expect(
        request=self.messages.RedisProjectsLocationsInstancesPatchRequest(
            instance=expected_instance,
            name=expected_instance.name,
            updateMask=expected_update_mask),
        response=operation)

    if is_async:
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


class UpdateTest(InstancesUpdateUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testUpdate(self):
    self._SetUpExpectations()

    actual_instance = self.Run(
        'redis instances update {instance_id} --region {region_id}'
        ' {update_options}'.format(
            instance_id=self.instance_id,
            region_id=self.region_id,
            update_options=self.update_options))

    self.assertEqual(actual_instance, self.expected_instance)
    self.AssertErrContains('Request issued for: [my-redis-instance]\n')
    self.AssertErrContains('Updated instance [my-redis-instance].\n')
    self.AssertErrContains('Do you want to proceed with update?')

  def testUpdate_UsingRegionProperty(self):
    self._SetUpExpectations()

    properties.VALUES.redis.region.Set(self.region_id)
    actual_instance = self.Run(
        'redis instances update {instance_id} {update_options}'.format(
            instance_id=self.instance_id, update_options=self.update_options))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdate_UsingRelativeInstanceName(self):
    self._SetUpExpectations()

    actual_instance = self.Run(
        'redis instances update {name} {update_options}'.format(
            name=self.instance_relative_name,
            update_options=self.update_options))

    self.assertEqual(actual_instance, self.expected_instance)

  def testUpdate_NoRegion(self):
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('redis instances update {instance_id}'.format(
          instance_id=self.instance_id))

  def testUpdate_Async(self):
    self._SetUpExpectations(is_async=True)

    self.Run('redis instances update {instance_id} --region {region_id} --async'
             ' {update_options}'.format(
                 instance_id=self.instance_id,
                 region_id=self.region_id,
                 update_options=self.update_options))

    self.AssertErrContains('Request issued for: [{}]'.format(self.instance_id))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.wait_operation_relative_name))

  def testUpdate_NoOptions(self):
    instances_to_get = self.messages.Instance(name=self.instance_relative_name)
    self.ExpectGet(instances_to_get)
    with self.assertRaises(instances_update_util.NoFieldsSpecified):
      self.Run('redis instances update {} --region {}'.format(
          self.instance_id, self.region_id))

  def _SetUpExpectations(self, is_async=False):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    update_options = (
        ' --display-name new-display-name --size 6 --update-redis-config'
        ' maxmemory-gb=5.0,maxmemory-policy=volatile-lru,'
        'notify-keyspace-events=kx,activedefrag=yes,lfu-log-factor=2,'
        'lfu-decay-time=60 --update-labels a=3,b=4,c=5')
    expected_update_mask = ('labels,display_name,memory_size_gb,redis_configs')

    expected_instance = self.messages.Instance(name=self.instance_relative_name)
    expected_instance.displayName = 'new-display-name'
    expected_instance.memorySizeGb = 6
    expected_instance.redisConfigs = self.RedisConfigs({
        'activedefrag': 'yes',
        'lfu-decay-time': '60',
        'lfu-log-factor': '2',
        'maxmemory-gb': '5.0',
        'maxmemory-policy': 'volatile-lru',
        'notify-keyspace-events': 'kx'
    })
    expected_instance.labels = self.Labels({'a': '3', 'b': '4', 'c': '5'})

    self.WriteInput('y\n')
    self.ExpectUpdate(
        instance_to_update,
        expected_instance,
        expected_update_mask,
        is_async=is_async)

    self.expected_instance = expected_instance
    self.update_options = update_options

  @parameterized.parameters(
      ('BASIC', 'Scaling a Basic Tier instance will result in a full cache '
       'flush, and the instance will be unavailable during the operation.'),
      ('STANDARD_HA',
       'Scaling a Standard Tier instance may result in the loss of '
       'unreplicated data, and the instance will be briefly unavailable during '
       'failover.'),
      (None,
       'Scaling a redis instance may result in data loss, and the instance '
       'will be briefly unavailable during scaling.'))
  def testUpdate_SizePrompts(self, tier, prompt_message):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    if tier:
      instance_to_update.tier = self.messages.Instance.TierValueValuesEnum(tier)
    expected_update_mask = 'memory_size_gb'

    expected_instance = self.messages.Instance(
        name=self.instance_relative_name,
        tier=instance_to_update.tier,
        memorySizeGb=6)

    self.ExpectUpdate(instance_to_update, expected_instance,
                      expected_update_mask)
    self.WriteInput('y\n')
    self.Run('redis instances update {instance_id} --region {region_id} '
             '--size 6'.format(
                 instance_id=self.instance_id, region_id=self.region_id))

    self.AssertErrContains('Change to instance size requested.')
    self.AssertErrContains(prompt_message)
    self.AssertErrContains(
        'https://cloud.google.com/memorystore/docs/redis/scaling-instances')
    self.AssertErrContains('Do you want to proceed with update?')

  def testUpdate_NoSizeNoPrompt(self):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    expected_update_mask = 'display_name'

    expected_instance = self.messages.Instance(
        name=self.instance_relative_name, displayName='new-display-name')
    expected_instance.displayName = 'new-display-name'

    self.ExpectUpdate(instance_to_update, expected_instance,
                      expected_update_mask)
    self.Run('redis instances update {instance_id} --region {region_id} '
             '--display-name new-display-name'.format(
                 instance_id=self.instance_id, region_id=self.region_id))
    self.AssertErrNotContains('Do you want to proceed with update?')

  def testUpdate_SizePromptCancel(self):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    self.instances_service.Get.Expect(
        request=self.messages.RedisProjectsLocationsInstancesGetRequest(
            name=instance_to_update.name),
        response=instance_to_update)

    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('redis instances update {instance_id} --region {region_id} '
               '--size 6'.format(
                   instance_id=self.instance_id, region_id=self.region_id))
    self.AssertErrContains('Do you want to proceed with update?')


class UpdateTestBeta(UpdateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class UpdateTestAlpha(UpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class RemoveRedisConfigsTest(InstancesUpdateUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testRemoveRedisConfig(self):
    original_redis_configs = {
        'activedefrag': 'yes',
        'maxmemory-policy': 'noeviction',
        'notify-keyspace-events': 'El'
    }
    new_redis_configs = {
        'activedefrag': 'yes',
        'maxmemory-policy': 'noeviction'
    }
    self._SetUpExpectations(original_redis_configs, new_redis_configs)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-redis-config notify-keyspace-events'.format(
            self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemovePreviouslyRemovedRedisConfig(self):
    original_redis_configs = {'maxmemory-policy': 'noeviction'}
    # Removing a non-existent Redis config should silently have no effect.
    new_redis_configs = {'maxmemory-policy': 'noeviction'}
    self._SetUpExpectations(original_redis_configs, new_redis_configs)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-redis-config notify-keyspace-events'.format(
            self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveAndUpdateRedisConfig(self):
    original_redis_configs = {
        'activedefrag': 'yes',
        'maxmemory-policy': 'noeviction',
        'notify-keyspace-events': 'El'
    }
    new_redis_configs = {
        'activedefrag': 'yes',
        'maxmemory-policy': 'noeviction',
        'notify-keyspace-events': 'kx'
    }
    self._SetUpExpectations(original_redis_configs, new_redis_configs)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-redis-config notify-keyspace-events'
        ' --update-redis-config notify-keyspace-events=kx'.format(
            self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveAllRedisConfigs(self):
    original_redis_configs = {
        'activedefrag': 'yes',
        'maxmemory-gb': '5.0',
        'maxmemory-policy': 'noeviction',
        'notify-keyspace-events': 'El'
    }
    new_redis_configs = {}
    self._SetUpExpectations(original_redis_configs, new_redis_configs)

    actual_instance = self.Run(
        'redis instances update {} --region {}'
        ' --remove-redis-config activedefrag,maxmemory-gb,maxmemory-policy,'
        'notify-keyspace-events'
        .format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def _SetUpExpectations(self,
                         original_redis_configs,
                         new_redis_configs,
                         expected_update_mask='redis_configs',
                         is_async=False):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    instance_to_update.redisConfigs = self.RedisConfigs(new_redis_configs)

    expected_instance = self.messages.Instance(name=self.instance_relative_name)
    expected_instance.redisConfigs = self.RedisConfigs(new_redis_configs)

    self.ExpectUpdate(
        instance_to_update,
        expected_instance,
        expected_update_mask=expected_update_mask,
        is_async=is_async)

    self.expected_instance = expected_instance


class RemoveRedisConfigsTestBeta(RemoveRedisConfigsTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class RemoveRedisConfigsTestAlpha(RemoveRedisConfigsTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class LabelsTest(InstancesUpdateUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testUpdateNonExistentLabel(self):
    original_labels = {'b': '2'}
    new_labels = {'a': '3', 'b': '2'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {} --update-labels a=3'.format(
            self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveLabel(self):
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {'b': '2'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run('redis instances update {} --region {}'
                               ' --remove-labels a'.format(
                                   self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemovePreviouslyRemovedLabel(self):
    original_labels = {'b': '2'}
    # Removing a non-existent label should silently have no effect.
    new_labels = {'b': '2'}
    self._SetUpExpectations(
        original_labels, new_labels, expected_update_mask='')

    actual_instance = self.Run('redis instances update {} --region {}'
                               ' --remove-labels a'.format(
                                   self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveAndUpdateLabel(self):
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {'b': '4', 'c': '5'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run('redis instances update {} --region {}'
                               ' --remove-labels a'
                               ' --update-labels a=3,b=4,c=5'.format(
                                   self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testRemoveAllLabels(self):
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {} --remove-labels a,b'.format(
            self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testClearLabels(self):
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {} --clear-labels'.format(
            self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def testClearAndUpdateLabels(self):
    original_labels = {'a': '1', 'b': '2'}
    new_labels = {'a': '3', 'b': '4', 'c': '5'}
    self._SetUpExpectations(original_labels, new_labels)

    actual_instance = self.Run(
        'redis instances update {} --region {} --clear-labels'
        ' --update-labels a=3,b=4,c=5'.format(self.instance_id, self.region_id))

    self.assertEqual(actual_instance, self.expected_instance)

  def _SetUpExpectations(self,
                         original_labels,
                         new_labels,
                         is_async=False,
                         expected_update_mask='labels'):
    instance_to_update = self.messages.Instance(
        name=self.instance_relative_name)
    instance_to_update.labels = self.Labels(original_labels)

    expected_instance = self.messages.Instance(name=self.instance_relative_name)
    expected_instance.labels = self.Labels(new_labels)

    self.ExpectUpdate(
        instance_to_update,
        expected_instance,
        expected_update_mask,
        is_async=is_async)

    self.expected_instance = expected_instance


class LabelsTestBeta(LabelsTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class LabelsTestAlpha(LabelsTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
