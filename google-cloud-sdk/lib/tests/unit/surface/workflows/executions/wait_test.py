# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for workflows executions wait."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib.apitools import http_error
from tests.lib.surface.workflows.executions import base

EXECUTION_ID = '6646c6a9-ccc3-405c-a73e-6b09407ad206'
WORKFLOW_ID = 'hodas_workflow'
LOCATION_ID = 'us-central2'


class WorkflowsExecutionsWaitTest(parameterized.TestCase,
                                  base.WorkflowsExecutionsTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testWait_noId(self):
    error_message = (
        'argument --workflow: EXECUTION must be specified.')
    with self.AssertRaisesArgumentErrorMatches(error_message):
      self.Run('workflows executions wait --workflow=ignored_workflow')
    self.AssertOutputEquals('')

  def testWait_SuccessfulExecution(self):
    execution_name = self.GetExecutionName(EXECUTION_ID, WORKFLOW_ID)
    execution_states = [
        self.GetExecutionStateEnum().ACTIVE,
        self.GetExecutionStateEnum().SUCCEEDED
    ]
    self.MockExecutionWait(execution_name, execution_states)

    result = self.Run('workflows executions wait {} --workflow={}'.format(
        EXECUTION_ID, WORKFLOW_ID))
    self.assertEqual(result.name, execution_name)
    self.assertEqual(result.state.name, 'SUCCEEDED')

  def testWait_FailedExecution(self):
    execution_name = self.GetExecutionName(EXECUTION_ID, WORKFLOW_ID)
    execution_states = [
        self.GetExecutionStateEnum().ACTIVE,
        self.GetExecutionStateEnum().FAILED
    ]
    self.MockExecutionWait(execution_name, execution_states)

    result = self.Run('workflows executions wait {} --workflow={}'.format(
        EXECUTION_ID, WORKFLOW_ID))
    self.assertEqual(result.name, execution_name)
    self.assertEqual(result.state.name, 'FAILED')

  def testWait_Location(self):
    execution_name = self.GetExecutionName(EXECUTION_ID, WORKFLOW_ID,
                                           LOCATION_ID)
    execution_states = [
        self.GetExecutionStateEnum().ACTIVE,
        self.GetExecutionStateEnum().SUCCEEDED
    ]
    self.MockExecutionWait(execution_name, execution_states)

    result = self.Run(
        'workflows executions wait {} --workflow={} --location={}'.format(
            EXECUTION_ID, WORKFLOW_ID, LOCATION_ID))
    self.assertEqual(result.name, execution_name)
    self.assertEqual(result.state.name, 'SUCCEEDED')

  def testWait_NonExistentExecution(self):
    execution_name = self.GetExecutionName(EXECUTION_ID, WORKFLOW_ID)
    self.MockExecutionWait(
        execution_name,
        exception=http_error.MakeHttpError(
            code=404,
            message='workflow execution {} not found'.format(
                self.GetExecutionName(EXECUTION_ID, WORKFLOW_ID))))

    with self.assertRaises(exceptions.HttpException):
      self.Run('workflows executions wait {} --workflow={}'.format(
          EXECUTION_ID, WORKFLOW_ID))
    self.AssertErrContains(
        'workflow execution {} not found'.format(
            self.GetExecutionName(EXECUTION_ID, WORKFLOW_ID)))


class WorkflowsExecutionsWaitTestAlpha(WorkflowsExecutionsWaitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

