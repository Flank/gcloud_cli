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
"""Tests for the delegated sub prefixes create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.compute.public_delegated_prefixes import PublicDelegatedPrefixPatchError
from tests.lib import test_case
from tests.lib.surface.compute import public_delegated_prefixes_test_utils
from tests.lib.surface.compute.public_prefixes import test_resources


class DelegateSubPrefixesCreateTest(
    public_delegated_prefixes_test_utils.PublicDelegatedPrefixPatchTestBase):

  def testCreate_global(self):
    self.make_requests.side_effect = iter(
        [[copy.deepcopy(test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[0])]])

    resource = copy.deepcopy(test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[0])
    resource.publicDelegatedSubPrefixs.append(
        self.messages.PublicDelegatedPrefixPublicDelegatedSubPrefix(
            name='my-sub-prefix', isAddress=False))

    self._ExpectPatch(
        self.messages.PublicDelegatedPrefix(
            fingerprint=resource.fingerprint,
            publicDelegatedSubPrefixs=resource.publicDelegatedSubPrefixs))
    self._ExpectPollAndGet(resource)

    result = self.Run(
        'compute public-delegated-prefixes delegated-sub-prefixes '
        'create my-sub-prefix --public-delegated-prefix {} '
        '--global-public-delegated-prefix'.format(self.pdp_name))

    self.assertEqual(resource, result)
    self.AssertErrContains('Updating public delegated prefix [{}].'.format(
        self.pdp_name))

  def testCreate_regional(self):
    self.make_requests.side_effect = iter(
        [[copy.deepcopy(test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[1])]])

    resource = copy.deepcopy(test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[1])
    resource.publicDelegatedSubPrefixs.append(
        self.messages.PublicDelegatedPrefixPublicDelegatedSubPrefix(
            name='my-sub-prefix', isAddress=False))

    self._ExpectPatch(
        self.messages.PublicDelegatedPrefix(
            fingerprint=resource.fingerprint,
            publicDelegatedSubPrefixs=resource.publicDelegatedSubPrefixs),
        region='us-east1')
    self._ExpectPollAndGet(resource, region='us-east1')

    result = self.Run(
        'compute public-delegated-prefixes delegated-sub-prefixes '
        'create my-sub-prefix --public-delegated-prefix {} '
        '--public-delegated-prefix-region us-east1'.format(self.pdp_name))

    self.assertEqual(resource, result)
    self.AssertErrContains('Updating public delegated prefix [{}].'.format(
        self.pdp_name))

  def testCreate_allOptions(self):
    self.make_requests.side_effect = iter(
        [[copy.deepcopy(test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[1])]])

    resource = copy.deepcopy(test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[1])
    resource.publicDelegatedSubPrefixs.append(
        self.messages.PublicDelegatedPrefixPublicDelegatedSubPrefix(
            name='my-sub-prefix',
            description='best prefix',
            ipCidrRange='1.2.3.4/31',
            delegateeProject='my-other-project',
            isAddress=True))

    self._ExpectPatch(
        self.messages.PublicDelegatedPrefix(
            fingerprint=resource.fingerprint,
            publicDelegatedSubPrefixs=resource.publicDelegatedSubPrefixs),
        region='us-east1')
    self._ExpectPollAndGet(resource, region='us-east1')

    result = self.Run(
        'compute public-delegated-prefixes delegated-sub-prefixes '
        'create my-sub-prefix --public-delegated-prefix {} '
        '--public-delegated-prefix-region us-east1 '
        '--description "best prefix" --range "1.2.3.4/31" '
        '--delegatee-project my-other-project --create-addresses'.format(
            self.pdp_name))

    self.assertEqual(resource, result)
    self.AssertErrContains('Updating public delegated prefix [{}].'.format(
        self.pdp_name))

  def testCreate_invalidName(self):
    resource = copy.deepcopy(test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[1])
    resource.publicDelegatedSubPrefixs.append(
        self.messages.PublicDelegatedPrefixPublicDelegatedSubPrefix(
            name='my-sub-prefix', isAddress=False))
    self.make_requests.side_effect = iter([[resource]])

    with self.AssertRaisesExceptionRegexp(
        PublicDelegatedPrefixPatchError,
        r'Delegated sub prefix \[my-sub-prefix\] already exists in public '
        r'delegated prefix \[{}\]'.format(self.pdp_name)):
      self.Run('compute public-delegated-prefixes delegated-sub-prefixes '
               'create my-sub-prefix --public-delegated-prefix {} '
               '--public-delegated-prefix-region us-east1'.format(
                   self.pdp_name))


if __name__ == '__main__':
  test_case.main()
