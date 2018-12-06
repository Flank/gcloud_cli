# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Test of the 'workflow-templates export' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk import calliope
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateExportUnitTest(unit_base.DataprocUnitTestBase,
                                     compute_base.BaseComputeUnitTest):
  """Tests for workflow template export."""

  def testExportWorkflowTemplatesToStdOut(self):
    workflow_template = self.MakeWorkflowTemplate(labels={'foo': 'bar'})

    # Expected output has template-specific info cleared.
    expected_output = copy.deepcopy(workflow_template)
    expected_output.id = None
    expected_output.name = None

    self.ExpectGetWorkflowTemplate(response=workflow_template)
    self.RunDataproc('workflow-templates export {0}'.format(
        self.WORKFLOW_TEMPLATE))
    self.AssertOutputEquals(export_util.Export(expected_output))

  def testExportWorkflowTemplatesHttpError(self):
    self.ExpectGetWorkflowTemplate(exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('workflow-templates export {0}'.format(
          self.WORKFLOW_TEMPLATE))

  def testExportWorkflowTemplatesWithVersion(self):
    workflow_template = self.MakeWorkflowTemplate(
        version=2, labels={'foo': 'bar'})

    # Expected output has template-specific info cleared.
    expected_output = copy.deepcopy(workflow_template)
    expected_output.id = None
    expected_output.name = None
    expected_output.version = None

    self.ExpectGetWorkflowTemplate(version=2, response=workflow_template)
    self.RunDataproc('workflow-templates export {0} --version 2'.format(
        self.WORKFLOW_TEMPLATE))
    self.AssertOutputEquals(export_util.Export(expected_output))

  def testExportWorkflowTemplatesToFile(self):
    dataproc = dp.Dataproc(calliope.base.ReleaseTrack.GA)
    msgs = dataproc.messages
    workflow_template = self.MakeWorkflowTemplate(labels={'foo': 'bar'})

    # Expected output has template-specific info cleared.
    expected_output = copy.deepcopy(workflow_template)
    expected_output.id = None
    expected_output.name = None

    self.ExpectGetWorkflowTemplate(response=workflow_template)
    file_name = os.path.join(self.temp_path, 'template.yaml')
    result = self.RunDataproc(
        'workflow-templates export {0} --destination {1}'.format(
            self.WORKFLOW_TEMPLATE, file_name))
    self.assertIsNone(result)
    data = console_io.ReadFromFileOrStdin(file_name or '-', binary=False)
    exported_template = export_util.Import(
        message_type=msgs.WorkflowTemplate, stream=data)
    self.AssertMessagesEqual(expected_output, exported_template)


class WorkflowTemplateExportUnitTestBeta(WorkflowTemplateExportUnitTest):

  def SetUp(self):
    self.SetupForReleaseTrack(calliope.base.ReleaseTrack.BETA)

  def testExportWorkflowTemplatesToFile(self):
    dataproc = dp.Dataproc(calliope.base.ReleaseTrack.BETA)
    msgs = dataproc.messages
    workflow_template = self.MakeWorkflowTemplate(labels={'foo': 'bar'})

    # Expected output has template-specific info cleared.
    expected_output = copy.deepcopy(workflow_template)
    expected_output.id = None
    expected_output.name = None

    self.ExpectGetWorkflowTemplate(response=workflow_template)
    file_name = os.path.join(self.temp_path, 'template.yaml')
    result = self.RunDataproc(
        'workflow-templates export {0} --destination {1}'.format(
            self.WORKFLOW_TEMPLATE, file_name))
    self.assertIsNone(result)
    data = console_io.ReadFromFileOrStdin(file_name or '-', binary=False)
    exported_template = export_util.Import(
        message_type=msgs.WorkflowTemplate, stream=data)
    self.AssertMessagesEqual(expected_output, exported_template)

if __name__ == '__main__':
  sdk_test_base.main()
