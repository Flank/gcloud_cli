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

"""Tests for projects set-iam-policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util as test_util


class ProjectsAddIamPolicyBindingTestGA(base.ProjectsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testAddIamPolicyBinding(self):
    test_project = test_util.GetTestActiveProject()
    new_role = 'roles/editor'
    new_user = 'user:fox@google.com'
    start_policy = copy.deepcopy(test_util.GetTestIamPolicy())
    new_policy = copy.deepcopy(start_policy)
    new_policy.bindings[0].members.append(new_user)
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
        'add-iam-policy-binding',
        test_project.projectId,
        '--role={0}'.format(new_role),
        '--member={0}'.format(new_user))

    self.assertEqual(response, new_policy)


class ProjectsAddIamPolicyBindingTestBeta(ProjectsAddIamPolicyBindingTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ProjectsAddIamPolicyBindingTestAlpha(ProjectsAddIamPolicyBindingTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

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
        ],
        etag=b'an etag',
        version=1)

  def testPromptForExistingCondition(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    test_project = test_util.GetTestActiveProject()
    new_role = 'roles/another-non-primitive'
    new_user = 'user:owner@google.com'
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    new_policy = copy.deepcopy(start_policy)
    new_condition = self.messages.Expr(
        expression='expr', title='title', description='descr')
    new_policy.bindings.append(
        self.messages.Binding(
            members=['user:owner@google.com'],
            role='roles/another-non-primitive',
            condition=new_condition))
    self.WriteInput('1')
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId), start_policy)
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunProjects(
        'add-iam-policy-binding', test_project.projectId,
        '--role={0}'.format(new_role), '--member={0}'.format(new_user))
    self.assertEqual(response, new_policy)
    self.AssertErrContains('The policy contains bindings with conditions')

  def testPromptForNewCondition(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    test_project = test_util.GetTestActiveProject()
    new_role = 'roles/another-non-primitive'
    new_user = 'user:owner@google.com'
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    new_policy = copy.deepcopy(start_policy)
    new_condition = self.messages.Expr(
        expression='expr', title='title', description='descr')
    new_policy.bindings.append(
        self.messages.Binding(
            members=['user:owner@google.com'],
            role='roles/another-non-primitive',
            condition=new_condition))
    self.WriteInput('3')
    self.WriteInput('expression=expr,title=title,description=descr')
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId), start_policy)
    self.mock_client.projects.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource=test_project.projectId,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunProjects(
        'add-iam-policy-binding', test_project.projectId,
        '--role={0}'.format(new_role), '--member={0}'.format(new_user))
    self.assertEqual(response, new_policy)
    self.AssertErrContains('The policy contains bindings with conditions')
    self.AssertErrContains('Condition is either `None`')

  def testPromptForNewCondition_Condition_And_PrimitiveRole(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    test_project = test_util.GetTestActiveProject()
    new_role = 'roles/editor'
    new_user = 'user:owner@google.com'
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    self.WriteInput('3')
    self.WriteInput('expression=expr,title=title,description=descr')
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId), start_policy)

    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingInvalidError,
        '.*Binding with a condition and a primitive role is not allowed.*'):
      self.RunProjects('add-iam-policy-binding', test_project.projectId,
                       '--role={0}'.format(new_role),
                       '--member={0}'.format(new_user))

  def testPromptForCondition_CannotPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=False)
    test_project = test_util.GetTestActiveProject()
    new_role = 'roles/another-non-primitive'
    new_user = 'user:owner@google.com'
    start_policy = self.test_iam_policy_with_condition
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId), start_policy)

    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingIncompleteError,
        '.*Adding a binding without specifying a condition to a policy.*'):
      self.RunProjects('add-iam-policy-binding', test_project.projectId,
                       '--role={0}'.format(new_role),
                       '--member={0}'.format(new_user))


class ProjectsAddIamPolicyBindingCompletionTestGA(base.ProjectsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testRoleCompletion(self):
    test_project = test_util.GetTestActiveProject()

    iam_client = mock.Client(core_apis.GetClientClass('iam', 'v1'))
    iam_client.Mock()
    self.addCleanup(iam_client.Unmock)
    iam_msgs = core_apis.GetMessagesModule('iam', 'v1')

    returned_roles = [
        iam_msgs.Role(
            description='Read access to all resources.',
            name='roles/viewer',
            title='Viewer',
        ),
        iam_msgs.Role(
            description='Read-only access to GCE networking resources.',
            name='roles/compute.networkViewer',
            title='Compute Network Viewer',
        ),
    ]
    iam_client.roles.QueryGrantableRoles.Expect(
        request=iam_msgs.QueryGrantableRolesRequest(
            fullResourceName=(
                '//cloudresourcemanager.googleapis.com/projects/{0}'.format(
                    test_project.projectId)),
            pageSize=100),
        response=iam_msgs.QueryGrantableRolesResponse(roles=returned_roles),
    )

    self.RunCompletion(
        'projects add-iam-policy-binding {0} --role '.format(
            test_project.projectId),
        ['roles/viewer', 'roles/compute.networkViewer'])


class ProjectsAddIamPolicyBindingCompletionTestBeta(
    ProjectsAddIamPolicyBindingCompletionTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ProjectsAddIamPolicyBindingCompletionTestAlpha(
    ProjectsAddIamPolicyBindingCompletionTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
