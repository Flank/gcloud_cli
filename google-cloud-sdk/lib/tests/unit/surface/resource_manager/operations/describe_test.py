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
from __future__ import unicode_literals
from googlecloudsdk.api_lib.resource_manager import operations
from tests.lib import test_case
from tests.lib.surface.resource_manager import testbase


class OperationsDescribeTest(testbase.OperationsUnitTestBase):

  def testDescribeOperation(self):
    self.mock_operations.Get.Expect(self.ExpectedRequest(), self.TEST_OPERATION)
    self.assertEqual(self.DoRequest(), self.TEST_OPERATION)

  def ExpectedRequest(self):
    messages = operations.OperationsMessages()
    return messages.CloudresourcemanagerOperationsGetRequest(
        operationsId=operations.OperationNameToId(self.TEST_OPERATION.name))

  def DoRequest(self):
    return self.RunOperations(
        'describe', operations.OperationNameToId(self.TEST_OPERATION.name))


if __name__ == '__main__':
  test_case.main()
