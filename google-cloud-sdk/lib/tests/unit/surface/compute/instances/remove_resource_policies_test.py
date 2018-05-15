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
"""Tests for the instances remove-resource-policies subcommand."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InstancesRemoveResourcePoliciesTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.instance_name = 'my-instance'
    self.zone = 'central2-a'
    self.region = 'central2'

    self.reg = resources.REGISTRY.Clone()
    self.reg.RegisterApiByName('compute', 'alpha')

  def _CheckRemoveRequest(self, policy_names):
    request_cls = self.messages.ComputeInstancesRemoveResourcePoliciesRequest
    remove_request = request_cls(
        instance=self.instance_name,
        project=self.Project(),
        zone=self.zone,
        instancesRemoveResourcePoliciesRequest=
        self.messages.InstancesRemoveResourcePoliciesRequest(
            resourcePolicies=[
                self.compute_uri + '/projects/{0}/regions/{1}/'
                'resourcePolicies/{2}'.format(
                    self.Project(), self.region, name)
                for name in policy_names]))
    self.CheckRequests(
        [(self.compute_alpha.instances,
          'RemoveResourcePolicies',
          remove_request)],
    )

  def testRemoveSinglePolicy(self):
    self.Run('compute instances remove-resource-policies {instance} '
             '--zone {zone} --resource-policies pol1'
             .format(instance=self.instance_name,
                     zone=self.zone))
    self._CheckRemoveRequest(['pol1'])

  def testRemoveMultiplePolicies(self):
    self.Run('compute instances remove-resource-policies {instance} '
             '--zone {zone} --resource-policies pol1,pol2'
             .format(instance=self.instance_name,
                     zone=self.zone))
    self._CheckRemoveRequest(['pol1', 'pol2'])

  def testRemoveSinglePolicySelfLink(self):
    policy_name = 'pol1'
    policy_self_link = (self.compute_uri + '/projects/{0}/regions/{1}/'
                        'resourcePolicies/{2}'.format(
                            self.Project(), self.region, policy_name))
    self.Run('compute instances remove-resource-policies {instance} '
             '--zone {zone} --resource-policies {policy}'
             .format(instance=self.instance_name,
                     zone=self.zone,
                     policy=policy_self_link))
    self._CheckRemoveRequest([policy_name])

  def testRemoveNoPolicies(self):
    with self.assertRaisesRegexp(
        cli_test_base.MockArgumentError,
        'argument --resource-policies: Must be specified.'):
      self.Run('compute instances remove-resource-policies {instance} '
               '--zone {zone}'
               .format(instance=self.instance_name, zone=self.zone))


if __name__ == '__main__':
  test_case.main()
