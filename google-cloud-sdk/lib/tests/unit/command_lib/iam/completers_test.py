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

"""Tests for the IAM completers module."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.command_lib.iam import completers
from tests.lib import completer_test_base
from tests.lib import completer_test_data
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class _IamRoleCompleter(completers.IamRolesCompleter):

  def __init__(self, **kwargs):
    super(_IamRoleCompleter, self).__init__(
        resource_collection='compute.instances',
        resource_dest='instance',
        **kwargs)


_COMMAND_RESOURCES = {
    'beta.iam.list-grantable-roles':
    [role.name for role in completer_test_data.IAM_GRANTABLE_ROLES],
}

_ARGS = {
    'instance': completer_test_data.INSTANCE_URIS[0],
}


class IamRolesCompleterTest(completer_test_base.CompleterBase):

  def testIamRolesCompleter(self):
    completer = self.Completer(_IamRoleCompleter,
                               args=_ARGS,
                               command_resources=_COMMAND_RESOURCES)

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


class IamServiceAccountsCompleterTest(unit_test_base.BaseTest,
                                      completer_test_base.CompleterBase):

  def testIamServiceAccountCompleter(self):
    self.client.projects_serviceAccounts.List.Expect(
        request=self.msgs.IamProjectsServiceAccountsListRequest(
            name='projects/test-project',
            pageSize=100),
        response=self.msgs.ListServiceAccountsResponse(accounts=[
            self.msgs.ServiceAccount(
                displayName='Test Account',
                email='test@test-project.iam.gserviceaccount.com',
                uniqueId='000000001',
                projectId=self.Project()),
            self.msgs.ServiceAccount(
                displayName='Example Account',
                email='example@test-project.iam.gserviceaccount.com',
                uniqueId='000000002',
                projectId=self.Project()),
        ]))

    self.RunCompleter(
        completers.IamServiceAccountCompleter,
        expected_command=[
            'iam',
            'service-accounts',
            'list',
            '--quiet',
            '--flatten=email',
            '--format=disable',
        ],
        expected_completions=[
            'example@test-project.iam.gserviceaccount.com',
            'test@test-project.iam.gserviceaccount.com',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
