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
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class UpdateTest(unit_test_base.BaseTest):

  def SetUp(self):
    self.role_from_file = self.msgs.Role(
        description='Access to view GCP projects.',
        title='Viewer',
        etag=b'\x00',
        stage=iam_util.StageTypeFromString('alpha'),
        includedPermissions=[
            'resourcemanager.projects.get',
            'resourcemanager.projects.list',
        ],)
    self.origin_role = self.msgs.Role(
        description='Access to view GCP projects.',
        title='Viewer',
        stage=iam_util.StageTypeFromString('alpha'),
        includedPermissions=[
            'resourcemanager.projects.get',
            'resourcemanager.projects.list',
        ],)
    self.origin_role2 = self.msgs.Role(
        name='organizations/123/roles/viewer',
        description='A custom role.',
        title='Custom Project Creator',
        stage=iam_util.StageTypeFromString('beta'),
        includedPermissions=['resourcemanager.projects.get'],)
    self.updated_role = self.msgs.Role(
        description='A custom role.',
        title='Custom Project Creator',
        stage=iam_util.StageTypeFromString('beta'),
        includedPermissions=['resourcemanager.projects.create'],)
    self.res_role1 = self.msgs.Role(
        name='organizations/123/roles/viewer',
        description='Access to view GCP projects.',
        title='Viewer',
        includedPermissions=[
            'resourcemanager.projects.get',
            'resourcemanager.projects.list',
        ],)
    self.res_role2 = self.msgs.Role(
        name='organizations/123/roles/viewer',
        description='A custom role.',
        title='Custom Project Creator',
        stage=iam_util.StageTypeFromString('beta'),
        includedPermissions=['resourcemanager.projects.create'],)
    self.role_no_permissions = self.msgs.Role(
        name='organizations/123/roles/viewer',
        description='Access to view GCP projects.',
        title='Viewer',
        stage=iam_util.StageTypeFromString('alpha'),)

  def testUpdateRoleWithFile(self):
    self.client.organizations_roles.Patch.Expect(
        request=self.msgs.IamOrganizationsRolesPatchRequest(
            name='organizations/123/roles/viewer', role=self.role_from_file),
        response=self.res_role1)
    in_file = self.Touch(
        self.temp_path,
        contents='title: "Viewer"\n'
                 'etag: "AA=="\n'
                 'description: "Access to view GCP projects."\n'
                 'stage: "alpha"\n'
                 'includedPermissions:\n'
                 '- resourcemanager.projects.get\n'
                 '- resourcemanager.projects.list')
    result = self.Run(
        'iam roles update viewer --organization 123 --file={0} --quiet'.
        format(in_file))
    self.assertEqual(result, self.res_role1)

  def testUpdateRoleWithFlags(self):
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/123/roles/viewer'),
        response=self.res_role1)
    self.client.organizations_roles.Patch.Expect(
        request=self.msgs.IamOrganizationsRolesPatchRequest(
            name='organizations/123/roles/viewer',
            role=self.updated_role,
            updateMask='description,title,stage,includedPermissions'),
        response=self.res_role2)
    result = self.Run(
        'iam roles update viewer --organization 123 --title='
        "'Custom Project Creator' --description='A custom role.' "
        '--stage beta --add-permissions resourcemanager.projects.create '
        '--remove-permissions resourcemanager.projects.get,'
        'resourcemanager.projects.list --quiet')

    self.assertEqual(result, self.res_role2)

  def testUpdateRoleWithFlagsSetPermissions(self):
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/123/roles/viewer'),
        response=self.res_role2)
    self.client.organizations_roles.Patch.Expect(
        request=self.msgs.IamOrganizationsRolesPatchRequest(
            name='organizations/123/roles/viewer',
            role=self.origin_role,
            updateMask='description,title,stage,includedPermissions'),
        response=self.res_role1)
    result = self.Run(
        'iam roles update viewer --organization 123 --title='
        "'Viewer' --description='Access to view GCP projects.' "
        '--stage alpha --permissions resourcemanager.projects.get,'
        'resourcemanager.projects.list --quiet')

    self.assertEqual(result, self.res_role1)
    self.AssertOutputContains('stage: ALPHA')

  def testUpdateSetPermissionsReplyingYesToTestingPermissionsWarning(self):
    self.WriteInput('y\n')
    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=
            '//cloudresourcemanager.googleapis.com/organizations/123',
            pageSize=1000),
        response=self.msgs.QueryTestablePermissionsResponse(
            permissions=[
                self.msgs.Permission(
                    name='resourcemanager.projects.list',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.TESTING),
                self.msgs.Permission(
                    name='resourcemanager.projects.get',
                    apiDisabled=True),
            ],
            nextPageToken=None))
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/123/roles/viewer'),
        response=self.origin_role2)
    self.client.organizations_roles.Patch.Expect(
        request=self.msgs.IamOrganizationsRolesPatchRequest(
            name='organizations/123/roles/viewer',
            role=self.origin_role,
            updateMask='description,title,stage,includedPermissions'),
        response=self.res_role1)
    result = self.Run(
        'iam roles update viewer --organization 123 --title='
        "'Viewer' --description='Access to view GCP projects.' "
        '--stage alpha --permissions resourcemanager.projects.get,'
        'resourcemanager.projects.list')

    self.assertEqual(result, self.res_role1)
    self.AssertOutputContains('stage: ALPHA')
    self.AssertErrContains(
        'Note: permissions [resourcemanager.projects.list] are in '
        '\'TESTING\' stage')
    self.AssertErrContains(
        'API is not enabled for permissions: [resourcemanager.projects.get]')

  def testUpdateSetPermissionsReplyingNoToTestingPermissionsWarning(self):
    self.WriteInput('n\n')
    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=
            '//cloudresourcemanager.googleapis.com/organizations/123',
            pageSize=1000),
        response=self.msgs.QueryTestablePermissionsResponse(
            permissions=[
                self.msgs.Permission(
                    name='resourcemanager.projects.list',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.TESTING),
            ],
            nextPageToken=None))
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('iam roles update viewer --organization 123 --title='
               "'Viewer' --description='Access to view GCP projects.' "
               '--stage alpha --permissions resourcemanager.projects.get,'
               'resourcemanager.projects.list')

    self.AssertErrContains(
        'Note: permissions [resourcemanager.projects.list] are in '
        '\'TESTING\' stage')
    self.AssertErrContains('Aborted by user.')

  def testUpdateAddPermissionsReplyingYesToTestingPermissionsWarning(self):
    self.WriteInput('y\n')
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/123/roles/viewer'),
        response=self.origin_role2)
    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=
            '//cloudresourcemanager.googleapis.com/organizations/123',
            pageSize=1000),
        response=self.msgs.QueryTestablePermissionsResponse(
            permissions=[
                self.msgs.Permission(
                    name='resourcemanager.projects.get',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.TESTING),
                self.msgs.Permission(
                    name='resourcemanager.projects.list',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.TESTING),
            ],
            nextPageToken=None))
    self.client.organizations_roles.Patch.Expect(
        request=self.msgs.IamOrganizationsRolesPatchRequest(
            name='organizations/123/roles/viewer',
            role=self.origin_role,
            updateMask='description,title,stage,includedPermissions'),
        response=self.res_role1)
    result = self.Run(
        'iam roles update viewer --organization 123 --title='
        "'Viewer' --description='Access to view GCP projects.' "
        '--stage alpha --add-permissions resourcemanager.projects.get,'
        'resourcemanager.projects.list')

    self.assertEqual(result, self.res_role1)
    self.AssertOutputContains('stage: ALPHA')
    self.AssertErrContains(
        'Note: permissions [resourcemanager.projects.list] are in '
        '\'TESTING\' stage')

  def testUpdateAddPermissionsReplyingNoToTestingPermissionsWarning(self):
    self.WriteInput('n\n')
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/123/roles/viewer'),
        response=self.origin_role2)
    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=
            '//cloudresourcemanager.googleapis.com/organizations/123',
            pageSize=1000),
        response=self.msgs.QueryTestablePermissionsResponse(
            permissions=[
                self.msgs.Permission(
                    name='resourcemanager.projects.get',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.TESTING),
                self.msgs.Permission(
                    name='resourcemanager.projects.list',
                    customRolesSupportLevel=self.msgs.Permission.
                    CustomRolesSupportLevelValueValuesEnum.TESTING),
            ],
            nextPageToken=None))
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('iam roles update viewer --organization 123 --title='
               "'Viewer' --description='Access to view GCP projects.' "
               '--stage alpha --add-permissions resourcemanager.projects.get,'
               'resourcemanager.projects.list')

    self.AssertErrContains(
        'Note: permissions [resourcemanager.projects.list] are in '
        '\'TESTING\' stage')
    self.AssertErrContains('Aborted by user.')

  def testUpdateRoleWithFileConflict(self):
    self.client.organizations_roles.Patch.Expect(
        request=self.msgs.IamOrganizationsRolesPatchRequest(
            name='organizations/123/roles/viewer', role=self.role_from_file),
        exception=self.MockHttpError(409, 'Conflict'))
    in_file = self.Touch(
        self.temp_path,
        contents='title: "Viewer"\n'
                 'etag: "AA=="\n'
                 'description: "Access to view GCP projects."\n'
                 'stage: "alpha"\n'
                 'includedPermissions:\n'
                 '- resourcemanager.projects.get\n'
                 '- resourcemanager.projects.list')
    with self.assertRaises(exceptions.HttpException):
      self.Run(
          'iam roles update viewer --organization 123 --file={0} --quiet'
          .format(in_file))

  def testUpdateRoleWithEmptyPermissions(self):
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/123/roles/viewer'),
        response=self.res_role1)
    self.client.organizations_roles.Patch.Expect(
        request=self.msgs.IamOrganizationsRolesPatchRequest(
            name='organizations/123/roles/viewer',
            role=self.msgs.Role(includedPermissions=[]),
            updateMask='includedPermissions'),
        response=self.role_no_permissions)
    result = self.Run('iam roles update viewer --organization 123 '
                      "--permissions ''")

    self.assertEqual(result, self.role_no_permissions)

  def testUpdateErrors(self):
    in_file = self.Touch(
        self.temp_path,
        contents='title: "Viewer"\n'
                 'description: "Access to delete GCP projects."\n'
                 'stage: "alpha"')
    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run('iam roles update viewer')

    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run('iam roles update viewer --organization 123 --title Viewer '
               '--file={0}'.format(in_file))

    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run('iam roles update viewer --organization 123 --title Viewer '
               '--add-permissions resourcemanager.projects.delete '
               '--permissions resourcemanager.projects.list')


if __name__ == '__main__':
  test_case.main()
