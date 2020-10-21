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

"""Tests for the remove-bgp-peer subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import router_test_utils
from tests.lib.surface.compute import test_base


class RemoveBgpPeerTest(test_base.BaseTest):

  def testSimple(self):
    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    expected = copy.deepcopy(orig)

    expected.bgpPeers.pop()

    self.make_requests.side_effect = iter([
        [orig],
        []
    ])

    self.Run("""
        compute routers remove-bgp-peer my-router --peer-name my-peer
        --region us-central1
        """)

    self.CheckRequests(
        [(self.compute.routers,
          'Get',
          self.messages.ComputeRoutersGetRequest(
              router='my-router',
              region='us-central1',
              project='my-project'))],
        [(self.compute.routers,
          'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],
    )


class RemoveBgpPeerTestAlpha(RemoveBgpPeerTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testRemoveListOfBgpPeers(self):
    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    orig.bgpPeers.append(
        self.messages.RouterBgpPeer(
            name='my-peer-2', interfaceName='my-if-2', peerAsn=66000))
    expected = copy.deepcopy(orig)

    expected.bgpPeers.pop()
    expected.bgpPeers.pop()

    self.make_requests.side_effect = iter([
        [orig],
        []
    ])

    self.Run("""
        compute routers remove-bgp-peer my-router
        --peer-names my-peer,my-peer-2 --region us-central1
        """)

    self.CheckRequests(
        [(self.compute.routers,
          'Get',
          self.messages.ComputeRoutersGetRequest(
              router='my-router',
              region='us-central1',
              project='my-project'))],
        [(self.compute.routers,
          'Patch',
          self.messages.ComputeRoutersPatchRequest(
              router='my-router',
              routerResource=expected,
              region='us-central1',
              project='my-project'))],
    )

  def testUsingBothPeerNameAndPeerNameListError(self):
    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    orig.bgpPeers.append(
        self.messages.RouterBgpPeer(
            name='my-peer-2', interfaceName='my-if-2', peerAsn=66000))
    expected = copy.deepcopy(orig)

    expected.bgpPeers.pop()
    expected.bgpPeers.pop()

    self.make_requests.side_effect = iter([
        [orig],
        []
    ])

    with self.AssertRaisesArgumentErrorMatches(
        'argument --peer-name: Exactly one of (--peer-name | '
        '--peer-names) must be specified.'):
      self.Run("""
          compute routers remove-bgp-peer my-router
          --peer-names my-peer,my-peer-2 --region us-central1
          --peer-name my-peer
          """)


if __name__ == '__main__':
  test_case.main()
