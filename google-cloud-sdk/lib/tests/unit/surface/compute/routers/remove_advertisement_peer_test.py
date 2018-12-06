# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the update-bgp-peer command with remove advertisement flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.routers import router_utils
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base
from tests.lib.surface.compute import router_test_utils


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA, 'alpha'),
                          (calliope_base.ReleaseTrack.BETA, 'beta'),
                          (calliope_base.ReleaseTrack.GA, 'v1'))
class RemoveAdvertisementPeerTest(parameterized.TestCase,
                                  router_test_base.RouterTestBase):

  def testRemoveAdvertisementPeerGroups_success(self, track, api_version):
    self.SelectApi(track, api_version)

    # Start with a router in custom mode.
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    updated.bgpPeers[0].advertisedGroups = []

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsGet()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update-bgp-peer my-router --region us-central1
        --peer-name=my-peer
        --remove-advertisement-groups=ALL_SUBNETS
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating peer [my-peer] in router [my-router]')

  def testRemoveAdvertisementPeerGroups_groupNotFoundError(
      self, track, api_version):
    self.SelectApi(track, api_version)

    # Start with a router in custom mode.
    orig = router_test_utils.CreateEmptyCustomRouterMessage(self.messages)

    self.ExpectGet(orig)

    error_msg = 'Advertised group ALL_SUBNETS not found on this peer.'
    with self.AssertRaisesExceptionMatches(router_utils.GroupNotFoundError,
                                           error_msg):
      self.Run("""
          compute routers update-bgp-peer my-router --region us-central1
          --peer-name my-peer
          --remove-advertisement-groups=ALL_SUBNETS
          """)

  def testRemoveAdvertisementPeerRanges_success(self, track, api_version):
    self.SelectApi(track, api_version)

    # Start with a router in custom mode.
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.20/30', description='my-desc'),
    ]
    updated.bgpPeers[0].advertisedIpRanges = ranges

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsGet()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update-bgp-peer my-router --region us-central1
        --peer-name=my-peer
        --remove-advertisement-ranges=10.10.10.10/30
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating peer [my-peer] in router [my-router]')

  def testRemoveAdvertisementPeerRanges_multiSuccess(self, track, api_version):
    self.SelectApi(track, api_version)

    # Start with a router in custom mode.
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    ranges = []
    updated.bgpPeers[0].advertisedIpRanges = ranges

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsGet()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update-bgp-peer my-router --region us-central1
        --peer-name=my-peer
        --remove-advertisement-ranges=10.10.10.10/30,10.10.10.20/30
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating peer [my-peer] in router [my-router]')

  def testRemoveAdvertisementRanges_ipRangeNotFoundError(
      self, track, api_version):
    self.SelectApi(track, api_version)

    # Start with a router in custom mode.
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)

    self.ExpectGet(orig)

    error_msg = 'Advertised IP range 192.168.0.0/30 not found on this peer.'
    with self.AssertRaisesExceptionMatches(router_utils.IpRangeNotFoundError,
                                           error_msg):
      self.Run("""
          compute routers update-bgp-peer my-router --region us-central1
          --peer-name my-peer
          --remove-advertisement-ranges=192.168.0.0/30
          """)

  def testRemoveAdvertisementPeer_mutallyExclusiveError(self, track,
                                                        api_version):
    self.SelectApi(track, api_version)

    error_msg = ('argument --remove-advertisement-groups: At most one of '
                 '--add-advertisement-groups | --add-advertisement-ranges | '
                 '--remove-advertisement-groups | '
                 '--remove-advertisement-ranges may be specified.')
    with self.AssertRaisesArgumentErrorMatches(error_msg):
      self.Run("""
          compute routers update-bgp-peer my-router --region us-central1
          --peer-name=my-peer
          --remove-advertisement-groups=ALL_SUBNETS
          --remove-advertisement-ranges=10.10.10.10/30
          """)

  def testRemoveAdvertisementPeer_peerNotFoundError(self, track, api_version):
    self.SelectApi(track, api_version)

    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)

    self.ExpectGet(orig)

    error_msg = ('peer `nonexistent-peer` not found')
    with self.AssertRaisesExceptionMatches(router_utils.PeerNotFoundError,
                                           error_msg):
      self.Run("""
          compute routers update-bgp-peer my-router --region us-central1
          --peer-name=nonexistent-peer
          --remove-advertisement-groups=ALL_SUBNETS
          """)

  def testRemoveAdvertisementPeer_defaultModeError(self, track, api_version):
    self.SelectApi(track, api_version)

    # Start with a router in default mode.
    orig = router_test_utils.CreateDefaultRouterMessage(self.messages)

    self.ExpectGet(orig)

    error_msg = ('Cannot specify custom advertisements for a peer with default '
                 'mode.')
    with self.AssertRaisesExceptionMatches(router_utils.CustomWithDefaultError,
                                           error_msg):
      self.Run("""
          compute routers update-bgp-peer my-router --region us-central1
          --peer-name=my-peer
          --remove-advertisement-groups=ALL_SUBNETS
          """)


if __name__ == '__main__':
  test_case.main()
