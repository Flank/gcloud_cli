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
"""Tests for the external VPN gateway describe alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import external_vpn_gateways_test_base


class ExternalVpnGatewayDescribeBetaTest(
    external_vpn_gateways_test_base.ExternalVpnGatewaysTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testDescribeNonCustomProfile(self):
    interface_list = []
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=0, ipAddress='8.8.8.8'))

    name = 'my-external-gateway'
    description = 'my gateway'

    external_vpn_gateway_ref = self.GetExternalVpnGatewayRef(name)
    external_vpn_gateway_result = self.messages.ExternalVpnGateway(
        name=name,
        description=description,
        redundancyType=self.messages.ExternalVpnGateway
        .RedundancyTypeValueValuesEnum.SINGLE_IP_INTERNALLY_REDUNDANT,
        interfaces=interface_list)

    self.ExpectGetRequest(external_vpn_gateway_ref, external_vpn_gateway_result)

    response = self.Run(
        'compute external-vpn-gateways describe {}'.format(name))
    self.assertEqual(response, external_vpn_gateway_result)


class ExternalVpnGatewayDescribeAlphaTest(ExternalVpnGatewayDescribeBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
