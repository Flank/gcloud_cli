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
"""Tests for `gcloud access-context-manager policies describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six import text_type


class PoliciesDescribeTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakePolicy(self, policy_id, parent=None):
    return self.messages.AccessPolicy(
        name='accessPolicies/{}'.format(policy_id),
        parent=parent,
        title='My Policy')

  def _ExpectGet(self, policy):
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesGetRequest
    self.client.accessPolicies.Get.Expect(
        request_type(name=policy.name,), policy)

  def testDescribe(self):
    self.SetUpForTrack(self.track)
    organization_id = '12345'
    policy = self._MakePolicy(
        'MY_POLICY', parent='organizations/' + organization_id)
    self._ExpectGet(policy)

    result = self.Run('access-context-manager policies describe MY_POLICY')

    self.assertEqual(result, policy)

  def testDescribe_Format(self):
    self.SetUpForTrack(self.track)
    properties.VALUES.core.user_output_enabled.Set(True)

    organization_id = '12345'
    policy = self._MakePolicy(
        'MY_POLICY', parent='organizations/' + organization_id)
    self._ExpectGet(policy)

    self.Run('access-context-manager policies describe MY_POLICY')

    self.AssertOutputEquals(
        """\
        name: accessPolicies/MY_POLICY
        parent: organizations/12345
        title: My Policy
        """,
        normalize_space=True)

  def test_InvalidPolicyFormatFromProperty(self):
    self.SetUpForTrack(self.track)

    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      policy_string = 'accessPolicies/789'
      properties.VALUES.access_context_manager.policy.Set(policy_string)
    self.assertIn('set to the policy number', text_type(ex.exception))


class PoliciesDescribeTestBeta(PoliciesDescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class PoliciesDescribeTestAlpha(PoliciesDescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
