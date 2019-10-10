# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import vpn_tunnels_test_base


class VpnTunnelsDescribeGATest(vpn_tunnels_test_base.VpnTunnelsTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testDescribeClassicVpnTunnel(self):
    name = 'my-tunnel'
    description = 'My tunnel description.'
    ike_version = 2
    peer_ip_address = '71.72.73.74'
    shared_secret = 'secret-xyz'
    local_traffic_selector = ['192.168.100.14/24', '10.0.0.0/16']
    remote_traffic_selector = ['192.168.100.15/24', '10.1.0.0/16']
    target_vpn_gateway = 'my-gateway'

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    result_vpn_tunnel = self.messages.VpnTunnel(
        name=name,
        description=description,
        ikeVersion=ike_version,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        localTrafficSelector=local_traffic_selector,
        remoteTrafficSelector=remote_traffic_selector,
        targetVpnGateway=self.GetTargetVpnGatewayRef(
            target_vpn_gateway).SelfLink(),
        selfLink=vpn_tunnel_ref.SelfLink())

    self.ExpectGetRequest(vpn_tunnel_ref, result_vpn_tunnel)

    response = self.Run('compute vpn-tunnels describe {} --region {}'.format(
        name, self.REGION))
    self.assertEqual(response, result_vpn_tunnel)


class VpnTunnelsDescribeBetaTest(VpnTunnelsDescribeGATest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class VpnTunnelsDescribeAlphaTest(VpnTunnelsDescribeBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDescribeHighAvailabilityVpnTunnel(self):
    name = 'my-tunnel'
    description = 'My tunnel description.'
    ike_version = 2
    peer_ip_address = '71.72.73.74'
    shared_secret = 'secret-xyz'
    vpn_gateway = 'my-gateway'
    interface = 1

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    result_vpn_tunnel = self.messages.VpnTunnel(
        name=name,
        description=description,
        ikeVersion=ike_version,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        vpnGateway=self.GetVpnGatewayRef(vpn_gateway).SelfLink(),
        vpnGatewayInterface=interface,
        selfLink=vpn_tunnel_ref.SelfLink())

    self.ExpectGetRequest(vpn_tunnel_ref, result_vpn_tunnel)

    response = self.Run('compute vpn-tunnels describe {} --region {}'.format(
        name, self.REGION))
    self.assertEqual(response, result_vpn_tunnel)


if __name__ == '__main__':
  test_case.main()
