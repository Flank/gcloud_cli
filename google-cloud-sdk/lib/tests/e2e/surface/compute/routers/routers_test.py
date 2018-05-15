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
"""Integration tests for manipulating routers."""

from __future__ import absolute_import
from __future__ import unicode_literals
import logging

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.sdk_test_base import Retry
from tests.lib.surface.compute import e2e_test_base


class RoutersTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.network_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-network'))
    self.router_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-router'))
    self.peer_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-bgp-peer'))

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    self.CleanUpResource(
        self.router_name, 'routers', scope=e2e_test_base.REGIONAL)
    self.CleanUpResource(
        self.network_name, 'networks', scope=e2e_test_base.GLOBAL)

  def testBasicCommands(self):
    # TODO(b/62286653) Add a context manager to handle test resource creation.
    self.Run('compute networks create {0} --subnet-mode custom'.format(
        self.network_name))

    self.Run('compute routers create {0} --network {1} --region {2} '
             '--asn 65000'.format(self.router_name, self.network_name,
                                  self.region))
    self.AssertNewOutputContains(self.router_name)

    self.Run('compute routers describe {0} --region {1}'.format(
        self.router_name, self.region))
    self.AssertNewOutputContains('name: {0}'.format(self.router_name))

    self.Run('compute routers get-status {} --region {}'.format(
        self.router_name, self.region))
    self.AssertNewOutputContains('kind: compute#routerStatusResponse')

    self.Run('compute routers add-interface {0} --region {1} '
             '--interface-name my-interface --vpn-tunnel vpn'.format(
                 self.router_name, self.region))
    self.Run('compute routers describe {0} --region {1}'.format(
        self.router_name, self.region))
    self.AssertNewOutputContains('my-interface')

    self.Run('compute routers remove-interface {0} --region {1} '
             '--interface-name my-interface'.format(self.router_name,
                                                    self.region))
    self.Run('compute routers describe {0} --region {1}'.format(
        self.router_name, self.region))
    self.AssertNewOutputNotContains('my-interface')

    self.Run('compute routers add-bgp-peer {0} --region {1} '
             '--peer-name {2} --peer-asn 65100 --interface my-interface'.format(
                 self.router_name, self.region, self.peer_name))
    self.Run('compute routers describe {0} --region {1}'.format(
        self.router_name, self.region))
    self.AssertNewOutputContains(self.peer_name)

    self.Run('compute routers remove-bgp-peer {0} --region {1} '
             '--peer-name {2}'.format(self.router_name, self.region,
                                      self.peer_name))
    self.Run('compute routers describe {0} --region {1}'.format(
        self.router_name, self.region))
    self.AssertNewOutputNotContains(self.peer_name)

    # Retry deletion in case resource was not ready yet.
    cmd = 'compute routers delete {0} --region {1}'.format(
        self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))

  def testCreateWithAdvertisements(self):
    self.Run('compute networks create {0} --subnet-mode custom'.format(
        self.network_name))

    self.Run('compute routers create {0} --network {1} --region {2} '
             '--asn 65000 '
             '--advertisement-mode CUSTOM '
             '--set-advertisement-groups ALL_SUBNETS '
             '--set-advertisement-ranges 10.0.10.0/30'.format(
                 self.router_name, self.network_name, self.region))

    result = self.Run('compute routers describe {0} --region {1} --format '
                      'disable'.format(self.router_name, self.region))
    self.assertEqual(result.bgp.advertiseMode.name, 'CUSTOM')
    self.assertEqual(result.bgp.advertisedGroups[0].name, 'ALL_SUBNETS')
    self.assertEqual(result.bgp.advertisedIpRanges[0].range, '10.0.10.0/30')

    # Retry deletion in case resource was not ready yet.
    cmd = 'compute routers delete {0} --region {1}'.format(
        self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))

  def testAddBgpPeerWithAdvertisements(self):
    self.Run('compute networks create {0} --subnet-mode custom'.format(
        self.network_name))

    self.Run('compute routers create {0} --network {1} --region {2} '
             '--asn 65000 '.format(self.router_name, self.network_name,
                                   self.region))

    self.Run('compute routers add-interface {0} --region {1} '
             '--interface-name my-interface --vpn-tunnel vpn'.format(
                 self.router_name, self.region))
    self.Run('compute routers add-bgp-peer {0} --region {1} --peer-name {2} '
             '--peer-asn 65100 --interface my-interface '
             '--advertisement-mode CUSTOM '
             '--set-advertisement-groups ALL_SUBNETS '
             '--set-advertisement-ranges 10.0.10.0/30'.format(
                 self.router_name, self.region, self.peer_name))

    result = self.Run(
        'compute routers describe {0} --region {1} --format disable'.format(
            self.router_name, self.region))
    self.assertEqual(result.bgpPeers[0].advertiseMode.name, 'CUSTOM')
    self.assertEqual(result.bgpPeers[0].advertisedGroups[0].name,
                     'ALL_SUBNETS')
    self.assertEqual(result.bgpPeers[0].advertisedIpRanges[0].range,
                     '10.0.10.0/30')

    # Retry deletion in case resource was not ready yet.
    cmd = 'compute routers delete {0} --region {1}'.format(
        self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))


if __name__ == '__main__':
  e2e_test_base.main()
