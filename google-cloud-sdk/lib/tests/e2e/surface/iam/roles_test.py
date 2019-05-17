# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Integration tests for manipulating IAM custom roles."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.iam import e2e_test_base


# This test requires the 'Google Identity and Access Management' API to be
# enabled on the current project.
class RolesTest(e2e_test_base.CustomRolesBaseTest):

  def testRoles(self):
    self.SetRole()
    self.SetPermissions('buckets')
    self.CreateRole()
    self.DescribeRole()
    self.SetPermissions('objects')
    self.UpdateRole()
    self.ListRole()
    self.SetCopiedRole()
    self.CopyRole()
    self.ListGrantableRolesRoleAndCopiedRole()
    self.SetPermissions('buckets')
    self.DeleteRole()
    self.UndeleteRole()

  @test_case.Filters.skip('Failing', 'b/132247210')
  def testListTestablePermissions(self):
    self.SetPermissions('buckets')
    self.ClearOutputs()
    self.Run(
        'iam list-testable-permissions '
        'https://cloudresourcemanager.googleapis.com/v1/projects/{project}'.
        format(project=self.Project()))
    self.AssertOutputContainsPermissions()

  def ClearOutputs(self):
    self.ClearOutput()
    self.ClearErr()

  def CreateRole(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam roles create {role} --project {project} --permissions '
        '{permissions}'
    )
    self.requires_cleanup = True
    self.AssertErrContains('Created role [{0}].\n'.format(self.role))
    self.AssertErrContainsPermissionsWarning()
    self.AssertOutputContainsRole(self.role)

  def DescribeRole(self):
    self.ClearOutputs()
    self.RunFormat('iam roles describe {role} --project {project}')
    self.AssertOutputContainsRole(self.role)

  def UpdateRole(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam roles update {role} --project {project} --permissions '
        '{permissions}')
    self.AssertErrContainsPermissionsWarning()
    self.AssertOutputContainsRole(self.role)

    self.ClearOutputs()
    self.RunFormat('iam roles describe {role} --project {project}')
    self.AssertOutputContainsRole(self.role)

  def ListRole(self):
    self.ClearOutputs()
    self.RunFormat('iam roles list --project {project}')
    self.AssertOutputContains(self.role)

  def CopyRole(self):
    self.ClearOutputs()
    self.Run('iam roles copy --source {source} --source-project {project} '
             '--destination {destination} --dest-project {project}'.format(
                 source=self.role,
                 project=self.Project(),
                 destination=self.copied_role))
    self.requires_cleanup_copied_role = True
    self.AssertErrContainsPermissionsWarning()
    self.AssertOutputContainsRole(self.copied_role)

  def ListGrantableRolesRoleAndCopiedRole(self):
    self.ClearOutputs()
    self.RunFormat(
        'iam list-grantable-roles '
        'https://cloudresourcemanager.googleapis.com/v1/projects/{project}'
    )
    self.AssertOutputContains(self.role)
    self.AssertOutputContains(self.copied_role)

  def DeleteRole(self):
    self.ClearOutputs()
    self.Run('iam roles delete {role} --project {project}'.format(
        role=self.delete_undelete_tests_role, project=self.Project()))
    self.requires_recover_deleted_role = True
    self.AssertOutputContains('deleted: true')
    self.AssertOutputContains(self.delete_undelete_tests_role)

  def UndeleteRole(self):
    self.ClearOutputs()
    self.Run('iam roles undelete {role} --project {project}'.format(
        role=self.delete_undelete_tests_role, project=self.Project()))
    self.requires_recover_deleted_role = False
    self.AssertOutputContains(self.delete_undelete_tests_role)

if __name__ == '__main__':
  e2e_test_base.main()
