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

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class OrgPoliciesListTest(testbase.OrgPoliciesUnitTestBase):

  UNSET_CONSTRAINT = 'constraints/serviceZ.unsetConstraint'

  def testListOrgPolicies(self):
    self.mock_projects.ListOrgPolicies.Expect(
        self.ExpectedListRequest(self.PROJECT_ARG), self.ExpectedListResponse())
    self.mock_organizations.ListOrgPolicies.Expect(
        self.ExpectedListRequest(self.ORG_ARG), self.ExpectedListResponse())
    self.mock_folders.ListOrgPolicies.Expect(
        self.ExpectedListRequest(self.FOLDER_ARG), self.ExpectedListResponse())
    self.assertEqual(
        list(self.DoRequest(self.PROJECT_ARG)), self.ExpectedCommandResponse())
    self.assertEqual(
        list(self.DoRequest(self.ORG_ARG)), self.ExpectedCommandResponse())
    self.assertEqual(
        list(self.DoRequest(self.FOLDER_ARG)), self.ExpectedCommandResponse())
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments:\n  --No-SuCh-FlAg\n  no-such-flag'):
      self.DoRequest(self.WRONG_ARG)

  def testListOrgPoliciesShowUnset(self):
    self.mock_projects.ListOrgPolicies.Expect(
        self.ExpectedListRequest(self.PROJECT_ARG), self.ExpectedListResponse())
    self.mock_projects.ListAvailableOrgPolicyConstraints.Expect(
        self.ExpectedListConstraintsRequest(self.PROJECT_ARG),
        self.ExpectedListConstraintsResponse())

    self.mock_organizations.ListOrgPolicies.Expect(
        self.ExpectedListRequest(self.ORG_ARG), self.ExpectedListResponse())
    self.mock_organizations.ListAvailableOrgPolicyConstraints.Expect(
        self.ExpectedListConstraintsRequest(self.ORG_ARG),
        self.ExpectedListConstraintsResponse())

    self.mock_folders.ListOrgPolicies.Expect(
        self.ExpectedListRequest(self.FOLDER_ARG), self.ExpectedListResponse())
    self.mock_folders.ListAvailableOrgPolicyConstraints.Expect(
        self.ExpectedListConstraintsRequest(self.FOLDER_ARG),
        self.ExpectedListConstraintsResponse())

    self.assertEqual(
        list(self.DoRequestShowUnset(self.PROJECT_ARG)),
        self.ExpectedCommandResponseShowUnset())
    self.assertEqual(
        list(self.DoRequestShowUnset(self.ORG_ARG)),
        self.ExpectedCommandResponseShowUnset())
    self.assertEqual(
        list(self.DoRequestShowUnset(self.FOLDER_ARG)),
        self.ExpectedCommandResponseShowUnset())
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments:\n  --No-SuCh-FlAg\n  no-such-flag'):
      self.DoRequestShowUnset(self.WRONG_ARG)

  def ExpectedListRequest(self, arg):
    messages = self.messages
    request = messages.ListOrgPoliciesRequest()

    if arg == self.PROJECT_ARG:
      return messages.CloudresourcemanagerProjectsListOrgPoliciesRequest(
          projectsId=self.PROJECT_ARG[1], listOrgPoliciesRequest=request)
    elif arg == self.ORG_ARG:
      return messages.CloudresourcemanagerOrganizationsListOrgPoliciesRequest(
          organizationsId=self.ORG_ARG[1], listOrgPoliciesRequest=request)
    elif arg == self.FOLDER_ARG:
      return messages.CloudresourcemanagerFoldersListOrgPoliciesRequest(
          foldersId=self.FOLDER_ARG[1], listOrgPoliciesRequest=request)

  def ExpectedListResponse(self):
    return self.messages.ListOrgPoliciesResponse(
        policies=[self.TestPolicy(), self.WhitelistPolicy([self.VALUE_A])])

  def ExpectedListConstraintsRequest(self, arg):
    msg = self.messages
    request = msg.ListAvailableOrgPolicyConstraintsRequest()

    if arg == self.PROJECT_ARG:
      # pylint: disable=line-too-long
      return msg.CloudresourcemanagerProjectsListAvailableOrgPolicyConstraintsRequest(
          projectsId=self.PROJECT_ARG[1],
          listAvailableOrgPolicyConstraintsRequest=request)
    elif arg == self.ORG_ARG:
      # pylint: disable=line-too-long
      return msg.CloudresourcemanagerOrganizationsListAvailableOrgPolicyConstraintsRequest(
          organizationsId=self.ORG_ARG[1],
          listAvailableOrgPolicyConstraintsRequest=request)
    elif arg == self.FOLDER_ARG:
      # pylint: disable=line-too-long
      return msg.CloudresourcemanagerFoldersListAvailableOrgPolicyConstraintsRequest(
          foldersId=self.FOLDER_ARG[1],
          listAvailableOrgPolicyConstraintsRequest=request)

  def ExpectedListConstraintsResponse(self):
    return self.messages.ListAvailableOrgPolicyConstraintsResponse(
        constraints=[
            self.messages.Constraint(name=self.WHITELIST_CONSTRAINT),
            self.messages.Constraint(name=self.TEST_CONSTRAINT),
            self.messages.Constraint(name=self.UNSET_CONSTRAINT),
        ])

  def ExpectedCommandResponse(self):
    return [self.TestPolicy(), self.WhitelistPolicy([self.VALUE_A])]

  def ExpectedCommandResponseShowUnset(self):
    return [
        self.TestPolicy(),
        self.WhitelistPolicy([self.VALUE_A]),
        self.messages.OrgPolicy(constraint=self.UNSET_CONSTRAINT)
    ]

  def DoRequest(self, args):
    return self.RunOrgPolicies('list', '--format=disable', *args)

  def DoRequestShowUnset(self, args):
    return self.RunOrgPolicies('list', '--show-unset', '--format=disable',
                               *args)


if __name__ == '__main__':
  test_case.main()
