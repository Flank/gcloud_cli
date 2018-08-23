# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for the networks list-ip-owners subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock


class NetworksListIpAddressesTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = base.ReleaseTrack.ALPHA
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', 'alpha'),
        real_client=core_apis.GetClientInstance(
            'compute', 'alpha', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def _GetInternalIpRangesForTest(self):
    return [
        self.messages.InternalIpAddress(
            cidr='10.128.0.0/20',
            type=self.messages.InternalIpAddressType.SUBNETWORK,
            region='region-1',
            owner='subnet-1',
        ),
        self.messages.InternalIpAddress(
            cidr='10.130.0.0/20',
            type=self.messages.InternalIpAddressType.SUBNETWORK,
            region='region-2',
            owner='subnet-2',
        ),
        self.messages.InternalIpAddress(
            cidr='10.240.0.0/16',
            type=self.messages.InternalIpAddressType.RESERVED,
            owner='range-1',
            purpose='VPC_PEERING',
        ),
    ]

  def NetworksListIpAddressesTest(self):
    self.mock_client.networks.ListIpAddresses.Expect(
        self.messages.ComputeNetworksListIpAddressesRequest(
            network='network-1',
            networksListIpAddressesRequest=self.messages.
            NetworksListIpAddressesRequest(),
            project='fake-project'),
        response=self.messages.IpAddressesList(
            items=self._GetInternalIpRangesForTest()))

    self.Run('compute networks list-ip-addresses network-1')
    self.AssertOutputEquals("""\
        TYPE       IP_RANGE       REGION   OWNER    PURPOSE
        SUBNETWORK 10.128.0.0/20  region-1 subnet-1
        SUBNETWORK 10.130.0.0/20  region-2 subnet-2
        RESERVED   10.240.0.0/16           range-1  VPC_PEERNIG
        """)


if __name__ == '__main__':
  test_case.main()
