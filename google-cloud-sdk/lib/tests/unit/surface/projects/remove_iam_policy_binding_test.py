# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util as test_util


class ProjectsRemoveIamPolicyBindingTestGA(base.ProjectsUnitTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testRemoveIamPolicyBinding(self):
    test_project = test_util.GetTestActiveProject()
    start_policy = copy.deepcopy(test_util.GetTestIamPolicy())
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:tester@gmail.com'
    remove_role = 'roles/owner'
    # In the test policy the first binding is for editors, second for owners.
    new_policy.bindings[1].members.remove(remove_user)
    resource_name = test_project.projectId
    new_policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=resource_name,
            getIamPolicyRequest=self.messages.GetIamPolicyRequest(
                options=self.messages.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION))),
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


class ProjectsRemoveIamPolicyBindingTestBeta(
    ProjectsRemoveIamPolicyBindingTestGA):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
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

  def testBindingWithoutConditionPolicyWithCondition_CannotPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=False)
    test_project = test_util.GetTestActiveProject()
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.mock_client.projects.GetIamPolicy.Expect(
        self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource=test_project.projectId,
            getIamPolicyRequest=self.messages.GetIamPolicyRequest(
                options=self.messages.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION))),
        start_policy)
    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingIncompleteError,
        '.*Removing a binding without specifying a condition from a policy.*'):
      self.RunProjects('remove-iam-policy-binding', test_project.projectId,
                       '--role={0}'.format(remove_role),
                       '--member={0}'.format(remove_user))


class ProjectsRemoveIamPolicyBindingTestAlpha(
    ProjectsRemoveIamPolicyBindingTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
