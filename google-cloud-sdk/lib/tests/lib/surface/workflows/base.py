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
"""Base class for all workflows tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.workflows import workflows
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class WorkflowsTestBase(cli_test_base.CliTestBase):
  """Base class for all Workflows tests."""

  def SetUp(self):
    self.api_version = workflows.ReleaseTrackToApiVersion(self.track)
    self.messages = core_apis.GetMessagesModule('workflows', self.api_version)


class WorkflowsUnitTestBase(WorkflowsTestBase, sdk_test_base.WithFakeAuth):
  """Base class for all Workflows unit tests that use fake auth and mocks."""

  def SetUp(self):
    super(WorkflowsUnitTestBase, self).SetUp()
    self.mock_client = mock.Client(
        core_apis.GetClientClass('workflows', self.api_version),
        real_client=core_apis.GetClientInstance(
            'workflows', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.StartPatch('time.sleep')

    self.operation_name = 'projects/{}/locations/us-central1/operations/op-123'.format(
        self.Project())

  def ExpectGet(self, workflow_name, result=None, exception=None):
    self.mock_client.projects_locations_workflows.Get.Expect(
        self.messages.WorkflowsProjectsLocationsWorkflowsGetRequest(
            name=workflow_name), result, exception)

  def ExpectCreate(self, parent, workflow_id, workflow):
    self.mock_client.projects_locations_workflows.Create.Expect(
        self.messages.WorkflowsProjectsLocationsWorkflowsCreateRequest(
            parent=parent, workflowId=workflow_id, workflow=workflow),
        self.messages.Operation(name=self.operation_name))

  def ExpectUpdate(self, workflow_name, workflow, update_mask):
    self.mock_client.projects_locations_workflows.Patch.Expect(
        self.messages.WorkflowsProjectsLocationsWorkflowsPatchRequest(
            name=workflow_name, workflow=workflow, updateMask=update_mask),
        self.messages.Operation(name=self.operation_name))

  def MockOperationWait(self, response_dict=None, final_error_code=None):
    response = None
    if response_dict:
      response = encoding.DictToMessage(response_dict,
                                        self.messages.Operation.ResponseValue)

    # First, expect a call where the op is not yet done
    self.mock_client.projects_locations_operations.Get.Expect(
        request=self.messages.WorkflowsProjectsLocationsOperationsGetRequest(
            name=self.operation_name,),
        response=self.messages.Operation(
            name=self.operation_name,
            done=False,
        ))

    # Then, expect a call where the op has now completed
    self.mock_client.projects_locations_operations.Get.Expect(
        request=self.messages.WorkflowsProjectsLocationsOperationsGetRequest(
            name=self.operation_name,),
        response=self.messages.Operation(
            name=self.operation_name,
            done=True,
            error=(self.services_messages.Status(
                code=final_error_code) if final_error_code else None),
            response=response,
        ))

  def GetWorkflowName(self, workflow_id, region='us-central1'):
    return 'projects/{}/locations/{}/workflows/{}'.format(
        self.Project(), region, workflow_id)

  def GetLocationName(self, region='us-central1'):
    return 'projects/{}/locations/{}'.format(self.Project(), region)
