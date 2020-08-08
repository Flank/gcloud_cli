# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Integration tests for public delegated prefixes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import logging

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class PublicDelegatedPrefixesTest(e2e_test_base.BaseTest):
  """Public Delegated Prefixes tests."""

  # Special values that are treated as test by Arcus so it skips RPC steps.
  TEST_RANGE = '127.127.0.0/20'
  TEST_PDP_RANGE = '127.127.0.0/22'
  TEST_SUB_RANGE = '127.127.1.0/24'
  TEST_VERIFICATION_IP = '127.127.1.1'
  TEST_DESCRIPTION = 'GOOGLE_INTERNAL_TEST_PREFIX'

  @staticmethod
  def _GetResourceName():
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-byoip-test'))

  def SetupCommon(self):
    self.pap_name = self._GetResourceName()

    self.Run('compute public-advertised-prefixes create {0} '
             '--range={1} --dns-verification-ip={2} --description={3}'
             .format(self.pap_name, self.TEST_RANGE, self.TEST_VERIFICATION_IP,
                     self.TEST_DESCRIPTION))

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.registry = resources.REGISTRY.Clone()
    self.registry.RegisterApiByName('compute', 'alpha')
    self.SetupCommon()

  @contextlib.contextmanager
  def _CreatePublicDelegatedPrefix(self):
    pdp_name = self._GetResourceName()
    try:
      self.Run('compute public-delegated-prefixes create {0} '
               '--global --range={1} --public-advertised-prefix={2}'
               .format(pdp_name, self.TEST_PDP_RANGE, self.pap_name))
      self.AssertNewErrContains(pdp_name)
      yield pdp_name
    finally:
      self.Run('compute public-delegated-prefixes delete {0} --global '
               '--quiet'.format(pdp_name))

  def testPublicDelegatedPrefixes(self):
    # Set public advertised prefix status to PTR_CONFIGURED
    self.Run('compute public-advertised-prefixes update {0} '
             '--status=ptr-configured'.format(self.pap_name))
    self.Run('compute public-advertised-prefixes describe {0}'
             .format(self.pap_name))
    self.AssertNewOutputContains('PTR_CONFIGURED')

    with self._CreatePublicDelegatedPrefix() as pdp_name:
      # Create a sub-prefix
      sub_prefix_name = self._GetResourceName()
      self.Run('compute public-delegated-prefixes delegated-sub-prefixes '
               'create {0} --range={1} --public-delegated-prefix={2} '
               '--global-public-delegated-prefix'
               .format(sub_prefix_name, self.TEST_SUB_RANGE, pdp_name))
      self.Run('compute public-delegated-prefixes describe {0} --global'
               .format(pdp_name))
      self.AssertNewOutputContains(sub_prefix_name)
      self.Run('compute public-delegated-prefixes delegated-sub-prefixes '
               'delete {0} --public-delegated-prefix={1} '
               '--global-public-delegated-prefix'
               .format(sub_prefix_name, pdp_name))

  def TearDown(self):
    logging.info('Starting TearDown.')
    self.CleanUpResource(self.pap_name, 'public-advertised-prefixes',
                         scope=e2e_test_base.GLOBAL)
