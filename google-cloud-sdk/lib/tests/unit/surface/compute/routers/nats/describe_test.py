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
"""Tests for the update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils
from tests.lib import test_case
from tests.lib.surface.compute import router_test_utils
from tests.lib.surface.compute import test_base


class DescribeTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA
    self.router = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='v1')
    self.router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat.
            NatIpAllocateOptionValueValuesEnum.AUTO_ONLY)
    ]

    self.make_requests.side_effect = iter([[self.router]])

  def testSimple(self):
    self.Run("""
        compute routers nats describe my-nat --router my-router
        --region us-central1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            name: my-nat
            natIpAllocateOption: AUTO_ONLY
            """))

  def testNatNotFound(self):
    with self.AssertRaisesExceptionRegexp(nats_utils.NatNotFoundError,
                                          'NAT `invalid-nat` not found'):
      self.Run("""
          compute routers nats describe invalid-nat --router my-router
          --region us-central1
          """)


class BetaDescribeTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.router = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='beta')


class AlphaDescribeTest(BetaDescribeTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.router = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='alpha')


if __name__ == '__main__':
  test_case.main()
