# -*- coding: utf-8 -*- #
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

"""Unit tests for genomics completers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.genomics import completers
from tests.lib import completer_test_base
from tests.lib.surface.iam import unit_test_base


class GenomicsIamRolesAccountsCompletionTest(unit_test_base.BaseTest,
                                             completer_test_base.CompleterBase):

  def SetUp(self):
    roles = [
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
    self.roles_response = self.msgs.QueryGrantableRolesResponse(roles=roles)

  def testGenomicsIamRolesCompletion(self):
    self.client.roles.QueryGrantableRoles.Expect(
        request=self.msgs.QueryGrantableRolesRequest(
            fullResourceName=(
                '//genomics.googleapis.com/datasets/my-x-dataset'),
            pageSize=100),
        response=self.roles_response,
    )

    self.RunCompleter(
        completers.GenomicsIamRolesCompleter,
        expected_command=[
            'beta',
            'iam',
            'list-grantable-roles',
            '--quiet',
            '--flatten=name',
            '--format=disable',
            'https://genomics.googleapis.com/v1/datasets/my-x-dataset',
        ],
        expected_completions=['roles/viewer', 'roles/compute.networkViewer'],
        cli=self.cli,
        args={
            'id': 'https://genomics.googleapis.com/v1/datasets/my-x-dataset',
        },
    )


if __name__ == '__main__':
  completer_test_base.main()
