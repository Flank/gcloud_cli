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
"""Tests for the VPN Gateways describe alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import vpn_gateways_test_base


class VpnGatewayDescribeGaTest(vpn_gateways_test_base.VpnGatewaysTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def testDescribe(self):
    name = 'my-vpn-gateway'
    description = 'My VPN Gateway Description'
    network_uri = self.GetNetworkRef('network1').SelfLink()
    labels = self.MakeLabelsMessage(self.messages.VpnGateway.LabelsValue,
                                    [('foo', 'bar'), ('key1', 'val1')])

    vpn_gateway_ref = self.GetVpnGatewayRef(name)
    result_vpn_gateway = self.messages.VpnGateway(
        name=name,
        description=description,
        region=self.GetRegionUri(self.REGION),
        network=network_uri,
        labels=labels,
        labelFingerprint=b'SOME_FINGERPRINT',
        selfLink=vpn_gateway_ref.SelfLink())

    self.ExpectGetRequest(vpn_gateway_ref, result_vpn_gateway)

    response = self.Run('compute vpn-gateways describe {} --region {}'.format(
        name, self.REGION))
    self.assertEqual(response, result_vpn_gateway)


class VpnGatewayDescribeBetaTest(VpnGatewayDescribeGaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class VpnGatewayDescribeAlphaTest(VpnGatewayDescribeBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
