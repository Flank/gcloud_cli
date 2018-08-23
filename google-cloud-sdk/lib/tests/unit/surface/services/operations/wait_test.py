# -*- coding: utf-8 -*- #
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

"""Unit tests for services operations wait command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class ServiceManagementOperationsWaitTest(unit_test_base.SV1UnitTestBase):

  def testWaitForOperation(self):
    operation_name = 'operation-12345'

    # Have the operation remain unfinished for the first call
    self.MockOperationWait(operation_name)

    self.Run('services operations wait ' + operation_name)
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
      self.Run('services operations wait ' + operation_name)


class WaitTest(unit_test_base.SUUnitTestBase):
  """Unit tests for services operations wait command."""
  OPERATION_NAME = 'operations/abc.0000000000'

  def testWait(self):
    self.ExpectOperation(self.OPERATION_NAME, 3)

    self.Run('alpha services operations wait %s' % self.OPERATION_NAME)
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testWaitPermissionDenied(self):
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectOperation(self.OPERATION_NAME, 3, server_error)

    with self.assertRaisesRegex(exceptions.OperationErrorException, r'Error.'):
      self.Run('alpha services operations wait %s' % self.OPERATION_NAME)


if __name__ == '__main__':
  test_case.main()
