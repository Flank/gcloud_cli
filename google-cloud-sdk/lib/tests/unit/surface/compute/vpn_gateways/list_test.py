# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for the VPN Gateways describe alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import vpn_gateways_test_base


class VpnGatewayListBetaTest(vpn_gateways_test_base.VpnGatewaysTestBase):
  _OUTPUT_HEADER = 'NAME INTERFACE0 INTERFACE1 NETWORK REGION'

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)
    # Since list command returns a generator, we do not want the items to
    # go to STDOUT (which will cause the test to fail otherwise).
    self._ConfigureOutput(False)

  def _ConfigureOutput(self, enabled):
    properties.VALUES.core.user_output_enabled.Set(enabled)

  def _MakeVpnGateway(self,
                      name,
                      region,
                      network,
                      ip_address_0,
                      ip_address_1,
                      description=None):
    return self.messages.VpnGateway(
        name=name,
        description=description,
        region=self.GetRegionUri(region),
        network=self.GetNetworkRef(network).SelfLink(),
        vpnInterfaces=[
            self.messages.VpnGatewayVpnGatewayInterface(
                id=0, ipAddress=ip_address_0),
            self.messages.VpnGatewayVpnGatewayInterface(
                id=1, ipAddress=ip_address_1)
        ],
        selfLink=self.GetVpnGatewayRef(name).SelfLink())

  def testListEmptyResult(self):
    scoped_vpn_gateways = [(self.REGION, []), (self.REGION2, []),
                           (self.REGION3, [])]

    self.ExpectListRequest(scoped_vpn_gateways)
    results = list(self.Run('compute vpn-gateways list'))
    self.assertEqual(results, [])

  def testListResultsInSingleScope(self):
    vpn_gateways = [
        self._MakeVpnGateway(
            name='vg-1',
            description='My VPN gateway',
            region=self.REGION,
            network='network1',
            ip_address_0='1.2.3.4',
            ip_address_1='1.2.3.5'),
        self._MakeVpnGateway(
            name='vg-2',
            region=self.REGION,
            network='network2',
            ip_address_0='1.2.3.6',
            ip_address_1='1.2.3.7'),
    ]
    scoped_vpn_gateways = [(self.REGION, vpn_gateways)]

    self.ExpectListRequest(scoped_vpn_gateways)
    results = list(self.Run('compute vpn-gateways list'))
    self.assertEqual(results, vpn_gateways)

  def testListResultsInMultipleScopes(self):
    vpn_gateways_in_scope_1 = [
        self._MakeVpnGateway(
            name='vg-1',
            description='My VPN gateway',
            region=self.REGION,
            network='network1',
            ip_address_0='1.2.3.4',
            ip_address_1='1.2.3.5'),
        self._MakeVpnGateway(
            name='vg-2',
            region=self.REGION,
            network='network2',
            ip_address_0='1.2.3.6',
            ip_address_1='1.2.3.7'),
    ]
    vpn_gateways_in_scope_2 = []
    vpn_gateways_in_scope_3 = [
        self._MakeVpnGateway(
            name='vg-3',
            region=self.REGION3,
            network='network3',
            ip_address_0='1.2.3.8',
            ip_address_1='1.2.3.9'),
    ]
    scoped_vpn_gateways = [(self.REGION, vpn_gateways_in_scope_1),
                           (self.REGION2, vpn_gateways_in_scope_2),
                           (self.REGION3, vpn_gateways_in_scope_3)]
    expected_vpn_gateways = [
        vpn_gateway for vpn_gateway in itertools.chain.from_iterable([
            vpn_gateways_in_scope_1, vpn_gateways_in_scope_2,
            vpn_gateways_in_scope_3
        ])
    ]

    self.ExpectListRequest(scoped_vpn_gateways)
    results = list(self.Run('compute vpn-gateways list'))
    self.assertEqual(results, expected_vpn_gateways)

  def testOutput(self):
    self._ConfigureOutput(True)
    vpn_gateways_in_scope_1 = [
        self._MakeVpnGateway(
            name='vg-1',
            description='My VPN gateway',
            region=self.REGION,
            network='network1',
            ip_address_0='1.2.3.4',
            ip_address_1='1.2.3.5'),
        self._MakeVpnGateway(
            name='vg-2',
            region=self.REGION,
            network='network2',
            ip_address_0='1.2.3.6',
            ip_address_1='1.2.3.7'),
    ]
    vpn_gateways_in_scope_2 = []
    vpn_gateways_in_scope_3 = [
        self._MakeVpnGateway(
            name='vg-3',
            region=self.REGION3,
            network='network3',
            ip_address_0='1.2.3.8',
            ip_address_1='1.2.3.9'),
    ]
    scoped_vpn_gateways = [(self.REGION, vpn_gateways_in_scope_1),
                           (self.REGION2, vpn_gateways_in_scope_2),
                           (self.REGION3, vpn_gateways_in_scope_3)]
    expected_output = '\n'.join([
        self._OUTPUT_HEADER,
        ' '.join(['vg-1', '1.2.3.4', '1.2.3.5', 'network1', self.REGION]),
        ' '.join(['vg-2', '1.2.3.6', '1.2.3.7', 'network2', self.REGION]),
        ' '.join(['vg-3', '1.2.3.8', '1.2.3.9', 'network3', self.REGION3]),
        '',
    ])

    self.ExpectListRequest(scoped_vpn_gateways)
    list(self.Run('compute vpn-gateways list'))
    self.AssertOutputEquals(expected_output, normalize_space=True)


class VpnGatewayListAlphaTest(VpnGatewayListBetaTest):
  _OUTPUT_HEADER = 'NAME INTERFACE0 INTERFACE1 NETWORK REGION'

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)
    # Since list command returns a generator, we do not want the items to
    # go to STDOUT (which will cause the test to fail otherwise).
    self._ConfigureOutput(False)


if __name__ == '__main__':
  test_case.main()
