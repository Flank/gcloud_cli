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

"""Tests for surface.container.binauthz.policy.import."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.container.binauthz import encoding
from googlecloudsdk.command_lib.container.binauthz import parsing
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class ImportTest(sdk_test_base.WithTempCWD,
                 base.BinauthzMockedPolicyClientUnitTest):

  def testSuccessYaml(self):
    policy_fname = self.Touch(
        name='foo.yaml',
        directory=self.cwd_path,
        contents=textwrap.dedent("""
            admissionWhitelistPatterns:
            - namePattern: gcr.io/{0}/*
            clusterAdmissionRules:
              us-east1-b.my-cluster-1:
                evaluationMode: REQUIRE_ATTESTATION
                nonConformanceAction: DENY_AND_AUDIT_LOG
                requireAttestationAuthorities:
                - projects/{0}/attestationAuthorities/build-env
            defaultAdmissionRule:
              evaluationMode: ALWAYS_CONFORMANT
              nonConformanceAction: DENY_AND_AUDIT_LOG
        """).format(self.Project())
    )

    # Create the expected policy proto.
    EvaluationModeEnum = (  # pylint: disable=invalid-name
        self.messages.AdmissionRule.EvaluationModeValueValuesEnum)
    NonConformanceActionEnum = (  # pylint: disable=invalid-name
        self.messages.AdmissionRule.NonConformanceActionValueValuesEnum)
    cluster_rules = [
        self.messages.Policy.ClusterAdmissionRulesValue.AdditionalProperty(
            key=u'us-east1-b.my-cluster-1',
            value=self.messages.AdmissionRule(
                evaluationMode=EvaluationModeEnum.REQUIRE_ATTESTATION,
                nonConformanceAction=(
                    NonConformanceActionEnum.DENY_AND_AUDIT_LOG),
                requireAttestationAuthorities=[
                    'projects/fake-project/attestationAuthorities/build-env',
                ],
            ),
        ),
    ]
    policy_proto = self.messages.Policy(
        name='projects/{}/policy'.format(self.Project()),
        admissionWhitelistPatterns=[
            self.messages.AdmissionWhitelistPattern(
                namePattern=u'gcr.io/{}/*'.format(self.Project()),
            ),
        ],
        clusterAdmissionRules=self.messages.Policy.ClusterAdmissionRulesValue(
            additionalProperties=cluster_rules,
        ),
        defaultAdmissionRule=self.messages.AdmissionRule(
            evaluationMode=EvaluationModeEnum.ALWAYS_CONFORMANT,
            nonConformanceAction=(
                NonConformanceActionEnum.DENY_AND_AUDIT_LOG),
            requireAttestationAuthorities=[],
        ),

    )
    self.client.projects.UpdatePolicy.Expect(
        policy_proto, response=policy_proto)

    response = self.RunBinauthz('policy import ' + policy_fname)

    self.assertEqual(response, policy_proto)

  def testSuccessJson(self):
    policy_fname = self.Touch(
        name='foo.json',
        directory=self.cwd_path,
        contents=textwrap.dedent("""
            {
              "admissionWhitelistPatterns": [
                {
                  "namePattern": "gcr.io/google/*"
                }
              ],
              "clusterAdmissionRules": {
                "us-east1-b.my-cluster-1": {
                  "evaluationMode": "REQUIRE_ATTESTATION",
                  "nonConformanceAction": "DENY_AND_AUDIT_LOG",
                  "requireAttestationAuthorities": [
                    "projects/fake-project/attestationAuthorities/build-env"
                  ]
                }
              },
              "defaultAdmissionRule": {
                "evaluationMode": "ALWAYS_CONFORMANT",
                "nonConformanceAction": "DENY_AND_AUDIT_LOG"
              }
            }
        """)
    )

    # Create the expected policy proto.
    EvaluationModeEnum = (  # pylint: disable=invalid-name
        self.messages.AdmissionRule.EvaluationModeValueValuesEnum)
    NonConformanceActionEnum = (  # pylint: disable=invalid-name
        self.messages.AdmissionRule.NonConformanceActionValueValuesEnum)
    cluster_rules = [
        self.messages.Policy.ClusterAdmissionRulesValue.AdditionalProperty(
            key=u'us-east1-b.my-cluster-1',
            value=self.messages.AdmissionRule(
                evaluationMode=EvaluationModeEnum.REQUIRE_ATTESTATION,
                nonConformanceAction=(
                    NonConformanceActionEnum.DENY_AND_AUDIT_LOG),
                requireAttestationAuthorities=[
                    'projects/fake-project/attestationAuthorities/build-env',
                ],
            ),
        ),
    ]
    policy_proto = self.messages.Policy(
        name='projects/{}/policy'.format(self.Project()),
        admissionWhitelistPatterns=[
            self.messages.AdmissionWhitelistPattern(
                namePattern=u'gcr.io/google/*',
            ),
        ],
        clusterAdmissionRules=self.messages.Policy.ClusterAdmissionRulesValue(
            additionalProperties=cluster_rules,
        ),
        defaultAdmissionRule=self.messages.AdmissionRule(
            evaluationMode=EvaluationModeEnum.ALWAYS_CONFORMANT,
            nonConformanceAction=(
                NonConformanceActionEnum.DENY_AND_AUDIT_LOG),
            requireAttestationAuthorities=[],
        ),

    )
    self.client.projects.UpdatePolicy.Expect(
        policy_proto, response=policy_proto)

    response = self.RunBinauthz('policy import ' + policy_fname)

    self.assertEqual(response, policy_proto)

  def testEmptyPolicy_Continue(self):
    policy_fname = self.Touch(
        name='foo.yaml',
        directory=self.cwd_path,
        contents='',
    )

    policy_proto = self.messages.Policy(
        name='projects/{}/policy'.format(self.Project()),
    )

    self.client.projects.UpdatePolicy.Expect(
        policy_proto, response=policy_proto)

    self.WriteInput('Y\n')

    response = self.RunBinauthz('policy import ' + policy_fname)

    self.assertEqual(response, policy_proto)

  def testEmptyPolicy_Abort(self):
    policy_fname = self.Touch(
        name='foo.yaml',
        directory=self.cwd_path,
        contents='',
    )

    self.WriteInput('n\n')

    with self.assertRaisesRegexp(
        console_io.OperationCancelledError, 'Aborted by user'):
      self.RunBinauthz('policy import ' + policy_fname)

  def testBadJson(self):
    policy_fname = self.Touch(
        name='foo.json',
        directory=self.cwd_path,
        contents=''
    )

    with self.assertRaises(parsing.ResourceFileParseError):
      self.RunBinauthz('policy import ' + policy_fname)

  def testInvalidPolicy(self):
    policy_fname = self.Touch(
        name='foo.yaml',
        directory=self.cwd_path,
        contents=textwrap.dedent("""
            clusterAdmissionRules:
              us-east1-b.my-cluster-1:
                evaluationMode: INVALID_ENUM_VALUE
        """)
    )

    with self.assertRaisesRegexp(
        encoding.DecodeError,
        r'clusterAdmissionRules.*us-east1-b\.my-cluster-1.*evaluationMode'):
      self.RunBinauthz('policy import ' + policy_fname)

  def testPolicyFileNotFound(self):
    with self.assertRaises(parsing.ResourceFileReadError):
      self.RunBinauthz('policy import doesnt_exist.yaml')

  def testNoPolicyFile(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunBinauthz('policy import')


if __name__ == '__main__':
  test_case.main()
