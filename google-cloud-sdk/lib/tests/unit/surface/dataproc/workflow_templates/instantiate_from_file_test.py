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
"""Test of the 'workflow-templates instantiate-from-file' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import os
import textwrap
import uuid

from googlecloudsdk import calliope

from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplatesInstantiateFromFileUnitTest(
    unit_base.DataprocUnitTestBase, compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow-templates instantiate-from-file."""

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
    request = self.messages.\
        DataprocProjectsRegionsWorkflowTemplatesInstantiateInlineRequest(
            requestId=self.frozen_uuid.hex,
            parent=parent,
            workflowTemplate=workflow_template)
    client.projects_regions_workflowTemplates.InstantiateInline.Expect(
        request, response=response, exception=exception)

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
    self.ExpectGetOperation(self.MakeOperation(
        metadata=collections.OrderedDict([('state', 'RUNNING')])))
    # Second get operation returns done
    self.ExpectGetOperation(
        operation=self.MakeCompletedOperation(
            error=error,
            metadata=collections.OrderedDict([('state', 'DONE')])))

  def testInstantiateFromFileWorkflowTemplates(self):
    workflow_template = self.MakeWorkflowTemplate()
    workflow_template.id = None
    workflow_template.name = None
    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=workflow_template, stream=stream)
    self.ExpectWorkflowTemplatesInstantiateInlineCalls(
        workflow_template=workflow_template)
    done = self.MakeCompletedOperation(
        metadata=collections.OrderedDict([('state', 'DONE')]))
    result = self.RunDataproc(
        'workflow-templates instantiate-from-file --file {0}'.format(file_name))
    self.AssertMessagesEqual(done, result)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        textwrap.dedent("""\
      Waiting on operation [{0}].
      WorkflowTemplate RUNNING
      WorkflowTemplate DONE
        """.format(self.OperationName())))

  def testInstantiateFromFileWorkflowTemplatesAsync(self):
    workflow_template = self.MakeWorkflowTemplate()
    workflow_template.id = None
    workflow_template.name = None
    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=workflow_template, stream=stream)
    self.ExpectWorkflowTemplatesInstantiateInline(
        workflow_template=workflow_template)
    self.RunDataproc(
        'workflow-templates instantiate-from-file --file {0} --async'.format(
            file_name))
    self.AssertOutputEquals('')
    self.AssertErrContains('Instantiating with operation [{0}].'.format(
        self.OperationName()))

  def testInstantiateFromFileWorkflowTemplatesWithRegion(self):
    properties.VALUES.dataproc.region.Set('us-test1')
    parent = self.WorkflowTemplateParentName(region='us-test1')
    workflow_template = self.MakeWorkflowTemplate()
    workflow_template.id = None
    workflow_template.name = None
    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=workflow_template, stream=stream)
    self.ExpectWorkflowTemplatesInstantiateInlineCalls(
        workflow_template=workflow_template, parent=parent)
    done = self.MakeCompletedOperation(
        metadata=collections.OrderedDict([('state', 'DONE')]))
    result = self.RunDataproc(
        'workflow-templates instantiate-from-file --file {0}'.format(file_name))
    self.AssertMessagesEqual(done, result)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        textwrap.dedent("""\
      Waiting on operation [{0}].
      WorkflowTemplate RUNNING
      WorkflowTemplate DONE
        """.format(self.OperationName())))


class WorkflowTemplatesInstantiateFromFileUnitTestBeta(
    WorkflowTemplatesInstantiateFromFileUnitTest):

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
    request = self.messages.\
      DataprocProjectsRegionsWorkflowTemplatesInstantiateInlineRequest(
          instanceId=self.frozen_uuid.hex,
          parent=parent,
          workflowTemplate=workflow_template)
    client.projects_regions_workflowTemplates.InstantiateInline.Expect(
        request, response=response, exception=exception)

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA


class WorkflowTemplatesInstantiateFromFileUnitTestAlpha(
    WorkflowTemplatesInstantiateFromFileUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
