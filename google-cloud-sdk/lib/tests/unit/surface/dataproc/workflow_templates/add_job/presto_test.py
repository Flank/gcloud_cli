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
"""Test of the `workflow-template add-job presto` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope

from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplatesJobPrestoUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for workflow-template add-job presto."""
  pass


class WorkflowTemplatesJobPrestoUnitTestBeta(WorkflowTemplatesJobPrestoUnitTest,
                                             base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testPrestoJob(self):
    workflow_template = self.MakeWorkflowTemplate()
    ordered_job = self.MakeOrderedJob(
        prestoJob=self.PRESTO_JOB, step_id='XYZ', start_after=['001'])
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job presto --workflow-template {0} '
        '--step-id XYZ --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--query-output-format foo-output '
        '--client-tags foo-tag,bar-tag '
        '--file {1} '
        .format(self.WORKFLOW_TEMPLATE, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)

  def testPrestoJobWithExecute(self):
    workflow_template = self.MakeWorkflowTemplate()
    presto_job = self.PRESTO_JOB
    presto_job.queryFileUri = None
    presto_job.queryList = self.messages.QueryList(queries=[self.QUERY])
    ordered_job = self.MakeOrderedJob(
        prestoJob=presto_job, step_id='XYZ', start_after=['001'])
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job presto --workflow-template {0} '
        '--step-id XYZ --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--query-output-format foo-output '
        '--client-tags foo-tag,bar-tag '
        '--execute "{1}" '
        .format(self.WORKFLOW_TEMPLATE, self.QUERY))
    self.AssertMessagesEqual(expected, result)

  def testPrestoJobWithLabels(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(prestoJob=self.PRESTO_JOB, step_id='XYZ',
                                      start_after=['001'], labels=labels)
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job presto --workflow-template {0} '
        '--step-id XYZ --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--query-output-format foo-output '
        '--client-tags foo-tag,bar-tag '
        '--labels some_label_key=some_label_value '
        '--file {1} '
        .format(self.WORKFLOW_TEMPLATE, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)


class WorkflowTemplatesJobPrestoUnitTestAlpha(
    WorkflowTemplatesJobPrestoUnitTest, base.DataprocTestBaseAlpha):
  pass
