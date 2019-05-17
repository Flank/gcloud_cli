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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class FoldersDeleteTest(testbase.FoldersUnitTestBase):

  def testDeleteFolder(self):
    self.mock_folders.Delete.Expect(self.ExpectedRequest(), self.TEST_FOLDER)
    self.assertEqual(self.DoRequest(), None)

  def ExpectedRequest(self):
    return folders.FoldersMessages().CloudresourcemanagerFoldersDeleteRequest(
        foldersId=folders.FolderNameToId(self.TEST_FOLDER.name))

  def DoRequest(self):
    return self.RunFolders('delete',
                           folders.FolderNameToId(self.TEST_FOLDER.name))


class FoldersDeleteAlphaTest(FoldersDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class FoldersDeleteBetaTest(FoldersDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
