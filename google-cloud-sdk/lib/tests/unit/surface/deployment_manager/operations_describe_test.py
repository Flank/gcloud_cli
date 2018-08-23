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

"""Unit tests for operations describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base

messages = core_apis.GetMessagesModule('deploymentmanager', 'v2')

OPERATION_NAME = 'operation-name'
OPERATION_ID = 12345
OPERATION_SELF_LINK = 'self-link'


class OperationsDescribeTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for operations describe command."""

  # TODO(b/36054661): Figure out how to respond to mocked call with exception.
  # Add tests where exception is raised.

  def createOperation(self):
    """Helper function to create a simple operation.

    Returns:
      Operation with name, id, and self link set.
    """
    return messages.Operation(
        name=OPERATION_NAME,
        id=OPERATION_ID,
        selfLink=OPERATION_SELF_LINK
    )

  def testOperationsDescribe(self):
    self.mocked_client.operations.Get.Expect(
        request=messages.DeploymentmanagerOperationsGetRequest(
            operation=OPERATION_NAME,
            project=self.Project(),
        ),
        response=self.createOperation()
    )
    self.Run('deployment-manager operations describe ' + OPERATION_NAME)
    self.AssertOutputContains(OPERATION_NAME)
    self.AssertOutputContains(str(OPERATION_ID))
    self.AssertOutputContains(OPERATION_SELF_LINK)

  def testOperationsDescribe_OperationWithErrors(self):
    # Make sure operation errors are printed in the output.
    errors = ['error ' + c for c in ['a', 'b', 'c', 'd']]
    operation_with_errors = self.createOperation()
    operation_with_errors.error = messages.Operation.ErrorValue(
        errors=[
            messages.Operation.ErrorValue.ErrorsValueListEntry(message=error)
            for error in errors]
    )
    self.mocked_client.operations.Get.Expect(
        request=messages.DeploymentmanagerOperationsGetRequest(
            operation=OPERATION_NAME,
            project=self.Project(),
        ),
        response=operation_with_errors
    )
    self.Run('deployment-manager operations describe ' + OPERATION_NAME)
    self.AssertOutputContains(OPERATION_NAME)
    self.AssertOutputContains(str(OPERATION_ID))
    self.AssertOutputContains(OPERATION_SELF_LINK)
    for error in errors:
      self.AssertOutputContains(error)

if __name__ == '__main__':
  test_case.main()
