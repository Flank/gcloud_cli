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
"""Tests for `gcloud access-context-manager policies list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class PoliciesListTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakePolicy(self, policy_id, parent=None):
    return self.messages.AccessPolicy(
        name='policies/{}'.format(policy_id),
        parent=parent,
        title='My Policy')

  def _ExpectList(self, policies, organization):
    organization_name = 'organizations/{}'.format(organization)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesListRequest
    self.client.accessPolicies.List.Expect(
        request_type(
            parent=organization_name,
        ),
        self.messages.ListAccessPoliciesResponse(accessPolicies=policies))

  def testList(self):
    self.SetUpForTrack(self.track)

    organization_id = '12345'
    policy = self._MakePolicy('MY_POLICY',
                              parent='organizations/' + organization_id)
    self._ExpectList([policy], organization_id)

    results = self.Run(
        'access-context-manager policies list --organization 12345')

    self.assertEqual(results, [policy])

  def testList_Format(self):
    self.SetUpForTrack(self.track)
    properties.VALUES.core.user_output_enabled.Set(True)

    organization_id = '12345'
    policy = self._MakePolicy('MY_POLICY',
                              parent='organizations/' + organization_id)
    self._ExpectList([policy], organization_id)

    self.Run('access-context-manager policies list --organization 12345')

    self.AssertOutputEquals("""\
        NAME      ORGANIZATION  TITLE
        MY_POLICY 12345         My Policy
        """, normalize_space=True)


class PoliciesListTestBeta(PoliciesListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class PoliciesListTestAlpha(PoliciesListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
