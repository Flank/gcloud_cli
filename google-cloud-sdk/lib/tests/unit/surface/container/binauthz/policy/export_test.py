# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Tests for surface.container.binauthz.policy.export."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class ExportTest(base.WithMockBetaBinauthz, base.BinauthzTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSuccess(self):
    # Create the expected policy proto.
    EvaluationModeEnum = (  # pylint: disable=invalid-name
        self.messages.AdmissionRule.EvaluationModeValueValuesEnum)
    EnforcementModeEnum = (  # pylint: disable=invalid-name
        self.messages.AdmissionRule.EnforcementModeValueValuesEnum)
    cluster_rules = [
        self.messages.Policy.ClusterAdmissionRulesValue.AdditionalProperty(
            key='us-east1-b.my-cluster-1',
            value=self.messages.AdmissionRule(
                evaluationMode=EvaluationModeEnum.REQUIRE_ATTESTATION,
                enforcementMode=(
                    EnforcementModeEnum.ENFORCED_BLOCK_AND_AUDIT_LOG),
                requireAttestationsBy=[
                    'projects/fake-project/attestors/build-env',
                ],
            ),
        ),
    ]
    policy_proto = self.messages.Policy(
        name='projects/{}/policy'.format(self.Project()),
        admissionWhitelistPatterns=[
            self.messages.AdmissionWhitelistPattern(
                namePattern='gcr.io/{}/*'.format(self.Project()),
            ),
        ],
        clusterAdmissionRules=self.messages.Policy.ClusterAdmissionRulesValue(
            additionalProperties=cluster_rules,
        ),
        defaultAdmissionRule=self.messages.AdmissionRule(
            evaluationMode=EvaluationModeEnum.ALWAYS_ALLOW,
            enforcementMode=(
                EnforcementModeEnum.ENFORCED_BLOCK_AND_AUDIT_LOG),
            requireAttestationsBy=[],
        ),
    )

    self.mock_client.projects.GetPolicy.Expect(
        self.messages.BinaryauthorizationProjectsGetPolicyRequest(
            name='projects/{}/policy'.format(self.Project())),
        policy_proto,
    )

    response = self.RunBinauthz('policy export')

    self.assertEqual(response, policy_proto)


class ExportAlphaTest(base.WithMockAlphaBinauthz, ExportTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
