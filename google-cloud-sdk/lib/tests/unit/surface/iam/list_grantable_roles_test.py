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

"""Tests that ensure list grantable roles works properly."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class ListGrantableRolesTest(unit_test_base.BaseTest):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.returned_roles = [
        self.msgs.Role(
            description='Read access to all resources.',
            name='roles/viewer',
            title='Viewer',
        ),
        self.msgs.Role(
            description='Read-only access to GCE networking resources.',
            name='roles/compute.networkViewer',
            title='Compute Network Viewer',
        ),
    ]
    self.roles_response = self.msgs.QueryGrantableRolesResponse(
        roles=self.returned_roles)

  def testListRolesByFullResource(self):
    self.client.roles.QueryGrantableRoles.Expect(
        request=self.msgs.QueryGrantableRolesRequest(
            fullResourceName=('//compute.googleapis.com/projects/dummy_project'
                              '/zones/us-central1-f/instances/dummy_instance'),
            pageSize=100),
        response=self.roles_response,)

    roles_result = self.Run(
        'iam list-grantable-roles '
        '//compute.googleapis.com/projects/dummy_project'
        '/zones/us-central1-f/instances/dummy_instance')
    self.assertEqual(roles_result, self.returned_roles)

  def testListRolesByURI(self):
    self.client.roles.QueryGrantableRoles.Expect(
        request=self.msgs.QueryGrantableRolesRequest(
            fullResourceName=('//compute.googleapis.com/projects/dummy_project'
                              '/zones/us-central1-f/instances/dummy_instance'),
            pageSize=100),
        response=self.roles_response,)

    roles_result = self.Run(
        'iam list-grantable-roles '
        'https://www.googleapis.com/compute/v1/projects/dummy_project'
        '/zones/us-central1-f/instances/dummy_instance')
    self.assertEqual(roles_result, self.returned_roles)

  def testListRolesByURIForProject(self):
    self.client.roles.QueryGrantableRoles.Expect(
        request=self.msgs.QueryGrantableRolesRequest(
            fullResourceName=(
                '//cloudresourcemanager.googleapis.com/projects/foo'),
            pageSize=100),
        response=self.roles_response,)

    roles_result = self.Run(
        'iam list-grantable-roles '
        'https://cloudresourcemanager.googleapis.com/v1/projects/foo')
    self.assertEqual(roles_result, self.returned_roles)

  def testListRolesWithFilter(self):
    self.client.roles.QueryGrantableRoles.Expect(
        request=self.msgs.QueryGrantableRolesRequest(
            fullResourceName=('//compute.googleapis.com/projects/dummy_project'
                              '/zones/us-central1-f/instances/dummy_instance'),
            pageSize=100),
        response=self.roles_response,)

    roles_result = self.Run(
        'iam list-grantable-roles '
        '//compute.googleapis.com/projects/dummy_project'
        '/zones/us-central1-f/instances/dummy_instance --filter GCE')
    self.assertEqual(roles_result, self.returned_roles)

  def testListRolesWithPageSize(self):
    self.client.roles.QueryGrantableRoles.Expect(
        request=self.msgs.QueryGrantableRolesRequest(
            fullResourceName=('//compute.googleapis.com/projects/dummy_project'
                              '/zones/us-central1-f/instances/dummy_instance'),
            pageSize=200),
        response=self.roles_response,)

    roles_result = self.Run(
        'iam list-grantable-roles '
        '//compute.googleapis.com/projects/dummy_project'
        '/zones/us-central1-f/instances/dummy_instance --page-size 200')
    self.assertEqual(roles_result, self.returned_roles)

  def testInvalidInput(self):
    with self.assertRaises(exceptions.InvalidResourceException):
      self.Run('iam list-grantable-roles '
               'googleapis.com/v1beta1/projects/foo')


if __name__ == '__main__':
  test_case.main()
