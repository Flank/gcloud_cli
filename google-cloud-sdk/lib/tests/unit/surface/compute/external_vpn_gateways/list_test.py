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
"""Tests for the external VPN gateways list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import external_vpn_gateways_test_base


class ExternalVpnGatewayListGaTest(
    external_vpn_gateways_test_base.ExternalVpnGatewaysTestBase):

  def SetUp(self):
    # Since list command returns a generator, we do not want the items to
    # go to STDOUT (which will cause the test to fail otherwise).
    properties.VALUES.core.user_output_enabled.Set(False)

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _MakeExternalVpnGateway(self, name, interface_list, description=None):
    gateway_ref = self.GetExternalVpnGatewayRef(name)
    return self.messages.ExternalVpnGateway(
        name=name,
        description=description,
        redundancyType=self.messages.ExternalVpnGateway
        .RedundancyTypeValueValuesEnum.SINGLE_IP_INTERNALLY_REDUNDANT,
        interfaces=interface_list,
        selfLink=gateway_ref.SelfLink())

  def testList(self):
    interface_list = []
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=0, ipAddress='8.8.8.8'))

    external_vpn_gateways = [
        self._MakeExternalVpnGateway(
            'gateway1', interface_list, description='Some description1.'),
        self._MakeExternalVpnGateway(
            'gateway2', interface_list, description='Some description2.'),
        self._MakeExternalVpnGateway(
            'gateway3', interface_list, description='Some description3.')
    ]

    self.ExpectListRequest(external_vpn_gateways)

    results = self.Run('compute external-vpn-gateways list')
    self.assertEqual(results, external_vpn_gateways)


class ExternalVpnGatewayListBetaTest(ExternalVpnGatewayListGaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ExternalVpnGatewayListAlphaTest(ExternalVpnGatewayListBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
