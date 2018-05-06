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
"""Integration tests for network endpoint groups."""
import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class NetworkEndpointGroupsTest(e2e_test_base.BaseTest):
  """Network endpoint groups tests."""

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', 'alpha')

    # Currently only us-east2-a is supported.
    self.region = 'us-east2'
    self.zone = 'us-east2-a'

  def _GetResourceName(self):
    return e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-neg-test').next()

  @contextlib.contextmanager
  def _CreateInstance(self):
    instance_name = self._GetResourceName()
    try:
      self.Run('compute instances create {0} --zone {1}'
               .format(instance_name, self.zone))
      yield instance_name
    finally:
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))

  @contextlib.contextmanager
  def _CreateHealthCheck(self, health_check_name):
    try:
      self.Run(
          'compute health-checks create tcp {} '
          '--port-specification USE_SERVING_PORT'.format(
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
  def _CreateNetworkEndpointGroup(self):
    neg_name = self._GetResourceName()
    try:
      self.Run('compute network-endpoint-groups create {0} --zone {1}'
               .format(neg_name, self.zone))
      self.Run('compute network-endpoint-groups list')
      self.AssertNewOutputContains(neg_name)
      yield neg_name
    finally:
      self.Run('compute network-endpoint-groups delete {0} --zone {1} '
               '--quiet'.format(neg_name, self.zone))

  def testNetworkEndpointGroups(self):
    health_check_name = self._GetResourceName()
    with self._CreateHealthCheck(health_check_name), \
         self._CreateNetworkEndpointGroup() as neg_name, \
         self._CreateBackendService(health_check_name) as backend_name, \
         self._CreateInstance() as instance_name:
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
