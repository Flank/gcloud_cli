# -*- coding: utf-8 -*- #
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

"""Unit tests for operations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base
from six.moves import range  # pylint: disable=redefined-builtin

messages = apis.GetMessagesModule('deploymentmanager', 'v2')

OPERATION_NAME = 'operation-name'
OPERATION_ID = 12345
OPERATION_SELF_LINK = ('https://www.googleapis.com/deploymentmanager/v2/'
                       'projects/mock-project/global/operations/operation-1')


class OperationsListTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for operations list command."""

  # TODO(b/36054660): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def createOperation(self, identifier=None):
    """Helper function to create a simple operation.

    Args:
      identifier: Optional integer to act as id and append to name.

    Returns:
      Operation with name, id, and selfLink set.
    """
    if identifier is not None:
      name = OPERATION_NAME + str(identifier)
      operation_id = identifier
      self_link = OPERATION_SELF_LINK + str(identifier)
    else:
      name = OPERATION_NAME
      operation_id = OPERATION_ID
      self_link = OPERATION_SELF_LINK
    return messages.Operation(
        name=name,
        id=operation_id,
        selfLink=self_link,
    )

  def testOperationsList(self):
    num_operations = 10
    self.mocked_client.operations.List.Expect(
        request=messages.DeploymentmanagerOperationsListRequest(
            project=self.Project()
        ),
        response=messages.OperationsListResponse(
            operations=[self.createOperation(i) for i in range(num_operations)]
        )
    )
    self.Run('deployment-manager operations list')
    for i in range(num_operations):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(OPERATION_NAME + str(i))

  def testOperationsList_EmptySimpleList(self):
    self.mocked_client.operations.List.Expect(
        request=messages.DeploymentmanagerOperationsListRequest(
            project=self.Project()
        ),
        response=messages.OperationsListResponse()
    )
    self.Run('deployment-manager operations list --simple-list')
    self.AssertOutputEquals('')

  def testOperationsList_EmptyList(self):
    self.mocked_client.operations.List.Expect(
        request=messages.DeploymentmanagerOperationsListRequest(
            project=self.Project()
        ),
        response=messages.OperationsListResponse()
    )
    self.Run('deployment-manager operations list')
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testOperationsList_SimpleList(self):
    num_operations = 10
    self.mocked_client.operations.List.Expect(
        request=messages.DeploymentmanagerOperationsListRequest(
            project=self.Project()
        ),
        response=messages.OperationsListResponse(
            operations=[self.createOperation(i) for i in range(num_operations)]
        )
    )
    self.Run('deployment-manager operations list --simple-list')
    expected_output = '\n'.join(
        [OPERATION_NAME + str(i) for i in range(num_operations)]) + '\n'
    self.AssertOutputEquals(expected_output)

  def testOperationsList_Limit(self):
    num_operations = 10
    limit = 5
    self.mocked_client.operations.List.Expect(
        request=messages.DeploymentmanagerOperationsListRequest(
            project=self.Project(),
        ),
        response=messages.OperationsListResponse(
            operations=[self.createOperation(i) for i in range(num_operations)]
        )
    )
    self.Run('deployment-manager operations list --limit ' + str(limit))
    for i in range(limit):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(OPERATION_NAME + str(i))
    for i in range(limit, num_operations):
      self.AssertOutputNotContains(str(i))
      self.AssertOutputNotContains(OPERATION_NAME + str(i))

  def testOperationsList_WithErrors(self):
    num_operations = 10
    error_string = 'error-string-'
    error_suffixes = ['a', 'b', 'c']
    operations = []
    for i in range(num_operations):
      operation = self.createOperation(i)
      operation.error = messages.Operation.ErrorValue(
          errors=[
              messages.Operation.ErrorValue.ErrorsValueListEntry(
                  code=error_string + str(i) + error_suffix
              )
              for error_suffix in error_suffixes]
      )
      operations.append(operation)
    self.mocked_client.operations.List.Expect(
        request=messages.DeploymentmanagerOperationsListRequest(
            project=self.Project()
        ),
        response=messages.OperationsListResponse(
            operations=operations
        )
    )
    self.Run('deployment-manager operations list')
    for i in range(num_operations):
      self.AssertOutputContains(str(i))
      self.AssertOutputContains(OPERATION_NAME + str(i))
      for error_suffix in error_suffixes:
        self.AssertOutputContains(error_string + str(i) + error_suffix)

if __name__ == '__main__':
  test_case.main()
