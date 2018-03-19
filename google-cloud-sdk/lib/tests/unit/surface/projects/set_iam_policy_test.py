# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests for projects set-iam-policy."""

from apitools.base.py import encoding

from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util as test_util


class ProjectsSetIamPolicyTest(base.ProjectsUnitTestBase):

  def testSetIamPolicyProject(self):
    new_policy = test_util.GetTestIamPolicy()
    json = encoding.MessageToJson(new_policy)
    temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy,
                updateMask='auditConfigs,bindings,etag,version')),
        new_policy)
    response = self.RunProjectsBeta('set-iam-policy',
                                    test_project.projectId,
                                    temp_file)
    self.assertEqual(response, new_policy)
    self.AssertErrContains(
        'Updated IAM policy for project [{}]'.format(test_project.projectId))

  def testClearBindingsAndEtagSetIamPolicyProject(self):
    new_policy = test_util.GetTestIamPolicy(clear_fields=['bindings', 'etag'])
    json = encoding.MessageToJson(new_policy)
    temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy,
                updateMask='auditConfigs,version,bindings,etag')),
        new_policy)
    response = self.RunProjectsBeta('set-iam-policy',
                                    test_project.projectId,
                                    temp_file)
    self.assertEqual(response, new_policy)

  def testAuditConfigsPreservedSetIamPolicyProject(self):
    start_policy = test_util.GetTestIamPolicy()
    new_policy = test_util.GetTestIamPolicy(clear_fields=['auditConfigs'])
    json = encoding.MessageToJson(new_policy)
    temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy,
                updateMask='bindings,etag,version')),
        start_policy)
    response = self.RunProjectsBeta('set-iam-policy',
                                    test_project.projectId,
                                    temp_file)
    self.assertEqual(response, start_policy)

  def testBadJsonOrYamlSetIamPolicyProject(self):
    temp_file = self.Touch(self.temp_path, 'bad', contents='bad')

    with self.assertRaises(exceptions.Error):
      self.RunProjectsBeta('set-iam-policy',
                           test_util.GetTestActiveProject().projectId,
                           temp_file)

  def testBadJsonSetIamPolicyProject(self):
    file_path = '/some/bad/path/to/non/existend/file'
    with self.assertRaisesRegexp(
        exceptions.Error,
        r'Failed to load YAML from \[{}\]'.format(file_path)):
      self.RunProjectsBeta(
          'set-iam-policy', test_util.GetTestActiveProject().projectId,
          file_path)


if __name__ == '__main__':
  test_case.main()
