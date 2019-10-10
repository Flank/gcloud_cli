# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util as test_util


# TODO(b/117336602) Stop using parameterized for track parameterization.
class ProjectsSetIamPolicyTestGA(base.ProjectsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSetIamPolicyProject(self):
    new_policy = test_util.GetTestIamPolicy()
    json = encoding.MessageToJson(new_policy)
    temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

    # set the expected version to 3
    new_policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy,
                updateMask='auditConfigs,bindings,etag')), new_policy)
    response = self.RunProjects('set-iam-policy', test_project.projectId,
                                temp_file)
    self.assertEqual(response, new_policy)
    self.AssertErrContains('Updated IAM policy for project')

  def testClearBindingsAndEtagSetIamPolicyProject(self):
    new_policy = test_util.GetTestIamPolicy(clear_fields=['bindings', 'etag'])
    json = encoding.MessageToJson(new_policy)
    temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

    # set the expected version to 3
    new_policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy,
                updateMask='auditConfigs,bindings,etag')), new_policy)
    response = self.RunProjects('set-iam-policy', test_project.projectId,
                                temp_file)
    self.assertEqual(response, new_policy)

  def testAuditConfigsPreservedSetIamPolicyProject(self):
    start_policy = test_util.GetTestIamPolicy()
    new_policy = test_util.GetTestIamPolicy(clear_fields=['auditConfigs'])
    json = encoding.MessageToJson(new_policy)
    temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

    # set the expected version to 3
    new_policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    test_project = test_util.GetTestActiveProject()
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy, updateMask='bindings,etag')),
        start_policy)
    response = self.RunProjects('set-iam-policy', test_project.projectId,
                                temp_file)
    self.assertEqual(response, start_policy)

  def testBadJsonOrYamlSetIamPolicyProject(self):
    temp_file = self.Touch(self.temp_path, 'bad', contents='bad')

    with self.assertRaises(exceptions.Error):
      self.RunProjects('set-iam-policy',
                       test_util.GetTestActiveProject().projectId, temp_file)

  def testBadJsonSetIamPolicyProject(self):
    file_path = '/some/bad/path/to/non/existend/file'
    with self.assertRaisesRegex(
        exceptions.Error, r'Failed to load YAML from \[{}\]'.format(file_path)):
      self.RunProjects('set-iam-policy',
                       test_util.GetTestActiveProject().projectId,
                       file_path)


class ProjectsSetIamPolicyTestBeta(ProjectsSetIamPolicyTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ProjectsSetIamPolicyTestAlpha(ProjectsSetIamPolicyTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
