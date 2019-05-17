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
"""Tests for the vpn-gateways create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import vpn_gateways_test_base


class VpnGatewaysCreateBetaTest(vpn_gateways_test_base.VpnGatewaysTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)

  def testSimpleCase(self):
    name = 'my-vpn-gateway'
    description = 'My VPN Gateway'
    network = 'network1'

    vpn_gateway_ref = self.GetVpnGatewayRef(name)
    vpn_gateway_to_insert = self.messages.VpnGateway(
        name=name,
        description=description,
        network=self.GetNetworkRef(network).SelfLink())
    created_vpn_gateway = copy.deepcopy(vpn_gateway_to_insert)
    created_vpn_gateway.selfLink = vpn_gateway_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_gateway_ref)

    self.ExpectInsertRequest(vpn_gateway_ref, vpn_gateway_to_insert, operation)
    self.ExpectOperationGetRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_gateway_ref, created_vpn_gateway)

    response = self.Run('compute vpn-gateways create {} '
                        '--description "{}" '
                        '--network {} '
                        '--region {} '
                        '--format=disable'.format(name, description, network,
                                                  self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_gateway)

  def testWithNetworkUri(self):
    name = 'my-vpn-gateway'
    network_uri = self.GetNetworkRef('network2').SelfLink()

    vpn_gateway_ref = self.GetVpnGatewayRef(name)
    vpn_gateway_to_insert = self.messages.VpnGateway(
        name=name, network=network_uri)
    created_vpn_gateway = copy.deepcopy(vpn_gateway_to_insert)
    created_vpn_gateway.selfLink = vpn_gateway_ref.SelfLink()

    operation_ref = self.GetOperationRef(name='operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_gateway_ref)

    self.ExpectInsertRequest(vpn_gateway_ref, vpn_gateway_to_insert, operation)
    self.ExpectOperationGetRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_gateway_ref, created_vpn_gateway)

    response = self.Run('compute vpn-gateways create {} '
                        '--network {} '
                        '--region {} '
                        '--format=disable'.format(name, network_uri,
                                                  self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_gateway)

  def WithLabels(self):
    pass

  def testWithoutNetwork(self):
    name = 'my-vpn-gateway'
    with self.AssertRaisesArgumentErrorMatches(
        'argument --network: Must be specified.'):
      self.Run('compute vpn-gateways create {} --region {} '.format(
          name, self.REGION))


class VpnGatewaysCreateAlphaTest(VpnGatewaysCreateBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
