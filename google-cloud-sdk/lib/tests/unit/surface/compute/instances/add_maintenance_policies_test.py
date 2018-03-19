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
"""Tests for the instances add-maintenance-policies subcommand."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.maintenance_policies import util
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InstancesAddMaintenancePoliciesTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.instance_name = 'my-instance'
    self.zone = 'central2-a'
    self.region = 'central2'

    self.reg = resources.REGISTRY.Clone()
    self.reg.RegisterApiByName('compute', 'alpha')

    self.maintenance_policy_ref = util.ParseMaintenancePolicy(
        self.reg, 'pol1', project=self.Project(), region=self.region)

  def _CheckAddRequest(self, policy_ref):
    add_request = self.messages.ComputeInstancesAddMaintenancePoliciesRequest(
        instance=self.instance_name,
        project=self.Project(),
        zone=self.zone,
        instancesAddMaintenancePoliciesRequest=
        self.messages.InstancesAddMaintenancePoliciesRequest(
            maintenancePolicies=[policy_ref.SelfLink()]))
    self.CheckRequests(
        [(self.compute_alpha.instances,
          'AddMaintenancePolicies',
          add_request)],
    )

  def testAddSinglePolicy(self):
    self.Run('compute instances add-maintenance-policies {instance} '
             '--zone {zone} --resource-maintenance-policies pol1'
             .format(instance=self.instance_name,
                     zone=self.zone))
    self._CheckAddRequest(self.maintenance_policy_ref)

  def testAddSinglePolicySelfLink(self):
    self.Run('compute instances add-maintenance-policies {instance} '
             '--zone {zone} --resource-maintenance-policies {policy}'
             .format(instance=self.instance_name,
                     zone=self.zone,
                     policy=self.maintenance_policy_ref.SelfLink()))
    self._CheckAddRequest(self.maintenance_policy_ref)

  def testAddNoPolicies(self):
    with self.assertRaisesRegexp(
        cli_test_base.MockArgumentError,
        'argument --resource-maintenance-policies: Must be specified.'):
      self.Run('compute instances add-maintenance-policies {instance} '
               '--zone {zone}'
               .format(instance=self.instance_name, zone=self.zone))


if __name__ == '__main__':
  test_case.main()
