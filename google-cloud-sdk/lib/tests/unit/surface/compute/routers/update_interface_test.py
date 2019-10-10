# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for the update-interface subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.compute.routers import router_utils
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class UpdateInterfaceTest(test_base.BaseTest):

  def GetRouter(self):
    return self.messages.Router(
        name='my-router',
        bgpPeers=[
            self.messages.RouterBgpPeer(
                name='my-peer',
                interfaceName='my-if',
                ipAddress='10.0.0.1',
                peerIpAddress='10.0.0.2',
                peerAsn=65000)
        ],
        interfaces=[
            self.messages.RouterInterface(
                name='my-if', linkedVpnTunnel='', ipRange='10.0.0.1/24')
        ],
        region='us-central1',
        network=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                 'global/networks/default'),)

  def testNoUpdates(self):
    orig = self.GetRouter()

    self.make_requests.side_effect = iter([[orig]])

    self.Run("""
        compute routers update-interface my-router --interface-name my-if
        --region us-central1
        """)

    self.CheckRequests(
        [(self.compute.routers, 'Get', self.messages.ComputeRoutersGetRequest(
            router='my-router', region='us-central1', project='my-project'))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'No change requested; skipping update for [my-router].\n')

  def testAllUpdates(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces[0].ipRange = '10.10.0.1/25'
    expected.interfaces[0].linkedVpnTunnel = (
        self.compute_uri +
        '/projects/my-project/regions/us-central1/vpnTunnels/vpn')

    self.make_requests.side_effect = [[orig], []]

    self.Run("""
        compute routers update-interface my-router --interface-name my-if
        --vpn-tunnel vpn --region us-central1 --ip-address 10.10.0.1
        --mask-length 25
        """)

    self.CheckRequests(
        [(self.compute.routers, 'Get', self.messages.ComputeRoutersGetRequest(
            router='my-router', region='us-central1', project='my-project'))],
        [(self.compute.routers, 'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],)

  def testWithIpAddressNoMaskLength(self):
    orig = self.GetRouter()

    self.make_requests.side_effect = iter([[orig]])

    error_msg = '--ip-address and --mask-length must be set together.'
    with self.AssertRaisesExceptionMatches(
        router_utils.RequireIpAddressAndMaskLengthError, error_msg):
      self.Run("""
          compute routers update-interface my-router
          --interface-name my-if --region us-central1 --ip-address=10.0.0.1
          """)
    self.AssertOutputEquals('')

  def testWithMaskLengthNoIpAddress(self):
    orig = self.GetRouter()

    self.make_requests.side_effect = iter([[orig]])

    error_msg = '--ip-address and --mask-length must be set together.'
    with self.AssertRaisesExceptionMatches(
        router_utils.RequireIpAddressAndMaskLengthError, error_msg):
      self.Run("""
          compute routers update-interface my-router
          --interface-name my-if --region us-central1 --mask-length=24
          """)
    self.AssertOutputEquals('')

  def testWithBadIp(self):
    orig = self.GetRouter()

    self.make_requests.side_effect = iter([[orig]])

    with self.AssertRaisesArgumentError():
      self.Run("""
          compute routers update-interface my-router
          --interface-name my-if --region us-central1 --ip-address=10.0.0.
          --mask-length 24
          """)

  def testWithBadMask(self):
    orig = self.GetRouter()

    self.make_requests.side_effect = iter([[orig]])

    with self.AssertRaisesArgumentError():
      self.Run("""
          compute routers update-interface my-router
          --interface-name my-if --region us-central1 --ip-address=10.0.0.1
          --mask-length 33
          """)

  def testUpdatesWithInterfaceNotExist(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces[0].ipRange = '10.10.0.1/25'
    expected.interfaces[0].linkedVpnTunnel = (
        self.compute_uri +
        '/projects/my-project/regions/us-central1/vpnTunnels/'
        'my-vpn')

    self.make_requests.side_effect = iter([[orig]])

    with self.assertRaises(router_utils.InterfaceNotFoundError):
      self.Run("""
          compute routers update-interface my-router --interface-name my-if2
          --vpn-tunnel my-vpn-1 --region us-central1
          --ip-address 10.10.0.1
          --mask-length 25
          """)


class BetaUpdateInterfaceTest(UpdateInterfaceTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.network_url = ('https://compute.googleapis.com/compute/beta/projects/'
                        'my-project/global/networks/default')

  def GetRouter(self):
    return self.messages.Router(
        name='my-router',
        bgpPeers=[
            self.messages.RouterBgpPeer(
                name='my-peer',
                interfaceName='my-if',
                ipAddress='10.0.0.1',
                peerIpAddress='10.0.0.2',
                peerAsn=65000)
        ],
        interfaces=[
            self.messages.RouterInterface(
                name='my-if',
                linkedVpnTunnel=None,
                linkedInterconnectAttachment=None,
                ipRange='10.0.0.1/24')
        ],
        region='us-central1',
        network=self.network_url,)

  def testAllUpdatesForBeta(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces[0].ipRange = '10.10.0.1/25'
    expected.interfaces[0].linkedInterconnectAttachment = (
        self.compute_uri +
        '/projects/my-project/regions/us-central1/interconnectAttachments/'
        'my-attachment')

    self.make_requests.side_effect = [[orig], []]

    self.Run("""
        compute routers update-interface my-router --interface-name my-if
        --interconnect-attachment my-attachment --region us-central1
        --ip-address 10.10.0.1
        --mask-length 25
        """)

    self.CheckRequests(
        [(self.compute.routers, 'Get', self.messages.ComputeRoutersGetRequest(
            router='my-router', region='us-central1', project='my-project'))],
        [(self.compute.routers, 'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],)

  def testUpdatesWithBothVpnAndAttachment(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces[0].ipRange = '10.10.0.1/25'
    expected.interfaces[0].linkedInterconnectAttachment = (
        self.compute_uri +
        '/projects/my-project/regions/us-central1/interconnectAttachments/'
        'my-attachment')
    expected.interfaces[0].linkedVpnTunnel = (
        self.compute_uri +
        '/projects/my-project/regions/us-central1/vpnTunnels/vpn')

    self.make_requests.side_effect = iter([[orig]])

    with self.AssertRaisesArgumentErrorMatches(
        'argument --interconnect-attachment: At most one of '
        '--interconnect-attachment | --interconnect-attachment-region | '
        '--vpn-tunnel | --vpn-tunnel-region may be specified.'):
      self.Run("""
          compute routers update-interface my-router --interface-name my-if
          --interconnect-attachment my-attachment --region us-central1
          --vpn-tunnel vpn
          --ip-address 10.10.0.1
          --mask-length 25
          """)

  def testAddAttachmentWhenVpnTunnelAlreadyExist(self):
    orig = self.messages.Router(
        name='my-router',
        bgpPeers=[
            self.messages.RouterBgpPeer(
                name='my-peer',
                interfaceName='my-if',
                ipAddress='10.0.0.1',
                peerIpAddress='10.0.0.2',
                peerAsn=65000)
        ],
        interfaces=[
            self.messages.RouterInterface(
                name='my-if',
                linkedVpnTunnel=self.compute_uri +
                '/projects/my-project/regions/us-central1/vpnTunnels/vpn',
                ipRange='10.0.0.1/24',
                linkedInterconnectAttachment='')
        ],
        region='us-central1',
        network=self.network_url,)
    expected = copy.deepcopy(orig)

    expected.interfaces[0].ipRange = '10.10.0.1/25'
    expected.interfaces[0].linkedInterconnectAttachment = (
        self.compute_uri +
        '/projects/my-project/regions/us-central1/interconnectAttachments/'
        'my-attachment')

    self.make_requests.side_effect = iter([[orig]])

    with self.assertRaises(parser_errors.ArgumentException):
      self.Run("""
          compute routers update-interface my-router --interface-name my-if
          --interconnect-attachment my-attachment --region us-central1
          --ip-address 10.10.0.1
          --mask-length 25
          """)

  def testUpdatesWithInterfaceNotExist(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces[0].ipRange = '10.10.0.1/25'
    expected.interfaces[0].linkedInterconnectAttachment = (
        self.compute_uri +
        '/projects/my-project/regions/us-central1/interconnectAttachments/'
        'my-attachment')

    self.make_requests.side_effect = iter([[orig]])

    with self.assertRaises(router_utils.InterfaceNotFoundError):
      self.Run("""
          compute routers update-interface my-router --interface-name my-if2
          --interconnect-attachment my-attachment --region us-central1
          --ip-address 10.10.0.1
          --mask-length 25
          """)


class GAUpdateInterfaceTest(BetaUpdateInterfaceTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA
    self.network_url = ('https://compute.googleapis.com/compute/v1/projects/'
                        'my-project/global/networks/default')


class AlphaUpdateInterfaceTest(BetaUpdateInterfaceTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.network_url = ('https://compute.googleapis.com/compute/alpha/projects/'
                        'my-project/global/networks/default')


if __name__ == '__main__':
  test_case.main()
