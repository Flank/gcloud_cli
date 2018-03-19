# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for creating/deleting vpn tunnels."""

import json
import logging

from googlecloudsdk.calliope import base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class VpnTest(e2e_test_base.BaseTest):

  def UniqueName(self, name):
    return e2e_utils.GetResourceNameGenerator(
        prefix='compute-vpn-test-' + name).next()

  def SetUp(self):
    self.vpn_gateway_names_used = []
    self.network_names_used = []
    self.address_names_used = []
    self.forwarding_rule_esp_names_used = []
    self.forwarding_rule_udp500_names_used = []
    self.forwarding_rule_udp4500_names_used = []
    self.route_names_used = []
    self.vpn_tunnel_names_used = []

  def GetResourceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.vpn_gateway_name = self.UniqueName('vpn-gateway')
    self.network_name = self.UniqueName('network')
    self.address_name = self.UniqueName('address')
    self.forwarding_rule_esp_name = self.UniqueName('fwd-rule-esp')
    self.forwarding_rule_udp500_name = self.UniqueName(
        'fw-rule-udp500')
    self.forwarding_rule_udp4500_name = self.UniqueName(
        'fwd-rule-udp4500')
    self.route_name = self.UniqueName('route')
    self.vpn_tunnel_name = self.UniqueName('vpn-tunnel')
    self.vpn_gateway_names_used.append(self.vpn_gateway_name)
    self.network_names_used.append(self.network_name)
    self.address_names_used.append(self.address_name)
    self.forwarding_rule_esp_names_used.append(self.forwarding_rule_esp_name)
    self.forwarding_rule_udp500_names_used.append(
        self.forwarding_rule_udp500_name)
    self.forwarding_rule_udp4500_names_used.append(
        self.forwarding_rule_udp4500_name)
    self.route_names_used.append(self.route_name)
    self.vpn_tunnel_names_used.append(self.vpn_tunnel_name)

  def testVpn(self):
    self.GetResourceName()
    self.BringUpVpn()
    self.DeleteVpn()

  def testVpnWithAddressURI(self):
    self.GetResourceName()
    self.BringUpVpn(address_field='name')
    self.DeleteVpn()

  def BringUpVpn(self, address_field='address'):

    self.Run('compute networks create '
             '--range 10.120.0.0/16 --subnet-mode LEGACY {network}'.format(
                 network=self.network_name))
    self.Run('compute target-vpn-gateways create --region {region} '
             '--network {network} {vpn_gateway}'.format(
                 region=e2e_test_base.REGION,
                 network=self.network_name,
                 vpn_gateway=self.vpn_gateway_name))
    self.GetNewOutput()  # As a side effect reset the output buffer

    self.Run('compute addresses create --region {region} {address} '
             '--format json'.format(
                 region=e2e_test_base.REGION, address=self.address_name))

    address_as_json = json.loads(self.GetNewOutput())
    ip = address_as_json[0][address_field]

    self.Run("""compute forwarding-rules create --region {region}
                --ip-protocol ESP --address {ip}
                --target-vpn-gateway {vpn_gateway} {fr_esp}
             """.format(
                 region=e2e_test_base.REGION,
                 ip=ip,
                 vpn_gateway=self.vpn_gateway_name,
                 fr_esp=self.forwarding_rule_esp_name))

    self.Run("""compute forwarding-rules create --region {region}
                --ip-protocol UDP --ports 500 --address {ip}
                --target-vpn-gateway {vpn_gateway} {fr_udp500}
             """.format(
                 region=e2e_test_base.REGION,
                 ip=ip,
                 vpn_gateway=self.vpn_gateway_name,
                 fr_udp500=self.forwarding_rule_udp500_name))

    self.Run("""compute forwarding-rules create --region {region}
                --ip-protocol UDP --ports 4500 --address {ip}
                --target-vpn-gateway {vpn_gateway} {fr_udp4500}
             """.format(
                 region=e2e_test_base.REGION,
                 ip=ip,
                 vpn_gateway=self.vpn_gateway_name,
                 fr_udp4500=self.forwarding_rule_udp4500_name))

    self.Run("""compute vpn-tunnels create --region {region}
                --peer-address 8.8.8.8 --shared-secret 'whatever'
                --target-vpn-gateway {vpn_gateway} {vpn_tunnel}
             """.format(
                 region=e2e_test_base.REGION,
                 vpn_gateway=self.vpn_gateway_name,
                 vpn_tunnel=self.vpn_tunnel_name))

    self.Run("""compute routes create
                --next-hop-vpn-tunnel-region {region}
                --network {network}
                --next-hop-vpn-tunnel {vpn_tunnel}
                --destination-range 192.168.100.0/24 {route}
             """.format(
                 region=e2e_test_base.REGION,
                 network=self.network_name,
                 vpn_tunnel=self.vpn_tunnel_name,
                 route=self.route_name))

  def DeleteVpn(self):
    self.Run('compute routes delete {route} --quiet'.format(
        route=self.route_name))

    self.Run("""compute vpn-tunnels delete {vpn_tunnel}
                --region {region} --quiet
             """.format(
                 region=e2e_test_base.REGION, vpn_tunnel=self.vpn_tunnel_name))

    self.Run("""compute forwarding-rules delete {fr_esp}
                 --region {region} --quiet
             """.format(
                 region=e2e_test_base.REGION,
                 fr_esp=self.forwarding_rule_esp_name))

    self.Run("""compute forwarding-rules delete {fr_udp500}
                 --region {region} --quiet
             """.format(
                 region=e2e_test_base.REGION,
                 fr_udp500=self.forwarding_rule_udp500_name))

    self.Run("""compute forwarding-rules delete {fr_udp4500}
                 --region {region} --quiet
             """.format(
                 region=e2e_test_base.REGION,
                 fr_udp4500=self.forwarding_rule_udp4500_name))

    self.Run("""compute addresses delete {address}
                --region {region} --quiet
             """.format(
                 address=self.address_name, region=e2e_test_base.REGION))

    self.Run("""compute target-vpn-gateways delete {vpn_gateway}
                --region {region} --quiet""".format(
                    region=e2e_test_base.REGION,
                    vpn_gateway=self.vpn_gateway_name))

    self.Run('compute networks delete {network} --quiet'.format(
        network=self.network_name))

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')

    for name in self.route_names_used:
      self.CleanUpResource(name, 'routes',
                           scope=e2e_test_base.GLOBAL)
    for name in self.vpn_tunnel_names_used:
      self.CleanUpResource(name, 'vpn-tunnels',
                           scope=e2e_test_base.REGIONAL)
    for name in self.forwarding_rule_esp_names_used:
      self.CleanUpResource(name, 'forwarding-rules',
                           scope=e2e_test_base.REGIONAL)
    for name in self.forwarding_rule_udp500_names_used:
      self.CleanUpResource(name, 'forwarding-rules',
                           scope=e2e_test_base.REGIONAL)
    for name in self.forwarding_rule_udp4500_names_used:
      self.CleanUpResource(name, 'forwarding-rules',
                           scope=e2e_test_base.REGIONAL)
    for name in self.address_names_used:
      self.CleanUpResource(name, 'addresses',
                           scope=e2e_test_base.REGIONAL)
    for name in self.vpn_gateway_names_used:
      self.CleanUpResource(name, 'target-vpn-gateways',
                           scope=e2e_test_base.REGIONAL)
    for name in self.network_names_used:
      self.CleanUpResource(name, 'networks',
                           scope=e2e_test_base.GLOBAL)


class BetaVpnTest(VpnTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA

  def testVpnLabels(self):
    self.GetResourceName()
    self.BringUpVpn()
    self._TestLabels()
    self.DeleteVpn()

  def _TestLabels(self):

    def CreateUpdateLabelsArg(labels):
      return ','.join('{0}={1}'.format(pair[0], pair[1]) for pair in labels)

    add_labels_arg = CreateUpdateLabelsArg([('x', 'y'), ('abc', 'xyz')])
    self.Run(('compute vpn-tunnels update '
              '{0} --region {1} --update-labels {2}').format(
                  self.vpn_tunnel_name, self.region, add_labels_arg))
    self.Run('compute vpn-tunnels describe {0} --region {1}'.format(
        self.vpn_tunnel_name, self.region))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

    # Modify the label with key 'x', remove the label with key 'abc', and
    # add label with key 't123'.
    # Remove should take precedence over update for 'abc'.
    update_labels_arg = CreateUpdateLabelsArg([('x', 'a'), ('abc', 'xyz'),
                                               ('t123', 't7890')])
    remove_labels_arg = 'abc'
    self.Run("""
         compute vpn-tunnels update {0} --region {1}
             --update-labels {2} --remove-labels {3}
        """.format(self.vpn_tunnel_name, self.region, update_labels_arg,
                   remove_labels_arg))

    self.Run('compute vpn-tunnels describe {0} --region {1}'.format(
        self.vpn_tunnel_name, self.region))
    self.AssertNewOutputContains('t123: t7890', reset=False)
    self.AssertNewOutputContains('x: a', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')


class AlphaVpnTest(BetaVpnTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  e2e_test_base.main()
