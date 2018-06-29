# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests that ensure deserialization of server responses work properly."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class ListTest(unit_test_base.BaseTest):

  def testEmptyResponse(self):
    self.client.organizations_roles.List.Expect(
        request=self.msgs.IamOrganizationsRolesListRequest(
            parent='organizations/1', showDeleted=False, pageSize=100),
        response=self.msgs.ListRolesResponse(roles=[]))

    self.Run('iam roles list --organization 1')

  def testListCuratedRoles(self):
    self.client.roles.List.Expect(
        request=self.msgs.IamRolesListRequest(showDeleted=False, pageSize=100),
        response=self.msgs.ListRolesResponse(roles=[
            self.msgs.Role(
                name='roles/customEditor',
                description='A customEditor role.',
                title='Custom Project Editor'),
            self.msgs.Role(
                name='roles/viewer',
                description='A viewer role.',
                title='Custom Project Viewer'),
        ]))

    self.Run('iam roles list')

    self.AssertOutputContains('roles/customEditor')
    self.AssertOutputContains('title: Custom Project Editor')
    self.AssertOutputContains('description: A customEditor role.')

    self.AssertOutputContains('roles/viewer')
    self.AssertOutputContains('title: Custom Project Viewer')
    self.AssertOutputContains('description: A viewer role.')

  def testPopulatedResponse(self):
    self.client.organizations_roles.List.Expect(
        request=self.msgs.IamOrganizationsRolesListRequest(
            parent='organizations/1', showDeleted=True, pageSize=100),
        response=self.msgs.ListRolesResponse(roles=[
            self.msgs.Role(
                name='organizations/1/roles/customEditor',
                description='A customEditor role.',
                title='Custom Project Editor'),
            self.msgs.Role(
                name='organizations/1/roles/viewer',
                description='A viewer role.',
                title='Custom Project Viewer'),
        ]))

    self.Run('iam roles list --organization 1 --show-deleted')

    self.AssertOutputContains('organizations/1/roles/customEditor')
    self.AssertOutputContains('title: Custom Project Editor')
    self.AssertOutputContains('description: A customEditor role.')

    self.AssertOutputContains('organizations/1/roles/viewer')
    self.AssertOutputContains('title: Custom Project Viewer')
    self.AssertOutputContains('description: A viewer role.')

  def testLimitedResponse(self):
    self.client.organizations_roles.List.Expect(
        request=self.msgs.IamOrganizationsRolesListRequest(
            parent='organizations/1', showDeleted=False, pageSize=1),
        response=self.msgs.ListRolesResponse(roles=[
            self.msgs.Role(
                name='organizations/1/roles/customEditor',
                description='A customEditor role.',
                title='Custom Project Editor'),
            self.msgs.Role(
                name='organizations/1/roles/viewer',
                description='A viewer role.',
                title='Custom Project Viewer'),
        ]))

    self.Run('iam roles list --organization 1 --limit 1')

    self.AssertOutputContains('organizations/1/roles/customEditor')
    self.AssertOutputContains('title: Custom Project Editor')
    self.AssertOutputContains('description: A customEditor role.')

    self.AssertOutputNotContains('organizations/1/roles/viewer')
    self.AssertOutputNotContains('title: Custom Project Viewer')
    self.AssertOutputNotContains('description: A viewer role.')

  def testFilteredResponse(self):
    self.client.organizations_roles.List.Expect(
        request=self.msgs.IamOrganizationsRolesListRequest(
            parent='organizations/1', showDeleted=False, pageSize=100),
        response=self.msgs.ListRolesResponse(roles=[
            self.msgs.Role(
                name='organizations/1/roles/customEditor',
                description='A customEditor role.',
                title='Custom Project Editor'),
            self.msgs.Role(
                name='organizations/1/roles/viewer',
                description='A viewer role.',
                title='Custom Project Viewer'),
        ]))

    self.Run('iam roles list --organization 1 --filter=name:*viewer')

    self.AssertOutputNotContains('organizations/1/roles/customEditor')
    self.AssertOutputNotContains('title: Custom Project Editor')
    self.AssertOutputNotContains('description: A customEditor role.')

    self.AssertOutputContains('organizations/1/roles/viewer')
    self.AssertOutputContains('title: Custom Project Viewer')
    self.AssertOutputContains('description: A viewer role.')

  def testBadLength(self):
    with self.AssertRaisesArgumentError():
      self.Run('iam roles list --organization 1 --limit 0')
    with self.AssertRaisesArgumentError():
      self.Run('iam roles list --organization 1 --limit -1')

  def testInvalidArgument(self):
    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run('iam roles list --organization 123 --project myproject')


if __name__ == '__main__':
  test_case.main()
