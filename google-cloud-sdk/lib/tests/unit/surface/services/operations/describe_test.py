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

"""Unit tests for service-management operations describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.services import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class ServicesOperationsDescribeTest(unit_test_base.SV1UnitTestBase):
  """Unit tests for services operations describe command."""

  def SetUp(self):
    self.op_name = 'operation-12345'
    self.op = self.services_messages.Operation(name=self.op_name, done=False)
    self.op_dict = encoding.MessageToDict(self.op)

  def testServicesOperationsDescribe(self):
    self.mocked_client.operations.Get.Expect(
        request=self.services_messages.ServicemanagementOperationsGetRequest(
            operationsId=self.op_name,
        ),
        response=self.op
    )

    response = self.Run(
        'services operations describe ' + self.op_name)
    self.assertEqual(response, self.op_dict)

  def testServicesOperationsDescribeWithPrefix(self):
    self.mocked_client.operations.Get.Expect(
        request=self.services_messages.ServicemanagementOperationsGetRequest(
            operationsId=self.op_name,
        ),
        response=self.op
    )

    response = self.Run('services operations describe operations/%s' %
                        self.op_name)
    self.assertEqual(response, self.op_dict)


class DescribeTest(unit_test_base.SUUnitTestBase):
  """Unit tests for services operations describe command."""
  OPERATION_NAME = 'operations/abc.0000000000'

  def testDescribe(self):
    self.ExpectOperation(self.OPERATION_NAME, 0)

    self.Run('alpha services operations describe %s' % self.OPERATION_NAME)
    self.AssertErrContains(self.OPERATION_NAME)
    self.AssertErrContains('finished successfully')

  def testDescribePermissionDenied(self):
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectOperation(self.OPERATION_NAME, 0, server_error)

    with self.assertRaisesRegex(exceptions.OperationErrorException, r'Error.'):
      self.Run('alpha services operations describe %s' % self.OPERATION_NAME)


if __name__ == '__main__':
  test_case.main()
