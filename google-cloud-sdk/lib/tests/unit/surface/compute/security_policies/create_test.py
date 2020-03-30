# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the security policies create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.security_policies import security_policies_utils
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

_JSON_FILE_PATH = sdk_test_base.SdkBase.Resource(
    'tests', 'unit', 'surface', 'compute', 'security_policies', 'test_data',
    'security-policy-exported.json')
_YAML_FILE_PATH = sdk_test_base.SdkBase.Resource(
    'tests', 'unit', 'surface', 'compute', 'security_policies', 'test_data',
    'security-policy-exported.yaml')
_JSON_FILE_MATCH_EXPRESSION_PATH = sdk_test_base.SdkBase.Resource(
    'tests', 'unit', 'surface', 'compute', 'security_policies', 'test_data',
    'security-policy-match-expression-exported.json')
_YAML_FILE_MATCH_EXPRESSION_PATH = sdk_test_base.SdkBase.Resource(
    'tests', 'unit', 'surface', 'compute', 'security_policies', 'test_data',
    'security-policy-match-expression-exported.yaml')
_JSON_FILE_PATH_NO_DESCRIPTIONS = sdk_test_base.SdkBase.Resource(
    'tests', 'unit', 'surface', 'compute', 'security_policies', 'test_data',
    'security-policy-no-descriptions-exported.json')
_YAML_FILE_PATH_NO_DESCRIPTIONS = sdk_test_base.SdkBase.Resource(
    'tests', 'unit', 'surface', 'compute', 'security_policies', 'test_data',
    'security-policy-no-descriptions-exported.yaml')
_BAD_FILE_PATH = sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface',
                                                'compute', 'security_policies',
                                                'test_data', 'not-a-file')
_JSON_INVALID_FILE_PATH = sdk_test_base.SdkBase.Resource(
    'tests', 'unit', 'surface', 'compute', 'security_policies', 'test_data',
    'security-policy-invalid.json')
_YAML_INVALID_FILE_PATH = sdk_test_base.SdkBase.Resource(
    'tests', 'unit', 'surface', 'compute', 'security_policies', 'test_data',
    'security-policy-invalid.yaml')


class SecurityPoliciesCreateTest(test_base.BaseTest, parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')

  def CreateSecurityPolicy(self):
    return self.resources.Create(
        'compute.securityPolicies',
        securityPolicy='my-policy',
        project='my-project')

  def CheckSecurityPolicyRequest(self, **kwargs):
    security_policy_msg = {}
    security_policy_msg.update(kwargs)
    self.CheckRequests([(self.compute.securityPolicies, 'Insert',
                         self.messages.ComputeSecurityPoliciesInsertRequest(
                             project='my-project',
                             securityPolicy=self.messages.SecurityPolicy(
                                 **security_policy_msg)))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testDefaultOptions(self):
    self.Run("""
        compute security-policies create my-policy
        """)
    self.CheckSecurityPolicyRequest(name='my-policy')

  def testUriSupport(self):
    self.Run('compute security-policies create {}'.format(
        self.CreateSecurityPolicy().SelfLink()))
    self.CheckSecurityPolicyRequest(name='my-policy')

  def testDescription(self):
    self.Run("""
        compute security-policies create my-policy
        --description my-description
        """)
    self.CheckSecurityPolicyRequest(
        name='my-policy', description='my-description')

  @parameterized.named_parameters(('JsonFile', _JSON_FILE_PATH, 'json'),
                                  ('YamlFile', _YAML_FILE_PATH, 'yaml'))
  def testSecurityPolicyFromFile(self, file_path, file_format):
    template = open(file_path)
    actual = security_policies_utils.SecurityPolicyFromFile(
        template, self.messages, file_format)

    expected = test_resources.MakeSecurityPolicy(self.messages,
                                                 self.CreateSecurityPolicy())

    # Add fields that are not required for an actual import, but are required
    # for the sake of this test.
    actual.name = expected.name
    actual.id = expected.id
    actual.selfLink = expected.selfLink

    self.assertEqual(expected, actual)
    template.close()

  @parameterized.named_parameters(
      ('JsonFile', _JSON_FILE_MATCH_EXPRESSION_PATH, 'json'),
      ('YamlFile', _YAML_FILE_MATCH_EXPRESSION_PATH, 'yaml'))
  def testSecurityPolicyMatchExpressionFromFile(self, file_path, file_format):
    template = open(file_path)
    actual = security_policies_utils.SecurityPolicyFromFile(
        template, self.messages, file_format)

    expected = test_resources.MakeSecurityPolicyMatchExpression(
        self.messages, self.CreateSecurityPolicy())

    # Add fields that are not required for an actual import, but are required
    # for the sake of this test.
    actual.name = expected.name
    actual.id = expected.id
    actual.selfLink = expected.selfLink

    self.assertEqual(expected, actual)
    template.close()

  @parameterized.named_parameters(
      ('JsonFile', _JSON_FILE_PATH, 'json', 'my description', 'default rule'),
      ('JsonFileOptionalFieldAbsent', _JSON_FILE_PATH_NO_DESCRIPTIONS, 'json',
       None, None),
      ('YamlFile', _YAML_FILE_PATH, 'yaml', 'my description', 'default rule'),
      ('YamlFileOptionalFieldsAbsent', _YAML_FILE_PATH_NO_DESCRIPTIONS, 'yaml',
       None, None))
  def testCreateFromTemplate(self, file_path, file_format, description,
                             rule_description):
    messages = self.messages
    self.Run('compute security-policies create my-policy --file-name "{0}" '
             '--file-format {1}'.format(file_path, file_format))

    self.CheckSecurityPolicyRequest(
        name='my-policy',
        description=description,
        fingerprint=b'=g\xcb\x185\x90\x0c\xb6',
        rules=[
            messages.SecurityPolicyRule(
                description=rule_description,
                priority=2147483647,
                match=messages.SecurityPolicyRuleMatcher(
                    versionedExpr=messages.SecurityPolicyRuleMatcher
                    .VersionedExprValueValuesEnum('SRC_IPS_V1'),
                    config=messages.SecurityPolicyRuleMatcherConfig(
                        srcIpRanges=['*'])),
                action='allow',
                preview=False)
        ])

  @parameterized.named_parameters(
      # Python 2 and 3 produce different json parsing error messages.
      ('InvalidJsonFile', _JSON_INVALID_FILE_PATH, 'json',
       'Error parsing JSON: .*'),
      ('InvalidYamlFile', _YAML_INVALID_FILE_PATH, 'yaml',
       'Failed to parse YAML: while parsing a block mapping\n.*\n.*\n.*'))
  def testCreateFromInvalidTemplate(self, file_path, file_format,
                                    expected_error):
    with self.AssertRaisesExceptionRegexp(
        exceptions.BadFileException,
        r'Unable to read security policy config from specified file \[{0}\] '
        r'because \[{1}\]'.format(re.escape(file_path), expected_error)):
      self.Run('compute security-policies create my-policy --file-name "{0}" '
               '--file-format {1}'.format(file_path, file_format))

  def testBadFilePath(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.BadFileException, r'No such file \[{0}\]'.format(
            re.escape(_BAD_FILE_PATH))):
      self.Run('compute security-policies create my-policy --file-name "{0}" '
               '--file-format {1}'.format(_BAD_FILE_PATH, 'yaml'))


class SecurityPoliciesCreateTestBeta(SecurityPoliciesCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')


class SecurityPoliciesCreateTestAlpha(SecurityPoliciesCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')


if __name__ == '__main__':
  test_case.main()
