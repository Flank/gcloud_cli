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
"""Tests for the update subcommand. Does not include incremental flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.compute.routers import router_utils
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base
from tests.lib.surface.compute import router_test_utils


class UpdateTestGA(router_test_base.RouterTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testUpdate_noop(self):
    """Sanity test to verify no changes when no flags are specified."""

    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsGet()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update my-router --region us-central1
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating router [my-router]')

  def testUpdate_async(self):
    """Test command with --async flag."""

    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    self.ExpectGet(orig)
    self.ExpectPatch(updated)

    result = self.Run("""
        compute routers update my-router --region us-central1 --async
        """)
    self.assertEqual('operation-X', result.name)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Update in progress for router [my-router] '
        '[https://compute.googleapis.com/compute/v1/'
        'projects/fake-project/regions/us-central1/operations/operation-X] '
        'Run the [gcloud compute operations describe] command to check the '
        'status of this operation.\n')

  def testUpdateAdvertisements_default(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateBaseRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    mode = self.messages.RouterBgp.AdvertiseModeValueValuesEnum.DEFAULT
    updated.bgp.advertiseMode = mode

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsGet()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update my-router --region us-central1
        --advertisement-mode=DEFAULT
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating router [my-router]')

  def testUpdateAdvertisements_custom(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateDefaultRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    mode = self.messages.RouterBgp.AdvertiseModeValueValuesEnum.CUSTOM
    groups = [(self.messages.RouterBgp.AdvertisedGroupsValueListEntryValuesEnum.
               ALL_SUBNETS)]
    ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.10/30', description='custom-range'),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.20/30', description=''),
    ]
    updated.bgp.advertiseMode = mode
    updated.bgp.advertisedGroups = groups
    updated.bgp.advertisedIpRanges = ranges

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsGet()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update my-router --region us-central1
        --advertisement-mode=CUSTOM
        --set-advertisement-groups=ALL_SUBNETS
        --set-advertisement-ranges=10.10.10.10/30=custom-range,10.10.10.20/30
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating router [my-router]')

  def testUpdateAdvertisements_incompatibleIncrementalFlagsError(self):
    self.SelectApi(self.track, self.api_version)

    error_msg = ('--add/remove-advertisement flags are not compatible with '
                 '--set-advertisement flags.')
    with self.assertRaisesRegex(parser_errors.ArgumentError, error_msg):
      self.Run("""
          compute routers update my-router --region us-central1
          --set-advertisement-groups=ALL_SUBNETS
          --add-advertisement-groups=ALL_SUBNETS
          """)
    with self.assertRaisesRegex(parser_errors.ArgumentError, error_msg):
      self.Run("""
          compute routers update my-router --region us-central1
          --set-advertisement-ranges=10.10.10.10/30
          --add-advertisement-ranges=10.10.10.10/30
          """)

  def testUpdateAdvertisements_customWithDefaultError(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateEmptyCustomRouterMessage(self.messages)
    self.ExpectGet(orig)

    error_msg = ('Cannot specify custom advertisements for a router with '
                 'default mode.')
    with self.AssertRaisesExceptionMatches(router_utils.CustomWithDefaultError,
                                           error_msg):
      self.Run("""
          compute routers update my-router --region us-central1
          --advertisement-mode=DEFAULT
          --set-advertisement-groups=ALL_SUBNETS
          --set-advertisement-ranges=10.10.10.10/30=custom-range,10.10.10.20/30
          """)

  def testSwitchAdvertiseMode_yes(self):
    self.SelectApi(self.track, self.api_version)

    self.WriteInput('y\n')
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)
    updated = copy.deepcopy(orig)

    mode = self.messages.RouterBgp.AdvertiseModeValueValuesEnum.DEFAULT
    updated.bgp.advertiseMode = mode
    updated.bgp.advertisedGroups = []
    updated.bgp.advertisedIpRanges = []

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsGet()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update my-router --region us-central1
        --advertisement-mode=DEFAULT
        """)
    self.AssertOutputEquals('')
    prompt_msg = ('WARNING: switching from custom advertisement mode to '
                  'default will clear out any existing advertised '
                  'groups/ranges from this router.')
    self.AssertErrContains(prompt_msg)
    self.AssertErrContains('Updating router [my-router]')

  def testSwitchAdvertiseMode_no(self):
    self.SelectApi(self.track, self.api_version)

    self.WriteInput('n\n')
    orig = router_test_utils.CreateFullCustomRouterMessage(self.messages)
    self.ExpectGet(orig)

    cancel_msg = 'Aborted by user.'
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           cancel_msg):
      self.Run("""
          compute routers update my-router --region us-central1
          --advertisement-mode=DEFAULT
          """)


class UpdateTestBeta(UpdateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testUpdateKeepaliveInterval(self):
    self.SelectApi(self.track, self.api_version)

    orig = router_test_utils.CreateMinimalRouterMessage(self.messages,
                                                        self.api_version)
    orig.bgp.keepaliveInterval = 40
    updated = copy.deepcopy(orig)
    updated.bgp.keepaliveInterval = 50

    self.ExpectGet(orig)
    self.ExpectPatch(updated)
    self.ExpectOperationsGet()
    self.ExpectGet(updated)

    self.Run("""
        compute routers update my-router --region us-central1
        --keepalive-interval=50
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating router [my-router]')


class UpdateTestAlpha(UpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
