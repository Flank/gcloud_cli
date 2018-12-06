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
"""Tests for the list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base
from tests.lib.surface.compute import router_test_utils


class ListTest(router_test_base.RouterTestBase):

  def SetUp(self):
    self.SelectApi(calliope_base.ReleaseTrack.GA, 'v1')
    self.router = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='v1')
    self.version = 'v1'

  def testList(self):
    self.router.nats = [
        self.messages.RouterNat(
            name='nat-1',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_PRIMARY_IP_RANGES),
        self.messages.RouterNat(
            name='nat-2',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.MANUAL_ONLY,
            natIps=[
                ('https://www.googleapis.com/compute/{0}/projects/'
                 'fake-project/regions/us-central1/addresses/address-1').format(
                     self.version),
                ('https://www.googleapis.com/compute/{0}/projects/'
                 'fake-project/regions/us-central1/addresses/address-2').format(
                     self.version),
                ('https://www.googleapis.com/compute/{0}/projects/'
                 'fake-project/regions/us-central1/addresses/address-3').format(
                     self.version),
            ],
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]

    self.ExpectGet(self.router)

    self.Run("""
        compute routers nats list --router my-router
        --region us-central1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME NAT_IP_ALLOCATE_OPTION SOURCE_SUBNETWORK_IP_RANGES_TO_NAT
            nat-1 AUTO_ONLY ALL_SUBNETWORKS_ALL_PRIMARY_IP_RANGES
            nat-2 MANUAL_ONLY ALL_SUBNETWORKS_ALL_IP_RANGES
            """),
        normalize_space=True)


class BetaListTest(ListTest):

  def SetUp(self):
    self.SelectApi(calliope_base.ReleaseTrack.BETA, 'beta')
    self.router = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='beta')
    self.version = 'beta'


class AlphaListTest(BetaListTest):

  def SetUp(self):
    self.SelectApi(calliope_base.ReleaseTrack.ALPHA, 'alpha')
    self.router = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='alpha')
    self.version = 'alpha'


if __name__ == '__main__':
  test_case.main()
