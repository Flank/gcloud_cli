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
"""Tests for the add-bgp-peer subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.routers import router_utils
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base
from tests.lib.surface.compute import router_test_utils


class AddBgpPeerTestGA(router_test_base.RouterTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testAddBgpPeerBasic_success(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateMinimalRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    new_peer = router_test_utils.CreateMinimalBgpPeerMessage(self.messages)
    new_peer.interfaceName = 'my-if'
    new_peer.peerIpAddress = '10.0.0.2'
    new_peer.advertisedRoutePriority = 1

    updated.bgpPeers.append(new_peer)

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsPolling()
    self.ExpectGet(updated)

    self.Run("""
        compute routers add-bgp-peer my-router --region us-central1
        --peer-name my-peer
        --peer-asn 66000
        --interface my-if
        --peer-ip-address 10.0.0.2
        --advertised-route-priority 1
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating peer [my-peer] in router [my-router]')

  def testAddBgpPeer_async(self):
    """Test command with --async flag."""

    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateMinimalRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    updated.bgpPeers.append(
        router_test_utils.CreateMinimalBgpPeerMessage(self.messages))

    self.ExpectGet(orig)
    self.ExpectPatch(updated)

    result = self.Run("""
        compute routers add-bgp-peer my-router --region us-central1
        --async
        --peer-name my-peer
        --peer-asn 66000
        --interface my-if
        """)
    self.assertIn('operation-X', result.name)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Update in progress for router [my-router] to add peer [my-peer] '
        '[https://compute.googleapis.com/compute/{0}/'
        'projects/fake-project/regions/us-central1/operations/operation-X] '
        'Run the [gcloud compute operations describe] command to check the '
        'status of this operation.\n'.format(self.api_version))

  def testAddBgpPeerWithAdvertisements_default(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateMinimalRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    new_peer = router_test_utils.CreateMinimalBgpPeerMessage(self.messages)
    mode = self.messages.RouterBgpPeer.AdvertiseModeValueValuesEnum.DEFAULT
    new_peer.advertiseMode = mode

    updated.bgpPeers.append(new_peer)

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsPolling()
    self.ExpectGet(updated)

    self.Run("""
        compute routers add-bgp-peer my-router --region us-central1
        --peer-name my-peer
        --peer-asn 66000
        --interface my-if
        --advertisement-mode=DEFAULT
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating peer [my-peer] in router [my-router]')

  def testAddBgpPeerWithAdvertisements_custom(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateMinimalRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    new_peer = router_test_utils.CreateMinimalBgpPeerMessage(self.messages)
    mode = self.messages.RouterBgpPeer.AdvertiseModeValueValuesEnum.CUSTOM
    groups = [(self.messages.RouterBgpPeer.
               AdvertisedGroupsValueListEntryValuesEnum.ALL_SUBNETS)]
    ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.10/30', description='custom-range'),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.20/30', description='')
    ]
    new_peer.advertiseMode = mode
    new_peer.advertisedGroups = groups
    new_peer.advertisedIpRanges = ranges

    updated.bgpPeers.append(new_peer)

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsPolling()
    self.ExpectGet(updated)

    self.Run("""
        compute routers add-bgp-peer my-router --region us-central1
        --peer-name my-peer
        --peer-asn 66000
        --interface my-if
        --advertisement-mode=CUSTOM
        --set-advertisement-groups=ALL_SUBNETS
        --set-advertisement-ranges=10.10.10.10/30=custom-range,10.10.10.20/30
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating peer [my-peer] in router [my-router]')

  def testAddBgpPeerWithAdvertisements_customWithDefaultError(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateEmptyCustomRouterMessage(self.messages)

    self.ExpectGet(orig)

    error_msg = ('Cannot specify custom advertisements for a peer with '
                 'default mode.')
    with self.AssertRaisesExceptionMatches(router_utils.CustomWithDefaultError,
                                           error_msg):
      self.Run("""
          compute routers add-bgp-peer my-router --region us-central1
          --peer-name my-peer
          --peer-asn 66000
          --interface my-if
          --advertisement-mode=DEFAULT
          --set-advertisement-groups=ALL_SUBNETS
          --set-advertisement-ranges=10.10.10.10/30=custom-range,10.10.10.20/30
          """)


class AddBgpPeerTestBeta(AddBgpPeerTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testAddBgpPeerBfd_success(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateMinimalRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    new_peer = router_test_utils.CreateMinimalBgpPeerMessage(self.messages)
    new_peer.interfaceName = 'my-if'
    new_peer.peerIpAddress = '10.0.0.2'
    new_peer.advertisedRoutePriority = 1
    new_peer.enable = self.messages.RouterBgpPeer.EnableValueValuesEnum.FALSE
    new_peer.bfd = self._GetRouterBgpPeerBfdMessage()
    updated.bgpPeers.append(new_peer)

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsPolling()
    self.ExpectGet(updated)

    self.Run("""
        compute routers add-bgp-peer my-router --region us-central1
        --peer-name my-peer
        --peer-asn 66000
        --interface my-if
        --peer-ip-address 10.0.0.2
        --advertised-route-priority 1
        --no-enabled
        --bfd-session-initialization-mode ACTIVE
        --bfd-min-receive-interval 400
        --bfd-min-transmit-interval 500
        --bfd-multiplier 5
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Creating peer [my-peer] in router [my-router]')

  def _GetRouterBgpPeerBfdMessage(self):
    return self.messages.RouterBgpPeerBfd(
        sessionInitializationMode=self.messages.RouterBgpPeerBfd
        .SessionInitializationModeValueValuesEnum.ACTIVE,
        minReceiveInterval=400,
        minTransmitInterval=500,
        multiplier=5)


class AddBgpPeerTestAlpha(AddBgpPeerTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def _GetRouterBgpPeerBfdMessage(self):
    return self.messages.RouterBgpPeerBfd(
        mode=self.messages.RouterBgpPeerBfd.ModeValueValuesEnum.ACTIVE,
        sessionInitializationMode=self.messages.RouterBgpPeerBfd
        .SessionInitializationModeValueValuesEnum.ACTIVE,
        minReceiveInterval=400,
        minTransmitInterval=500,
        multiplier=5)


if __name__ == '__main__':
  test_case.main()
