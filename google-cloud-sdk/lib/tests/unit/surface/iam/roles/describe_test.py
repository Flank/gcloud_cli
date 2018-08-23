# -*- coding: utf-8 -*- #
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

"""Tests that ensure describe role command work properly."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.exceptions import RequiredArgumentException
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class DescribeTest(unit_test_base.BaseTest):

  def testDescribeCuratedRoles(self):
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(name='roles/viewer'),
        response=self.msgs.Role(
            description='Read access to all resources.',
            name='roles/viewer',
            title='Viewer',))
    self.Run('iam roles describe roles/viewer')

    self.AssertOutputContains('name: roles/viewer')
    self.AssertOutputContains('title: Viewer')
    self.AssertOutputContains('description: Read access to all resources.')
    self.AssertOutputContains('stage: ALPHA')

  def testDescribeCustomRoles(self):
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(
            name='organizations/819542162391/roles/customEditor'),
        response=self.msgs.Role(
            name='organizations/819542162391/roles/customEditor',
            description='A customEditor role.',
            includedPermissions=[
                'resourcemanager.projects.create',
                'resourcemanager.projects.delete'
            ],
            title='Custom Project Editor'))
    self.Run('iam roles describe --organization 819542162391 customEditor')

    self.AssertOutputContains('name: organizations/819542162391/'
                              'roles/customEditor')
    self.AssertOutputContains('title: Custom Project Editor')
    self.AssertOutputContains('description: A customEditor role.')
    self.AssertOutputContains('stage: ALPHA')
    self.AssertOutputContains('includedPermissions:')
    self.AssertOutputContains('resourcemanager.projects.create')
    self.AssertOutputContains('resourcemanager.projects.delete')

  def testDescribeCustomProjectRoles(self):
    self.client.organizations_roles.Get.Expect(
        request=self.msgs.IamOrganizationsRolesGetRequest(
            name='projects/myproject/roles/customEditor'),
        response=self.msgs.Role(
            name='projects/myproject/roles/customEditor',
            description='A customEditor role.',
            includedPermissions=[
                'resourcemanager.projects.create',
                'resourcemanager.projects.delete'
            ],
            title='Custom Project Editor'))
    self.Run('iam roles describe --project myproject customEditor')

    self.AssertOutputContains('name: projects/myproject/roles/customEditor')
    self.AssertOutputContains('title: Custom Project Editor')
    self.AssertOutputContains('description: A customEditor role.')
    self.AssertOutputContains('stage: ALPHA')

  def testInvalidArgument(self):
    with self.assertRaises(RequiredArgumentException):
      self.Run('iam roles describe viewer')

    self.AssertErrContains(
        'Missing required argument [--organization or --project]: Should '
        'specify the project or organization name for custom roles')


if __name__ == '__main__':
  test_case.main()
