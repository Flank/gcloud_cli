# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for endpoints operations wait command."""

from googlecloudsdk.api_lib.endpoints import exceptions
from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsOperationsWaitTest(unit_test_base.EV1UnitTestBase):

  def testWaitForOperation(self):
    operation_name = 'operation-12345'

    # Have the operation remain unfinished for the first call
    self.MockOperationWait(operation_name)

    self.Run('endpoints operations wait ' + operation_name)
    self.AssertErrContains(operation_name)

  def testWaitForOperationWithError(self):
    operation_name = 'operation-12345'

    # Have the operation remain unfinished for the first call
    self.mocked_client.operations.Get.Expect(
        request=self.services_messages.ServicemanagementOperationsGetRequest(
            operationsId=operation_name,
        ),
        response=self.services_messages.Operation(
            name=operation_name,
            done=False
        )
    )

    # This time, the operation will have completed with an error
    self.mocked_client.operations.Get.Expect(
        request=self.services_messages.ServicemanagementOperationsGetRequest(
            operationsId=operation_name,
        ),
        response=self.services_messages.Operation(
            name=operation_name,
            done=True,
            error=self.services_messages.Status()
        )
    )

    with self.assertRaisesRegex(
        exceptions.OperationErrorException,
        'The operation with ID operation-12345 resulted in a failure.'):
      self.Run('endpoints operations wait ' + operation_name)


if __name__ == '__main__':
  test_case.main()
