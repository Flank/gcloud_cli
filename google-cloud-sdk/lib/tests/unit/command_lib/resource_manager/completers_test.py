# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for the IAM completers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.resource_manager import completers
from tests.lib import completer_test_base
from tests.lib import completer_test_data
from tests.lib import test_case
from tests.lib.surface.organizations import testbase


_COMMAND_RESOURCES = {
    'beta.iam.list-grantable-roles':
    [role.name for role in completer_test_data.IAM_GRANTABLE_ROLES],
}


class ProjectCompleterTest(completer_test_base.CompleterBase):

  def testProjectCompleter(self):
    completer = self.Completer(completers.ProjectCompleter)
    self.assertEqual(
        completer_test_data.PROJECT_NAMES,
        completer.Complete('', self.parameter_info))


class OrganizationCompleterTest(testbase.OrganizationsUnitTestBase,
                                completer_test_base.CompleterBase):

  messages = testbase.OrganizationsUnitTestBase.messages

  TEST_ORG_1 = messages.Organization(
      name='organizations/298357488294',
      displayName='Test Organization For Testing',
      owner=messages.OrganizationOwner(directoryCustomerId='C0123n456'))
  TEST_ORG_2 = messages.Organization(
      name='organizations/309468599305',
      displayName='A Secondary Organization',
      owner=messages.OrganizationOwner(directoryCustomerId='C9876n543'))

  def testOrganizationCompleter(self):
    self.mock_client.organizations.Search.Expect(
        self.messages.SearchOrganizationsRequest(),
        self.messages.SearchOrganizationsResponse(
            organizations=[self.TEST_ORG_2, self.TEST_ORG_1]))

    self.RunCompleter(
        completers.OrganizationCompleter,
        expected_command=[
            'organizations',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=['298357488294', '309468599305'],
        cli=self.cli,
    )


class IamCompletersTest(completer_test_base.CompleterBase):

  def _CommonAssertions(self, completer):
    self.assertEqual(
        10,
        len(completer.Complete('', self.parameter_info)))
    self.assertEqual(
        [
            'roles/compute.admin',
            'roles/compute.instanceAdmin',
            'roles/compute.instanceAdmin.v1',
            'roles/compute.networkAdmin',
            'roles/compute.networkViewer',
            'roles/compute.securityAdmin',
            'roles/editor',
            'roles/iam.securityReviewer',
            'roles/owner',
            'roles/viewer',
        ],
        completer.Complete('', self.parameter_info))
    self.assertEqual(
        [
            'roles/owner',
        ],
        completer.Complete('roles/o', self.parameter_info))
    self.assertEqual(
        [],
        completer.Complete('x', self.parameter_info))


if __name__ == '__main__':
  test_case.main()
