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
"""Tests for asset utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.asset import utils
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case


class AssetUtilsTest(cli_test_base.CliTestBase, parameterized.TestCase):

  def testVerifyParentForExport_Conflicting(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.ConflictingArgumentsException,
        '.*arguments not allowed simultaneously.*'):
      utils.VerifyParentForExport('org_id', 'project_id', None)
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.ConflictingArgumentsException,
        '.*arguments not allowed simultaneously.*'):
      utils.VerifyParentForExport('org_id', None, 'folder_id')
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.ConflictingArgumentsException,
        '.*arguments not allowed simultaneously.*'):
      utils.VerifyParentForExport(None, 'project_id', 'folder_id')
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.ConflictingArgumentsException,
        '.*arguments not allowed simultaneously.*'):
      utils.VerifyParentForExport('org_id', 'project_id', 'folder_id')

  def testVerifyParentForGetHistory_Conflicting(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.ConflictingArgumentsException,
        '.*arguments not allowed simultaneously.*'):
      utils.VerifyParentForGetHistory('org_id', 'project_id')

  def testVerifyParentForExport_Missing(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.RequiredArgumentException,
        '.*Should specify the organization, or project, or the folder.*'):
      utils.VerifyParentForExport(None, None, None)

  def testVerifyParentForGetHistory_Missing(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.RequiredArgumentException,
        '.*Should specify the organization, or project for.*'):
      utils.VerifyParentForGetHistory(None, None)

  @parameterized.parameters(('org_id', None, None), (None, 'project_id', None),
                            (None, None, 'folder_id'))
  def testVerifyParentForExport_Normal(self, org_id, project_id, folder_id):
    utils.VerifyParentForExport(org_id, project_id, folder_id)

  @parameterized.parameters(('org_id', None), (None, 'project_id'))
  def testVerifyParentForGetHistory_Normal(self, org_id, project_id):
    utils.VerifyParentForGetHistory(org_id, project_id)

  def testGetParentNameForExport_Organization(self):
    self.assertEqual(
        utils.GetParentNameForExport('org_id', None, None),
        'organizations/org_id')

  def testGetParentNameForExport_Project(self):
    self.assertEqual(
        utils.GetParentNameForExport(None, 'project_id', None),
        'projects/project_id')

  def testGetParentNameForExport_Folder(self):
    self.assertEqual(
        utils.GetParentNameForExport(None, None, 'folder_id'),
        'folders/folder_id')

  def testGetParentNameForGetHistory_Organization(self):
    self.assertEqual(
        utils.GetParentNameForGetHistory('org_id', None),
        'organizations/org_id')

  def testGetParentNameForGetHistory_Project(self):
    self.assertEqual(
        utils.GetParentNameForGetHistory(None, 'project_id'),
        'projects/project_id')

  def testVerifyScopeForSearch_OneLevel(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.InvalidArgumentException,
        '.*A valid scope should be.*'):
      utils.VerifyScopeForSearch('projects123')

  def testVerifyScopeForSearch_ThreeLevel(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.InvalidArgumentException,
        '.*A valid scope should be.*'):
      utils.VerifyScopeForSearch('abc/def/123')

  def testVerifyScopeForSearch_Prefix(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.InvalidArgumentException,
        '.*A valid scope should be.*'):
      utils.VerifyScopeForSearch('/projects/123')

  def testVerifyScopeForSearch_Suffix(self):
    with self.AssertRaisesExceptionRegexp(
        gcloud_exceptions.InvalidArgumentException,
        '.*A valid scope should be.*'):
      utils.VerifyScopeForSearch('projects/123/')

  @parameterized.parameters(('organizations/123'), ('folders/1234'),
                            ('projects/12345'), ('projects/abc'), ('123/456'))
  def testVerifyScopeForSearch_Normal(self, scope):
    utils.VerifyScopeForSearch(scope)

if __name__ == '__main__':
  test_case.main()
