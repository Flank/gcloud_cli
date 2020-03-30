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
"""Tests for the vpn-tunnels create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import vpn_tunnels_test_base

_LONG_SECRET = ('So long as you are praised think only that you are not '
                'yet on your own path but on that of another.'
                '- Friedrich Nietzsche !@#$%^&*()_+=')


class ClassicVpnTunnelsCreateGATest(vpn_tunnels_test_base.VpnTunnelsTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSimpleCase(self):
    name = 'my-tunnel'
    description = 'My tunnel description.'
    ike_version = 2
    peer_ip_address = '71.72.73.74'
    shared_secret = 'secret-xyz'
    target_vpn_gateway = 'my-gateway'

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        description=description,
        ikeVersion=ike_version,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        targetVpnGateway=self.GetTargetVpnGatewayRef(
            target_vpn_gateway).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run('compute vpn-tunnels create {} '
                        '--description "{}" '
                        '--ike-version {} '
                        '--peer-address {} '
                        '--shared-secret {} '
                        '--target-vpn-gateway {} '
                        '--region {} '
                        '--format=disable'.format(
                            name, description, ike_version, peer_ip_address,
                            shared_secret, target_vpn_gateway, self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)

  def testFlagsAcceptUris(self):
    name = 'my-tunnel'
    peer_ip_address = '71.72.73.74'
    shared_secret = 'secret-xyz'
    target_vpn_gateway = 'my-gateway'

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        targetVpnGateway=self.GetTargetVpnGatewayRef(
            target_vpn_gateway).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels create '
        '{base_uri}/regions/{region}/vpnTunnels/{vpn_tunnel_name} '
        '--peer-address {peer_address} '
        '--shared-secret {shared_secret} '
        '--target-vpn-gateway '
        '{base_uri}/regions/{region}/targetVpnGateways/{gateway_name} '
        '--format=disable'.format(
            vpn_tunnel_name=name,
            peer_address=peer_ip_address,
            shared_secret=shared_secret,
            gateway_name=target_vpn_gateway,
            base_uri=self.base_uri,
            region=self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)

  def testInvocationWithoutOptionalArgsOk(self):
    name = 'my-tunnel'
    peer_ip_address = '71.72.73.74'
    shared_secret = 'secret-xyz'
    target_vpn_gateway = 'my-gateway'

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        targetVpnGateway=self.GetTargetVpnGatewayRef(
            target_vpn_gateway).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels create {} '
        '--peer-address {} '
        '--shared-secret {} '
        '--target-vpn-gateway {} '
        '--region {} '
        '--format=disable'.format(name, peer_ip_address, shared_secret,
                                  target_vpn_gateway, self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)

  def testInvocationWithoutPeerAddressFails(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'When creating Classic VPN tunnels, the peer address '
        'must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --shared-secret secret-xyz
            --target-vpn-gateway my-gateway
            --region my-region
            --router my-router
            --peer-gcp-gateway peer-gateways
          """)

  def testInvocationWithoutSharedSecretFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --shared-secret: Must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-address 71.72.73.74
            --target-vpn-gateway my-gateway
          """)

  def testInvocationWithBadSharedSecretFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'The argument to --shared-secret is not valid it contains '
        'non-printable charcters.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-address 71.72.73.74
            --target-vpn-gateway my-gateway
            --shared-secret '\n'
          """)

  def testInvocationWithoutAnyVpnGatewayTypeFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--target-vpn-gateway | --target-vpn-gateway-region | '
        + '--vpn-gateway | --vpn-gateway-region) must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-address 71.72.73.74
            --shared-secret secret-xyz
          """)

  def testRemoteTrafficSelector(self):
    name = 'my-tunnel'
    ike_version = 2
    peer_ip_address = '71.72.73.74'
    shared_secret = 'secret-xyz'
    target_vpn_gateway = 'my-gateway'
    remote_traffic_selector = ['192.168.100.14/24', '10.0.0.0/8']

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        ikeVersion=ike_version,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        remoteTrafficSelector=remote_traffic_selector,
        targetVpnGateway=self.GetTargetVpnGatewayRef(
            target_vpn_gateway).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run('compute vpn-tunnels create {} '
                        '--ike-version {} '
                        '--peer-address {} '
                        '--shared-secret {} '
                        '--remote-traffic-selector {} '
                        '--target-vpn-gateway {} '
                        '--region {} '
                        '--format=disable'.format(
                            name, ike_version, peer_ip_address, shared_secret,
                            ','.join(remote_traffic_selector),
                            target_vpn_gateway, self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)

  def testLocalTrafficSelector(self):
    name = 'my-tunnel'
    ike_version = 2
    peer_ip_address = '71.72.73.74'
    shared_secret = 'secret-xyz'
    target_vpn_gateway = 'my-gateway'
    local_traffic_selector = ['192.168.100.14/24', '10.0.0.0/8']

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        ikeVersion=ike_version,
        peerIp=peer_ip_address,
        sharedSecret=shared_secret,
        localTrafficSelector=local_traffic_selector,
        targetVpnGateway=self.GetTargetVpnGatewayRef(
            target_vpn_gateway).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run('compute vpn-tunnels create {} '
                        '--ike-version {} '
                        '--peer-address {} '
                        '--shared-secret {} '
                        '--local-traffic-selector {} '
                        '--target-vpn-gateway {} '
                        '--region {} '
                        '--format=disable'.format(
                            name, ike_version, peer_ip_address, shared_secret,
                            ','.join(local_traffic_selector),
                            target_vpn_gateway, self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)


class ClassicVpnTunnelsCreateBetaTest(ClassicVpnTunnelsCreateGATest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ClassicVpnTunnelsCreateAlphaTest(ClassicVpnTunnelsCreateBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class HighAvailabilityVpnTunnelsCreateGaTest(
    vpn_tunnels_test_base.VpnTunnelsTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSimpleCaseWithPeerGcpGateway(self):
    name = 'my-tunnel'
    description = 'My tunnel description.'
    ike_version = 2
    shared_secret = 'secret-xyz'
    vpn_gateway = 'my-gateway'
    interface = 0
    router = 'my-router'
    peer_gcp_gateway = 'peer-gateway'

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        description=description,
        ikeVersion=ike_version,
        peerGcpGateway=self.GetVpnGatewayRef(peer_gcp_gateway).SelfLink(),
        sharedSecret=shared_secret,
        vpnGateway=self.GetVpnGatewayRef(vpn_gateway).SelfLink(),
        vpnGatewayInterface=interface,
        router=self.GetRouterRef(router).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels create {} '
        '--description "{}" '
        '--ike-version {} '
        '--peer-gcp-gateway {} '
        '--shared-secret {} '
        '--vpn-gateway {} '
        '--interface {} '
        '--router {} '
        '--region {} '
        '--format=disable'.format(name, description, ike_version,
                                  peer_gcp_gateway, shared_secret, vpn_gateway,
                                  interface, router, self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)

  def testSimpleCaseWithPeerExternalGateway(self):
    name = 'my-tunnel'
    description = 'My tunnel description.'
    ike_version = 2
    shared_secret = 'secret-xyz'
    vpn_gateway = 'my-gateway'
    interface = 0
    router = 'my-router'
    peer_external_gateway = 'external-gateway'
    peer_external_gateway_interface = 3

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        description=description,
        ikeVersion=ike_version,
        peerExternalGateway=self.GetExternalVpnGatewayRef(
            peer_external_gateway).SelfLink(),
        peerExternalGatewayInterface=3,
        sharedSecret=shared_secret,
        vpnGateway=self.GetVpnGatewayRef(vpn_gateway).SelfLink(),
        vpnGatewayInterface=interface,
        router=self.GetRouterRef(router).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run('compute vpn-tunnels create {} '
                        '--description "{}" '
                        '--ike-version {} '
                        '--peer-external-gateway {} '
                        '--peer-external-gateway-interface {} '
                        '--shared-secret {} '
                        '--vpn-gateway {} '
                        '--interface {} '
                        '--router {} '
                        '--region {} '
                        '--format=disable'.format(
                            name, description, ike_version,
                            peer_external_gateway,
                            peer_external_gateway_interface, shared_secret,
                            vpn_gateway, interface, router, self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)

  def testFlagsAcceptUris(self):
    name = 'my-tunnel'
    peer_gcp_gateway = 'peer-gateway'
    shared_secret = 'secret-xyz'
    vpn_gateway = 'my-gateway'
    interface = 1
    router = 'my-router'

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        peerGcpGateway=self.GetVpnGatewayRef(peer_gcp_gateway).SelfLink(),
        sharedSecret=shared_secret,
        vpnGateway=self.GetVpnGatewayRef(vpn_gateway).SelfLink(),
        vpnGatewayInterface=interface,
        router=self.GetRouterRef(router).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels create '
        '{base_uri}/regions/{region}/vpnTunnels/{vpn_tunnel_name} '
        '--peer-gcp-gateway '
        'projects/{project}/regions/{region}/vpnGateways/{peer_gcp_gateway} '
        '--shared-secret {shared_secret} '
        '--vpn-gateway {base_uri}/regions/{region}/vpnGateways/{gateway_name} '
        '--interface {vpn_gateway_interface} '
        '--router {router} '
        '--format=disable'.format(
            vpn_tunnel_name=name,
            peer_gcp_gateway=peer_gcp_gateway,
            shared_secret=shared_secret,
            gateway_name=vpn_gateway,
            vpn_gateway_interface=interface,
            router=router,
            base_uri=self.base_uri,
            region=self.REGION,
            project=self.Project()))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)

  def testInvocationWithoutOptionalArgsOk(self):
    name = 'my-tunnel'
    peer_gcp_gateway = 'peer-gateway'
    shared_secret = 'secret-xyz'
    vpn_gateway = 'my-gateway'
    interface = 0
    router = 'my-router'

    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    vpn_tunnel_to_insert = self.messages.VpnTunnel(
        name=name,
        peerGcpGateway=self.GetVpnGatewayRef(peer_gcp_gateway).SelfLink(),
        sharedSecret=shared_secret,
        vpnGateway=self.GetVpnGatewayRef(vpn_gateway).SelfLink(),
        vpnGatewayInterface=interface,
        router=self.GetRouterRef(router).SelfLink())
    created_vpn_tunnel = copy.deepcopy(vpn_tunnel_to_insert)
    created_vpn_tunnel.selfLink = vpn_tunnel_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectInsertRequest(vpn_tunnel_ref, vpn_tunnel_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, created_vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels create {} '
        '--peer-gcp-gateway {} '
        '--shared-secret {} '
        '--vpn-gateway {} '
        '--interface {} '
        '--router {} '
        '--region {} '
        '--format=disable'.format(name, peer_gcp_gateway, shared_secret,
                                  vpn_gateway, interface, router, self.REGION))
    resources = list(response)
    self.assertEqual(resources[0], created_vpn_tunnel)

  def testInvocationWithoutSharedSecretFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --shared-secret: Must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-gcp-gateway peer-gateway
            --vpn-gateway my-gateway
            --interface 1
            --router my-router
          """)

  def testInvocationWithBadSharedSecretFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'The argument to --shared-secret is not valid it contains '
        'non-printable charcters.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-gcp-gateway peer-gateway
            --vpn-gateway my-gateway
            --interface 1
            --router my-router
            --shared-secret '\n'
          """)

  def testInvocationWithoutAnyVpnGatewayTypeFails(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--target-vpn-gateway | --target-vpn-gateway-region | '
        + '--vpn-gateway | --vpn-gateway-region) ' + 'must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-gcp-gateway peer-gateway
            --interface 1
            --router my-router
            --shared-secret secret-xyz
          """)

  def testInvocationWithoutInterfaceFails(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--interface]: When creating Highly Available VPN '
        'tunnels, the VPN gateway interface must be specified using the '
        '--interface flag.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-gcp-gateway peer-gateway
            --shared-secret secret-xyz
            --vpn-gateway my-gateway
            --router my-router
          """)

  def testInvocationWithoutRouterFails(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--router]: When creating Highly Available VPN '
        'tunnels, a Cloud Router must be specified using the --router flag.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-gcp-gateway peer-gateway
            --shared-secret secret-xyz
            --vpn-gateway my-gateway
            --interface 1
          """)

  def testInvocationWithRemoteTrafficSelectorFails(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--remote-traffic-selector]: Cannot specify remote '
        'traffic selector with Highly Available VPN tunnels.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-gcp-gateway peer-gateway
            --shared-secret secret-xyz
            --vpn-gateway my-gateway
            --interface 0
            --router my-router
            --remote-traffic-selector 192.168.100.14/24,10.0.0.0/8
          """)

  def testInvocationWithLocalTrafficSelectorFails(self):
    with self.AssertRaisesToolExceptionMatches(
        'Invalid value for [--local-traffic-selector]: Cannot specify local '
        'traffic selector with Highly Available VPN tunnels.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --region my-region
            --peer-gcp-gateway peer-gateway
            --shared-secret secret-xyz
            --vpn-gateway my-gateway
            --interface 0
            --router my-router
            --local-traffic-selector 192.168.100.14/24,10.0.0.0/8
          """)

  def testInvocationWithoutPeerAddressFails(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'When creating Highly Available VPN tunnels, either '
        '--peer-gcp-gateway or --peer-external-gateway must be specified.'):
      self.Run("""\
          compute vpn-tunnels create my-tunnel
            --shared-secret secret-xyz
            --vpn-gateway my-gateway
            --interface 0
            --peer-address 71.72.73.74
            --region my-region
            --router my-router
          """)


class HighAvailabilityVpnTunnelsCreateBetaTest(
    HighAvailabilityVpnTunnelsCreateGaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class HighAvailabilityVpnTunnelsCreateAlphaTest(
    HighAvailabilityVpnTunnelsCreateBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
