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
"""Test of the 'workflow-template run' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
import uuid
from apitools.base.py import encoding
from googlecloudsdk import calliope
from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplatesInstantiateUnitTest(unit_base.DataprocUnitTestBase,
                                           compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow template run."""

  def SetUp(self):
    self.frozen_uuid = uuid.uuid4()
    self.StartPatch('uuid.uuid4', return_value=self.frozen_uuid)

  def ExpectWorkflowTemplatesInstantiate(self,
                                         workflow_template_name=None,
                                         version=None,
                                         parameters=None,
                                         response=None,
                                         exception=None):
    if not workflow_template_name:
      workflow_template = self.MakeWorkflowTemplate()
      workflow_template_name = workflow_template.name
    instantiate_request = self.messages.InstantiateWorkflowTemplateRequest()
    instantiate_request.instanceId = self.frozen_uuid.hex
    if version:
      instantiate_request.version = version
    if parameters:
      instantiate_request.parameters = encoding.DictToMessage(
          parameters,
          self.messages.InstantiateWorkflowTemplateRequest.ParametersValue)
    if not (response or exception):
      response = self.MakeOperation()
    self.mock_client.projects_regions_workflowTemplates.Instantiate.Expect(
        self.messages.
        DataprocProjectsRegionsWorkflowTemplatesInstantiateRequest(
            instantiateWorkflowTemplateRequest=instantiate_request,
            name=workflow_template_name),
        response=response,
        exception=exception)

  def ExpectWorkflowTemplatesInstantiateCalls(self,
                                              workflow_template_name=None,
                                              version=None,
                                              parameters=None,
                                              error=None):

    self.ExpectWorkflowTemplatesInstantiate(
        workflow_template_name=workflow_template_name,
        version=version,
        parameters=parameters)
    # Initial get operation returns pending
    self.ExpectGetOperation(
        self.MakeOperation(template=workflow_template_name, state='RUNNING'))
    # Second get operation returns done
    self.ExpectGetOperation(
        operation=self.MakeCompletedOperation(
            error=error, template=workflow_template_name, state='DONE'))


class WorkflowTemplatesInstantiateUnitTestBeta(
    WorkflowTemplatesInstantiateUnitTest):

  def SetUp(self):
    self.SetupForReleaseTrack(calliope.base.ReleaseTrack.BETA)

  def testInstantiateWorkflowTemplates(self):
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectWorkflowTemplatesInstantiateCalls(workflow_template.name)
    done = self.MakeCompletedOperation(
        template=workflow_template.name, state='DONE')
    result = self.RunDataproc('workflow-templates instantiate {0}'.format(
        self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(done, result)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        textwrap.dedent("""\
      Waiting on operation [{0}].
      WorkflowTemplate [{1}] RUNNING
      WorkflowTemplate [{1}] DONE
        """.format(self.OperationName(), workflow_template.name)))

  def testInstantiateWorkflowTemplatesAsync(self):
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectWorkflowTemplatesInstantiate(workflow_template.name)
    self.RunDataproc('workflow-templates instantiate {0} --async'.format(
        self.WORKFLOW_TEMPLATE))
    self.AssertErrContains('Instantiating [{0}] with operation [{1}].'.format(
        self.WORKFLOW_TEMPLATE, self.OperationName()))

  def testInstantiateWorkflowTemplatesBadTimeout(self):
    err_msg = (
        'argument --timeout: given value must be of the form INTEGER[UNIT]'
        ' where units can be one of s, m, h, d; received: abc')
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           err_msg):
      self.RunDataproc(
          'workflow-templates instantiate {0} --timeout abc'.format(
              self.WORKFLOW_TEMPLATE))

  def testInstantiateWorkflowTemplatesHttpError(self):
    message = 'internal error stuff'
    err = self.MakeHttpError(500, message)
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectWorkflowTemplatesInstantiate(
        workflow_template.name, exception=err)
    with self.AssertRaisesExceptionMatches(exceptions.HttpException, message):
      self.RunDataproc('workflow-templates instantiate {0}'.format(
          self.WORKFLOW_TEMPLATE))

  def testInstantiateWorkflowTemplatesWithParameters(self):
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectWorkflowTemplatesInstantiateCalls(
        workflow_template_name=workflow_template.name,
        parameters={
            'k1': 'v1',
            'k2': 'v2'
        })
    done = self.MakeCompletedOperation(
        template=workflow_template.name, state='DONE')
    result = self.RunDataproc(
        'workflow-templates instantiate {0} --parameters=k1=v1,k2=v2'.format(
            self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(done, result)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        textwrap.dedent("""\
        Waiting on operation [{0}].
        WorkflowTemplate [{1}] RUNNING
        WorkflowTemplate [{1}] DONE
          """.format(self.OperationName(), workflow_template.name)))
