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
"""Tests for the router utils library."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.compute.routers import router_utils
from tests.lib import cli_test_base
from tests.lib import test_case

import mock


class ParseAdvertisementsAlphaTest(test_case.Base):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.resource_classes = [
        self.messages.RouterBgp, self.messages.RouterBgpPeer
    ]

  def testParseDefaultAdvertisements(self):
    for resource_class in self.resource_classes:
      args = mock.Mock()
      args.advertisement_mode = 'DEFAULT'
      args.set_advertisement_groups = None
      args.set_advertisement_ranges = None

      expected_mode = resource_class.AdvertiseModeValueValuesEnum.DEFAULT
      expected_groups = []
      expected_ranges = []

      (mode, groups, ranges) = router_utils.ParseAdvertisements(
          self.messages, resource_class, args)
      self.assertEqual(expected_mode, mode)
      self.assertEqual(expected_groups, groups)
      self.assertEqual(expected_ranges, ranges)

  def testParseCustomAdvertisements(self):
    for resource_class in self.resource_classes:
      args = mock.Mock()
      args.advertisement_mode = 'CUSTOM'
      args.set_advertisement_groups = ['ALL_SUBNETS']
      args.set_advertisement_ranges = {
          '10.10.10.10/30': 'custom-range',
          '10.10.10.20/30': ''
      }

      expected_mode = resource_class.AdvertiseModeValueValuesEnum.CUSTOM
      expected_groups = [
          resource_class.AdvertisedGroupsValueListEntryValuesEnum.ALL_SUBNETS
      ]
      expected_ranges = [
          self.messages.RouterAdvertisedIpRange(
              range='10.10.10.10/30', description='custom-range'),
          self.messages.RouterAdvertisedIpRange(
              range='10.10.10.20/30', description=''),
      ]

      (mode, groups, ranges) = router_utils.ParseAdvertisements(
          self.messages, resource_class, args)
      self.assertEqual(expected_mode, mode)
      self.assertEqual(expected_groups, groups)
      self.assertEqual(expected_ranges, ranges)


class ValidateCustomModeAlphaTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')

  def testValidateCustomModeForRouter(self):
    resource_class = self.messages.RouterBgp
    router_bgp = self.messages.RouterBgp()

    router_bgp.advertiseMode = (
        self.messages.RouterBgp.AdvertiseModeValueValuesEnum.CUSTOM)
    router_utils.ValidateCustomMode(
        messages=self.messages,
        resource_class=resource_class,
        resource=router_bgp)

    router_bgp.advertiseMode = (
        self.messages.RouterBgp.AdvertiseModeValueValuesEnum.DEFAULT)
    error_msg = ('Cannot specify custom advertisements for a router with '
                 'default mode.')
    with self.AssertRaisesExceptionMatches(router_utils.CustomWithDefaultError,
                                           error_msg):
      router_utils.ValidateCustomMode(
          messages=self.messages,
          resource_class=resource_class,
          resource=router_bgp)

  def testValidateCustomModeForPeer(self):
    resource_class = self.messages.RouterBgpPeer
    router_bgp_peer = self.messages.RouterBgpPeer()

    router_bgp_peer.advertiseMode = (
        self.messages.RouterBgpPeer.AdvertiseModeValueValuesEnum.CUSTOM)
    router_utils.ValidateCustomMode(
        messages=self.messages,
        resource_class=resource_class,
        resource=router_bgp_peer)

    router_bgp_peer.advertiseMode = (
        self.messages.RouterBgpPeer.AdvertiseModeValueValuesEnum.DEFAULT)
    error_msg = ('Cannot specify custom advertisements for a peer with '
                 'default mode.')
    with self.AssertRaisesExceptionMatches(router_utils.CustomWithDefaultError,
                                           error_msg):
      router_utils.ValidateCustomMode(
          messages=self.messages,
          resource_class=resource_class,
          resource=router_bgp_peer)


class PromptIfSwitchToDefaultModeAlphaTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.prompt_msg = ('WARNING: switching from custom advertisement mode to '
                       'default will clear out any existing advertised '
                       'groups/ranges from this {resource}.')

  def testPromptForRouter(self):
    resource_class = self.messages.RouterBgp
    resource_enum = resource_class.AdvertiseModeValueValuesEnum
    prompt_msg = self.prompt_msg.format(resource='router')

    router_utils.PromptIfSwitchToDefaultMode(
        messages=self.messages,
        resource_class=resource_class,
        existing_mode=resource_enum.DEFAULT,
        new_mode=resource_enum.CUSTOM)
    self.AssertErrNotContains(expected=prompt_msg, normalize_space=True)

    router_utils.PromptIfSwitchToDefaultMode(
        messages=self.messages,
        resource_class=resource_class,
        existing_mode=resource_enum.CUSTOM,
        new_mode=resource_enum.DEFAULT)
    self.AssertErrContains(expected=prompt_msg, normalize_space=True)

  def testPromptForPeer(self):
    resource_class = self.messages.RouterBgpPeer
    resource_enum = resource_class.AdvertiseModeValueValuesEnum
    prompt_msg = self.prompt_msg.format(resource='peer')

    router_utils.PromptIfSwitchToDefaultMode(
        messages=self.messages,
        resource_class=resource_class,
        existing_mode=resource_enum.DEFAULT,
        new_mode=resource_enum.CUSTOM)
    self.AssertErrNotContains(expected=prompt_msg, normalize_space=True)

    router_utils.PromptIfSwitchToDefaultMode(
        messages=self.messages,
        resource_class=resource_class,
        existing_mode=resource_enum.CUSTOM,
        new_mode=resource_enum.DEFAULT)
    self.AssertErrContains(expected=prompt_msg, normalize_space=True)


class FindBgpPeerOrRaiseAlphaTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')

  def testFindBgpPeerOrRaise(self):
    router = self.messages.Router()
    router.bgpPeers.append(
        self.messages.RouterBgpPeer(
            name='my-peer',
            interfaceName='a',
            peerAsn=65002,
            ipAddress='1.1.1.1',
            peerIpAddress='1.1.1.2',
            advertisedRoutePriority=1))

    peer = router_utils.FindBgpPeerOrRaise(router, 'my-peer')
    self.assertEqual(peer, router.bgpPeers[0])

    error_msg = 'peer `nonexistent-peer` not found'
    with self.AssertRaisesExceptionMatches(router_utils.PeerNotFoundError,
                                           error_msg):
      router_utils.FindBgpPeerOrRaise(router, 'nonexistent-peer')


class RemoveGroupsFromAdvertisementsAlphaTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')

  def testRemoveGroupsFromAdvertisementsBgp_success(self):
    router_bgp = self.messages.RouterBgp()
    groups = [(self.messages.RouterBgp.AdvertisedGroupsValueListEntryValuesEnum.
               ALL_SUBNETS)]
    router_bgp.advertisedGroups = groups

    groups_to_remove = [(self.messages.RouterBgp.
                         AdvertisedGroupsValueListEntryValuesEnum.ALL_SUBNETS)]
    router_utils.RemoveGroupsFromAdvertisements(
        messages=self.messages,
        resource_class=self.messages.RouterBgp,
        resource=router_bgp,
        groups=groups_to_remove)

    expected_groups = []
    self.assertEqual(router_bgp.advertisedGroups, expected_groups)

  def testRemoveGroupsFromAdvertisements_groupNotFoundError(self):
    router_bgp = self.messages.RouterBgp()
    router_bgp.advertisedGroups = []

    groups_to_remove = [(self.messages.RouterBgp.
                         AdvertisedGroupsValueListEntryValuesEnum.ALL_SUBNETS)]
    error_msg = 'Advertised group ALL_SUBNETS not found on this router.'
    with self.AssertRaisesExceptionMatches(router_utils.GroupNotFoundError,
                                           error_msg):
      router_utils.RemoveGroupsFromAdvertisements(
          messages=self.messages,
          resource_class=self.messages.RouterBgp,
          resource=router_bgp,
          groups=groups_to_remove)


class RemoveIpRangesFromAdvertisementsAlphaTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')

  def testRemoveIpRangesFromAdvertisementsBgp_success(self):
    router_bgp = self.messages.RouterBgp()
    ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.10/30', description='custom-range'),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.20/30', description=''),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.30/30', description=''),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.40/30', description=''),
    ]
    router_bgp.advertisedIpRanges = ranges

    ip_ranges_to_remove = ['10.10.10.20/30', '10.10.10.30/30']
    router_utils.RemoveIpRangesFromAdvertisements(
        messages=self.messages,
        resource_class=self.messages.RouterBgp,
        resource=router_bgp,
        ip_ranges=ip_ranges_to_remove)

    expected_ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.10/30', description='custom-range'),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.40/30', description=''),
    ]
    self.assertEqual(router_bgp.advertisedIpRanges, expected_ranges)

  def testRemoveIpRangesFromAdvertisementsBgp_ipRangeNotFoundError(self):
    router_bgp = self.messages.RouterBgp()
    ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.10/30', description='custom-range'),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.20/30', description=''),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.30/30', description=''),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.40/30', description=''),
    ]
    router_bgp.advertisedIpRanges = ranges

    ip_ranges_to_remove = ['192.168.0.0/30']
    error_msg = 'Advertised IP range 192.168.0.0/30 not found on this router.'
    with self.AssertRaisesExceptionMatches(router_utils.IpRangeNotFoundError,
                                           error_msg):
      router_utils.RemoveIpRangesFromAdvertisements(
          messages=self.messages,
          resource_class=self.messages.RouterBgp,
          resource=router_bgp,
          ip_ranges=ip_ranges_to_remove)


if __name__ == '__main__':
  test_case.main()
