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

"""Tests for the vpn-tunnels create subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

_LONG_SECRET = ('So long as you are praised think only that you are not '
                'yet on your own path but on that of another.'
                '- Friedrich Nietzsche !@#$%^&*()_+=')


class VpnTunnelsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')

  def testSimpleInvocationMakesRightRequest(self):
    messages = self.messages
    self.make_requests.side_effect = [[
        messages.VpnTunnel(
            name='my-tunnel',
            region='my-region',
            targetVpnGateway='my-gateway',
            peerIp='1.2.3.4')
    ]]

    self.Run("""\
        compute vpn-tunnels create my-tunnel
          --region my-region
          --description "foo bar"
          --ike-version 2
          --peer-address 1.2.3.4
          --shared-secret secret-xyz
          --target-vpn-gateway my-gateway
        """)

    self.CheckRequests(
        [(self.compute.vpnTunnels,
          'Insert',
          messages.ComputeVpnTunnelsInsertRequest(
              project='my-project',
              region='my-region',
              vpnTunnel=messages.VpnTunnel(
                  name='my-tunnel',
                  description='foo bar',
                  ikeVersion=2,
                  peerIp='1.2.3.4',
                  sharedSecret='secret-xyz',
                  targetVpnGateway=(self.compute_uri +
                                    '/projects/my-project/regions'
                                    '/my-region/targetVpnGateways/my-gateway')
                  )))]
    )

    self.AssertOutputEquals("""\
      NAME       REGION     GATEWAY     PEER_ADDRESS
      my-tunnel  my-region  my-gateway  1.2.3.4
      """, normalize_space=True)

  def TemplateTestWithDefaultValuesForOptionalArgs(self, cmd,
                                                   list_regions=False):
    messages = self.messages
    self.Run(cmd)

    self.CheckRequests(
        ([self.regions_list_request] if list_regions else []) +
        [(self.compute.vpnTunnels,
          'Insert',
          messages.ComputeVpnTunnelsInsertRequest(
              project='my-project',
              region='my-region',
              vpnTunnel=messages.VpnTunnel(
                  name='my-tunnel',
                  peerIp='1.2.3.4',
                  sharedSecret='secret-xyz',
                  targetVpnGateway=(self.compute_uri +
                                    '/projects/my-project/regions'
                                    '/my-region/targetVpnGateways/my-gateway')
                  )))])

  def testFlagsAcceptUris(self):
    self.TemplateTestWithDefaultValuesForOptionalArgs("""\
        compute vpn-tunnels create {uri}/projects/my-project/regions/my-region/vpnTunnels/my-tunnel
          --region {uri}/projects/my-project/regions/my-region
          --peer-address 1.2.3.4
          --shared-secret secret-xyz
          --target-vpn-gateway {uri}/projects/my-project/regions/my-region/targetVpnGateways/my-gateway
        """.format(uri=self.compute_uri))

  def testInvocationWithoutOptionalArgsOk(self):
    self.TemplateTestWithDefaultValuesForOptionalArgs("""\
        compute vpn-tunnels create my-tunnel
          --region my-region
          --peer-address 1.2.3.4
          --shared-secret secret-xyz
          --target-vpn-gateway my-gateway
        """)

  def testInvocationWithoutRegionPrompts(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    messages = self.messages
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [
            messages.Region(name='us-central1'),
            messages.Region(name='my-region'),
        ],

        [],
    ])

    self.Run("""\
        compute vpn-tunnels create my-tunnel
          --peer-address 1.2.3.4
          --shared-secret secret-xyz
          --target-vpn-gateway my-gateway
        """)

  def testInvocationWithoutPeerAddressFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --peer-address: Must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --shared-secret secret-xyz
            --target-vpn-gateway my-gateway
          """)

    self.CheckRequests()

  def testInvocationWithoutSharedSecretFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --shared-secret: Must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-address 1.2.3.4
            --target-vpn-gateway my-gateway
          """)

    self.CheckRequests()

  def testInvocationWithBadSharedSecretFails(self):
    with self.AssertRaisesArgumentError():
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-address 1.2.3.4
            --target-vpn-gateway my-gateway
            --shared-secret '\n'
          """)

    self.CheckRequests()
    self.AssertErrContains(
        'The argument to --shared-secret is not valid it contains '
        'non-printable charcters.')

  def testInvocationWithoutTargetVpnGatewayFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-vpn-gateway: Must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-address 1.2.3.4
            --shared-secret secret-xyz
          """)

    self.CheckRequests()

  def testRemoteTrafficSelector(self):
    messages = self.messages
    self.Run("""\
        compute vpn-tunnels create my-tunnel
          --region my-region
          --description "foo bar"
          --ike-version 2
          --remote-traffic-selector 192.168.100.14/24,10.0.0.0/8
          --peer-address 1.2.3.4
          --shared-secret secret-xyz
          --target-vpn-gateway my-gateway
        """)

    self.CheckRequests(
        [(self.compute.vpnTunnels,
          'Insert',
          messages.ComputeVpnTunnelsInsertRequest(
              project='my-project',
              region='my-region',
              vpnTunnel=messages.VpnTunnel(
                  name='my-tunnel',
                  description='foo bar',
                  ikeVersion=2,
                  remoteTrafficSelector=['192.168.100.14/24', '10.0.0.0/8'],
                  peerIp='1.2.3.4',
                  sharedSecret='secret-xyz',
                  targetVpnGateway=(self.compute_uri +
                                    '/projects/my-project/regions'
                                    '/my-region/targetVpnGateways/my-gateway')
                  )))]
    )


class VpnTunnelsCreateTestBeta(VpnTunnelsCreateTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testLocalTrafficSelector(self):
    messages = self.messages
    self.Run("""\
        compute vpn-tunnels create my-tunnel
          --region my-region
          --description "foo bar"
          --ike-version 2
          --local-traffic-selector 192.168.100.14/24,10.0.0.0/8
          --peer-address 1.2.3.4
          --shared-secret secret-xyz
          --target-vpn-gateway my-gateway
        """)

    self.CheckRequests(
        [(self.compute.vpnTunnels,
          'Insert',
          messages.ComputeVpnTunnelsInsertRequest(
              project='my-project',
              region='my-region',
              vpnTunnel=messages.VpnTunnel(
                  name='my-tunnel',
                  description='foo bar',
                  ikeVersion=2,
                  localTrafficSelector=['192.168.100.14/24', '10.0.0.0/8'],
                  peerIp='1.2.3.4',
                  sharedSecret='secret-xyz',
                  targetVpnGateway=(self.compute_uri +
                                    '/projects/my-project/regions'
                                    '/my-region/targetVpnGateways/my-gateway')
                  )))]
    )

if __name__ == '__main__':
  test_case.main()
