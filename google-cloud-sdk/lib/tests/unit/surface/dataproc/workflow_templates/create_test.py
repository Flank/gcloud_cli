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
"""Test of the 'workflow template create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope

from googlecloudsdk.core import properties
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateCreateUnitTest(unit_base.DataprocUnitTestBase,
                                     compute_base.BaseComputeUnitTest):
  """Tests for workflow template create."""

  def ExpectCreateWorkflowTemplate(self,
                                   workflow_template=None,
                                   response=None,
                                   parent=None,
                                   region=None,
                                   exception=None):
    if not parent:
      parent = self.WorkflowTemplateParentName()
    if not workflow_template:
      workflow_template = self.MakeWorkflowTemplate()
    if not (response or exception):
      response = workflow_template
    self.mock_client.projects_regions_workflowTemplates.Create.Expect(
        self.messages.DataprocProjectsRegionsWorkflowTemplatesCreateRequest(
            workflowTemplate=workflow_template, parent=parent),
        response=response,
        exception=exception)


class WorkflowTemplateCreateUnitTestBeta(WorkflowTemplateCreateUnitTest):

  def SetUp(self):
    self.SetupForReleaseTrack(calliope.base.ReleaseTrack.BETA)

  def testCreateWorkflowTemplates(self):
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectCreateWorkflowTemplate(workflow_template, workflow_template)
    result = self.RunDataproc(
        'workflow-templates create {0}'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)

  def testCreateWorkflowTemplatesWithRegion(self):
    properties.VALUES.dataproc.region.Set('us-test1')
    parent = self.WorkflowTemplateParentName(region='us-test1')
    template_name = self.WorkflowTemplateName(region='us-test1')
    workflow_template = self.MakeWorkflowTemplate(name=template_name)
    self.ExpectCreateWorkflowTemplate(workflow_template, workflow_template,
                                      parent)
    result = self.RunDataproc(
        'workflow-templates create {0}'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)

  def testCreateWorkflowTemplatesWithLabels(self):
    labels = {'k1': 'v1'}
    workflow_template = self.MakeWorkflowTemplate(labels=labels)
    self.assertTrue(workflow_template.labels is not None)
    self.ExpectCreateWorkflowTemplate(workflow_template, workflow_template)
    result = self.RunDataproc('workflow-templates create {0} --labels=k1=v1'.
                              format(self.WORKFLOW_TEMPLATE))
    self.assertTrue(result.labels is not None)
    self.assertEqual(workflow_template.labels, result.labels)
    self.AssertMessagesEqual(workflow_template, result)
