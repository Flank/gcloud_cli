# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Unit tests for endpoints operations describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsOperationsDescribeTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints operations describe command."""

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
        'endpoints operations describe ' + self.op_name)
    self.assertEqual(response, self.op_dict)

  def testServicesOperationsDescribeWithPrefix(self):
    self.mocked_client.operations.Get.Expect(
        request=self.services_messages.ServicemanagementOperationsGetRequest(
            operationsId=self.op_name,
        ),
        response=self.op
    )

    response = self.Run('endpoints operations describe operations/%s' %
                        self.op_name)
    self.assertEqual(response, self.op_dict)


if __name__ == '__main__':
  test_case.main()
