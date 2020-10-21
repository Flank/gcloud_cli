# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the networks create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import parser_errors
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NetworksCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testUriSupport(self):
    expected = self.messages.Network(
        name='my-network', IPv4Range='10.240.0.0/16')
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run("""
        compute networks create --range 10.240.0.0/16 --subnet-mode legacy
             {compute}/projects/my-project/global/networks/my-network
        """.format(compute=self.compute_uri))

    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])

  def testRangeOption(self):
    expected = self.messages.Network(
        name='my-network', IPv4Range='10.240.0.0/16')
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run("""
        compute networks create my-network --range 10.240.0.0/16 --subnet-mode
        legacy
        """)
    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])

  def testDescriptionOption(self):
    expected = self.messages.Network(
        name='my-network',
        IPv4Range='10.240.0.0/16',
        description='my description')
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run("""
        compute networks create my-network --range 10.240.0.0/16 --subnet-mode
        legacy --description "my description"
        """)
    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])

  def testAutoSubnetModeRangeError(self):
    error_msg = '--range can only be used with --subnet-mode=legacy.'
    with self.assertRaisesRegex(parser_errors.ArgumentError, error_msg):
      self.Run('compute networks create my-network --range 10.245.0.0/16 '
               '--subnet-mode auto')

  def testCustomSubnetModeRangeError(self):
    error_msg = '--range can only be used with --subnet-mode=legacy.'
    with self.assertRaisesRegex(parser_errors.ArgumentError, error_msg):
      self.Run('compute networks create my-network --range 10.245.0.0/16 '
               '--subnet-mode custom')

  def testCreateAutoSubnetModeNetwork(self):
    expected = self.messages.Network(
        name='my-network', autoCreateSubnetworks=True)
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run('compute networks create my-network --subnet-mode auto')
    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])

  def testCreateCustomSubnetModeNetwork(self):
    expected = self.messages.Network(
        name='my-network', autoCreateSubnetworks=False)
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run('compute networks create my-network --subnet-mode custom')
    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])

  def testCreateRegionalBgpRoutingModeNetwork(self):
    expected = self.messages.Network(
        name='my-network', autoCreateSubnetworks=False)
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run('compute networks create my-network --subnet-mode custom '
             '--bgp-routing-mode regional')
    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])

  def testCreateGlobalBgpRoutingModeNetwork(self):
    expected = self.messages.Network(
        name='my-network', autoCreateSubnetworks=False)
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.GLOBAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run('compute networks create my-network --subnet-mode custom '
             '--bgp-routing-mode global')
    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])

  def testOutputListsModes(self):
    expected = self.messages.Network(
        name='my-network', autoCreateSubnetworks=True)
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run('compute networks create my-network --subnet-mode auto '
             '--bgp-routing-mode regional')
    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME          SUBNET_MODE    BGP_ROUTING_MODE    IPV4_RANGE    GATEWAY_IPV4
            my-network    AUTO           REGIONAL
            """),
        normalize_space=True)
    self.AssertErrEquals(
        textwrap.dedent("""\

Instances on this network will not be reachable until firewall rules
are created. As an example, you can allow all internal traffic between
instances as well as SSH, RDP, and ICMP by running:

$ gcloud compute firewall-rules create <FIREWALL_NAME> --network my-network \
--allow tcp,udp,icmp --source-ranges <IP_RANGE>
$ gcloud compute firewall-rules create <FIREWALL_NAME> --network my-network \
--allow tcp:22,tcp:3389,icmp

            """),
        normalize_space=True)

  def testCreateWithMtu(self):
    expected = self.messages.Network(
        name='my-network', autoCreateSubnetworks=True, mtu=1500)
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)

    self.make_requests.side_effect = iter([[expected]])

    self.Run('compute networks create my-network --mtu 1500')
    expected_insert = (self.compute.networks, 'Insert',
                       self.messages.ComputeNetworksInsertRequest(
                           project='my-project', network=expected))
    self.CheckRequests([expected_insert])


class NetworksCreateBetaTest(NetworksCreateTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA


class NetworksCreateAlphaTest(NetworksCreateBetaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
