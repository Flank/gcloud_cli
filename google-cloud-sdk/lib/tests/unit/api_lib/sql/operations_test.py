# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for googlecloudsdk.api_lib.sql.operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import operations
from tests.lib import test_case
from tests.lib.surface.sql import base


def _GetOperationStatus(sql_client, operation_ref):
  return operations.OperationsV1Beta4.GetOperationStatus(
      sql_client, operation_ref)


class OperationStatusTest(base.SqlMockTestBeta):
  """Tests operations.OperationsV1Beta4.GetOperationStatus."""

  def SetUp(self):
    self.client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    self.instance = self.GetV2Instance()

  def GetOperationRef(self, operation):
    return self.client.resource_parser.Create(
        'sql.operations', operation=operation.name, project=self.Project())

  def AssertErrorsEqual(self, first, second):
    self.assertEqual(type(first), type(second))
    self.assertEqual(str(first), str(second))

  def testDoneOperation(self):
    operation = self.GetOperation(
        self.client.sql_messages.Operation.OperationTypeValueValuesEnum.CREATE,
        self.client.sql_messages.Operation.StatusValueValuesEnum.DONE)
    self.ExpectOperationGet(operation)
    status = _GetOperationStatus(self.mocked_client,
                                 self.GetOperationRef(operation))
    self.assertTrue(status)

  def testPendingOperation(self):
    operation = self.GetOperation(
        self.client.sql_messages.Operation.OperationTypeValueValuesEnum.CREATE,
        self.client.sql_messages.Operation.StatusValueValuesEnum.PENDING)
    self.ExpectOperationGet(operation)
    status = _GetOperationStatus(self.mocked_client,
                                 self.GetOperationRef(operation))
    self.assertFalse(status)

  def testUnknownOperation(self):
    operation = self.GetOperation(
        self.client.sql_messages.Operation.OperationTypeValueValuesEnum.CREATE,
        self.client.sql_messages.Operation.StatusValueValuesEnum
        .SQL_OPERATION_STATUS_UNSPECIFIED)
    self.ExpectOperationGet(operation)
    status = _GetOperationStatus(self.mocked_client,
                                 self.GetOperationRef(operation))
    self.AssertErrorsEqual(
        status, exceptions.OperationError('SQL_OPERATION_STATUS_UNSPECIFIED'))

  def testFailedOperationWithMessage(self):
    error = self.messages.OperationErrors(
        kind='sql#operationErrors',
        errors=[
            self.messages.OperationError(
                kind='sql#operationError',
                code='bad_thing',
                message='Error: A Bad Thing (tm) happened.')
        ])
    operation = self.GetOperation(
        self.client.sql_messages.Operation.OperationTypeValueValuesEnum.CREATE,
        self.client.sql_messages.Operation.StatusValueValuesEnum.DONE, error)
    self.ExpectOperationGet(operation)
    status = _GetOperationStatus(self.mocked_client,
                                 self.GetOperationRef(operation))

    # The error returned should contain the operation error message.
    self.AssertErrorsEqual(
        status,
        exceptions.OperationError(
            '[bad_thing] Error: A Bad Thing (tm) happened.'))

  def testFailedOperationWithoutMessage(self):
    error = self.messages.OperationErrors(
        kind='sql#operationErrors',
        errors=[
            self.messages.OperationError(
                kind='sql#operationError', code='bad_thing')
        ])
    operation = self.GetOperation(
        self.client.sql_messages.Operation.OperationTypeValueValuesEnum.CREATE,
        self.client.sql_messages.Operation.StatusValueValuesEnum.DONE, error)
    self.ExpectOperationGet(operation)
    status = _GetOperationStatus(self.mocked_client,
                                 self.GetOperationRef(operation))

    # The error returned should contain the operation error code.
    self.AssertErrorsEqual(status, exceptions.OperationError('[bad_thing]'))


if __name__ == '__main__':
  test_case.main()
