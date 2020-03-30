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
"""Tests for the update command with remove advertisements flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.routers import router_utils
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base
from tests.lib.surface.compute import router_test_utils


class RemoveAdvertisementTestGA(router_test_base.RouterTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.messages = getattr(self, self.api_version + '_messages')
    self.mock_client = getattr(self, 'compute_' + self.api_version)
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testRemoveAdvertisementGroups_success(self):

    # Start with a router in custom mode.
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    updated.bgp.advertisedGroups = []

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsPolling()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update my-router --region us-central1
        --remove-advertisement-groups=ALL_SUBNETS
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating router [my-router]')

  def testRemoveAdvertisementGroups_groupNotFoundError(self):

    # Start with a router in custom mode.
    orig = router_test_utils.CreateEmptyCustomRouterMessage(self.messages)

    self.ExpectGet(orig)

    error_msg = 'Advertised group ALL_SUBNETS not found on this router.'
    with self.AssertRaisesExceptionMatches(router_utils.GroupNotFoundError,
                                           error_msg):
      self.Run("""
          compute routers update my-router --region us-central1
          --remove-advertisement-groups=ALL_SUBNETS
          """)

  def testRemoveAdvertisementRanges_success(self):

    # Start with a router in custom mode.
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.20/30', description='my-desc'),
    ]
    updated.bgp.advertisedIpRanges = ranges

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsPolling()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update my-router --region us-central1
        --remove-advertisement-ranges=10.10.10.10/30
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating router [my-router]')

  def testRemoveAdvertisementRanges_multiSuccess(self):

    # Start with a router in custom mode.
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    ranges = []
    updated.bgp.advertisedIpRanges = ranges

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsPolling()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update my-router --region us-central1
        --remove-advertisement-ranges=10.10.10.10/30,10.10.10.20/30
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating router [my-router]')

  def testRemoveAdvertisementRanges_ipRangeNotFoundError(self):

    # Start with a router in custom mode.
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)

    self.ExpectGet(orig)

    error_msg = 'Advertised IP range 192.168.0.0/30 not found on this router.'
    with self.AssertRaisesExceptionMatches(router_utils.IpRangeNotFoundError,
                                           error_msg):
      self.Run("""
          compute routers update my-router --region us-central1
          --remove-advertisement-ranges=192.168.0.0/30
          """)

  def testRemoveAdvertisement_mutallyExclusiveError(self):

    error_msg = ('argument --remove-advertisement-groups: At most one of '
                 '--add-advertisement-groups | --add-advertisement-ranges | '
                 '--remove-advertisement-groups | '
                 '--remove-advertisement-ranges may be specified.')
    with self.AssertRaisesArgumentErrorMatches(error_msg):
      self.Run("""
          compute routers update my-router --region us-central1
          --remove-advertisement-groups=ALL_SUBNETS
          --remove-advertisement-ranges=10.10.10.10/30
          """)

  def testRemoveAdvertisement_defaultModeError(self):

    # Start with a router in default mode.
    orig = router_test_utils.CreateDefaultRouterMessage(self.messages)

    self.ExpectGet(orig)

    error_msg = ('Cannot specify custom advertisements for a router with '
                 'default mode.')
    with self.AssertRaisesExceptionMatches(router_utils.CustomWithDefaultError,
                                           error_msg):
      self.Run("""
          compute routers update my-router --region us-central1
          --remove-advertisement-groups=ALL_SUBNETS
          """)


class RemoveAdvertisementTestBeta(RemoveAdvertisementTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class RemoveAdvertisementTestAlpha(RemoveAdvertisementTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
