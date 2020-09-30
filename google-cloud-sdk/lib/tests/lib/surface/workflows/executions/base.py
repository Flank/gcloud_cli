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
"""Base class for all workflows tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.workflows import workflows
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class WorkflowsExecutionsTestBase(sdk_test_base.WithFakeAuth,
                                  cli_test_base.CliTestBase):
  """Base class for all Workflows executions unit tests that use fake auth and mocks."""

  def SetUp(self):
    self.api_version = workflows.ReleaseTrackToApiVersion(self.track)
    self.messages = apis.GetMessagesModule('workflowexecutions',
                                           self.api_version)
    self.mock_client = mock.Client(
        apis.GetClientClass('workflowexecutions', self.api_version),
        real_client=apis.GetClientInstance(
            'workflowexecutions', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def MockExecutionWait(self,
                        execution_name,
                        execution_states=None,
                        exception=None):

    if exception is not None:
      self.mock_client.projects_locations_workflows_executions.Get.Expect(
          request=self.messages
          .WorkflowexecutionsProjectsLocationsWorkflowsExecutionsGetRequest(
              name=execution_name),
          response=None,
          exception=exception)
      return

    for state in execution_states:
      self.mock_client.projects_locations_workflows_executions.Get.Expect(
          request=self.messages
          .WorkflowexecutionsProjectsLocationsWorkflowsExecutionsGetRequest(
              name=execution_name),
          response=self.messages.Execution(name=execution_name, state=state),
          exception=exception)

  def GetExecutionStateEnum(self):
    return self.messages.Execution.StateValueValuesEnum

  def GetExecutionName(self, execution_id, workflow, region='us-central1'):
    return 'projects/{}/locations/{}/workflows/{}/executions/{}'.format(
        self.Project(), region, workflow, execution_id)
