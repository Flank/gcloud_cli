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
"""Tests for the target-vpn-gateways describe subcommand."""
import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  if api_version == 'v1':
    test_obj.target_vpn_gateways = test_resources.TARGET_VPN_GATEWAYS_V1
  elif api_version == 'beta':
    test_obj.target_vpn_gateways = test_resources.TARGET_VPN_GATEWAYS_BETA
  else:
    raise ValueError('api_version must be \'v1\' or \'beta\'. '
                     'Got [{0}].'.format(api_version))


class TargetVpnGatewaysDescribeTest(test_base.BaseTest,
                                    test_case.WithOutputCapture):

  def SetUp(self):
    SetUp(self, 'v1')

  def testSimpleInvocationMakesRightRequest(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.target_vpn_gateways[0]],
    ])

    self.Run("""
        compute target-vpn-gateways describe gateway-1
            --region region-1
        """)

    self.CheckRequests(
        [(self.compute.targetVpnGateways,
          'Get',
          messages.ComputeTargetVpnGatewaysGetRequest(
              project='my-project',
              region='region-1',
              targetVpnGateway='gateway-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: gateway 1 description
            id: '123456'
            name: gateway-1
            network: my-network
            region: {uri}/projects/my-project/regions/region-1
            selfLink: {uri}/projects/my-project/regions/region-1/targetVpnGateways/gateway-1
            status: READY
            tunnels:
            - {uri}/projects/my-project/regions/region-1/tunnels/tunnel-1
            """.format(uri=self.compute_uri)))


if __name__ == '__main__':
  test_case.main()
