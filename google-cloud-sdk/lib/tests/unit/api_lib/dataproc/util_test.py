# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

import argparse
import collections
import copy
import os

from googlecloudsdk import calliope
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class UtilUnitTest(unit_base.DataprocUnitTestBase):
  """Tests for dataproc util."""

  def SetUp(self):
    self.dataproc_mock = dp.Dataproc(self.track)
    self.dataproc_mock._client = self.mock_client
    self.dataproc_mock._messages = self.messages


class UtilUnitTestBeta(UtilUnitTest, base.DataprocTestBaseBeta,
                       parameterized.TestCase):

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
    operation = self.MakeCompletedOperation(
        metadata={'createCluster': collections.OrderedDict([
            ('error', 'create error.'), ('operationId', 'test id')])})
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
    operation = self.MakeCompletedOperation(
        metadata={'deleteCluster': collections.OrderedDict([
            ('error', 'delete error.'), ('operationId', 'test id')])})
    self.ExpectGetOperation()
    self.ExpectGetOperation()
    self.ExpectGetOperation(operation=operation)
    exception_message = 'Operation [{0}] failed: {1}.'.format(
        'test id', 'delete error')
    with self.AssertRaisesExceptionMatches(exceptions.OperationError,
                                           exception_message):
      util.WaitForWorkflowTemplateOperation(self.dataproc_mock, operation, 10,
                                            0)

  def testReadAutoscalingPolicy_file(self):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'cool-policy')

    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=policy, stream=stream)

    expected_policy = copy.deepcopy(policy)
    expected_policy.name = None

    policy_read = util.ReadAutoscalingPolicy(
        dataproc=self.dataproc_mock,
        policy_id='cool-policy',
        policy_file_name=file_name)
    self.AssertMessagesEqual(expected_policy, policy_read)

  def testReadAutoscalingPolicy_stdin(self):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'cool-policy')

    self.WriteInput(export_util.Export(message=policy))

    expected_policy = copy.deepcopy(policy)
    expected_policy.name = None

    policy_read = util.ReadAutoscalingPolicy(
        dataproc=self.dataproc_mock,
        policy_id='cool-policy',
    )
    self.AssertMessagesEqual(expected_policy, policy_read)

  def testReadAutoscalingPolicy_invalid(self):
    self.WriteInput('foo: bar')
    policy_read = util.ReadAutoscalingPolicy(
        dataproc=self.dataproc_mock,
        policy_id='cool-policy',
    )
    # Invalid fields are ignored, so you end up with a mostly empty message
    self.AssertMessagesEqual(
        self.messages.AutoscalingPolicy(id='cool-policy'), policy_read)

  def testReadAutoscalingPolicy_handlesUnsetIdAndName(self):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'cool-policy')
    # id and name are unset
    policy.id = None
    policy.name = None

    self.WriteInput(export_util.Export(message=policy))

    expected_policy = copy.deepcopy(policy)
    expected_policy.id = 'cool-policy'  # gets set to correct value
    expected_policy.name = None  # stays unset

    policy_read = util.ReadAutoscalingPolicy(
        dataproc=self.dataproc_mock,
        policy_id='cool-policy',
    )
    self.AssertMessagesEqual(expected_policy, policy_read)

  @parameterized.parameters(
      ('200', '200s'),  # defaults to seconds if no units specified
      ('400s', '400s'),
      ('2m', '120s'),
      ('1h', '3600s'),
      ('1d', '86400s'),
      ('0.5d', '43200s'),  # decimals are allowed
      ('200.5s', '200s'),  # truncate partial seconds to next lowest
  )
  def testReadAutoscalingPolicy_durationFormats(self, duration, converted):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'cool-policy')
    policy.id = None
    policy.name = None
    policy.basicAlgorithm.cooldownPeriod = duration
    policy.basicAlgorithm.yarnConfig.gracefulDecommissionTimeout = duration

    self.WriteInput(export_util.Export(message=policy))

    expected_policy = copy.deepcopy(policy)
    expected_policy.id = 'cool-policy'
    expected_policy.name = None
    expected_policy.basicAlgorithm.cooldownPeriod = converted
    expected_policy.basicAlgorithm.yarnConfig.gracefulDecommissionTimeout = converted

    policy_read = util.ReadAutoscalingPolicy(
        dataproc=self.dataproc_mock,
        policy_id='cool-policy',
    )
    self.AssertMessagesEqual(expected_policy, policy_read)

  def testReadAutoscalingPolicy_omitCooldownPeriod(self):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'cool-policy')
    policy.id = None
    policy.name = None
    policy.basicAlgorithm.cooldownPeriod = None
    policy.basicAlgorithm.yarnConfig.gracefulDecommissionTimeout = '1h'

    self.WriteInput(export_util.Export(message=policy))

    expected_policy = copy.deepcopy(policy)
    expected_policy.id = 'cool-policy'
    expected_policy.name = None

    # cooldownPeriod remains None, and graceful timeout still gets converted.
    expected_policy.basicAlgorithm.yarnConfig.gracefulDecommissionTimeout = '3600s'

    policy_read = util.ReadAutoscalingPolicy(
        dataproc=self.dataproc_mock,
        policy_id='cool-policy',
    )
    # Cooldown period remains none
    self.AssertMessagesEqual(expected_policy, policy_read)

  @parameterized.parameters(
      ('-10m'),  # negative
      ('0s'),  # zero
      ('4k'),  # wrong letter
      ('2d'),  # too long
      ('1m'),  # too short
      ('119s'),  # too short
  )
  def testReadAutoscalingPolicy_cooldownFormat_illegal(self, illegal_duration):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'cool-policy')
    policy.id = None
    policy.name = None
    policy.basicAlgorithm.cooldownPeriod = illegal_duration

    self.WriteInput(export_util.Export(message=policy))

    with self.assertRaises(argparse.ArgumentTypeError):
      util.ReadAutoscalingPolicy(
          dataproc=self.dataproc_mock,
          policy_id='cool-policy',
      )

  @parameterized.parameters(
      ('-1s'),  # negative
      ('4k'),  # wrong letter
      ('2d'),  # too long
  )
  def testReadAutoscalingPolicy_gracefulTimeoutFormat_illegal(
      self, illegal_duration):
    policy = self.MakeAutoscalingPolicy('cool-project', 'cool-region',
                                        'cool-policy')
    policy.id = None
    policy.name = None
    policy.basicAlgorithm.yarnConfig.gracefulDecommissionTimeout = illegal_duration

    self.WriteInput(export_util.Export(message=policy))

    with self.assertRaises(argparse.ArgumentTypeError):
      util.ReadAutoscalingPolicy(
          dataproc=self.dataproc_mock,
          policy_id='cool-policy',
      )


if __name__ == '__main__':
  sdk_test_base.main()
