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
"""Tests for the organization security policy rules update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class OrgSecurityPoliciesRulesCreateAlphaTest(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.SelectApi(self.track.prefix)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

  def CreateTestOrgSecurityPolicyMessage(self, **kwargs):
    return self.messages.SecurityPolicyRule(
        priority=10,
        action='allow',
        enableLogging=True,
        direction=self.messages.SecurityPolicyRule.DirectionValueValuesEnum
        .INGRESS,
        match=self.messages.SecurityPolicyRuleMatcher(
            versionedExpr=self.messages.SecurityPolicyRuleMatcher
            .VersionedExprValueValuesEnum.FIREWALL,
            config=self.messages.SecurityPolicyRuleMatcherConfig(
                srcIpRanges=[], destIpRanges=[], destPorts=[])))

  def ExpectOrgSecurityPolicyRequest(self, **kwargs):
    self.make_requests.side_effect = iter(
        [[self.CreateTestOrgSecurityPolicyMessage(**kwargs)]])

  def CheckOrgSecurityPolicyRequest(self, **kwargs):
    self.CheckRequests([
        (self.compute.organizationSecurityPolicies, 'PatchRule',
         self.messages.ComputeOrganizationSecurityPoliciesPatchRuleRequest(
             priority=10,
             securityPolicy='12345',
             securityPolicyRule=self.CreateTestOrgSecurityPolicyMessage(
                 **kwargs)))
    ])

  def testRulesUpdateOrgSecurityPolicyRule(self):
    self.ExpectOrgSecurityPolicyRequest()

    self.Run(
        'compute org-security-policies rules update 10 '
        '--security-policy 12345 --action allow --direction INGRESS --enable-logging'
    )

    self.CheckOrgSecurityPolicyRequest()


if __name__ == '__main__':
  test_case.main()
