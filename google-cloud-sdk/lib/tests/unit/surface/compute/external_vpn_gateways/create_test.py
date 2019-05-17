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
"""Tests for the external-vpn-gateways create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import external_vpn_gateways_test_base


class ExternalVpnGatewaysCreateBetaTest(
    external_vpn_gateways_test_base.ExternalVpnGatewaysTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSimpleCase(self):
    interface_list = []
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=0, ipAddress='8.8.8.8'))

    name = 'my-external-gateway'
    description = 'my gateway'

    external_vpn_gateway_ref = self.GetExternalVpnGatewayRef(name)
    external_vpn_gateway_to_insert = self.messages.ExternalVpnGateway(
        name=name,
        description=description,
        redundancyType=self.messages.ExternalVpnGateway
        .RedundancyTypeValueValuesEnum.SINGLE_IP_INTERNALLY_REDUNDANT,
        interfaces=interface_list)

    self.runCmdAndVerify(name, description, external_vpn_gateway_ref,
                         external_vpn_gateway_to_insert, '0=8.8.8.8')

  def testWithTwoInterfaces(self):
    interface_list = []
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=0, ipAddress='8.8.8.8'))
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=1, ipAddress='8.8.8.9'))

    name = 'my-external-gateway'
    description = 'my gateway'

    external_vpn_gateway_ref = self.GetExternalVpnGatewayRef(name)
    external_vpn_gateway_to_insert = self.messages.ExternalVpnGateway(
        name=name,
        description=description,
        redundancyType=self.messages.ExternalVpnGateway
        .RedundancyTypeValueValuesEnum.TWO_IPS_REDUNDANCY,
        interfaces=interface_list)

    self.runCmdAndVerify(name, description, external_vpn_gateway_ref,
                         external_vpn_gateway_to_insert, '0=8.8.8.8,1=8.8.8.9')

  def testWithFourInterfaces(self):
    interface_list = []
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=0, ipAddress='8.8.8.8'))
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=1, ipAddress='8.8.8.9'))
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=2, ipAddress='8.8.8.10'))
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=3, ipAddress='8.8.8.11'))

    name = 'my-external-gateway'
    description = 'my gateway'

    external_vpn_gateway_ref = self.GetExternalVpnGatewayRef(name)
    external_vpn_gateway_to_insert = self.messages.ExternalVpnGateway(
        name=name,
        description=description,
        redundancyType=self.messages.ExternalVpnGateway
        .RedundancyTypeValueValuesEnum.FOUR_IPS_REDUNDANCY,
        interfaces=interface_list)

    self.runCmdAndVerify(name, description, external_vpn_gateway_ref,
                         external_vpn_gateway_to_insert,
                         '0=8.8.8.8,1=8.8.8.9,2=8.8.8.10,3=8.8.8.11')

  def runCmdAndVerify(self,
                      name=None,
                      description=None,
                      external_vpn_gateway_ref=None,
                      external_vpn_gateway_to_insert=None,
                      interface_list_in_str=None):

    created_external_vpn_gateway = copy.deepcopy(external_vpn_gateway_to_insert)
    created_external_vpn_gateway.selfLink = external_vpn_gateway_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=external_vpn_gateway_ref)

    self.ExpectInsertRequest(external_vpn_gateway_ref,
                             external_vpn_gateway_to_insert, operation)
    self.ExpectOperationGetRequest(operation_ref, operation)
    self.ExpectGetRequest(external_vpn_gateway_ref,
                          created_external_vpn_gateway)

    response = self.Run('compute external-vpn-gateways create {} '
                        '--interfaces {} '
                        '--description "{}" '
                        '--format=disable'.format(name,
                                                  interface_list_in_str,
                                                  description))

    resources_returned = list(response)
    self.assertEqual(resources_returned[0], created_external_vpn_gateway)

  def testInvocationWithInvalidIp(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Interfaces must be of the form ID=IP_ADDRESS, '
        r'ID must be an integer value in \[0,1,2,3\], '
        r'IP_ADDRESS must be a valid IPV4 address; '
        r'received \[0=8.8.8.8.9\].'):
      self.Run("""
          compute external-vpn-gateways create my-gateway
          --interfaces 0=8.8.8.8.9
          --description "hello"
          """)

  def testInvocationWithInvalidNumberOfInterfaces(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Number of interfaces must be either one, two, or four; '
        r'received \[3\] interface\(s\).'):
      self.Run("""
          compute external-vpn-gateways create my-gateway
          --interfaces 0=1.2.3.4,1=1.2.3.5,2=1.2.3.6
          --description "hello"
          """)


class ExternalVpnGatewaysCreateAlphaTest(ExternalVpnGatewaysCreateBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
