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
"""Integration tests for network endpoint groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import retry
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class NetworkEndpointGroupsTest(e2e_test_base.BaseTest):
  """Network endpoint groups tests."""

  SUBNET_RANGE = '10.33.0.0/16'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', 'v1')

  def _GetResourceName(self):
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-neg-test'))

  @contextlib.contextmanager
  def _CreateNetwork(self):
    network_name = self._GetResourceName()
    try:
      self.Run('compute networks create {0}'
               ' --subnet-mode=custom'.format(network_name))
      yield network_name
    finally:
      retry.RetryOnException(self.Run, max_retrials=3, sleep_ms=1000)(
          'compute networks delete {} -q'.format(network_name))

  @contextlib.contextmanager
  def _CreateSubnet(self, network_name):
    subnetwork_name = self._GetResourceName()
    try:
      self.Run('compute networks subnets create {0}'
               ' --network {1}'
               ' --region {2}'
               ' --range {3}'.format(subnetwork_name, network_name,
                                     self.region, self.SUBNET_RANGE))
      yield subnetwork_name
    finally:
      retry.RetryOnException(self.Run, max_retrials=3, sleep_ms=1000)(
          'compute networks subnets delete {0} --region {1} -q'.format(
              subnetwork_name, self.region))

  @contextlib.contextmanager
  def _CreateInstance(self, network_name, subnetwork_name):
    instance_name = self._GetResourceName()
    try:
      self.Run('compute instances create {0} --zone {1} '
               '--network {2} --subnet {3}'
               .format(instance_name, self.zone, network_name, subnetwork_name))
      yield instance_name
    finally:
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))

  @contextlib.contextmanager
  def _CreateHealthCheck(self, health_check_name):
    try:
      self.Run(
          'compute health-checks create http {} '
          '--use-serving-port'.format(
              health_check_name))
      yield health_check_name
    finally:
      self.Run('compute health-checks delete {0} --quiet'.format(
          health_check_name))

  @contextlib.contextmanager
  def _CreateBackendService(self, health_check_name):
    backend_name = self._GetResourceName()
    try:
      self.Run('compute backend-services create {0} --global '
               '--load-balancing-scheme=external '
               '--health-checks {1} --protocol tcp'
               .format(backend_name, health_check_name))
      yield backend_name
    finally:
      self.Run('compute backend-services delete {0} --global '
               '--quiet'.format(backend_name))

  @contextlib.contextmanager
  def _CreateBackendServiceForHybridNeg(self, health_check_name):
    backend_name = self._GetResourceName()
    try:
      self.Run('compute backend-services create {0} --global '
               '--load-balancing-scheme=INTERNAL_SELF_MANAGED '
               '--health-checks {1}'.format(backend_name, health_check_name))
      yield backend_name
    finally:
      self.Run('compute backend-services delete {0} --global '
               '--quiet'.format(backend_name))

  @contextlib.contextmanager
  def _CreateNetworkEndpointGroup(self, network_name, subnetwork_name):
    neg_name = self._GetResourceName()
    try:
      self.Run('compute network-endpoint-groups create {0} --zone {1} '
               '--network {2} --subnet {3}'
               .format(neg_name, self.zone, network_name, subnetwork_name))
      self.Run('compute network-endpoint-groups list')
      self.AssertNewOutputContains(neg_name)
      yield neg_name
    finally:
      self.Run('compute network-endpoint-groups delete {0} --zone {1} '
               '--quiet'.format(neg_name, self.zone))

  @contextlib.contextmanager
  def _CreateHybridNetworkEndpointGroup(self, network_name):
    neg_name = self._GetResourceName()
    try:
      self.Run('compute network-endpoint-groups create {0} --zone {1} '
               '--network {2} --network-endpoint-type non-gcp-private-ip-port'
               .format(neg_name, self.zone, network_name))
      self.Run('compute network-endpoint-groups list')
      self.AssertNewOutputContains(neg_name)
      yield neg_name
    finally:
      self.Run('compute network-endpoint-groups delete {0} --zone {1} '
               '--quiet'.format(neg_name, self.zone))

  @contextlib.contextmanager
  def _CreateBackendServiceForRegionalNeg(self):
    backend_name = self._GetResourceName()
    try:
      self.Run(
          'compute backend-services create {0} --global'.format(backend_name))
      yield backend_name
    finally:
      self.Run('compute backend-services delete {0} --global '
               '--quiet'.format(backend_name))

  @contextlib.contextmanager
  def _CreateRegionalNetworkEndpointGroup(self):
    neg_name = self._GetResourceName()
    try:
      self.Run('compute network-endpoint-groups create {0} --region {1} '
               '--network-endpoint-type=SERVERLESS --app-engine-service=default'
               .format(neg_name, self.region))
      self.Run('compute network-endpoint-groups list')
      self.AssertNewOutputContains(neg_name)
      yield neg_name
    finally:
      self.Run('compute network-endpoint-groups delete {0} --region {1} '
               '--quiet'.format(neg_name, self.region))

  def testNetworkEndpointGroups(self):
    health_check_name = self._GetResourceName()
    with self._CreateNetwork() as network_name, \
        self._CreateSubnet(network_name) as subnetwork_name, \
        self._CreateHealthCheck(health_check_name), \
         self._CreateNetworkEndpointGroup(network_name, subnetwork_name
                                          ) as neg_name, \
         self._CreateBackendService(health_check_name) as backend_name, \
         self._CreateInstance(network_name, subnetwork_name) as instance_name:
      self.Run('compute network-endpoint-groups update {0} --zone={1} '
               '--add-endpoint instance={2},port=80'.format(
                   neg_name, self.zone, instance_name))
      self.Run('compute network-endpoint-groups list-network-endpoints {0} '
               '--zone {1}'.format(neg_name, self.zone))
      self.AssertNewOutputContains(instance_name)

      self.Run('compute backend-services add-backend {0} --global '
               '--balancing-mode CONNECTION --max-connections 100 '
               '--network-endpoint-group {1} '
               '--network-endpoint-group-zone {2}'.format(
                   backend_name, neg_name, self.zone))

      self.Run('compute backend-services describe {0} --global'.format(
          backend_name))
      self.AssertNewOutputContains(neg_name)

      self.Run('compute backend-services remove-backend {0} --global '
               '--network-endpoint-group {1} '
               '--network-endpoint-group-zone {2}'.format(
                   backend_name, neg_name, self.zone))
      self.Run('compute backend-services describe {0} --global'.format(
          backend_name))
      self.AssertNewOutputNotContains(neg_name)

  def testHybridNetworkEndpointGroups(self):
    health_check_name = self._GetResourceName()
    with self._CreateNetwork() as network_name, \
        self._CreateHealthCheck(health_check_name), \
        self._CreateHybridNetworkEndpointGroup(network_name) as neg_name, \
        self._CreateBackendServiceForHybridNeg(health_check_name) as backend_name:
      self.Run('compute network-endpoint-groups update {0} --zone={1} '
               '--add-endpoint ip=10.138.0.2,port=80'.format(
                   neg_name, self.zone))
      self.Run('compute network-endpoint-groups list-network-endpoints {0} '
               '--zone {1}'.format(neg_name, self.zone))
      self.AssertNewOutputContains('10.138.0.2')

      self.Run('compute backend-services add-backend {0} --global '
               '--balancing-mode RATE --max-rate-per-endpoint 5 '
               '--network-endpoint-group {1} '
               '--network-endpoint-group-zone {2}'.format(
                   backend_name, neg_name, self.zone))

      self.Run(
          'compute backend-services describe {0} --global'.format(backend_name))
      self.AssertNewOutputContains(neg_name)

      self.Run('compute backend-services remove-backend {0} --global '
               '--network-endpoint-group {1} '
               '--network-endpoint-group-zone {2}'.format(
                   backend_name, neg_name, self.zone))
      self.Run(
          'compute backend-services describe {0} --global'.format(backend_name))
      self.AssertNewOutputNotContains(neg_name)

  def testRegionalNetworkEndpointGroups(self):
    with self._CreateRegionalNetworkEndpointGroup() as neg_name, \
        self._CreateBackendServiceForRegionalNeg() as backend_name:

      self.Run('compute backend-services add-backend {0} --global '
               '--network-endpoint-group {1} '
               '--network-endpoint-group-region {2}'.format(
                   backend_name, neg_name, self.region))

      self.Run(
          'compute backend-services describe {0} --global'.format(backend_name))
      self.AssertNewOutputContains(neg_name)

      self.Run('compute backend-services remove-backend {0} --global '
               '--network-endpoint-group {1} '
               '--network-endpoint-group-region {2}'.format(
                   backend_name, neg_name, self.region))
      self.Run(
          'compute backend-services describe {0} --global'.format(backend_name))
      self.AssertNewOutputNotContains(neg_name)


class NetworkEndpointGroupsBetaTest(NetworkEndpointGroupsTest):
  """Network endpoint groups alpha tests."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', 'beta')


class NetworkEndpointGroupsAlphaTest(NetworkEndpointGroupsBetaTest):
  """Network endpoint groups alpha tests."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', 'alpha')

  @contextlib.contextmanager
  def _CreateHealthCheck(self, health_check_name):
    try:
      self.Run('compute health-checks create http {} '
               '--use-serving-port --global'.format(health_check_name))
      yield health_check_name
    finally:
      self.Run('compute health-checks delete {0} --quiet --global'.format(
          health_check_name))

  @contextlib.contextmanager
  def _CreateBackendService(self, health_check_name):
    backend_name = self._GetResourceName()
    try:
      self.Run('compute backend-services create {0} --global '
               '--load-balancing-scheme=external '
               '--health-checks {1} --global-health-checks --protocol tcp'
               .format(backend_name, health_check_name))
      yield backend_name
    finally:
      self.Run('compute backend-services delete {0} --global '
               '--quiet'.format(backend_name))

if __name__ == '__main__':
  e2e_test_base.main()
