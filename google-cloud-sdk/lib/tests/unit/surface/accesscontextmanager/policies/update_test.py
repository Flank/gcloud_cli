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
"""Tests for `gcloud access-context-manager policies update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class PoliciesUpdateTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectPatch(self, policy_id, policy, update_mask):
    policy_name = 'accessPolicies/{}'.format(policy_id)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesPatchRequest
    self.client.accessPolicies.Patch.Expect(
        request_type(
            name=policy_name,
            accessPolicy=policy,
            updateMask=update_mask
        ),
        self.messages.Operation(done=False, name='operations/my-op'))
    self._ExpectGetOperation('operations/my-op')
    get_req_type = m.AccesscontextmanagerAccessPoliciesGetRequest
    self.client.accessPolicies.Get.Expect(get_req_type(name=policy_name),
                                          policy)

  def testUpdate_MissingRequired(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(handlers.ParseError,
                                           'Error parsing [policy]'):
      self.Run(
          'access-context-manager policies update')

  def testUpdate(self):
    self.SetUpForAPI(self.api_version)
    policy = self.messages.AccessPolicy(title='My Policy #2')
    self._ExpectPatch('MY_POLICY', policy, 'title')

    results = self.Run(
        'access-context-manager policies update MY_POLICY '
        '     --title "My Policy #2"')

    self.assertEqual(results, policy)


class PoliciesUpdateTestBeta(PoliciesUpdateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA


class PoliciesUpdateTestAlpha(PoliciesUpdateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
