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

"""Tests for organizations add-iam-policy-binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.organizations import testbase


class OrganizationsAddIamPolicyBindingTest(testbase.OrganizationsUnitTestBase):

  messages = testbase.OrganizationsUnitTestBase.messages

  NEW_ROLE = 'roles/resourcemanager.projectCreator'
  NEW_USER = 'user:fox@google.com'

  START_POLICY = messages.Policy(bindings=[
      messages.Binding(role='roles/resourcemanager.projectCreator',
                       members=['domain:foo.com']), messages.Binding(
                           role='roles/resourcemanager.organizationAdmin',
                           members=['user:admin@foo.com'])
  ],
                                 etag=b'someUniqueEtag',
                                 version=1)
  NEW_POLICY = messages.Policy(bindings=[
      messages.Binding(role='roles/resourcemanager.projectCreator',
                       members=['domain:foo.com', NEW_USER]), messages.Binding(
                           role='roles/resourcemanager.organizationAdmin',
                           members=['user:admin@foo.com'])
  ],
                               etag=b'someUniqueEtag',
                               version=1)

  def testAddIamPolicyBinding(self):
    """Test the standard use case."""
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), copy.deepcopy(self.START_POLICY))
    self.mock_client.organizations.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=self.NEW_POLICY)),
        self.NEW_POLICY)

    self.assertEqual(self.DoRequest(), self.NEW_POLICY)

  def testAddIamPolicyBindingOrganization_raisesOrganizationsNotFoundError(
      self):
    self.SetupGetIamPolicyFailure(self.HTTP_404_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'Organization [BAD_ID] not found: Resource not found.'):
      self.DoRequest()

  def testAddIamPolicyBindingOrganization_raisesOrganizationsAccessError(self):
    self.SetupGetIamPolicyFailure(self.HTTP_403_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access organization [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount())):
      self.DoRequest()

  def ExpectedGetRequest(self):
    return self.messages.CloudresourcemanagerOrganizationsGetIamPolicyRequest(
        organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
        getIamPolicyRequest=self.messages.GetIamPolicyRequest())

  def SetupGetIamPolicyFailure(self, exception):
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(),
        exception=exception)

  def DoRequest(self):
    return self.RunOrganizations(
        'add-iam-policy-binding',
        self.TEST_ORGANIZATION.name[len('organizations/'):],
        '--role={0}'.format(self.NEW_ROLE),
        '--member={0}'.format(self.NEW_USER))


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
class OrganizationsAddIamPolicyBindingWithConditionTest(
    testbase.OrganizationsUnitTestBase):

  def SetUp(self):
    self.messages = testbase.OrganizationsUnitTestBase.messages

    self.start_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                members=['user:test@gmail.com'],
                role='roles/non-primitive',
                condition=self.messages.Expr(
                    expression='expr', title='title', description='descr')),
        ],
        etag=b'someUniqueEtag',
        version=1)
    self.test_org_id = self.TEST_ORGANIZATION.name[len('organizations/'):]

  def testPromptForExistingCondition(self, track):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    new_role = 'roles/another-non-primitive'
    new_user = 'user:owner@google.com'
    start_policy = copy.deepcopy(self.start_policy)
    new_policy = copy.deepcopy(start_policy)
    new_condition = self.messages.Expr(
        expression='expr', title='title', description='descr')
    new_policy.bindings.append(
        self.messages.Binding(
            members=['user:owner@google.com'],
            role='roles/another-non-primitive',
            condition=new_condition))
    self.WriteInput('1')
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), copy.deepcopy(self.start_policy))
    self.mock_client.organizations.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.test_org_id,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunAddIamPolicyBinding(
        self.test_org_id,
        '--role={0}'.format(new_role),
        '--member={0}'.format(new_user),
        track=track)
    self.assertEqual(response, new_policy)
    self.AssertErrContains('The policy contains bindings with conditions')

  def testPromptForNewCondition(self, track):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    new_role = 'roles/another-non-primitive'
    new_user = 'user:owner@google.com'
    start_policy = copy.deepcopy(self.start_policy)
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
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), copy.deepcopy(start_policy))
    self.mock_client.organizations.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.test_org_id,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunAddIamPolicyBinding(
        self.test_org_id,
        '--role={0}'.format(new_role),
        '--member={0}'.format(new_user),
        track=track)
    self.assertEqual(response, new_policy)
    self.AssertErrContains('The policy contains bindings with conditions')
    self.AssertErrContains('Condition is either `None`')

  def testPromptForNewCondition_Condition_And_PrimitiveRole(self, track):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    new_role = 'roles/editor'
    new_user = 'user:owner@google.com'
    start_policy = self.start_policy
    self.WriteInput('3')
    self.WriteInput('expression=expr,title=title,description=descr')
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), start_policy)

    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingInvalidError,
        '.*Binding with a condition and a primitive role is not allowed.*'):
      self.RunAddIamPolicyBinding(
          self.test_org_id,
          '--role={0}'.format(new_role),
          '--member={0}'.format(new_user),
          track=track)

  def testPromptForCondition_CannotPrompt(self, track):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=False)
    new_role = 'roles/another-non-primitive'
    new_user = 'user:owner@google.com'
    start_policy = self.start_policy
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), start_policy)

    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingIncompleteError,
        '.*Adding a binding without specifying a condition to a policy.*'):
      self.RunAddIamPolicyBinding(
          self.test_org_id,
          '--role={0}'.format(new_role),
          '--member={0}'.format(new_user),
          track=track)

  def ExpectedGetRequest(self):
    return self.messages.CloudresourcemanagerOrganizationsGetIamPolicyRequest(
        organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
        getIamPolicyRequest=self.messages.GetIamPolicyRequest())

  def RunAddIamPolicyBinding(self, *args, **kwargs):
    command = ['organizations', 'add-iam-policy-binding']
    command.extend(args)
    track = kwargs.get('track')
    return self.Run(command, track=track)


if __name__ == '__main__':
  test_case.main()
