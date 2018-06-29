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

"""Tests that ensure delete role command work properly."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class DeleteTest(unit_test_base.BaseTest):

  def testDeleteRoles(self):
    self.client.organizations_roles.Delete.Expect(
        request=self.msgs.IamOrganizationsRolesDeleteRequest(
            name='organizations/819542162391/roles/customEditor'),
        response=self.msgs.Role(
            name='organizations/819542162391/roles/customEditor',
            description='A customEditor role.',
            includedPermissions=[
                'resourcemanager.projects.create',
                'resourcemanager.projects.delete'
            ],
            stage=iam_util.StageTypeFromString('alpha'),
            title='Custom Project Editor'))
    self.Run('iam roles delete --organization 819542162391 customEditor')

    self.AssertOutputContains('name: organizations/819542162391/'
                              'roles/customEditor')
    self.AssertOutputContains('title: Custom Project Editor')
    self.AssertOutputContains('description: A customEditor role.')
    self.AssertOutputContains('stage: ALPHA')
    self.AssertOutputContains('includedPermissions:')
    self.AssertOutputContains('resourcemanager.projects.create')
    self.AssertOutputContains('resourcemanager.projects.delete')

  def testInvalidArgument(self):
    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run('iam roles delete viewer')
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('iam roles delete roles/viewer')

if __name__ == '__main__':
  test_case.main()
