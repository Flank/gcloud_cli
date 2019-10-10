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
"""Tests for the securitypolicies list-preconfigured-expression-sets command."""

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


class SecurityPoliciesListPreconfiguredExpressionSetsTest(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.client = mock.Client(core_apis.GetClientClass('compute', 'alpha'))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

  def testListPreconfiguredExpressionSets(self):
    # Define the preconfigured expression sets to list
    preconfigured_expression_sets = self.messages.SecurityPoliciesWafConfig(
        wafRules=self.messages.PreconfiguredWafSet(expressionSets=[
            self.messages.WafExpressionSet(
                id='expression-set-1',
                expressions=[
                    self.messages.WafExpressionSetExpression(
                        id='expression-set-1-id-1'),
                    self.messages.WafExpressionSetExpression(
                        id='expression-set-1-id-2')
                ]),
            self.messages.WafExpressionSet(
                id='expression-set-2',
                aliases=['alias-1'],
                expressions=[
                    self.messages.WafExpressionSetExpression(
                        id='expression-set-2-id-1'),
                    self.messages.WafExpressionSetExpression(
                        id='expression-set-2-id-2')
                ])
        ]))

    # Setup the expected response
    request = (
        self.messages.
        ComputeSecurityPoliciesListPreconfiguredExpressionSetsRequest(
            project=self.Project()))
    response = (
        self.messages.SecurityPoliciesListPreconfiguredExpressionSetsResponse(
            preconfiguredExpressionSets=preconfigured_expression_sets))
    self.client.securityPolicies.ListPreconfiguredExpressionSets.Expect(
        request=request, response=response, exception=None)

    response = self.Run('compute security-policies '
                        'list-preconfigured-expression-sets')
    self.assertEqual(response,
                     preconfigured_expression_sets.wafRules.expressionSets)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        EXPRESSION_SET
        expression-set-1
            RULE_ID
            expression-set-1-id-1
            expression-set-1-id-2
        expression-set-2
            alias-1
            RULE_ID
            expression-set-2-id-1
            expression-set-2-id-2
        """))


if __name__ == '__main__':
  test_case.main()
