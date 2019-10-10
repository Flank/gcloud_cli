# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class NetworksListIpAddressesTest(sdk_test_base.WithFakeAuth,
                                  cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', 'alpha'),
        real_client=core_apis.GetClientInstance(
            'compute', 'alpha', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = self.mock_client.MESSAGES_MODULE

  def _GetInternalIpRangesForTest(self):
    return [
        self.messages.InternalIpAddress(
            cidr='10.128.0.0/20',
            type=self.messages.InternalIpAddress.TypeValueValuesEnum.SUBNETWORK,
            region='region-1',
            owner='subnet-1',
        ),
        self.messages.InternalIpAddress(
            cidr='10.130.0.0/20',
            type=self.messages.InternalIpAddress.TypeValueValuesEnum.SUBNETWORK,
            region='region-2',
            owner='subnet-2',
        ),
        self.messages.InternalIpAddress(
            cidr='10.240.0.0/16',
            type=self.messages.InternalIpAddress.TypeValueValuesEnum.RESERVED,
            owner='range-1',
            purpose='VPC_PEERING',
        ),
    ]

  def testNetworksListIpAddresses(self):
    self.mock_client.networks.ListIpAddresses.Expect(
        self.messages.ComputeNetworksListIpAddressesRequest(
            network='network-1',
            project='fake-project'),
        response=self.messages.IpAddressesList(
            items=self._GetInternalIpRangesForTest()))

    self.Run('compute networks list-ip-addresses network-1')
    self.AssertOutputEquals(
        """\
        TYPE       IP_RANGE       REGION   OWNER    PURPOSE
        SUBNETWORK 10.128.0.0/20  region-1 subnet-1
        SUBNETWORK 10.130.0.0/20  region-2 subnet-2
        RESERVED   10.240.0.0/16           range-1  VPC_PEERING
        """,
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
