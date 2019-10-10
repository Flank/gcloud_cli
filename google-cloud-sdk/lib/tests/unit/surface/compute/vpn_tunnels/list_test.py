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
"""Tests for the vpn-tunnels list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import vpn_tunnels_test_base


class VpnTunnelsListGATest(vpn_tunnels_test_base.VpnTunnelsTestBase):
  _DEFAULT_OUTPUT_HEADER = 'NAME REGION GATEWAY PEER_ADDRESS'
  _HA_VPN_OUTPUT_HEADER = 'NAME REGION GATEWAY VPN_INTERFACE PEER_ADDRESS'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    # Since list command returns a generator, we do not want the items to
    # go to STDOUT (which will cause the test to fail otherwise).
    self._ConfigureOutput(False)

  def _ConfigureOutput(self, enabled):
    properties.VALUES.core.user_output_enabled.Set(enabled)

  def _MakeClassicVpnTunnel(self,
                            name,
                            region,
                            ike_version,
                            peer_ip_address,
                            shared_secret,
                            target_vpn_gateway_name,
                            description=None):
    return self.messages.VpnTunnel(
        name=name,
        description=description,
        region=self.GetRegionUri(region),
        ikeVersion=ike_version,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        targetVpnGateway=self.GetTargetVpnGatewayRef(
            target_vpn_gateway_name).SelfLink(),
        selfLink=self.GetVpnTunnelRef(name).SelfLink())

  def _MakeHighAvailabilityVpnTunnel(self,
                                     name,
                                     region,
                                     ike_version,
                                     peer_ip_address,
                                     shared_secret,
                                     vpn_gateway_name,
                                     vpn_gateway_interface,
                                     description=None):
    return self.messages.VpnTunnel(
        name=name,
        description=description,
        region=self.GetRegionUri(region),
        ikeVersion=ike_version,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        vpnGateway=self.GetVpnGatewayRef(vpn_gateway_name).SelfLink(),
        vpnGatewayInterface=vpn_gateway_interface,
        selfLink=self.GetVpnTunnelRef(name).SelfLink())

  def testListEmptyResult(self):
    scoped_vpn_tunnels = [(self.REGION, []), (self.REGION2, []),
                          (self.REGION3, [])]
    self.ExpectListRequest(scoped_vpn_tunnels)
    results = list(self.Run('compute vpn-tunnels list'))
    self.assertEqual(results, [])

  def testListResultsInSingleScope(self):
    vpn_tunnels = [
        self._MakeClassicVpnTunnel(
            name='tun-0',
            description='My VPN tunnel',
            region=self.REGION,
            ike_version=2,
            peer_ip_address='71.72.73.74',
            shared_secret='SECRET0',
            target_vpn_gateway_name='gateway-1'),
        self._MakeClassicVpnTunnel(
            name='tun-1',
            region=self.REGION,
            ike_version=1,
            peer_ip_address='71.72.73.75',
            shared_secret='SECRET1',
            target_vpn_gateway_name='gateway-2'),
    ]
    scoped_vpn_tunnels = [(self.REGION, vpn_tunnels)]

    self.ExpectListRequest(scoped_vpn_tunnels)
    results = list(self.Run('compute vpn-tunnels list'))
    self.assertEqual(results, vpn_tunnels)

  def testListResultsInMultipleScopes(self):
    vpn_tunnels_in_scope_1 = [
        self._MakeClassicVpnTunnel(
            name='tun-0',
            description='My VPN tunnel',
            region=self.REGION,
            ike_version=2,
            peer_ip_address='71.72.73.74',
            shared_secret='SECRET0',
            target_vpn_gateway_name='gateway-1'),
        self._MakeClassicVpnTunnel(
            name='tun-1',
            region=self.REGION,
            ike_version=1,
            peer_ip_address='71.72.73.75',
            shared_secret='SECRET1',
            target_vpn_gateway_name='gateway-2'),
    ]
    vpn_tunnels_in_scope_2 = []
    vpn_tunnels_in_scope_3 = [
        self._MakeClassicVpnTunnel(
            name='tun-2',
            region=self.REGION3,
            ike_version=2,
            peer_ip_address='71.72.73.76',
            shared_secret='SECRET2',
            target_vpn_gateway_name='gateway-3'),
    ]
    scoped_vpn_tunnels = [(self.REGION, vpn_tunnels_in_scope_1),
                          (self.REGION2, vpn_tunnels_in_scope_2),
                          (self.REGION3, vpn_tunnels_in_scope_3)]
    expected_vpn_tunnels = [
        vpn_tunnel for vpn_tunnel in itertools.chain.from_iterable([
            vpn_tunnels_in_scope_1, vpn_tunnels_in_scope_2,
            vpn_tunnels_in_scope_3
        ])
    ]

    self.ExpectListRequest(scoped_vpn_tunnels)
    results = list(self.Run('compute vpn-tunnels list'))
    self.assertEqual(results, expected_vpn_tunnels)

  def testOutput(self):
    self._ConfigureOutput(True)
    vpn_tunnels_in_scope_1 = [
        self._MakeClassicVpnTunnel(
            name='tun-0',
            description='My VPN tunnel',
            region=self.REGION,
            ike_version=2,
            peer_ip_address='71.72.73.74',
            shared_secret='SECRET0',
            target_vpn_gateway_name='gateway-1'),
        self._MakeClassicVpnTunnel(
            name='tun-1',
            region=self.REGION,
            ike_version=1,
            peer_ip_address='71.72.73.75',
            shared_secret='SECRET1',
            target_vpn_gateway_name='gateway-2'),
    ]
    vpn_tunnels_in_scope_2 = []
    vpn_tunnels_in_scope_3 = [
        self._MakeClassicVpnTunnel(
            name='tun-2',
            region=self.REGION3,
            ike_version=2,
            peer_ip_address='71.72.73.76',
            shared_secret='SECRET2',
            target_vpn_gateway_name='gateway-3'),
    ]
    scoped_vpn_tunnels = [(self.REGION, vpn_tunnels_in_scope_1),
                          (self.REGION2, vpn_tunnels_in_scope_2),
                          (self.REGION3, vpn_tunnels_in_scope_3)]
    expected_output = '\n'.join([
        self._DEFAULT_OUTPUT_HEADER,
        ' '.join(['tun-0', self.REGION, 'gateway-1', '71.72.73.74']),
        ' '.join(['tun-1', self.REGION, 'gateway-2', '71.72.73.75']),
        ' '.join(['tun-2', self.REGION3, 'gateway-3', '71.72.73.76']),
        '',
    ])

    self.ExpectListRequest(scoped_vpn_tunnels)
    list(self.Run('compute vpn-tunnels list'))
    self.AssertOutputEquals(expected_output, normalize_space=True)


class VpnTunnelsListBetaTest(VpnTunnelsListGATest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class VpnTunnelsListAlphaTest(VpnTunnelsListBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testListResultsInMultipleScopes(self):
    vpn_tunnels_in_scope_1 = [
        self._MakeHighAvailabilityVpnTunnel(
            name='tun-0',
            description='My VPN tunnel',
            region=self.REGION,
            ike_version=2,
            peer_ip_address='71.72.73.74',
            shared_secret='SECRET0',
            vpn_gateway_name='gateway-1',
            vpn_gateway_interface=0),
        self._MakeClassicVpnTunnel(
            name='tun-1',
            region=self.REGION,
            ike_version=1,
            peer_ip_address='71.72.73.75',
            shared_secret='SECRET1',
            target_vpn_gateway_name='gateway-2'),
    ]
    vpn_tunnels_in_scope_2 = []
    vpn_tunnels_in_scope_3 = [
        self._MakeHighAvailabilityVpnTunnel(
            name='tun-2',
            region=self.REGION3,
            ike_version=2,
            peer_ip_address='71.72.73.76',
            shared_secret='SECRET2',
            vpn_gateway_name='gateway-3',
            vpn_gateway_interface=1),
    ]
    scoped_vpn_tunnels = [(self.REGION, vpn_tunnels_in_scope_1),
                          (self.REGION2, vpn_tunnels_in_scope_2),
                          (self.REGION3, vpn_tunnels_in_scope_3)]
    expected_vpn_tunnels = [
        vpn_tunnel for vpn_tunnel in itertools.chain.from_iterable([
            vpn_tunnels_in_scope_1, vpn_tunnels_in_scope_2,
            vpn_tunnels_in_scope_3
        ])
    ]

    self.ExpectListRequest(scoped_vpn_tunnels)
    results = list(self.Run('compute vpn-tunnels list'))
    self.assertEqual(results, expected_vpn_tunnels)

  def testOutput(self):
    self._ConfigureOutput(True)
    vpn_tunnels_in_scope_1 = [
        self._MakeHighAvailabilityVpnTunnel(
            name='tun-0',
            description='My VPN tunnel',
            region=self.REGION,
            ike_version=2,
            peer_ip_address='71.72.73.74',
            shared_secret='SECRET0',
            vpn_gateway_name='gateway-1',
            vpn_gateway_interface=0),
        self._MakeClassicVpnTunnel(
            name='tun-1',
            region=self.REGION,
            ike_version=1,
            peer_ip_address='71.72.73.75',
            shared_secret='SECRET1',
            target_vpn_gateway_name='gateway-2'),
    ]
    vpn_tunnels_in_scope_2 = []
    vpn_tunnels_in_scope_3 = [
        self._MakeHighAvailabilityVpnTunnel(
            name='tun-2',
            region=self.REGION3,
            ike_version=2,
            peer_ip_address='71.72.73.76',
            shared_secret='SECRET2',
            vpn_gateway_name='gateway-3',
            vpn_gateway_interface=1),
    ]
    scoped_vpn_tunnels = [(self.REGION, vpn_tunnels_in_scope_1),
                          (self.REGION2, vpn_tunnels_in_scope_2),
                          (self.REGION3, vpn_tunnels_in_scope_3)]
    expected_output = '\n'.join([
        self._HA_VPN_OUTPUT_HEADER,
        ' '.join(['tun-0', self.REGION, 'gateway-1', '0', '71.72.73.74']),
        ' '.join(['tun-1', self.REGION, 'gateway-2', '71.72.73.75']),
        ' '.join(['tun-2', self.REGION3, 'gateway-3', '1', '71.72.73.76']),
        '',
    ])

    self.ExpectListRequest(scoped_vpn_tunnels)
    list(self.Run('compute vpn-tunnels list'))
    self.AssertOutputEquals(expected_output, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
