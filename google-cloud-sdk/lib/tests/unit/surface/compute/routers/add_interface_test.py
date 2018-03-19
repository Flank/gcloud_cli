# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the add-interface subcommand."""

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import parser_errors
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class AddInterfaceTest(test_base.BaseTest):

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
        network=('https://www.googleapis.com/compute/v1/projects/my-project/'
                 'global/networks/default'),
    )

  def ComposeLinkedVpnTunnel(self):
    return ('https://www.googleapis.com/compute/v1/projects/'
            'my-project/regions/us-central1/vpnTunnels/my-vpn')

  def testSimple(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces.append(
        self.messages.RouterInterface(
            name='a-if', linkedVpnTunnel=self.ComposeLinkedVpnTunnel()))

    self.make_requests.side_effect = [[orig], []]

    self.Run("""
        compute routers add-interface my-router --vpn-tunnel=my-vpn
        --interface-name a-if --region us-central1
        """)

    self.CheckRequests(
        [(self.compute.routers, 'Get', self.messages.ComputeRoutersGetRequest(
            router='my-router', region='us-central1', project='my-project'))],
        [(self.compute.routers, 'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],
    )

  def testWithIp(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces.append(
        self.messages.RouterInterface(
            name='a-if',
            linkedVpnTunnel=self.ComposeLinkedVpnTunnel(),
            ipRange='10.0.0.1/24'))

    self.make_requests.side_effect = [[orig], []]

    self.Run("""
        compute routers add-interface my-router --vpn-tunnel=my-vpn
        --interface-name a-if --region us-central1 --ip-address=10.0.0.1
        --mask-length 24
        """)

    self.CheckRequests(
        [(self.compute.routers, 'Get', self.messages.ComputeRoutersGetRequest(
            router='my-router', region='us-central1', project='my-project'))],
        [(self.compute.routers, 'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],
    )

  def testWithIpNoMask(self):
    orig = self.GetRouter()

    self.make_requests.side_effect = iter([[orig]])

    with self.assertRaises(parser_errors.ArgumentException):
      self.Run("""
          compute routers add-interface my-router --vpn-tunnel=my-vpn
          --interface-name a-if --region us-central1 --ip-address=10.0.0.1
          """)

  def testWithBadIp(self):
    orig = self.GetRouter()

    self.make_requests.side_effect = iter([[orig]])

    with self.AssertRaisesArgumentError():
      self.Run("""
          compute routers add-interface my-router --vpn-tunnel=my-vpn
          --interface-name a-if --region us-central1 --ip-address=10.0.0.
          --mask-length 24
          """)

  def testWithBadMask(self):
    orig = self.GetRouter()

    self.make_requests.side_effect = iter([[orig]])

    with self.AssertRaisesArgumentError():
      self.Run("""
          compute routers add-interface my-router --vpn-tunnel=my-vpn
          --interface-name a-if --region us-central1 --ip-address=10.0.0.1
          --mask-length 33
          """)


class AddInterfaceWithAttachmentTest(AddInterfaceTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def ComposeLinkedVpnTunnel(self):
    return ('https://www.googleapis.com/compute/' + self.api_version +
            '/projects/my-project/'
            'regions/us-central1/vpnTunnels/my-vpn')

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
        network=('https://www.googleapis.com/compute/' + self.api_version +
                 '/projects/my-project/'
                 'global/networks/default'),
    )

  def composeLinkedInterconnectAttachment(self):
    return ('https://www.googleapis.com/compute/' + self.api_version +
            '/projects/my-project/'
            'regions/us-central1/interconnectAttachments/my-attachment')

  def testWithLinkedInterconnectAttachment(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces.append(
        self.messages.RouterInterface(
            name='a-if',
            linkedInterconnectAttachment=self.
            composeLinkedInterconnectAttachment()))

    self.make_requests.side_effect = [[orig], []]

    self.Run("""
        compute routers add-interface my-router
        --interconnect-attachment my-attachment
        --interface-name a-if --region us-central1
        """)

    self.CheckRequests(
        [(self.compute.routers, 'Get', self.messages.ComputeRoutersGetRequest(
            router='my-router', region='us-central1', project='my-project'))],
        [(self.compute.routers, 'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],
    )

  def testWithLinkedAttachmentAndVpn(self):
    orig = self.GetRouter()
    expected = copy.deepcopy(orig)

    expected.interfaces.append(
        self.messages.RouterInterface(
            name='a-if',
            linkedInterconnectAttachment=self.
            composeLinkedInterconnectAttachment()))

    self.make_requests.side_effect = iter([[orig]])
    with self.AssertRaisesArgumentErrorMatches(
        'argument --interconnect-attachment: Exactly one of '
        '(--interconnect-attachment | --interconnect-attachment-region | '
        '--vpn-tunnel | --vpn-tunnel-region) must be specified.'):
      self.Run("""
          compute routers add-interface my-router
          --interconnect-attachment my-attachment
          --vpn-tunnel my-vpn
          --interface-name a-if --region us-central1
          """)


class AddInterfaceWithAttachmentBetaTest(AddInterfaceWithAttachmentTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class AddInterfaceWithAttachmentAlphaTest(AddInterfaceWithAttachmentTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
