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

"""Unit tests for ml-engine completers module."""

from googlecloudsdk.command_lib.ml_engine import flags
from tests.lib import completer_test_base
from tests.lib.surface.iam import unit_test_base


class CompletionTest(unit_test_base.BaseTest,
                     completer_test_base.CompleterBase):

  def SetUp(self):
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

  def testMlEngineIamRolesCompleter(self):
    uri = 'https://ml.googleapis.com/v1/projects/my-a-project/models/my-b-model'
    self.client.roles.QueryGrantableRoles.Expect(
        request=self.msgs.QueryGrantableRolesRequest(
            fullResourceName=uri[6:].replace('/v1/', '/'),
            pageSize=100),
        response=self.roles_response,
    )

    self.RunCompleter(
        flags.MlEngineIamRolesCompleter,
        expected_command=[
            'beta',
            'iam',
            'list-grantable-roles',
            '--quiet',
            '--flatten=name',
            '--format=disable',
            uri,
        ],
        expected_completions=['roles/viewer', 'roles/compute.networkViewer'],
        cli=self.cli,
        args={
            '--model': uri,
            '--project': 'my-a-project',
        },
    )


if __name__ == '__main__':
  completer_test_base.main()
