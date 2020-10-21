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

"""Tests for organizations remove-iam-policy-binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import test_case
from tests.lib.surface.organizations import testbase


class OrganizationsRemoveIamPolicyBindingGA(testbase.OrganizationsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

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
                               version=
                               iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)

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
        'Organizations instance [BAD_ID] not found: Resource not found.'):
      self.DoRequest()

  def testRemoveIamPolicyBindingOrganization_raisesOrganizationsAccessError(
      self):
    self.SetupGetIamPolicyFailure(self.HTTP_403_ERR)
    with self.AssertRaisesHttpExceptionMatches(
        'User [{}] does not have permission to access organizations instance [SECRET_ID] '
        '(or it may not exist): Permission denied.'.format(
            self.FakeAuthAccount())):
      self.DoRequest()

  def ExpectedGetRequest(self):
    return self.messages.CloudresourcemanagerOrganizationsGetIamPolicyRequest(
        organizationsId=self.TEST_ORGANIZATION.name[len('organizations/'):],
        getIamPolicyRequest=self.messages.GetIamPolicyRequest(
            options=self.messages.GetPolicyOptions(
                requestedPolicyVersion=
                iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)))

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


class OrganizationsRemoveIamPolicyBindingBeta(
    OrganizationsRemoveIamPolicyBindingGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class OrganizationsRemoveIamPolicyBindingAlpha(
    OrganizationsRemoveIamPolicyBindingBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
