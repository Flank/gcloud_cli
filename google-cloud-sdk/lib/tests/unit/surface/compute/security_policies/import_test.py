# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for the security policies import subcommand."""

import re
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.security_policies import (
    security_policies_utils)
from googlecloudsdk.core import resources
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


class SecurityPoliciesImportTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.my_policy = self.resources.Create(
        'compute.securityPolicies',
        securityPolicy='my-policy',
        project='my-project')

  def testSecurityPolicyFromJsonFile(self):
    json_file = open(_JSON_FILE_PATH)
    security_policy = security_policies_utils.SecurityPolicyFromFile(
        json_file, self.messages, 'json')

    # Add fields that are not required for an actual import, but are required
    # for the sake of this test.
    test_policy = test_resources.MakeSecurityPolicy(self.messages,
                                                    self.my_policy)
    security_policy.id = test_policy.id
    security_policy.name = test_policy.name
    security_policy.selfLink = test_policy.selfLink

    self.assertEqual(test_policy, security_policy)
    json_file.close()

  def testSecurityPolicyFromYamlFile(self):
    yaml_file = open(_YAML_FILE_PATH)
    security_policy = security_policies_utils.SecurityPolicyFromFile(
        yaml_file, self.messages, 'yaml')

    # Add fields that are not required for an actual import, but are required
    # for the sake of this test.
    test_policy = test_resources.MakeSecurityPolicy(self.messages,
                                                    self.my_policy)
    security_policy.id = test_policy.id
    security_policy.name = test_policy.name
    security_policy.selfLink = test_policy.selfLink

    self.assertEqual(test_policy, security_policy)
    yaml_file.close()

  def _ImportFromFileHelper(self, file_path, file_format, has_optional=True):
    self.Run('compute security-policies import my-policy --file-name {0} '
             '--file-format {1}'.format(file_path, file_format))

    # Remove fields that are not included in a Patch request.
    resource = test_resources.MakeSecurityPolicy(self.messages, self.my_policy)
    resource.id = None
    resource.name = None
    resource.selfLink = None

    # Remove optional fields if has_optional is False.
    if not has_optional:
      resource.description = None
      for rule in resource.rules:
        rule.description = None

    self.CheckRequests(
        [(self.compute.securityPolicies, 'Patch',
          self.messages.ComputeSecurityPoliciesPatchRequest(
              project='my-project',
              securityPolicy='my-policy',
              securityPolicyResource=resource))],)
    self.AssertErrContains(
        textwrap.dedent("""\
        Updated [my-policy] with config from [{0}].
        """.format(file_path)))

  def _ImportInvalidFromFileHelper(self, file_path, file_format,
                                   expected_error):
    with self.AssertRaisesExceptionRegexp(
        exceptions.BadFileException,
        r'Unable to read security policy config from specified file \[{0}\] '
        r'because \[{1}\]'.format(re.escape(file_path), expected_error)):
      self.Run('compute security-policies import my-policy --file-name {0} '
               '--file-format {1}'.format(file_path, file_format))

  def testImportFromJsonFile(self):
    self._ImportFromFileHelper(_JSON_FILE_PATH, 'json')

  def testImportFromJsonFileOptionalFieldAbsent(self):
    self._ImportFromFileHelper(
        _JSON_FILE_PATH_NO_DESCRIPTIONS, 'json', has_optional=False)

  def testImportFromYamlFile(self):
    self._ImportFromFileHelper(_YAML_FILE_PATH, 'yaml')

  def testImportFromYamlFileOptionalFieldsAbsent(self):
    self._ImportFromFileHelper(
        _YAML_FILE_PATH_NO_DESCRIPTIONS, 'yaml', has_optional=False)

  def testBadFilePath(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.BadFileException,
        r'No such file \[{0}\]'.format(re.escape(_BAD_FILE_PATH))):
      self.Run('compute security-policies import my-policy --file-name {0} '
               '--file-format {1}'.format(_BAD_FILE_PATH, 'yaml'))

    self.CheckRequests()

  def testInvalidJsonFile(self):
    self._ImportInvalidFromFileHelper(
        _JSON_INVALID_FILE_PATH, 'json',
        'Error parsing JSON: No JSON object could be decoded')

  def testInvalidYamlFile(self):
    self._ImportInvalidFromFileHelper(
        _YAML_INVALID_FILE_PATH, 'yaml',
        'Failed to parse YAML: while parsing a block mapping\n.*\n.*\n.*')


if __name__ == '__main__':
  test_case.main()
