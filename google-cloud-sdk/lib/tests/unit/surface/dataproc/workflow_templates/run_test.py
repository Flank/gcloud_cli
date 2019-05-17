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
"""Test of the 'workflow-template run' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
import uuid

from googlecloudsdk import calliope

from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplatesRunUnitTest(unit_base.DataprocUnitTestBase,
                                   compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow template run."""

  def SetUp(self):
    self.frozen_uuid = uuid.uuid4()
    self.StartPatch('uuid.uuid4', return_value=self.frozen_uuid)

  def ExpectWorkflowTemplatesInstantiate(self,
                                         workflow_template_name=None,
                                         version=None,
                                         response=None,
                                         exception=None):
    if not workflow_template_name:
      workflow_template = self.MakeWorkflowTemplate()
      workflow_template_name = workflow_template.name
    instantiate_request = self.messages.InstantiateWorkflowTemplateRequest()
    instantiate_request.instanceId = self.frozen_uuid.hex
    if version:
      instantiate_request.version = version
    if not (response or exception):
      response = self.MakeOperation()
    self.mock_client.projects_regions_workflowTemplates.Instantiate.Expect(
        self.messages.
        DataprocProjectsRegionsWorkflowTemplatesInstantiateRequest(
            instantiateWorkflowTemplateRequest=instantiate_request,
            name=workflow_template_name),
        response=response,
        exception=exception)

  def ExpectWorkflowTemplatesRunCalls(self,
                                      workflow_template_name=None,
                                      version=None,
                                      error=None):

    self.ExpectWorkflowTemplatesInstantiate(
        workflow_template_name=workflow_template_name, version=version)
    # Initial get operation returns pending
    self.ExpectGetOperation()
    # Second get operation returns done
    self.ExpectGetOperation(operation=self.MakeCompletedOperation(error=error))


class WorkflowTemplatesRunUnitTestBeta(WorkflowTemplatesRunUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA

  def testRunWorkflowTemplates(self):
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectWorkflowTemplatesRunCalls(workflow_template.name)
    done = self.MakeCompletedOperation()
    result = self.RunDataproc(
        'workflow-templates run {0}'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(done, result)

  def testRunWorkflowTemplatesAsync(self):
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectWorkflowTemplatesInstantiate(workflow_template.name)
    self.RunDataproc(
        'workflow-templates run {0} --async'.format(self.WORKFLOW_TEMPLATE))
    self.AssertErrEquals(
        textwrap.dedent("""\
        WARNING: Workflow template run command is deprecated, please use instantiate command: "gcloud beta dataproc workflow-templates instantiate"
        Running [test-workflow-template].
        """))

  def testRunWorkflowTemplatesBadTimeout(self):
    err_msg = (
        "argument --timeout: Failed to parse duration: Duration unit 'abc' "
        "must be preceded by a number")
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           err_msg):
      self.RunDataproc('workflow-templates run {0} --timeout abc'.format(
          self.WORKFLOW_TEMPLATE))

  def testRunWorkflowTemplatesHttpError(self):
    message = 'internal error stuff'
    err = self.MakeHttpError(500, message)
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectWorkflowTemplatesInstantiate(
        workflow_template.name, exception=err)
    with self.AssertRaisesExceptionMatches(exceptions.HttpException, message):
      self.RunDataproc('workflow-templates run {0}'.format(
          self.WORKFLOW_TEMPLATE))


class WorkflowTemplatesRunUnitTestAlpha(WorkflowTemplatesRunUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
