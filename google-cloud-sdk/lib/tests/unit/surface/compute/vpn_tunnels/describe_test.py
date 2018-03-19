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
"""Tests for the vpn-tunnels describe subcommand."""
import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  if api_version == 'v1':
    test_obj.vpn_tunnels = test_resources.VPN_TUNNELS_V1
  elif api_version == 'beta':
    test_obj.vpn_tunnels = test_resources.VPN_TUNNELS_BETA
  else:
    raise ValueError('api_version must be \'v1\' or \'beta\'.'
                     'Got [{0}].'.format(api_version))


class VpnTunnelsDescribeTest(test_base.BaseTest, test_case.WithOutputCapture):

  def SetUp(self):
    SetUp(self, 'v1')

  def testSimpleInvocationMakesRightRequest(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.vpn_tunnels[0]],
    ])

    self.Run("""
        compute vpn-tunnels describe tunnel-1
            --region region-1
        """)

    self.CheckRequests(
        [(self.compute.vpnTunnels,
          'Get',
          messages.ComputeVpnTunnelsGetRequest(
              project='my-project',
              region='region-1',
              vpnTunnel='tunnel-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            creationTimestamp: '2011-11-11T17:54:10.636-07:00'
            description: the first tunnel
            ikeVersion: 1
            name: tunnel-1
            peerIp: 1.1.1.1
            region: {uri}/projects/my-project/regions/region-1
            selfLink: {uri}/projects/my-project/regions/region-1/vpnTunnels/tunnel-1
            sharedSecretHash: ff33f3a693905de7e85178529e3a13feb85a3964
            status: ESTABLISHED
            targetVpnGateway: {uri}/projects/my-project/regions/region-1/targetVpnGateways/gateway-1
            """.format(uri=self.compute_uri)))


if __name__ == '__main__':
  test_case.main()
