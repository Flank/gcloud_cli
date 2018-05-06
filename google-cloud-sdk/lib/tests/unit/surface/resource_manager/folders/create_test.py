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


class FoldersCreateTest(testbase.FoldersUnitTestBase):

  def testCreateFolder(self):
    response_value = operations.ToOperationResponse(self.TEST_FOLDER)
    test_create_operation = operations.OperationsMessages().Operation(
        done=False, name='operations/fc.123')
    test_create_operation_done = operations.OperationsMessages().Operation(
        done=True, name='operations/fc.123', response=response_value)
    self.mock_folders.Create.Expect(self.ExpectedCreateRequest(),
                                    test_create_operation)
    self.mock_operations.Get.Expect(
        self.ExpectedGetOperationRequest(test_create_operation),
        test_create_operation_done)
    self.assertEqual(self.DoCommand(), self.TEST_FOLDER)

  def testCreateMissingName(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --display-name: Must be specified.'):
      self.DoCommand(use_display_name=False)

  def testCreateMissingParent(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ArgumentError,
        'Neither --folder nor --organization provided, exactly one required'):
      self.DoCommand(use_org_parent=False)

  def testCreateConflictingParents(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --folder, --organization'):
      self.DoCommand(use_folder_parent=True)

  def testCreateAsync(self):
    test_create_operation = operations.OperationsMessages().Operation(
        done=False, name='operations/fc.123')
    self.mock_folders.Create.Expect(self.ExpectedCreateRequest(),
                                    test_create_operation)
    self.assertEqual(self.DoCommand(is_async=True), test_create_operation)

  def ExpectedCreateRequest(self):
    messages = folders.FoldersMessages()
    return messages.CloudresourcemanagerFoldersCreateRequest(
        parent=self.TEST_FOLDER.parent,
        folder=messages.Folder(
            displayName=self.TEST_FOLDER.displayName))

  def ExpectedGetOperationRequest(self, create_operation):
    expected_id = operations.OperationNameToId(create_operation.name)
    return operations.OperationsMessages(
    ).CloudresourcemanagerOperationsGetRequest(operationsId=expected_id)

  def DoCommand(self,
                use_org_parent=True,
                use_folder_parent=False,
                use_display_name=True,
                is_async=False):
    folder_parent_args = ['--folder', '528852'] if use_folder_parent else []
    org_parent_args = [
        '--organization', self.TEST_FOLDER.parent[len('organizations/'):]
    ] if use_org_parent else []
    display_name_args = [
        '--display-name', self.TEST_FOLDER.displayName
    ] if use_display_name else []
    async_args = ['--async'] if is_async else []
    all_args = (
        folder_parent_args + org_parent_args + display_name_args + async_args)
    return self.RunFolders('create', *all_args)


if __name__ == '__main__':
  test_case.main()
