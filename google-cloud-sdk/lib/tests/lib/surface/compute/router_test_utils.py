# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Test utils for compute routers unit tests."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def CreateMinimalBgpPeerMessage(messages):
  """Create a BGP peer with only required fields.

  Args:
    messages: A compute API messages client.

  Returns:
    A RouterBgpPeer message with only required fields.
  """
  return messages.RouterBgpPeer(
      name='my-peer', interfaceName='my-if', peerAsn=66000)


def CreateBaseBgpPeerMessage(messages):
  """Create a BGP peer with basic fields.

  Args:
    messages: A compute API messages client.

  Returns:
    A RouterBgpPeer message with required fields, IP addresses, and priority.
  """
  peer = CreateMinimalBgpPeerMessage(messages)
  peer.ipAddress = '10.0.0.1'
  peer.peerIpAddress = '10.0.0.2'
  peer.advertisedRoutePriority = 1
  return peer


def CreateMinimalRouterMessage(messages, api_version='v1'):
  """Create a minimal router with only required fields.

  Args:
    messages: A compute API messages client.
    api_version: The api version track, for generating the network ref.

  Returns:
    A Router message with only required fields.
  """
  return messages.Router(
      name='my-router',
      bgp=messages.RouterBgp(asn=65000),
      network=('https://compute.googleapis.com/compute/{0}/projects/fake-project/'
               'global/networks/default').format(api_version))


def CreateEmptyRouterMessage(messages, track='v1'):
  """Create a empty router with only metadata fields.

  Args:
    messages: A compute API messages client.
    track: The version track, for generating the network ref.

  Returns:
    A Router message with only required metadata fields.
  """
  return messages.Router(
      name='my-router',
      network=('https://compute.googleapis.com/compute/{0}/projects/fake-project/'
               'global/networks/default').format(track))


def CreateBaseRouterMessage(messages):
  """Create a router with basic fields and one BGP peer.

  Args:
    messages: A compute API messages client.

  Returns:
    A Router message with one BGP peer and no custom advertisements.
  """
  return messages.Router(
      name='my-router',
      bgp=messages.RouterBgp(asn=65000),
      bgpPeers=[CreateBaseBgpPeerMessage(messages)],
      interfaces=[
          messages.RouterInterface(
              name='my-if', linkedVpnTunnel='', ipRange='10.0.0.1/24')
      ],
      network=('https://compute.googleapis.com/compute/v1/projects/fake-project/'
               'global/networks/default'))


def CreateDefaultRouterMessage(messages):
  """Create a router with default advertisements.

  Args:
    messages: A compute API messages client.

  Returns:
    A Router message with default advertisements.
  """
  router = CreateBaseRouterMessage(messages)
  router.bgp.advertiseMode = (
      messages.RouterBgp.AdvertiseModeValueValuesEnum.DEFAULT)
  router.bgpPeers[0].advertiseMode = (
      messages.RouterBgpPeer.AdvertiseModeValueValuesEnum.DEFAULT)
  return router


def CreateEmptyCustomRouterMessage(messages):
  """Create a router with custom (but empty) advertisements.

  Args:
    messages: A compute API messages client.

  Returns:
    A Router message with custom (but empty) advertisements.
  """
  router = CreateBaseRouterMessage(messages)
  router.bgp.advertiseMode = (
      messages.RouterBgp.AdvertiseModeValueValuesEnum.CUSTOM)
  router.bgpPeers[0].advertiseMode = (
      messages.RouterBgpPeer.AdvertiseModeValueValuesEnum.CUSTOM)
  return router


def CreateFullCustomRouterMessage(messages):
  """Create a router with group and IP range custom advertisements.

  Args:
    messages: A compute API messages client.

  Returns:
    A Router message with group and IP range custom advertisements.
  """
  router = CreateBaseRouterMessage(messages)

  router.bgp.advertiseMode = (
      messages.RouterBgp.AdvertiseModeValueValuesEnum.CUSTOM)
  router.bgp.advertisedGroups = [
      messages.RouterBgp.AdvertisedGroupsValueListEntryValuesEnum.ALL_SUBNETS
  ]
  router.bgp.advertisedIpRanges = [
      messages.RouterAdvertisedIpRange(range='10.10.10.10/30'),
      messages.RouterAdvertisedIpRange(
          range='10.10.10.20/30', description='my-desc')
  ]

  router.bgpPeers[0].advertiseMode = (
      messages.RouterBgpPeer.AdvertiseModeValueValuesEnum.CUSTOM)
  router.bgpPeers[0].advertisedGroups = [
      messages.RouterBgpPeer.AdvertisedGroupsValueListEntryValuesEnum.
      ALL_SUBNETS
  ]
  router.bgpPeers[0].advertisedIpRanges = [
      messages.RouterAdvertisedIpRange(range='10.10.10.10/30'),
      messages.RouterAdvertisedIpRange(
          range='10.10.10.20/30', description='my-desc')
  ]
  return router
