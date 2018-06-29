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

"""Tests that ensure list testable permissions works properly."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class ListTestablePermissionsTest(unit_test_base.BaseTest):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.permissions = [
        self.msgs.Permission(
            name='appengine.applications.create',),
        self.msgs.Permission(
            name='appengine.applications.get',),
    ]
    self.response = self.msgs.QueryTestablePermissionsResponse(
        permissions=self.permissions)

  def testListPermissionsByFullResource(self):
    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=('//compute.googleapis.com/projects/dummy_project'
                              '/zones/us-central1-f/instances/dummy_instance'),
            pageSize=100),
        response=self.response,)

    result = self.Run('iam list-testable-permissions '
                      '//compute.googleapis.com/projects/dummy_project'
                      '/zones/us-central1-f/instances/dummy_instance')
    self.assertEqual(result, self.permissions)

  def testListPermissionsByURI(self):
    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=('//compute.googleapis.com/projects/dummy_project'
                              '/zones/us-central1-f/instances/dummy_instance'),
            pageSize=100),
        response=self.response,)

    result = self.Run(
        'iam list-testable-permissions '
        'https://www.googleapis.com/compute/v1/projects/dummy_project'
        '/zones/us-central1-f/instances/dummy_instance')
    self.assertEqual(result, self.permissions)

  def testListPermissionsByURIForProject(self):
    self.client.permissions.QueryTestablePermissions.Expect(
        request=self.msgs.QueryTestablePermissionsRequest(
            fullResourceName=(
                '//cloudresourcemanager.googleapis.com/projects/foo'),
            pageSize=100),
        response=self.response,)
    result = self.Run(
        'iam list-testable-permissions '
        'https://cloudresourcemanager.googleapis.com/v1beta1/projects/foo')
    self.assertEqual(result, self.permissions)

  def testInvalidInput(self):
    with self.assertRaises(exceptions.InvalidResourceException):
      self.Run('iam list-testable-permissions '
               'googleapis.com/v1beta1/projects/foo')


if __name__ == '__main__':
  test_case.main()
