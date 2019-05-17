# -*- coding: utf-8 -*- #
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

"""Module for integration test calliope_base classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case


def main():
  return test_case.main()


class ServiceAccountBaseTest(e2e_base.WithServiceAuth,
                             sdk_test_base.WithOutputCapture):
  """Base class for IAM service accounts integration tests."""

  def PreSetUp(self):
    self.account_name = next(e2e_utils.GetResourceNameGenerator(prefix='iam'))
    self.email = (
        '{0}@cloud-sdk-integration-testing.iam.gserviceaccount.com'.format(
            self.account_name))

  def SetUp(self):
    self.requires_cleanup = True

  def TearDown(self):
    if self.requires_cleanup:
      # TODO(b/36050343): b/26496763. Rapid deletions can lead to a server side
      # error, so any code paths which explicitly test deleting shouldn't use
      # this automatic cleanup.
      self.RunFormat('iam service-accounts delete {email}')

  def RunFormat(self, cmd, *args):
    return self.Run(cmd.format(*args, email=self.email))


class CustomRolesBaseTest(e2e_base.WithServiceAuth,
                          sdk_test_base.WithOutputCapture):
  """Base class for IAM custom roles integration tests.

  Deletion on roles whose name starts with 'iam_testing' on this testing project
  will be a hard deletion and can not be undeleted. In this class, roles with
  'iam_testing' prefix will be tested for create/copy commands and will be
  promptly cleaned up after finishing running the tests to avoid causing quota
  problem on the testing project. 'custom_role_for_delete_undelete_tests' role
  is for normal delete/undelete tests which doesn't require hard deletion
  cleanup.
  """

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.requires_cleanup = False
    self.requires_cleanup_copied_role = False
    self.requires_recover_deleted_role = False
    self.delete_undelete_tests_role = 'custom_role_for_delete_undelete_tests'

  def TearDown(self):
    if self.requires_cleanup:
      self.RunFormat('iam roles delete {role} --project {project}')
    if self.requires_cleanup_copied_role:
      self.Run('iam roles delete {role} --project {project}'.format(
          role=self.copied_role, project=self.Project()))
    if self.requires_recover_deleted_role:
      self.Run('iam roles undelete {role} --project {project}'.format(
          role=self.delete_undelete_tests_role, project=self.Project()))

  def SetRole(self):
    self.role = next(e2e_utils.GetResourceNameGenerator(
        prefix='iam_testing_customRole', delimiter='_'))

  def SetCopiedRole(self):
    self.copied_role = next(e2e_utils.GetResourceNameGenerator(
        prefix='iam_testing_copiedCustomRole', delimiter='_'))

  def SetPermissions(self, resource_type):
    self.permissions = ('example.{resource_type}.create,'
                        'example.{resource_type}.get,'
                        'example.{resource_type}.list,'
                        'example.{resource_type}.set'.format(
                            resource_type=resource_type))

  def RunFormat(self, cmd, *args):
    return self.Run(
        cmd.format(
            *args,
            role=self.role,
            project=self.Project(),
            permissions=self.permissions))

  def AssertErrContainsPermissionsWarning(self):
    self.AssertErrContains('Note: permissions')
    for permission in self.permissions.split(','):
      self.AssertErrContains(permission)

  def AssertOutputContainsRole(self, role):
    self.AssertOutputContains(role)
    self.AssertOutputContainsPermissions()

  def AssertOutputContainsPermissions(self):
    for permission in self.permissions.split(','):
      self.AssertOutputContains(permission)
