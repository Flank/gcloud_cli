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
"""Test of the 'workflow template describe' command."""

from googlecloudsdk import calliope

from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateDescribeUnitTest(unit_base.DataprocUnitTestBase,
                                       compute_base.BaseComputeUnitTest):
  """Tests for workflow template describe."""
  pass


class WorkflowTemplateDescribeUnitTestBeta(WorkflowTemplateDescribeUnitTest):

  def SetUp(self):
    self.SetupForReleaseTrack(calliope.base.ReleaseTrack.BETA)

  def testDescribeWorkflowTemplates(self):
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectGetWorkflowTemplate(workflow_template=workflow_template)
    result = self.RunDataproc(
        'workflow-templates describe {0}'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)

  def testCreateWorkflowTemplatesWithVersion(self):
    workflow_template = self.MakeWorkflowTemplate(version=2)
    self.ExpectGetWorkflowTemplate(workflow_template=workflow_template)
    result = self.RunDataproc('workflow-templates describe {0} --version 2'.
                              format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(workflow_template, result)


if __name__ == '__main__':
  sdk_test_base.main()
