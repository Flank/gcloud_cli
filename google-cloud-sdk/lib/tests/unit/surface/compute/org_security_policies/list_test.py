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
"""Tests for the organization security policy list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute.org_security_policies import test_resources


class OrgSecurityPoliciesListBetaTest(sdk_test_base.WithFakeAuth,
                                      cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

  def testSimpleCase(self):
    self.client.organizationSecurityPolicies.List.Expect(
        self.messages.ComputeOrganizationSecurityPoliciesListRequest(
            pageToken=None,
            parentId='organizations/9999999',
        ),
        response=self.messages.SecurityPolicyList(
            items=[
                test_resources.MakeOrgSecurityPolicy(
                    self.messages,
                    self.resources.Create(
                        'compute.organizationSecurityPolicies',
                        securityPolicy='123'))
            ],))

    self.Run("""
        compute org-security-policies list --organization 9999999
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        ID DISPLAY_NAME DESCRIPTION
        123 display-name  test-description
        """),
        normalize_space=True)
    self.AssertErrEquals('')


class OrgSecurityPoliciesListAlphaTest(OrgSecurityPoliciesListBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE


if __name__ == '__main__':
  test_case.main()
