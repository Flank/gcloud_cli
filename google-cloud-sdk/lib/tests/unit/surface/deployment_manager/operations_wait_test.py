# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Unit tests for operations wait command."""

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base

messages = core_apis.GetMessagesModule('deploymentmanager', 'v2')

OPERATION_NAME = 'operation-name'
OPERATION_ID = 12345


class OperationsWaitTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for operations wait command."""

  # TODO(b/36056505): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def createOperation(self, status, identifier=None):
    """Helper function to create a simple operation.

    Args:
      status: PENDING, DONE, or some other valid state string.
      identifier: Optional integer to act as id and append to name.

    Returns:
      Operation with name and id set.
    """
    if identifier is not None:
      name = OPERATION_NAME + str(identifier)
      operation_id = identifier
    else:
      name = OPERATION_NAME
      operation_id = OPERATION_ID
    return messages.Operation(
        name=name,
        id=operation_id,
        status=status,
    )

  def testOperationsWait(self):
    pending_operation = self.createOperation('PENDING')
    done_operation = self.createOperation('DONE')
    for _ in range(3):
      self.mocked_client.operations.Get.Expect(
          request=messages.DeploymentmanagerOperationsGetRequest(
              operation=OPERATION_NAME,
              project=self.Project(),
          ),
          response=pending_operation
      )
    # Operation is finally done
    self.mocked_client.operations.Get.Expect(
        request=messages.DeploymentmanagerOperationsGetRequest(
            operation=OPERATION_NAME,
            project=self.Project(),
        ),
        response=done_operation
    )
    self.Run('deployment-manager operations wait ' + OPERATION_NAME)
    self.AssertErrContains('All operations completed successfully.')
    self.AssertErrContains(OPERATION_NAME)
    self.AssertErrNotContains(pending_operation.status)

  def testOperationsWait_OperationErrors(self):
    errors_operation = self.createOperation('DONE')
    errors_operation.error = messages.Operation.ErrorValue(
        errors=[
            messages.Operation.ErrorValue.ErrorsValueListEntry(message='bad')]
    )
    self.mocked_client.operations.Get.Expect(
        request=messages.DeploymentmanagerOperationsGetRequest(
            operation=OPERATION_NAME,
            project=self.Project(),
        ),
        response=errors_operation
    )
    try:
      self.Run('deployment-manager operations wait ' + OPERATION_NAME)
      self.fail('expected exceptions.OperationError because of operation with'
                ' error field set.')
    except exceptions.OperationError as e:
      self.assertEquals(
          'Operation %s failed to complete or has errors.' % OPERATION_NAME,
          e.message)

  def testOperationsWait_OperationErrorsMultiple(self):
    num_bad_operations = 3
    bad_operations = []
    for i in range(num_bad_operations):
      errors_operation = self.createOperation('DONE', i)
      errors_operation.error = messages.Operation.ErrorValue(
          errors=[
              messages.Operation.ErrorValue.ErrorsValueListEntry(
                  message='bad')
          ]
      )
      bad_operations.append(errors_operation)
    for bad_operation in bad_operations:
      self.mocked_client.operations.Get.Expect(
          request=messages.DeploymentmanagerOperationsGetRequest(
              operation=bad_operation.name,
              project=self.Project(),
          ),
          response=bad_operation
      )
    ok_operation = self.createOperation('DONE', num_bad_operations)
    self.mocked_client.operations.Get.Expect(
        request=messages.DeploymentmanagerOperationsGetRequest(
            operation=ok_operation.name,
            project=self.Project(),
        ),
        response=ok_operation
    )
    try:
      self.Run('deployment-manager operations wait '
               + ' '.join([op.name for op in bad_operations]) + ' '
               + ok_operation.name)
      self.fail('expected exceptions.OperationError because of operations with '
                'error field set.')
    except exceptions.OperationError as e:
      self.assertTrue(
          'Some operations failed to complete without errors' in e.message)
      for bad_operation in bad_operations:
        self.assertTrue(bad_operation.name in e.message)
      self.assertFalse(ok_operation.name in e.message)


if __name__ == '__main__':
  test_case.main()
