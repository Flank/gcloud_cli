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
"""Tests for folders list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import exceptions
from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class FoldersListTest(testbase.FoldersUnitTestBase):

  def testNoFlagsEmptyList(self):
    self.mock_folders.List.Expect(
        self.ExpectedListRequest(),
        folders.FoldersMessages().ListFoldersResponse())
    self.DoCommand()
    self.AssertOutputEquals('', normalize_space=True)

  def testListOneFolder(self):
    self.mock_folders.List.Expect(
        self.ExpectedListRequest(),
        folders.FoldersMessages().ListFoldersResponse(
            folders=[self.TEST_FOLDER]))
    self.DoCommand()
    self.AssertOutputContains(
        """\
      DISPLAY_NAME               PARENT_NAME          ID
      Test Folder For Testing    organizations/24521  58219052
      """,
        normalize_space=True)

  def testListMultipleFoldersSortedById(self):
    self.mock_folders.List.Expect(
        self.ExpectedListRequest(),
        folders.FoldersMessages().ListFoldersResponse(
            folders=[self.ANOTHER_TEST_FOLDER, self.TEST_FOLDER]))
    self.DoCommand()
    self.AssertOutputContains(
        """\
      DISPLAY_NAME                     PARENT_NAME          ID
      Test Folder For Testing          organizations/24521  58219052
      Another Test Folder For Testing  organizations/24521  67045082
      """,
        normalize_space=True)

  def testPagination(self):
    test_token = 'next1'
    # First page
    self.mock_folders.List.Expect(
        folders.FoldersMessages().CloudresourcemanagerFoldersListRequest(
            parent=self.TEST_FOLDER.parent, pageSize=1),
        folders.FoldersMessages().ListFoldersResponse(
            folders=[self.TEST_FOLDER], nextPageToken=test_token))
    # Second page
    self.mock_folders.List.Expect(
        folders.FoldersMessages().CloudresourcemanagerFoldersListRequest(
            parent=self.TEST_FOLDER.parent, pageSize=1, pageToken=test_token),
        folders.FoldersMessages().ListFoldersResponse(
            folders=[self.ANOTHER_TEST_FOLDER]))
    self.DoCommand(page_size='1')
    self.AssertOutputContains(
        """\
      DISPLAY_NAME                     PARENT_NAME          ID
      Test Folder For Testing          organizations/24521  58219052
      DISPLAY_NAME                     PARENT_NAME          ID
      Another Test Folder For Testing  organizations/24521  67045082
      """,
        normalize_space=True)

  def testLimit(self):
    self.mock_folders.List.Expect(
        self.ExpectedListRequest(),
        folders.FoldersMessages().ListFoldersResponse(
            folders=[self.TEST_FOLDER, self.ANOTHER_TEST_FOLDER]))
    self.DoCommand(limit='1')
    self.AssertOutputContains(
        """\
      DISPLAY_NAME             PARENT_NAME          ID
      Test Folder For Testing  organizations/24521  58219052
      """,
        normalize_space=True)

  def testListMissingParent(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ArgumentError,
        'Neither --folder nor --organization provided, exactly one required'):
      self.DoCommand(use_org_parent=False)

  def testListConflictingParents(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --folder, --organization'):
      self.DoCommand(use_folder_parent=True)

  def ExpectedListRequest(self):
    return folders.FoldersMessages().CloudresourcemanagerFoldersListRequest(
        parent=self.TEST_FOLDER.parent)

  def DoCommand(self,
                use_org_parent=True,
                use_folder_parent=False,
                page_size=None,
                limit=None):
    folder_args = ['--folder', '528852'] if use_folder_parent else []
    org_args = [
        '--organization', self.TEST_FOLDER.parent[len('organizations/'):]
    ] if use_org_parent else []
    page_size_args = ['--page-size', page_size] if page_size is not None else []
    limit_args = ['--limit', limit] if limit is not None else []
    all_args = folder_args + org_args + page_size_args + limit_args
    return self.RunFolders('list', *all_args)


class FoldersListAlphaTest(FoldersListTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class FoldersListBetaTest(FoldersListTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
