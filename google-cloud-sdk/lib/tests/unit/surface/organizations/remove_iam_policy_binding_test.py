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

"""Tests for organizations remove-iam-policy-binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import json

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.organizations import testbase


class OrganizationsRemoveIamPolicyBindingTest(
    testbase.OrganizationsUnitTestBase):

  messages = testbase.OrganizationsUnitTestBase.messages

  REMOVE_USER = 'user:admin@foo.com'
  REMOVE_ROLE = 'roles/resourcemanager.organizationAdmin'
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
                       members=['domain:foo.com'])
  ],
                               etag=b'someUniqueEtag',
                               version=1)

  def testRemoveIamPolicyBinding(self):
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

  def testRemoveIamPolicyBindingOrganization_raisesOrganizationsNotFoundError(
      self):
    self.SetupGetIamPolicyFailure(self.HTTP_404_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'Organization [BAD_ID] not found: Resource not found.'):
      self.DoRequest()

  def testRemoveIamPolicyBindingOrganization_raisesOrganizationsAccessError(
      self):
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
        'remove-iam-policy-binding',
        self.TEST_ORGANIZATION.name[len('organizations/'):],
        '--role={0}'.format(self.REMOVE_ROLE),
        '--member={0}'.format(self.REMOVE_USER))


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
class OrganizationsRemoveIamPolicyBindingWithConditionTest(
    testbase.OrganizationsUnitTestBase):

  def SetUp(self):
    self.messages = testbase.OrganizationsUnitTestBase.messages
    self.test_iam_policy_with_condition = self.messages.Policy(
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
    self.test_org_id = self.TEST_ORGANIZATION.name[len('organizations/'):]

  def testBindingWithoutConditionPolicyWithCondition(self, track):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.WriteInput('1')
    new_policy.bindings[:] = new_policy.bindings[1:]

    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), copy.deepcopy(start_policy))
    self.mock_client.organizations.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.test_org_id,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunRemoveIamPolicyBinding(
        self.test_org_id,
        '--role={0}'.format(remove_role),
        '--member={0}'.format(remove_user),
        track=track)
    self.assertEqual(response, new_policy)
    choices_in_stderr = json.loads(self.GetErr())['choices']
    expected_choices = [
        'expression=expr,title=title,description=descr', 'None',
        'all conditions'
    ]
    self.assertEqual(choices_in_stderr, expected_choices)

  def testBindingWithoutConditionPolicyWithCondition_NoneCondition(self, track):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.WriteInput('2')
    new_policy.bindings[:] = new_policy.bindings[:1]

    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), copy.deepcopy(start_policy))
    self.mock_client.organizations.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.test_org_id,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunRemoveIamPolicyBinding(
        self.test_org_id,
        '--role={0}'.format(remove_role),
        '--member={0}'.format(remove_user),
        track=track)
    self.assertEqual(response, new_policy)
    choices_in_stderr = json.loads(self.GetErr())['choices']
    expected_choices = [
        'expression=expr,title=title,description=descr', 'None',
        'all conditions'
    ]
    self.assertEqual(choices_in_stderr, expected_choices)

  def testBindingWithoutConditionPolicyWithCondition_AllConditions(self, track):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    new_policy = copy.deepcopy(start_policy)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.WriteInput('3')
    new_policy.bindings[:] = []

    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), copy.deepcopy(start_policy))
    self.mock_client.organizations.SetIamPolicy.Expect(
        self.messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=self.test_org_id,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=new_policy)), new_policy)

    response = self.RunRemoveIamPolicyBinding(
        self.test_org_id,
        '--role={0}'.format(remove_role),
        '--member={0}'.format(remove_user),
        track=track)
    self.assertEqual(response, new_policy)
    choices_in_stderr = json.loads(self.GetErr())['choices']
    expected_choices = [
        'expression=expr,title=title,description=descr', 'None',
        'all conditions'
    ]
    self.assertEqual(choices_in_stderr, expected_choices)

  def testBindingWithoutConditionPolicyWithCondition_CannotPrompt(self, track):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=False)
    start_policy = copy.deepcopy(self.test_iam_policy_with_condition)
    remove_user = 'user:test@gmail.com'
    remove_role = 'roles/non-primitive'
    self.mock_client.organizations.GetIamPolicy.Expect(
        self.ExpectedGetRequest(), copy.deepcopy(start_policy))
    with self.AssertRaisesExceptionRegexp(
        iam_util.IamPolicyBindingIncompleteError,
        '.*Removing a binding without specifying a condition from a policy.*'):
      self.RunRemoveIamPolicyBinding(
          self.test_org_id,
          '--role={0}'.format(remove_role),
          '--member={0}'.format(remove_user),
          track=track)

  def ExpectedGetRequest(self):
    return self.messages.CloudresourcemanagerOrganizationsGetIamPolicyRequest(
        organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
        getIamPolicyRequest=self.messages.GetIamPolicyRequest())

  def RunRemoveIamPolicyBinding(self, *args, **kwargs):
    command = ['organizations', 'remove-iam-policy-binding']
    command.extend(args)
    track = kwargs.get('track')
    return self.Run(command, track=track)


if __name__ == '__main__':
  test_case.main()
