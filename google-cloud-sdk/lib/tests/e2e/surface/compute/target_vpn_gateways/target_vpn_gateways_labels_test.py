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
"""Integration tests for target VPN gateways labels."""

import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class TargetVpnGatewaysLabelsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

    self.network_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-network').next()
    self.target_vpn_gateway_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-target-vpn-gateway').next()

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    try:
      cmd = (subcommand, 'delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass

  @contextlib.contextmanager
  def _TargetVpnGateway(self, network_name, target_vpn_gateway_name, region):
    try:
      yield self.RunCompute('target-vpn-gateways', 'create',
                            target_vpn_gateway_name, '--region', region,
                            '--network', 'default')
    finally:
      self.CleanUpResource('target-vpn-gateways', target_vpn_gateway_name,
                           '--region', region)

  def testTargetVpnGateways(self):
    with self._TargetVpnGateway(self.network_name, self.target_vpn_gateway_name,
                                self.region):
      self._TestUpdateLabels()

  def _TestUpdateLabels(self):

    def CreateUpdateLabelsArg(labels):
      return ','.join('{0}={1}'.format(pair[0], pair[1]) for pair in labels)

    add_labels_arg = CreateUpdateLabelsArg([('x', 'y'), ('abc', 'xyz')])
    self.Run(('compute target-vpn-gateways update '
              '{0} --region {1} --update-labels {2}').format(
                  self.target_vpn_gateway_name, self.region, add_labels_arg))
    self.Run('compute target-vpn-gateways describe {0} --region {1}'.format(
        self.target_vpn_gateway_name, self.region))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

    # Modify the label with key 'x', remove the label with key 'abc', and
    # add label with key 't123'.
    # Remove should take precedence over update for 'abc'.
    update_labels_arg = CreateUpdateLabelsArg([('x', 'a'), ('abc', 'xyz'),
                                               ('t123', 't7890')])
    remove_labels_arg = 'abc'
    self.Run("""
         compute target-vpn-gateways update {0} --region {1}
             --update-labels {2} --remove-labels {3}
        """.format(self.target_vpn_gateway_name, self.region, update_labels_arg,
                   remove_labels_arg))

    self.Run('compute target-vpn-gateways describe {0} --region {1}'.format(
        self.target_vpn_gateway_name, self.region))
    self.AssertNewOutputContains('t123: t7890', reset=False)
    self.AssertNewOutputContains('x: a', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')


if __name__ == '__main__':
  e2e_test_base.main()
