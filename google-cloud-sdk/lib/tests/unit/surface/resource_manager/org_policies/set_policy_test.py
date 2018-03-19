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

from googlecloudsdk.api_lib.resource_manager import exceptions
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase

ORG_POLICY_JSON = """{
  "constraint": "constraints/goodService.betterBlacklist",
  "listPolicy":{
    "deniedValues": ["valueA", "valueB"]
  }
}
"""

ORG_POLICY_YAML = """
constraint: constraints/goodService.betterBlacklist
listPolicy:
  deniedValues:
  - valueA
  - valueB
"""

CONSTRAINT = 'constraints/goodService.betterBlacklist'


class OrgPoliciesSetPolicyTest(testbase.OrgPoliciesUnitTestBase):

  def testSetPolicyFileNotFound(self):
    filename = 'nonexistent'
    with self.assertRaises(files.Error):
      self.DoRequest(filename, self.PROJECT_ARG)

  def testSetPolicyBadJson(self):
    filename = self.Touch(self.temp_path, contents='malformed content')
    with self.assertRaises(exceptions.ResourceManagerInputFileError):
      self.DoRequest(filename, self.PROJECT_ARG)

  def testSetPolicyJson(self):
    self.DoTestSetPolicy(ORG_POLICY_JSON)

  def testSetPolicyYaml(self):
    self.DoTestSetPolicy(ORG_POLICY_YAML)

  def DoTestSetPolicy(self, file_content):
    filename = self.Touch(self.temp_path, contents=file_content)
    self.mock_projects.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.PROJECT_ARG, self.Policy()), self.Policy())
    self.mock_organizations.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.ORG_ARG, self.Policy()), self.Policy())
    self.mock_folders.SetOrgPolicy.Expect(
        self.ExpectedSetRequest(self.FOLDER_ARG, self.Policy()), self.Policy())
    self.assertEqual(self.DoRequest(filename, self.PROJECT_ARG), self.Policy())
    self.assertEqual(self.DoRequest(filename, self.ORG_ARG), self.Policy())
    self.assertEqual(self.DoRequest(filename, self.FOLDER_ARG), self.Policy())

  def DoRequest(self, filename, args):
    return self.RunOrgPolicies('set-policy', filename, *args)

  def Policy(self):
    return self.messages.OrgPolicy(
        constraint=CONSTRAINT,
        listPolicy=self.messages.ListPolicy(deniedValues=['valueA', 'valueB']))


if __name__ == '__main__':
  test_case.main()
