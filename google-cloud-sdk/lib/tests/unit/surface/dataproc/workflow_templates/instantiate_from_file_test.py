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
from __future__ import unicode_literals
import textwrap
import uuid

from googlecloudsdk import calliope

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.core import properties
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplatesInstantiateFromFileUnitTest(
    unit_base.DataprocUnitTestBase, compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow template run."""

  def SetUp(self):
    self.frozen_uuid = uuid.uuid4()
    self.StartPatch('uuid.uuid4', return_value=self.frozen_uuid)

  def ExpectWorkflowTemplatesInstantiateInline(self,
                                               parent=None,
                                               workflow_template=None,
                                               response=None,
                                               exception=None):
    if not parent:
      parent = self.WorkflowTemplateParentName()
    if not workflow_template:
      workflow_template = self.MakeWorkflowTemplate()
    if not (response or exception):
      response = self.MakeOperation()
    client = self.mock_client
    client.projects_regions_workflowTemplates.InstantiateInline.Expect(
        self.messages.
        DataprocProjectsRegionsWorkflowTemplatesInstantiateInlineRequest(
            instanceId=self.frozen_uuid.hex,
            parent=parent,
            workflowTemplate=workflow_template),
        response=response,
        exception=exception)

  def ExpectWorkflowTemplatesInstantiateInlineCalls(self,
                                                    workflow_template=None,
                                                    response=None,
                                                    parent=None,
                                                    exception=None,
                                                    error=None):

    self.ExpectWorkflowTemplatesInstantiateInline(
        parent=parent,
        workflow_template=workflow_template,
        response=response,
        exception=exception)
    # Initial get operation returns pending
    self.ExpectGetOperation(
        self.MakeOperation(template=workflow_template.name, state='RUNNING'))
    # Second get operation returns done
    self.ExpectGetOperation(
        operation=self.MakeCompletedOperation(
            error=error, template=workflow_template.name, state='DONE'))


class WorkflowTemplatesInstantiateFromFileUnitTestBeta(
    WorkflowTemplatesInstantiateFromFileUnitTest):

  def SetUp(self):
    self.SetupForReleaseTrack(calliope.base.ReleaseTrack.BETA)

  def testInstantiateFromFileWorkflowTemplates(self):
    workflow_template = self.MakeWorkflowTemplate()
    file_name = '{0}/{1}'.format(self.temp_path, 'template.yaml')
    util.WriteYaml(file_path=file_name, message=workflow_template)
    self.ExpectWorkflowTemplatesInstantiateInlineCalls(
        workflow_template=workflow_template)
    done = self.MakeCompletedOperation(
        template=workflow_template.name, state='DONE')
    result = self.RunDataproc(
        'workflow-templates instantiate-from-file --file {0}'.format(file_name))
    self.AssertMessagesEqual(done, result)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        textwrap.dedent("""\
      Waiting on operation [{0}].
      WorkflowTemplate [{1}] RUNNING
      WorkflowTemplate [{1}] DONE
        """.format(self.OperationName(), workflow_template.name)))

  def testInstantiateFromFileWorkflowTemplatesAsync(self):
    workflow_template = self.MakeWorkflowTemplate()
    file_name = '{0}/{1}'.format(self.temp_path, 'template.yaml')
    util.WriteYaml(file_path=file_name, message=workflow_template)
    self.ExpectWorkflowTemplatesInstantiateInline(
        workflow_template=workflow_template)
    self.RunDataproc(
        'workflow-templates instantiate-from-file --file {0} --async'.format(
            file_name))
    self.AssertOutputEquals('')
    self.AssertErrContains('Instantiating [{0}] with operation [{1}].'.format(
        self.WORKFLOW_TEMPLATE, self.OperationName()))

  def testInstantiateFromFileWorkflowTemplatesWithRegion(self):
    properties.VALUES.dataproc.region.Set('us-test1')
    parent = self.WorkflowTemplateParentName(region='us-test1')
    template_name = self.WorkflowTemplateName(region='us-test1')
    workflow_template = self.MakeWorkflowTemplate(name=template_name)
    file_name = '{0}/{1}'.format(self.temp_path, 'template.yaml')
    util.WriteYaml(file_path=file_name, message=workflow_template)
    self.ExpectWorkflowTemplatesInstantiateInlineCalls(
        workflow_template=workflow_template, parent=parent)
    done = self.MakeCompletedOperation(
        template=workflow_template.name, state='DONE')
    result = self.RunDataproc(
        'workflow-templates instantiate-from-file --file {0}'.format(file_name))
    self.AssertMessagesEqual(done, result)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        textwrap.dedent("""\
      Waiting on operation [{0}].
      WorkflowTemplate [{1}] RUNNING
      WorkflowTemplate [{1}] DONE
        """.format(self.OperationName(), workflow_template.name)))
