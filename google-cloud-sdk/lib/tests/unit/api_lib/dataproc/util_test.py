# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests of api_lib dataproc util methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk import calliope

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import util
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class UtilUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc util."""

  def SetUp(self):
    self.dataproc_mock = dp.Dataproc(self.track)
    self.dataproc_mock._client = self.mock_client
    self.dataproc_mock._messages = self.messages


class UtilUnitTestBeta(UtilUnitTest, base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testPrintWorkflowMetadata(self):
    metadata = self.messages.WorkflowMetadata(
        template='test-template',
        state=self.messages.WorkflowMetadata.StateValueValuesEnum.RUNNING,
        createCluster=self.messages.ClusterOperation(operationId='create-id'),
        deleteCluster=self.messages.ClusterOperation(operationId='delete-id'),
        graph=self.messages.WorkflowGraph(nodes=[
            self.messages.WorkflowNode(
                jobId='job-id-1',
                stepId='001',
                state=self.messages.WorkflowNode.StateValueValuesEnum.RUNNING)
        ]))
    operations = {'createCluster': None, 'deleteCluster': None}
    status = {}
    errors = {}
    util.PrintWorkflowMetadata(metadata, status, operations, errors)
    self.assertEqual(operations['createCluster'], metadata.createCluster)
    self.assertEqual(operations['deleteCluster'], metadata.deleteCluster)
    self.assertTrue(not errors)  # no errors
    self.assertEqual(status['job-id-1'],
                     self.messages.WorkflowNode.StateValueValuesEnum.RUNNING)
    self.assertEqual(
        status['wt'],
        self.messages.WorkflowMetadata.StateValueValuesEnum.RUNNING)

  def testPrintWorkflowMetadataErrors(self):
    metadata = self.messages.WorkflowMetadata(
        template='test-template',
        state=self.messages.WorkflowMetadata.StateValueValuesEnum.RUNNING,
        createCluster=self.messages.ClusterOperation(
            operationId='create-id', error='create-error'),
        deleteCluster=self.messages.ClusterOperation(
            operationId='delete-id', error='delete-error'),
        graph=self.messages.WorkflowGraph(nodes=[
            self.messages.WorkflowNode(
                jobId='job-id-1',
                stepId='001',
                error='job-error',
                state=self.messages.WorkflowNode.StateValueValuesEnum.FAILED)
        ]))
    operations = {'createCluster': None, 'deleteCluster': None}
    status = {}
    errors = {}
    util.PrintWorkflowMetadata(metadata, status, operations, errors)
    self.assertEqual(operations['createCluster'], metadata.createCluster)
    self.assertEqual(operations['deleteCluster'], metadata.deleteCluster)
    self.assertEqual(errors['job-id-1'], 'job-error')  # no errors
    self.assertEqual(status['job-id-1'],
                     self.messages.WorkflowNode.StateValueValuesEnum.FAILED)

  def testWaitForWorkflowTemplateOperation(self):
    expected = self.MakeCompletedOperation()
    self.ExpectGetOperation()
    self.ExpectGetOperation()
    self.ExpectGetOperation(operation=expected)
    result = util.WaitForWorkflowTemplateOperation(self.dataproc_mock,
                                                   self.MakeOperation(), 10, 0)
    self.assertEqual(result, expected)

  def testWaitForWorkflowTemplateOperationTimeout(self):
    operation = self.MakeOperation()
    exception_message = 'Operation [{0}] timed out.'.format(operation.name)
    with self.AssertRaisesExceptionMatches(exceptions.OperationTimeoutError,
                                           exception_message):
      util.WaitForWorkflowTemplateOperation(self.dataproc_mock, operation, 0, 1)

  def testWaitForWorkflowTemplateOperationError(self):
    operation = self.MakeOperation()
    rpc_error = self.MakeRpcError()
    self.ExpectGetOperation()
    self.ExpectGetOperation()
    self.ExpectGetOperation(operation=self.MakeCompletedOperation(
        error=rpc_error))
    exception_message = 'Operation [{0}] failed: {1}.'.format(
        operation.name, util.FormatRpcError(rpc_error))
    with self.AssertRaisesExceptionMatches(exceptions.OperationError,
                                           exception_message):
      util.WaitForWorkflowTemplateOperation(self.dataproc_mock, operation, 10,
                                            0)

  def testWaitForWorkflowTemplateOperationCreateClusterError(self):
    operation = self.MakeCompletedOperation()
    operation = self.MakeCompletedOperation(
        createCluster={'error': 'create error.',
                       'operationId': 'test id'})
    self.ExpectGetOperation()
    self.ExpectGetOperation()
    self.ExpectGetOperation(operation=operation)
    exception_message = 'Operation [{0}] failed: {1}.'.format(
        'test id', 'create error')
    with self.AssertRaisesExceptionMatches(exceptions.OperationError,
                                           exception_message):
      util.WaitForWorkflowTemplateOperation(self.dataproc_mock, operation, 10,
                                            0)

  def testWaitForWorkflowTemplateOperationDeleteClusterError(self):
    operation = self.MakeCompletedOperation()
    operation = self.MakeCompletedOperation(
        deleteCluster={'error': 'delete error.',
                       'operationId': 'test id'})
    self.ExpectGetOperation()
    self.ExpectGetOperation()
    self.ExpectGetOperation(operation=operation)
    exception_message = 'Operation [{0}] failed: {1}.'.format(
        'test id', 'delete error')
    with self.AssertRaisesExceptionMatches(exceptions.OperationError,
                                           exception_message):
      util.WaitForWorkflowTemplateOperation(self.dataproc_mock, operation, 10,
                                            0)


if __name__ == '__main__':
  sdk_test_base.main()
