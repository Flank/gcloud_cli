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
"""Tests for the organization security policy associations list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class OrgSecurityPoliciesAssociationsListBetaTest(sdk_test_base.WithFakeAuth,
                                                  cli_test_base.CliTestBase,
                                                  waiter_test_base.Base):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def CreateTestOrgSecurityPolicyMessage(self, **kwargs):
    return self.messages.OrganizationSecurityPoliciesListAssociationsResponse()

  def testAssociationsListOrgSecurityPolicy(self):
    self.mock_client.organizationSecurityPolicies.ListAssociations.Expect(
        self.messages
        .ComputeOrganizationSecurityPoliciesListAssociationsRequest(
            targetResource='organizations/9999999'),
        response=self.CreateTestOrgSecurityPolicyMessage())
    res = self.Run(
        'compute org-security-policies associations list --organization 9999999'
    )

    self.assertEqual(res,
                     self.CreateTestOrgSecurityPolicyMessage().associations)


class OrgSecurityPoliciesAssociationsListAlphaTest(
    OrgSecurityPoliciesAssociationsListBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)


if __name__ == '__main__':
  test_case.main()
