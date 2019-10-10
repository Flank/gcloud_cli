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
"""Integration tests for VPN gateways labels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class HaVpnGaTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.local_vpn_gateway_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-local-vpn-gateway'))
    self.peer_vpn_gateway_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-peer-vpn-gateway'))
    self.router_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-router'))
    self.tunnel_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-vpn-tunnel'))

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    try:
      cmd = (subcommand, 'delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass

  @contextlib.contextmanager
  def _VpnTunnel(self, region):
    try:
      self.RunCompute('vpn-gateways', 'create', self.local_vpn_gateway_name,
                      '--region', region, '--network', 'default')
      self.RunCompute('external-vpn-gateways', 'create',
                      self.peer_vpn_gateway_name, '--interfaces', '0=8.8.8.9')
      self.RunCompute('routers', 'create', self.router_name, '--region', region,
                      '--network', 'default')
      yield self.RunCompute(
          'vpn-tunnels', 'create', self.tunnel_name, '--region', region,
          '--vpn-gateway', self.local_vpn_gateway_name, '--interface', '0',
          '--router', self.router_name, '--shared-secret', 'abced',
          '--peer-external-gateway', self.peer_vpn_gateway_name,
          '--peer-external-gateway-interface', '0', '--region', region)
    finally:
      self.CleanUpResource('vpn-tunnels', self.tunnel_name, '--region', region)
      self.CleanUpResource('routers', self.router_name, '--region', region)
      self.CleanUpResource('vpn-gateways', self.local_vpn_gateway_name,
                           '--region', region)
      self.CleanUpResource('external-vpn-gateways', self.peer_vpn_gateway_name)

  def testVpnTunnel(self):
    with self._VpnTunnel(self.region):
      self.AssertNewOutputContains(self.tunnel_name)
      self.Run('compute vpn-tunnels describe {0} --region {1}'.format(
          self.tunnel_name, self.region))
      self.AssertNewOutputContains('name: {0}'.format(
          self.tunnel_name), reset=False)
      self.AssertNewOutputContains(
          'vpnGateway:', reset=False)
      self.AssertNewOutputContains(
          'vpnGatewayInterface: 0', reset=False)
      self.AssertNewOutputContains(
          'peerExternalGateway:', reset=False)


if __name__ == '__main__':
  e2e_test_base.main()
