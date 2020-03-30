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
"""Test of the 'workflow template create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope

from googlecloudsdk.calliope.concepts import handlers
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
      parent = self.WorkflowTemplateParentName(region=region)
    if not workflow_template:
      workflow_template = self.MakeWorkflowTemplate(region=region)
    if not (response or exception):
      response = workflow_template
    self.mock_client.projects_regions_workflowTemplates.Create.Expect(
        self.messages.DataprocProjectsRegionsWorkflowTemplatesCreateRequest(
            workflowTemplate=workflow_template, parent=parent),
        response=response,
        exception=exception)

  def _testCreateWorkflowTemplates(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    workflow_template = self.MakeWorkflowTemplate(region=region)
    self.ExpectCreateWorkflowTemplate(
        workflow_template, workflow_template, region=region)
    result = self.RunDataproc('workflow-templates create {0} {1}'.format(
        self.WORKFLOW_TEMPLATE, region_flag))
    self.AssertMessagesEqual(workflow_template, result)

  def testCreateWorkflowTemplates(self):
    self._testCreateWorkflowTemplates()

  def testCreateWorkflowTemplates_regionProperty(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testCreateWorkflowTemplates(region='us-central1')

  def testCreateWorkflowTemplates_regionFlag(self):
    properties.VALUES.dataproc.region.Set('us-central1')
    self._testCreateWorkflowTemplates(
        region='us-east4', region_flag='--region=us-east4')

  def testCreateWorkflowTemplates_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('workflow-templates create foo', set_region=False)

  def testCreateWorkflowTemplatesWithRegion(self):
    properties.VALUES.dataproc.region.Set('us-test1')
    parent = self.WorkflowTemplateParentName(region='us-test1')
    template_name = self.WorkflowTemplateName(region='us-test1')
    workflow_template = self.MakeWorkflowTemplate(name=template_name)
    self.ExpectCreateWorkflowTemplate(workflow_template, workflow_template,
                                      parent)
    result = self.RunDataproc('workflow-templates create {0}'.format(
        self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)

  def testCreateWorkflowTemplatesWithLabels(self):
    labels = {'k1': 'v1'}
    workflow_template = self.MakeWorkflowTemplate(labels=labels)
    self.assertIsNotNone(workflow_template.labels)
    self.ExpectCreateWorkflowTemplate(workflow_template, workflow_template)
    result = self.RunDataproc(
        'workflow-templates create {0} --labels=k1=v1'.format(
            self.WORKFLOW_TEMPLATE))
    self.assertIsNotNone(result.labels)
    self.assertEqual(workflow_template.labels, result.labels)
    self.AssertMessagesEqual(workflow_template, result)


class WorkflowTemplateCreateUnitTestBeta(WorkflowTemplateCreateUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA


class WorkflowTemplateCreateUnitTestAlpha(WorkflowTemplateCreateUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
