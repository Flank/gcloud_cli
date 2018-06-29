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
"""Tests for the security policies export subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
import os
import re

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.security_policies import (
    security_policies_utils)
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
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


class SecurityPoliciesExportTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.result_file_path = os.path.join(self.temp_path, 'exported')
    self.my_policy = self.resources.Create(
        'compute.securityPolicies',
        securityPolicy='my-policy',
        project='my-project')

  def testWriteToJsonFile(self):
    with open(self.result_file_path, 'w') as json_file:
      security_policies_utils.WriteToFile(json_file,
                                          test_resources.MakeSecurityPolicy(
                                              self.messages, self.my_policy),
                                          'json')

    with open(self.result_file_path) as results:
      with open(_JSON_FILE_PATH) as expected:
        self.assertEqual(expected.readlines(), results.readlines())

  def testWriteToYamlFile(self):
    with open(self.result_file_path, 'w') as yaml_file:
      security_policies_utils.WriteToFile(yaml_file,
                                          test_resources.MakeSecurityPolicy(
                                              self.messages, self.my_policy),
                                          'yaml')

    with open(self.result_file_path) as results:
      with open(_YAML_FILE_PATH) as expected:
        self.assertEqual(expected.readlines(), results.readlines())

  def _ExportToFileHelper(self, expected_file, file_format='json'):
    self.make_requests.side_effect = iter([
        [test_resources.MakeSecurityPolicy(self.messages, self.my_policy)],
    ])
    self.Run('compute security-policies export my-policy'
             ' --file-name {0} --file-format {1}'.format(
                 self.result_file_path, file_format))

    with open(self.result_file_path) as result:
      with open(expected_file) as expected:
        self.assertEqual(expected.readlines(), result.readlines())

  def testExportToJsonFile(self):
    self._ExportToFileHelper(_JSON_FILE_PATH)

  def testExportToYamlFile(self):
    self._ExportToFileHelper(_YAML_FILE_PATH, file_format='yaml')

  def testExportWithErrors(self):
    with self.AssertRaisesExceptionRegexp(
        files.Error,
        r'Unable to write file \[{0}\]: .*'.format(
            re.escape('/'))):
      self.Run('compute security-policies export my-policy'
               ' --file-name {0} --file-format {1}'.format('/', 'json'))


if __name__ == '__main__':
  test_case.main()
