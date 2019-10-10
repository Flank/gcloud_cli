# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for folders update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class FoldersUpdateTest(testbase.FoldersUnitTestBase):

  def testUpdateValidFolderWithNewName(self):
    self.mock_folders.Get.Expect(self.ExpectedGetRequest(),
                                 copy.deepcopy(self.TEST_FOLDER))
    self.mock_folders.Patch.Expect(self.ExpectedPatchRequest(),
                                   self.UPDATED_TEST_FOLDER)
    self.assertEqual(self.DoRequest(), None)

  def testUpdateMissingName(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --display-name: Must be specified.'):
      self.DoRequestWithoutName()

  def ExpectedGetRequest(self):
    return folders.FoldersMessages().CloudresourcemanagerFoldersGetRequest(
        foldersId=folders.FolderNameToId(self.TEST_FOLDER.name))

  def ExpectedPatchRequest(self):
    return folders.FoldersMessages().CloudresourcemanagerFoldersPatchRequest(
        folder=self.UPDATED_TEST_FOLDER,
        foldersId=folders.FolderNameToId(self.UPDATED_TEST_FOLDER.name),
        updateMask='display_name')

  def DoRequest(self):
    return self.RunFolders('update',
                           folders.FolderNameToId(self.TEST_FOLDER.name),
                           '--display-name',
                           self.UPDATED_TEST_FOLDER.displayName)

  def DoRequestWithoutName(self):
    self.RunFolders('update', folders.FolderNameToId(self.TEST_FOLDER.name))


class FoldersUpdateAlphaTest(FoldersUpdateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class FoldersUpdateBetaTest(FoldersUpdateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
