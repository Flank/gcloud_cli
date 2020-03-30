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
"""Test of the 'workflow template delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateDeleteUnitTest(unit_base.DataprocUnitTestBase,
                                     compute_base.BaseComputeUnitTest):
  """Tests for workflow template delete."""

  def ExpectDeleteWorkflowTemplate(self,
                                   workflow_template_name=None,
                                   version=None,
                                   response=None,
                                   exception=None,
                                   region=None):
    if region is None:
      region = self.REGION
    if not workflow_template_name:
      workflow_template_name = self.WorkflowTemplateName(region=region)
    if not (response or exception):
      response = self.messages.Empty()
    self.mock_client.projects_regions_workflowTemplates.Delete.Expect(
        self.messages.DataprocProjectsRegionsWorkflowTemplatesDeleteRequest(
            name=workflow_template_name, version=version),
        response=response,
        exception=exception)

  def _testDeleteWorkflowTemplates(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION
    self.ExpectDeleteWorkflowTemplate(region=region)
    self.WriteInput('Y\n')
    result = self.RunDataproc('workflow-templates delete {0} {1}'.format(
        self.WORKFLOW_TEMPLATE, region_flag))
    self.AssertErrContains(
        "The workflow template '[test-workflow-template]' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(None, result)

  def testDeleteWorkflowTemplates(self):
    self._testDeleteWorkflowTemplates()

  def testDeleteWorkflowTemplates_regionProperty(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testDeleteWorkflowTemplates(region='global')

  def testDeleteWorkflowTemplates_regionFlag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testDeleteWorkflowTemplates(
        region='us-central1', region_flag='--region=us-central1')

  def testDeleteWorkflowTemplates_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('workflow-templates delete foo', set_region=False)

  def testDeleteWorkflowTemplatesDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.RunDataproc(
          'workflow-templates delete {0}'.format(self.WORKFLOW_TEMPLATE))
      self.AssertErrContains(
          "The workflow template '[test-workflow-template]' will be deleted.")
      self.AssertErrContains('PROMPT_CONTINUE')

  def testDeleteWorkflowTemplatesRegion(self):
    properties.VALUES.dataproc.region.Set('us-west1-a')
    template_name = self.WorkflowTemplateName(region='us-west1-a')
    self.ExpectDeleteWorkflowTemplate(workflow_template_name=template_name)
    self.WriteInput('Y\n')
    result = self.RunDataproc(
        'workflow-templates delete {0}'.format(self.WORKFLOW_TEMPLATE))
    self.AssertErrContains(
        "The workflow template '[test-workflow-template]' will be deleted.")
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertMessagesEqual(None, result)


class WorkflowTemplateDeleteTestBeta(WorkflowTemplateDeleteUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA


class WorkflowTemplateDeleteTestAlpha(WorkflowTemplateDeleteTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  sdk_test_base.main()
