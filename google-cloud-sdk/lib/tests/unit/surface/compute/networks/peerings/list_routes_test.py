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
"""Tests for the networks peerings list-routes subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


# This test can be deleted once list_test.scenario.yaml covers all cases.
class ListRoutesBetaTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

  def testTableOutput(self):
    return_value = [
        self.messages.ExchangedPeeringRoute(
            destRange='10.2.10.0/24',
            type=self.messages.ExchangedPeeringRoute.TypeValueValuesEnum
            .SUBNET_PEERING_ROUTE,
            nextHopRegion='dev-central2',
            priority=900,
            imported=True),
        self.messages.ExchangedPeeringRoute(
            destRange='10.2.30.0/24',
            type=self.messages.ExchangedPeeringRoute.TypeValueValuesEnum
            .STATIC_PEERING_ROUTE,
            nextHopRegion='dev-central1',
            priority=800,
            imported=False),
        self.messages.ExchangedPeeringRoute(
            destRange='10.2.40.0/24',
            type=self.messages.ExchangedPeeringRoute.TypeValueValuesEnum
            .DYNAMIC_PEERING_ROUTE,
            nextHopRegion='dev-central2',
            priority=700,
            imported=True)
    ]
    self.client.networks.ListPeeringRoutes.Expect(
        request=self.messages.ComputeNetworksListPeeringRoutesRequest(
            project=self.Project(),
            network='test-network',
            peeringName='peering1',
            region='dev-central1',
            direction=self.messages.ComputeNetworksListPeeringRoutesRequest
            .DirectionValueValuesEnum.INCOMING),
        response=self.messages.ExchangedPeeringRoutesList(items=return_value))

    command = ('compute networks peerings list-routes peering1 --network '
               'test-network --region dev-central1 --direction INCOMING')
    self.Run(command)
    output = ("""\
        DEST_RANGE    TYPE                  NEXT_HOP_REGION  PRIORITY  STATUS
        10.2.10.0/24  SUBNET_PEERING_ROUTE  dev-central2     900       accepted
        10.2.30.0/24  STATIC_PEERING_ROUTE  dev-central1     800       rejected by config
        10.2.40.0/24  DYNAMIC_PEERING_ROUTE dev-central2     700       accepted
        """)
    self.AssertOutputEquals(output, normalize_space=True)

  def testWithoutNetwork(self):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                r'argument --network: Must be specified.'):
      self.Run("""\
          compute networks peerings list-routes peering1
          --region dev-central1 --direction INCOMING
          """)

  def testWithoutRegion(self):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                r'argument --region: Must be specified.'):
      self.Run("""\
          compute networks peerings list-routes peering1
          --network test-network --direction INCOMING
          """)

  def testWithoutDirection(self):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                r'argument --direction: Must be specified.'):
      self.Run("""\
          compute networks peerings list-routes peering1
          --network test-network --region dev-central1
          """)

  def testInvalidDirection(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'argument --direction: Invalid choice: \'NORTH\'.'):
      self.Run("""\
          compute networks peerings list-routes peering1
          --network test-network --region dev-central1 --direction NORTH
          """)


class ListRoutesAlphaTest(ListRoutesBetaTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
