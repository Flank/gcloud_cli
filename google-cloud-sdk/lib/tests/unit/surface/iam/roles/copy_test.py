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

"""Tests that ensure deserialization of server responses work properly."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class CopyTest(unit_test_base.BaseTest):

  def SetUp(self):
    self.source_curated_role = self.msgs.Role(
        name='roles/viewer',
        description='Read access to all resources.',
        title='Viewer',
    )

    self.created_role = self.msgs.Role(
        description='Read access to all resources.',
        title='Viewer',
    )

    self.source_custom_role = self.msgs.Role(
        name='organizations/819542162391/roles/customEditor',
        description='A customEditor role.',
        includedPermissions=[
            'resourcemanager.projects.create', 'resourcemanager.projects.get',
            'resourcemanager.projects.list', 'resourcemanager.projects.delete',
        ],
        title='Custom Project Editor',
    )

    self.created_role_from_custom_role = self.msgs.Role(
        description='A customEditor role.',
        includedPermissions=[
            'resourcemanager.projects.create', 'resourcemanager.projects.get'
        ],
        title='Custom Project Editor',
    )

  def testCopyFromCuratedRole(self):
    self.client.organizations_roles.Get.Expect(
        self.msgs.IamOrganizationsRolesGetRequest(name='roles/viewer'),
        response=self.source_curated_role)

    self.client.organizations_roles.Create.Expect(
        self.msgs.IamOrganizationsRolesCreateRequest(
            createRoleRequest=self.msgs.CreateRoleRequest(
                role=self.created_role, roleId='viewer'),
            parent='organizations/123456'),
        response=self.created_role)

    result = self.Run('iam roles copy --source roles/viewer --destination '
                      'viewer --dest-organization 123456')

    self.AssertOutputContains('stage: ALPHA')
    self.assertEqual(result, self.created_role)

  def testReplyingYesToTestingPermissionsWarning(self):
    self.WriteInput('y\n')
    self.client.organizations_roles.Get.Expect(
        self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/819542162391/roles/customEditor'),
        response=self.source_custom_role)

    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=
            '//cloudresourcemanager.googleapis.com/organizations/123456',
            pageSize=1000),
        response=self.msgs.QueryTestablePermissionsResponse(
            permissions=[
                self.msgs.Permission(
                    name='resourcemanager.projects.create',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.TESTING),
                self.msgs.Permission(
                    name='resourcemanager.projects.list',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.NOT_SUPPORTED),
                self.msgs.Permission(
                    name='resourcemanager.projects.get',
                    apiDisabled=True),
            ],
            nextPageToken=None))

    self.client.organizations_roles.Create.Expect(
        self.msgs.IamOrganizationsRolesCreateRequest(
            createRoleRequest=self.msgs.CreateRoleRequest(
                role=self.created_role_from_custom_role, roleId='editor'),
            parent='organizations/123456'),
        response=self.created_role_from_custom_role)

    result = self.Run('iam roles copy --source customEditor '
                      '--source-organization 819542162391 --destination '
                      'editor --dest-organization 123456')

    self.assertEqual(result, self.created_role_from_custom_role)
    self.AssertErrContains(
        'Note: permissions [resourcemanager.projects.create] are in '
        '\'TESTING\' stage')
    self.AssertErrContains(
        'Permissions don\'t support custom roles and won\'t be added: '
        '[resourcemanager.projects.list]')
    self.AssertErrContains(
        'Permissions not applicable to the current resource and won\'t be '
        'added: [resourcemanager.projects.delete]')
    self.AssertErrContains(
        'API is not enabled for permissions: [resourcemanager.projects.get]')

  def testReplyingNoToTestingPermissionsWarning(self):
    self.WriteInput('n\n')
    self.client.organizations_roles.Get.Expect(
        self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/819542162391/roles/customEditor'),
        response=self.source_custom_role)

    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=
            '//cloudresourcemanager.googleapis.com/organizations/123456',
            pageSize=1000),
        response=self.msgs.QueryTestablePermissionsResponse(
            permissions=[
                self.msgs.Permission(
                    name='resourcemanager.projects.create',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.TESTING),
                self.msgs.Permission(name='resourcemanager.projects.get'),
            ],
            nextPageToken=None))

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('iam roles copy --source customEditor '
               '--source-organization 819542162391 --destination '
               'editor --dest-organization 123456')

    self.AssertErrContains(
        'Note: permissions [resourcemanager.projects.create] are in '
        '\'TESTING\' stage')
    self.AssertErrContains('Aborted by user.')

  def testCopyErrors(self):
    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run('iam roles copy --source roles/editor')

    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run(
          'iam roles copy --destination editor --dest-project project1')

    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run('iam roles copy --source editor --destination viewer '
               '--dest-organization 12345')

    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run('iam roles copy --source editor --destination viewer '
               '--source-organization 12345')


if __name__ == '__main__':
  test_case.main()
