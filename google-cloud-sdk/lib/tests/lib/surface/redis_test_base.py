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
"""Base classes for gcloud redis tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib import redis
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


TEST_REGION = 'us-central1'
# The default network in the cloud-sdk-integration-testing project is LEGACY
# and will not work with the Redis API.
E2E_TEST_NETWORK = 'do-not-delete-redis-test'


class UnitTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for `gcloud redis` unit tests."""

  def SetUpForTrack(self, track):
    self.track = track
    self.api_version = redis.API_VERSION_FOR_TRACK[track]
    self.mock_client = mock.Client(
        client_class=apis.GetClientClass('redis', self.api_version))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    self.messages = self.mock_client.MESSAGES_MODULE

    self.project_ref = resources.REGISTRY.Create('redis.projects',
                                                 projectsId=self.Project())

    self.locations_service = self.mock_client.projects_locations
    self.instances_service = self.mock_client.projects_locations_instances
    self.operations_service = self.mock_client.projects_locations_operations

    self.region_id = 'us-central1'
    self.region_ref = resources.REGISTRY.Parse(
        self.region_id, collection='redis.projects.locations',
        params={'locationsId': self.region_id, 'projectsId': self.Project()},
        api_version=self.api_version)
    self.region_relative_name = self.region_ref.RelativeName()


class InstancesUnitTestBase(UnitTestBase):
  """Base class for `gcloud redis instances` unit tests."""

  def SetUpInstancesForTrack(self):
    self.instance_id = 'my-redis-instance'
    self.instance_ref = resources.REGISTRY.Parse(
        self.instance_id, collection='redis.projects.locations.instances',
        params={'locationsId': self.region_id, 'projectsId': self.Project()},
        api_version=self.api_version)
    self.instance_relative_name = self.instance_ref.RelativeName()

    self.wait_operation_id = 'redis-wait-operation'
    self.wait_operation_ref = resources.REGISTRY.Parse(
        self.wait_operation_id,
        collection='redis.projects.locations.operations',
        params={'locationsId': self.region_id, 'projectsId': self.Project()},
        api_version=self.api_version)
    self.wait_operation_relative_name = self.wait_operation_ref.RelativeName()

  def MakeDefaultInstance(self, name=None):
    network_ref = resources.REGISTRY.Create(
        'compute.networks', project=self.Project(), network='default')
    return self.messages.Instance(
        name=name, authorizedNetwork=network_ref.RelativeName(), memorySizeGb=1,
        tier=self.messages.Instance.TierValueValuesEnum('BASIC'))

  def MakeAllOptionsInstance(self, name=None):
    network_ref = resources.REGISTRY.Create(
        'compute.networks', project=self.Project(), network='my-network')
    return self.messages.Instance(
        name=name,
        alternativeLocationId='zone2',
        authorizedNetwork=network_ref.RelativeName(),
        displayName='my-display-name',
        labels=encoding.DictToAdditionalPropertyMessage(
            {'a': '1', 'b': '2'}, self.messages.Instance.LabelsValue,
            sort_items=True),
        locationId='zone1',
        memorySizeGb=4,
        redisConfigs=encoding.DictToAdditionalPropertyMessage(
            {'maxmemory-policy': 'noeviction', 'notify-keyspace-events': 'El'},
            self.messages.Instance.RedisConfigsValue, sort_items=True),
        redisVersion='REDIS_3_2',
        reservedIpRange='10.0.0.0/29',
        tier=self.messages.Instance.TierValueValuesEnum('STANDARD_HA'))


class OperationsUnitTestBase(UnitTestBase):
  """Base class for `gcloud redis operations` unit tests."""

  def SetUpOperationsForTrack(self):
    self.operation_id = 'my-redis-operation'
    self.operation_ref = resources.REGISTRY.Parse(
        self.operation_id,
        collection='redis.projects.locations.operations',
        params={'locationsId': self.region_id, 'projectsId': self.Project()},
        api_version=self.api_version)
    self.operation_relative_name = self.operation_ref.RelativeName()


class E2eTestBase(e2e_base.WithServiceAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  @contextlib.contextmanager
  def CreateInstance(self, instance_id, region):
    try:
      yield self.Run(
          'redis instances create --region {region} {instance_id}'
          ' --network {network}'
          .format(region=region, instance_id=instance_id,
                  network=E2E_TEST_NETWORK))
    finally:
      self.Run('redis instances delete --region {region} {instance_id} --quiet'
               .format(region=region, instance_id=instance_id))
