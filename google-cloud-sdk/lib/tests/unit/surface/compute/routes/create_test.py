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
"""Tests for the routes create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class RoutesCreateTest(test_base.BaseTest):

  def testWithNextHopInstance(self):
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-instance my-instance
          --next-hop-instance-zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/default'
                          ).format(api=self.api),
                  nextHopInstance=(
                      'https://compute.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/us-central1-a/instances/my-instance'
                      ).format(api=self.api),
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testWithNextHopInstanceWithoutNextHopInstanceZone(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(name='my-instance', zone='zone-1'),
            self.messages.Instance(name='my-instance', zone='zone-2'),
            self.messages.Instance(name='my-instance', zone='zone-3'),
        ],

        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-instance my-instance
        """)

    self.AssertErrContains('zone-1')
    self.AssertErrContains('zone-2')
    self.AssertErrContains('zone-3')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('my-instance'),

        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/default'
                          ).format(api=self.api),
                  nextHopInstance=(
                      'https://compute.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/zone-1/instances/my-instance'
                      ).format(api=self.api),
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testWithNextHopInstanceZoneWithoutNextHopInstance(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--next-hop-instance-zone\] can only be specified in conjunction '
        r'with \[--next-hop-instance\].'):
      self.Run("""
          compute routes create my-route
            --destination-range 10.0.0.0/8
            --next-hop-address 10.240.0.2
            --next-hop-instance-zone us-central1-a
          """)

    self.CheckRequests()

  def testWithNextHopAddress(self):
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-address 10.240.0.2
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/default'
                          ).format(api=self.api),
                  nextHopIp='10.240.0.2',
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testWithDescription(self):
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-address 10.240.0.2
          --description "a route that routes packets"
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  description='a route that routes packets',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/default'
                          ).format(api=self.api),
                  nextHopIp='10.240.0.2',
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testWithNextHopGateway(self):
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-gateway default-internet-gateway
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/default'
                          ).format(api=self.api),
                  nextHopGateway=(
                      'https://compute.googleapis.com/compute/{api}/projects/'
                      'my-project/global/gateways/default-internet-gateway'
                      ).format(api=self.api),
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testWithNoNextHop(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--next-hop-address | --next-hop-gateway | '
        '--next-hop-instance | --next-hop-vpn-tunnel) '
        'must be specified.'):
      self.Run("""
          compute routes create my-route
            --destination-range 10.0.0.0/8
          """)

    self.CheckRequests()

  def testWithManyNextHops(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --next-hop-gateway: Exactly one of (--next-hop-address | '
        '--next-hop-gateway | --next-hop-instance | --next-hop-vpn-tunnel) '
        'must be specified.'):
      self.Run("""
          compute routes create my-route
            --destination-range 10.0.0.0/8
            --next-hop-instance my-instance
            --next-hop-instance-zone us-central1-a
            --next-hop-gateway default-internet-gateway
          """)

    self.CheckRequests()

  def testWithNoDestinationRange(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --destination-range: Must be specified.'):
      self.Run("""
          compute routes create my-route
            --next-hop-instance my-instance
            --next-hop-instance-zone us-central1-a
          """)

    self.CheckRequests()

  def testWithPriority(self):
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-instance my-instance
          --next-hop-instance-zone us-central1-a
          --priority 99
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/default'
                          ).format(api=self.api),
                  nextHopInstance=(
                      'https://compute.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/us-central1-a/instances/my-instance'
                      ).format(api=self.api),
                  priority=99,
              ),
              project='my-project'))],
    )

  def testWithTags(self):
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-instance my-instance
          --next-hop-instance-zone us-central1-a
          --tags tag-1,tag-2
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/default'
                          ).format(api=self.api),
                  nextHopInstance=(
                      'https://compute.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/us-central1-a/instances/my-instance'
                      ).format(api=self.api),
                  priority=1000,
                  tags=['tag-1', 'tag-2'],
              ),
              project='my-project'))],
    )

  def testWithNetwork(self):
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-instance my-instance
          --next-hop-instance-zone us-central1-a
          --network my-network
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/my-network'
                          ).format(api=self.api),
                  nextHopInstance=(
                      'https://compute.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/us-central1-a/instances/my-instance'
                      ).format(api=self.api),
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute routes create
          https://compute.googleapis.com/compute/{api}/projects/my-project/global/routes/my-route
          --destination-range 10.0.0.0/8
          --next-hop-instance https://compute.googleapis.com/compute/{api}/projects/my-project/zones/us-central1-a/instances/my-instance
          --network https://compute.googleapis.com/compute/{api}/projects/my-project/global/networks/my-network
        """.format(api=self.api))

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/my-network'
                          ).format(api=self.api),
                  nextHopInstance=(
                      'https://compute.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/us-central1-a/instances/my-instance'
                      ).format(api=self.api),
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testDefaultUsedForNextHopInstanceZone(self):
    properties.VALUES.compute.zone.Set('us-central1-a')
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-instance my-instance
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=('https://compute.googleapis.com/compute/{api}/projects/'
                           'my-project/global/networks/default'
                          ).format(api=self.api),
                  nextHopInstance=(
                      'https://compute.googleapis.com/compute/{api}/projects/'
                      'my-project/zones/us-central1-a/instances/my-instance'
                      ).format(api=self.api),
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testWithNextHopVpnTunnel(self):
    messages = self.messages
    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-vpn-tunnel my-tunnel
          --next-hop-vpn-tunnel-region us-central1
        """)

    self.CheckRequests(
        [(self.compute.routes,
          'Insert',
          messages.ComputeRoutesInsertRequest(
              route=messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=(self.compute_uri +
                           '/projects/my-project/global/networks/default'),
                  nextHopVpnTunnel=(
                      self.compute_uri + '/projects/my-project'
                      '/regions/us-central1/vpnTunnels/my-tunnel'),
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testWithNextHopVpnTunnelWithoutNextHopVpnTunnelRegion(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='region-1'),
            self.messages.Region(name='region-2'),
            self.messages.Region(name='region-3'),
        ],
        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute routes create my-route
          --destination-range 10.0.0.0/8
          --next-hop-vpn-tunnel my-tunnel
        """)
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains('"choices": ["region-1", "region-2", "region-3"]')
    self.CheckRequests(
        self.regions_list_request,
        [(self.compute.routes, 'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='10.0.0.0/8',
                  network=(self.compute_uri +
                           '/projects/my-project/global/networks/default'),
                  nextHopVpnTunnel=(self.compute_uri + '/projects/my-project'
                                    '/regions/region-1/vpnTunnels/my-tunnel'),
                  priority=1000,),
              project='my-project'))],)

  def testWithNextHopVpnTunnelRegionWithoutVpnTunnel(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--next-hop-vpn-tunnel-region\] can only be specified in '
        r'conjunction with \[--next-hop-vpn-tunnel\].'):
      self.Run("""
          compute routes create my-route
            --destination-range 10.0.0.0/8
            --next-hop-address 10.240.0.2
            --next-hop-vpn-tunnel-region us-central1-a
          """)


class RoutesCreateAlphaTest(RoutesCreateTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testWithNextHopIlb(self):
    messages = self.messages
    self.Run("""
       compute routes create my-route
          --destination-range 20.0.0.0/8
          --next-hop-ilb my-forwarding-rule
          --next-hop-ilb-region us-central1
        """)

    self.CheckRequests([
        (self.compute.routes, 'Insert',
         messages.ComputeRoutesInsertRequest(
             route=messages.Route(
                 name='my-route',
                 destRange='20.0.0.0/8',
                 network=(self.compute_uri +
                          '/projects/my-project/global/networks/default'),
                 nextHopIlb=(
                     self.compute_uri + '/projects/my-project'
                     '/regions/us-central1/forwardingRules/my-forwarding-rule'),
                 priority=1000,
             ),
             project='my-project'))
    ],)

  def testWithNextHopIlbWithoutNextHopIlbRegion(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='region-1'),
            self.messages.Region(name='region-2'),
            self.messages.Region(name='region-3'),
        ],
        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute routes create my-route
          --destination-range 20.0.0.0/8
          --next-hop-ilb my-forwarding-rule
        """)
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains('"choices": ["region-1", "region-2", "region-3"]')
    self.CheckRequests(
        self.regions_list_request,
        [(self.compute.routes, 'Insert',
          self.messages.ComputeRoutesInsertRequest(
              route=self.messages.Route(
                  name='my-route',
                  destRange='20.0.0.0/8',
                  network=(self.compute_uri +
                           '/projects/my-project/global/networks/default'),
                  nextHopIlb=(
                      self.compute_uri + '/projects/my-project'
                      '/regions/region-1/forwardingRules/my-forwarding-rule'),
                  priority=1000,
              ),
              project='my-project'))],
    )

  def testWithNextHopIlbRegionWithoutNextHopIlb(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--next-hop-ilb-region\] can only be specified in '
        r'conjunction with \[--next-hop-ilb\].'):
      self.Run("""
          compute routes create my-route
            --destination-range 20.0.0.0/8
            --next-hop-address 10.240.0.2
            --next-hop-ilb-region us-central1-a
          """)

  def testWithNoNextHop(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--next-hop-address | --next-hop-gateway | '
        '--next-hop-ilb | --next-hop-instance | --next-hop-vpn-tunnel) '
        'must be specified.'):
      self.Run("""
          compute routes create my-route
            --destination-range 10.0.0.0/8
          """)

    self.CheckRequests()

  def testWithManyNextHops(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --next-hop-gateway: Exactly one of (--next-hop-address | '
        '--next-hop-gateway | --next-hop-ilb | --next-hop-instance | '
        '--next-hop-vpn-tunnel) '
        'must be specified.'):
      self.Run("""
          compute routes create my-route
            --destination-range 10.0.0.0/8
            --next-hop-instance my-instance
            --next-hop-instance-zone us-central1-a
            --next-hop-gateway default-internet-gateway
          """)

    self.CheckRequests()


class RoutesCreateBetaTest(RoutesCreateAlphaTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
