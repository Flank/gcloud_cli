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
"""Tests that ensure create role command work properly."""

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core.console import console_io
from tests.lib.surface.iam import unit_test_base


class CreateTest(unit_test_base.BaseTest):

  def testCreateWithFile(self):
    role = self.msgs.Role(
        description='Access to delete GCP projects.',
        title='Viewer',
        stage=iam_util.StageTypeFromString('alpha'),
        includedPermissions=[
            'resourcemanager.projects.list', 'resourcemanager.projects.get',
            'resourcemanager.projects.delete'
        ],)
    role_res = self.msgs.Role(
        name='organizations/1/roles/viewer',
        description='Access to delete GCP projects.',
        title='Viewer',
        includedPermissions=[
            'resourcemanager.projects.list', 'resourcemanager.projects.get',
            'resourcemanager.projects.delete'
        ],)

    self.client.organizations_roles.Create.Expect(
        request=self.msgs.IamOrganizationsRolesCreateRequest(
            createRoleRequest=self.msgs.CreateRoleRequest(
                role=role, roleId='viewer'),
            parent='organizations/1'),
        response=role_res)

    in_file = self.MockFileRead(
        'title: "Viewer"\n'
        'description: "Access to delete GCP projects."\n'
        'stage: "alpha"\n'
        'includedPermissions:\n'
        '- resourcemanager.projects.list\n'
        '- resourcemanager.projects.get\n'
        '- resourcemanager.projects.delete')
    result = self.Run(
        'iam roles create viewer --organization 1 --file={0} --quiet'
        .format(in_file))

    self.assertEqual(result, role_res)
    self.AssertOutputContains('stage: ALPHA')

  def testCreateWithFlags(self):
    role = self.msgs.Role(
        description='Access to delete GCP projects.',
        title='Viewer',
        stage=iam_util.StageTypeFromString('alpha'),
        includedPermissions=[
            'resourcemanager.projects.list', 'resourcemanager.projects.get',
            'resourcemanager.projects.delete'
        ],)

    role_res = self.msgs.Role(
        name='organizations/1/roles/viewer',
        description='Access to delete GCP projects.',
        title='Viewer',
        includedPermissions=[
            'resourcemanager.projects.list', 'resourcemanager.projects.get',
            'resourcemanager.projects.delete'
        ],)

    self.client.organizations_roles.Create.Expect(
        request=self.msgs.IamOrganizationsRolesCreateRequest(
            createRoleRequest=self.msgs.CreateRoleRequest(
                role=role, roleId='viewer'),
            parent='organizations/1'),
        response=role_res)

    result = self.Run('iam roles create viewer --organization 1 --quiet '
                      '--permissions resourcemanager.projects.list,'
                      'resourcemanager.projects.get,'
                      'resourcemanager.projects.delete --stage alpha '
                      '--title Viewer '
                      '--description="Access to delete GCP projects." ')

    self.assertEqual(result, role_res)
    self.AssertOutputContains('stage: ALPHA')

  def testReplyingYesToTestingPermissionsWarning(self):
    self.WriteInput('y\n')
    role = self.msgs.Role(
        description='Access to delete GCP projects.',
        title='Viewer',
        stage=iam_util.StageTypeFromString('alpha'),
        includedPermissions=[
            'resourcemanager.projects.list', 'resourcemanager.projects.get',
            'resourcemanager.projects.delete'
        ],)

    role_res = self.msgs.Role(
        name='organizations/1/roles/viewer',
        description='Access to delete GCP projects.',
        title='Viewer',
        includedPermissions=[
            'resourcemanager.projects.list', 'resourcemanager.projects.get',
            'resourcemanager.projects.delete'
        ],)

    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=
            '//cloudresourcemanager.googleapis.com/organizations/1',
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

    self.client.organizations_roles.Create.Expect(
        request=self.msgs.IamOrganizationsRolesCreateRequest(
            createRoleRequest=self.msgs.CreateRoleRequest(
                role=role, roleId='viewer'),
            parent='organizations/1'),
        response=role_res)

    result = self.Run('iam roles create viewer --organization 1 '
                      '--permissions resourcemanager.projects.list,'
                      'resourcemanager.projects.get,'
                      'resourcemanager.projects.delete --stage alpha '
                      '--title Viewer '
                      '--description="Access to delete GCP projects." ')

    self.assertEqual(result, role_res)
    self.AssertOutputContains('stage: ALPHA')
    self.AssertErrContains(
        'Note: permissions [resourcemanager.projects.list] are in '
        '\'TESTING\' stage')
    self.AssertErrContains(
        'API is not enabled for permissions: [resourcemanager.projects.get]')

  def testReplyingNoToTestingPermissionsWarning(self):
    self.WriteInput('n\n')
    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=
            '//cloudresourcemanager.googleapis.com/organizations/1',
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
      self.Run('iam roles create viewer --organization 1 '
               '--permissions resourcemanager.projects.list,'
               'resourcemanager.projects.get,'
               'resourcemanager.projects.delete --stage alpha '
               '--title Viewer '
               '--description="Access to delete GCP projects." ')

    self.AssertErrContains(
        'Note: permissions [resourcemanager.projects.list] are in '
        '\'TESTING\' stage')
    self.AssertErrContains('Aborted by user.')

  def testCreateErrors(self):
    in_file = self.MockFileRead(
        'title: "Viewer"\n'
        'description: "Access to delete GCP projects."\n'
        'stage: "alpha"')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --file: At most one of --file | --description --permissions '
        '--stage --title may be specified.'):
      self.Run('iam roles create viewer --organization 1 --title Viewer '
               '--file={0}'.format(in_file))

    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run('iam roles create viewer  --title Viewer')

    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run('iam roles create viewer  --title Viewer --organization 1 '
               '--project myproject')
