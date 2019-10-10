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
"""Tests for the ML Operations library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import operations
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class OperationsClientTest(base.MlGaPlatformTestBase):

  def SetUp(self):
    self.operations_client = operations.OperationsClient()
    self.StartPatch('time.sleep')

  def testList(self):
    response_items = [
        self.msgs.GoogleLongrunningOperation(name='operations/op1'),
        self.msgs.GoogleLongrunningOperation(name='operations/op2')
    ]
    self.client.projects_operations.List.Expect(
        self.msgs.MlProjectsOperationsListRequest(
            name='projects/{}'.format(self.Project()), pageSize=100),
        self.msgs.GoogleLongrunningListOperationsResponse(
            operations=response_items))
    project_ref = resources.REGISTRY.Parse(self.Project(),
                                           collection='ml.projects')
    self.assertEqual(list(self.operations_client.List(project_ref)),
                     response_items)

  def testDescribe(self):
    response = self.msgs.GoogleLongrunningOperation(name='opName', done=True)
    self.client.projects_operations.Get.Expect(
        self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        response)
    operation_ref = resources.REGISTRY.Create(
        'ml.projects.operations',
        operationsId='opId', projectsId=self.Project())
    self.assertEqual(self.operations_client.Get(operation_ref), response)

  def testCancel(self):
    response = self.msgs.GoogleProtobufEmpty()
    self.client.projects_operations.Cancel.Expect(
        self.msgs.MlProjectsOperationsCancelRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        response)
    operation_ref = resources.REGISTRY.Create(
        'ml.projects.operations',
        operationsId='opId', projectsId=self.Project())
    self.assertEqual(self.operations_client.Cancel(operation_ref), response)

  def testWaitForOperation_Success(self):
    self.client.projects_operations.Get.Expect(
        self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        self.msgs.GoogleLongrunningOperation(
            name='opName',
            done=True))
    result = self.operations_client.WaitForOperation(
        self.msgs.GoogleLongrunningOperation(name='opId'))
    self.assertEqual(result.name, 'opName')

  def testWaitForOperation_Error(self):
    self.client.projects_operations.Get.Expect(
        self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        self.msgs.GoogleLongrunningOperation(
            name='opName',
            done=True,
            error=self.msgs.GoogleRpcStatus(message='failure!')))
    with self.AssertRaisesExceptionMatches(waiter.OperationError, 'failure!'):
      self.operations_client.WaitForOperation(
          self.msgs.GoogleLongrunningOperation(name='opId'))


if __name__ == '__main__':
  test_case.main()
