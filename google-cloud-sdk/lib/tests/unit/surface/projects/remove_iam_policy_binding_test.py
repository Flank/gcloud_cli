# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for projects remove-iam-policy-binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import json

from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util as test_util


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class ProjectsRemoveIamPolicyBindingTest(base.ProjectsUnitTestBase):

  def testRemoveIamPolicyBinding(self, track):
    self.track = track
    test_project = test_util.GetTestActiveProject()
    start_policy = copy.deepcopy(test_util.GetTestIamPolicy())
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:tester@gmail.com'
    remove_role = 'roles/owner'
    # In the test policy the first binding is for editors, second for owners.
    new_policy.bindings[1].members.remove(remove_user)
    resource_name = test_project.projectId

    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=resource_name),
        start_policy)
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=resource_name,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)),
        new_policy)

    response = self.RunProjects(
        'remove-iam-policy-binding',
        test_project.projectId,
        '--role={0}'.format(remove_role),
        '--member={0}'.format(remove_user))
    self.assertEqual(response, new_policy)


class ProjectsRemoveIamPolicyBindingTestAlpha(base.ProjectsUnitTestBase):

  def SetUp(self):
    self.messages = projects_util.GetMessages()
    self.test_iam_policy_with_condition = projects_util.GetMessages().Policy(
        auditConfigs=[
            self.messages.AuditConfig(
                auditLogConfigs=[
                    self.messages.AuditLogConfig(
                        logType=self.messages.AuditLogConfig
                        .LogTypeValueValuesEnum.ADMIN_READ)
                ],
                service='allServices')
        ],
        bindings=[
            self.messages.Binding(
                members=['user:test@gmail.com'],
                role='roles/non-primitive',
                condition=self.messages.Expr(
                    expression='expr', title='title', description='descr')),
            self.messages.Binding(
                members=['user:test@gmail.com'], role='roles/non-primitive')
        ],
        etag=b'an etag',
        version=1)

  def testBindingWithoutConditionPolicyWithCondition(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    test_project = test_util.GetTestActiveProject()
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.WriteInput('1')
    new_policy.bindings[:] = new_policy.bindings[1:]

    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId), start_policy)
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunProjectsAlpha(
        'remove-iam-policy-binding', test_project.projectId,
        '--role={0}'.format(remove_role), '--member={0}'.format(remove_user))
    self.assertEqual(response, new_policy)
    json_string = self.GetErr().split('\n')[0]
    choices_in_stderr = json.loads(json_string)['choices']
    expected_choices = [
        'expression=expr,title=title,description=descr', 'None',
        'all conditions'
    ]
    self.assertEqual(choices_in_stderr, expected_choices)

  def testBindingWithoutConditionPolicyWithCondition_NoneCondition(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    test_project = test_util.GetTestActiveProject()
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.WriteInput('2')
    new_policy.bindings[:] = new_policy.bindings[:1]

    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId), start_policy)
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunProjectsAlpha(
        'remove-iam-policy-binding', test_project.projectId,
        '--role={0}'.format(remove_role), '--member={0}'.format(remove_user))
    self.assertEqual(response, new_policy)
    json_string = self.GetErr().split('\n')[0]
    choices_in_stderr = json.loads(json_string)['choices']
    expected_choices = [
        'expression=expr,title=title,description=descr', 'None',
        'all conditions'
    ]
    self.assertEqual(choices_in_stderr, expected_choices)

  def testBindingWithoutConditionPolicyWithCondition_AllConditions(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    test_project = test_util.GetTestActiveProject()
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.WriteInput('3')
    new_policy.bindings[:] = []

    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId), start_policy)
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunProjectsAlpha(
        'remove-iam-policy-binding', test_project.projectId,
        '--role={0}'.format(remove_role), '--member={0}'.format(remove_user))
    self.assertEqual(response, new_policy)
    json_string = self.GetErr().split('\n')[0]
    choices_in_stderr = json.loads(json_string)['choices']
    expected_choices = [
        'expression=expr,title=title,description=descr', 'None',
        'all conditions'
    ]
    self.assertEqual(choices_in_stderr, expected_choices)

  def testBindingWithoutConditionPolicyWithCondition_CannotPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=False)
    test_project = test_util.GetTestActiveProject()
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId), start_policy)
    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingIncompleteError,
        '.*Removing a binding without specifying a condition from a policy.*'):
      self.RunProjectsAlpha('remove-iam-policy-binding', test_project.projectId,
                            '--role={0}'.format(remove_role),
                            '--member={0}'.format(remove_user))


if __name__ == '__main__':
  test_case.main()
