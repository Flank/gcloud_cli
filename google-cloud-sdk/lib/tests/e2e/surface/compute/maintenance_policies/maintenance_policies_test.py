# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration tests for maintenance policies."""
import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.maintenance_policies import util
from googlecloudsdk.core import resources
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class MaintenancePoliciesTest(e2e_test_base.BaseTest):
  """Maintenance policies tests."""

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', 'alpha')

  def _GetPolicyRef(self, policy_name):
    return util.ParseMaintenancePolicy(
        self.registry, policy_name, self.Project(), self.region)

  def _GetResourceName(self):
    return e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test').next()

  @contextlib.contextmanager
  def _CreateInstance(self):
    try:
      instance_name = self._GetResourceName()
      self.Run('compute instances create {0} --zone {1}'
               .format(instance_name, self.zone))
      self.Run('compute instances list')
      self.AssertNewOutputContains(instance_name)
      yield instance_name
    finally:
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))

  @contextlib.contextmanager
  def _CreateMaintenancePolicy(self):
    try:
      policy_name = self._GetResourceName()
      self.Run('compute maintenance-policies create {0} --region {1} '
               '--start-time 04:00Z' .format(policy_name, self.region))
      self.Run('compute maintenance-policies list')
      self.AssertNewOutputContains(policy_name)
      yield policy_name
    finally:
      self.Run('compute maintenance-policies delete {0} --region {1} '
               '--quiet'.format(policy_name, self.region))

  def _TestAddPolicyAndDescribeInstance(self, instance_name, policy_name):
    policy_ref = self._GetPolicyRef(policy_name)
    self.Run('compute instances add-maintenance-policies {0} --zone {1} '
             '--resource-maintenance-policies {2}'.format(
                 instance_name, self.zone, policy_name))
    self.Run('compute instances describe {0} --zone {1}'
             .format(instance_name, self.zone))
    self.AssertNewOutputContains(policy_ref.SelfLink())

  def testMaintenancePolicy(self):
    with self._CreateMaintenancePolicy() as policy_name:
      with self._CreateInstance() as instance_name:
        self._TestAddPolicyAndDescribeInstance(instance_name, policy_name)
