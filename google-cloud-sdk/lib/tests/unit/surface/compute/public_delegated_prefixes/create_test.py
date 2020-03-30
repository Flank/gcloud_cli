# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the public delegated prefix create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class PublicDelegatedPrefixesCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.region = 'us-central1'

  def _ExpectCreate(self, public_delegated_prefix, region=None):
    if region:
      request = self.messages.ComputePublicDelegatedPrefixesInsertRequest(
          project=self.Project(),
          region=region,
          publicDelegatedPrefix=public_delegated_prefix)
    else:
      request = self.messages.ComputeGlobalPublicDelegatedPrefixesInsertRequest(
          project=self.Project(),
          publicDelegatedPrefix=public_delegated_prefix)
    self.make_requests.side_effect = [[public_delegated_prefix]]
    return request

  def testCreate_global(self):
    public_delegated_prefix = self.messages.PublicDelegatedPrefix(
        name='my-pdp',
        ipCidrRange='1.2.3.8/30',
        parentPrefix=(
            self.compute_uri + '/projects/{project}/global/'
            'publicAdvertisedPrefixes/my-pap'
        ).format(project=self.Project()),
        description='test-pdp')
    request = self._ExpectCreate(public_delegated_prefix)

    result = self.Run('compute public-delegated-prefixes create my-pdp '
                      '--global '
                      '--public-advertised-prefix my-pap --range 1.2.3.8/30 '
                      '--description test-pdp')

    self.CheckRequests([(self.compute.globalPublicDelegatedPrefixes, 'Insert',
                         request)])
    self.assertEqual(result, public_delegated_prefix)
    self.AssertErrContains('Created public delegated prefix [my-pdp]')

  def testCreate_regional(self):
    public_delegated_prefix = self.messages.PublicDelegatedPrefix(
        name='my-pdp',
        ipCidrRange='1.2.3.0/25',
        parentPrefix=(
            self.compute_uri + '/projects/{project}/global/'
                               'publicAdvertisedPrefixes/my-pap'
        ).format(project=self.Project()),
        description='test-pdp')
    request = self._ExpectCreate(public_delegated_prefix, region=self.region)

    result = self.Run('compute public-delegated-prefixes create my-pdp '
                      '--region us-central1 '
                      '--public-advertised-prefix my-pap --range 1.2.3.0/25 '
                      '--description test-pdp')

    self.CheckRequests([(self.compute.publicDelegatedPrefixes, 'Insert',
                         request)])
    self.assertEqual(result, public_delegated_prefix)
    self.AssertErrContains('Created public delegated prefix [my-pdp]')


if __name__ == '__main__':
  test_case.main()
