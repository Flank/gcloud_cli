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
"""Base classes for gcloud redis tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib import redis
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class UnitTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for `gcloud redis` unit tests."""

  def SetUp(self):
    if not hasattr(self, 'api_version'):
      self.api_version = redis.API_VERSION_FOR_TRACK[self.track]
    self.mock_client = mock.Client(
        client_class=apis.GetClientClass('redis', self.api_version))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.messages = self.mock_client.MESSAGES_MODULE

    self.project_ref = resources.REGISTRY.Create(
        'redis.projects', projectsId=self.Project())

    self.locations_service = self.mock_client.projects_locations
    self.instances_service = self.mock_client.projects_locations_instances
    self.operations_service = self.mock_client.projects_locations_operations

    self.region_id = 'us-central1'
    self.region_ref = resources.REGISTRY.Parse(
        self.region_id,
        collection='redis.projects.locations',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.region_relative_name = self.region_ref.RelativeName()


class InstancesUnitTestBase(UnitTestBase):
  """Base class for `gcloud redis instances` unit tests."""

  def SetUp(self):
    self.SetUpInstancesForTrack()

  def SetUpInstancesForTrack(self):
    self.instance_id = 'my-redis-instance'
    self.instance_ref = resources.REGISTRY.Parse(
        self.instance_id,
        collection='redis.projects.locations.instances',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.instance_relative_name = self.instance_ref.RelativeName()

    self.wait_operation_id = 'redis-wait-operation'
    self.wait_operation_ref = resources.REGISTRY.Parse(
        self.wait_operation_id,
        collection='redis.projects.locations.operations',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.wait_operation_relative_name = self.wait_operation_ref.RelativeName()

  def MakeDefaultInstance(self, name=None):
    network_ref = resources.REGISTRY.Create(
        'compute.networks', project=self.Project(), network='default')
    return self.messages.Instance(
        name=name,
        authorizedNetwork=network_ref.RelativeName(),
        memorySizeGb=1,
        tier=self.messages.Instance.TierValueValuesEnum('BASIC'))

  def MakeAllOptionsInstance(self,
                             name=None,
                             redis_version='REDIS_3_2',
                             connect_mode='DIRECT_PEERING',
                             transit_encryption_mode=None):
    network_ref = resources.REGISTRY.Create(
        'compute.networks', project=self.Project(), network='my-network')
    redis_configs = {
        'maxmemory-policy': 'noeviction',
        'notify-keyspace-events': 'El'
    }
    if redis_version == 'REDIS_4_0' or redis_version == 'REDIS_5_0':
      redis_configs['maxmemory-policy'] = 'allkeys-lfu'
      redis_configs['activedefrag'] = 'yes'
      redis_configs['lfu-log-factor'] = '2'
      redis_configs['lfu-decay-time'] = '10'
    if redis_version == 'REDIS_5_0':
      redis_configs['stream-node-max-entries'] = '100'
      redis_configs['stream-node-max-bytes'] = '4096'

    redis_instance = self.messages.Instance(
        name=name,
        alternativeLocationId='zone2',
        authorizedNetwork=network_ref.RelativeName(),
        displayName='my-display-name',
        labels=encoding.DictToAdditionalPropertyMessage(
            {
                'a': '1',
                'b': '2'
            },
            self.messages.Instance.LabelsValue,
            sort_items=True),
        locationId='zone1',
        memorySizeGb=4,
        redisConfigs=encoding.DictToAdditionalPropertyMessage(
            redis_configs,
            self.messages.Instance.RedisConfigsValue,
            sort_items=True),
        redisVersion=redis_version,
        tier=self.messages.Instance.TierValueValuesEnum('STANDARD_HA'))

    if connect_mode == 'DIRECT_PEERING':
      redis_instance.reservedIpRange = '10.0.0.0/29'
      redis_instance.connectMode = self.messages.Instance.ConnectModeValueValuesEnum(
          'DIRECT_PEERING')
    else:
      redis_instance.connectMode = self.messages.Instance.ConnectModeValueValuesEnum(
          'PRIVATE_SERVICE_ACCESS')

    if transit_encryption_mode == 'SERVER_AUTHENTICATION':
      redis_instance.transitEncryptionMode = self.messages.Instance.TransitEncryptionModeValueValuesEnum(
          'SERVER_AUTHENTICATION')
    return redis_instance


class OperationsUnitTestBase(UnitTestBase):
  """Base class for `gcloud redis operations` unit tests."""

  def SetUp(self):
    self.SetUpOperationsForTrack()

  def SetUpOperationsForTrack(self):
    self.operation_id = 'my-redis-operation'
    self.operation_ref = resources.REGISTRY.Parse(
        self.operation_id,
        collection='redis.projects.locations.operations',
        params={
            'locationsId': self.region_id,
            'projectsId': self.Project()
        },
        api_version=self.api_version)
    self.operation_relative_name = self.operation_ref.RelativeName()
