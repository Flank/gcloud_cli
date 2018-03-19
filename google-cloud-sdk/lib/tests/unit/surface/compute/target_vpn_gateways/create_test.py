# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the target-vpn-gateways create subcommand."""

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class TargetVpnGatewaysCreateTest(test_base.BaseTest):

  def testSimpleInvocationMakesRightRequest(self):
    messages = self.messages
    self.Run("""
        compute target-vpn-gateways create my-gateway
          --region my-region
          --network my-network --description "foo bar"
        """)

    self.CheckRequests(
        [(self.compute.targetVpnGateways,
          'Insert',
          messages.ComputeTargetVpnGatewaysInsertRequest(
              project='my-project',
              region='my-region',
              targetVpnGateway=messages.TargetVpnGateway(
                  name='my-gateway',
                  network=(self.compute_uri +
                           '/projects/my-project/global/networks/my-network'),
                  description='foo bar')))]
    )

  def testSimpleInvocationWithRegionPrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    messages = self.messages

    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([test_resources.REGIONS, []])

    self.Run("""
        compute target-vpn-gateways create my-gateway
          --network my-network --description "foo bar"
        """)

    self.CheckRequests(
        [(self.compute.regions,
          'List',
          messages.ComputeRegionsListRequest(project='my-project',
                                             maxResults=500))],
        [(self.compute.targetVpnGateways,
          'Insert',
          messages.ComputeTargetVpnGatewaysInsertRequest(
              project='my-project',
              region='region-1',
              targetVpnGateway=messages.TargetVpnGateway(
                  name='my-gateway',
                  network=(self.compute_uri +
                           '/projects/my-project/global/networks/my-network'),
                  description='foo bar')))]
    )

  def testFlagsAcceptUris(self):
    messages = self.messages
    self.Run("""
        compute target-vpn-gateways create
          {uri}/projects/my-project/regions/my-region/targetVpnGateways/my-gateway
          --region {uri}/projects/my-project/regions/my-region
          --network {uri}/projects/my-project/global/networks/my-network
          --description "foo bar"
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.targetVpnGateways,
          'Insert',
          messages.ComputeTargetVpnGatewaysInsertRequest(
              project='my-project',
              region='my-region',
              targetVpnGateway=messages.TargetVpnGateway(
                  name='my-gateway',
                  network=(self.compute_uri +
                           '/projects/my-project/global/networks/my-network'),
                  description='foo bar')))]
    )

  def testInvocationWithoutNetworkFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --network: Must be specified.'):
      self.Run("""
        compute target-vpn-gateways create my-gateway
          --region my-region
          """)

    self.CheckRequests()

if __name__ == '__main__':
  test_case.main()
