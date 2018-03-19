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

from googlecloudsdk.api_lib.resource_manager import exceptions
from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase

TEST_OPERATION_NAME = 'operations/fm.123'


class FoldersMoveTest(testbase.FoldersUnitTestBase):

  def testMoveFolderToOrganization(self):
    self.SetUpFolderMove(self.TEST_FOLDER_WITH_FOLDER_PARENT, self.TEST_FOLDER)
    self.assertEqual(self.DoCommand(), None)

  def testMoveFolderToFolder(self):
    self.SetUpFolderMove(self.TEST_FOLDER, self.TEST_FOLDER_WITH_FOLDER_PARENT)
    self.assertEqual(
        self.DoCommand(
            use_folder_parent=True, use_org_parent=False),
        None)

  def testMoveMissingParent(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ArgumentError,
        'Neither --folder nor --organization provided, exactly one required'):
      self.DoCommand(use_org_parent=False)

  def testMoveConflictingParents(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --folder, --organization'):
      self.DoCommand(use_folder_parent=True)

  def testMoveAsync(self):
    self.SetUpFolderMove(
        self.TEST_FOLDER_WITH_FOLDER_PARENT, self.TEST_FOLDER, async=True)
    self.assertEqual(
        self.DoCommand(async=True),
        operations.OperationsMessages().Operation(
            done=False, name=TEST_OPERATION_NAME))

  def SetUpFolderMove(self, original, moved, async=False):
    response_value = operations.ToOperationResponse(moved)
    test_move_operation = operations.OperationsMessages().Operation(
        done=False, name=TEST_OPERATION_NAME)
    expected_move_request = folders.FoldersMessages(
    ).CloudresourcemanagerFoldersMoveRequest(
        foldersId=folders.FolderNameToId(original.name),
        moveFolderRequest=folders.FoldersMessages().MoveFolderRequest(
            destinationParent=moved.parent))
    self.mock_folders.Move.Expect(expected_move_request, test_move_operation)
    if not async:
      test_move_operation_done = operations.OperationsMessages().Operation(
          done=True, name=TEST_OPERATION_NAME, response=response_value)
      self.mock_operations.Get.Expect(
          self.ExpectedGetOperationRequest(test_move_operation),
          test_move_operation_done)

  def ExpectedGetOperationRequest(self, move_operation):
    expected_id = operations.OperationNameToId(move_operation.name)
    return operations.OperationsMessages(
    ).CloudresourcemanagerOperationsGetRequest(operationsId=expected_id)

  def DoCommand(self, use_org_parent=True, use_folder_parent=False,
                async=False):
    folder_parent_args = [
        '--folder',
        folders.FolderNameToId(self.TEST_FOLDER_WITH_FOLDER_PARENT.parent)
    ] if use_folder_parent else []
    org_parent_args = [
        '--organization', self.TEST_FOLDER.parent[len('organizations/'):]
    ] if use_org_parent else []
    async_args = ['--async'] if async else []
    all_args = folder_parent_args + org_parent_args + async_args
    return self.RunFolders('move',
                           folders.FolderNameToId(self.TEST_FOLDER.name),
                           *all_args)


if __name__ == '__main__':
  test_case.main()
