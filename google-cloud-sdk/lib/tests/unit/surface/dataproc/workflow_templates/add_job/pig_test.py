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
"""Test of the 'workflow-template add-job pig' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope

from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplatesJobPigUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for workflow-template add-job pig."""
  pass


class WorkflowTemplatesJobPigUnitTestBeta(WorkflowTemplatesJobPigUnitTest,
                                          base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testPigJob(self):
    workflow_template = self.MakeWorkflowTemplate()
    ordered_job = self.MakeOrderedJob(
        pigJob=self.PIG_JOB, step_id='XYZ', start_after=['001'])
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job pig --workflow-template {0} '
        '--step-id XYZ --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--file {1} --params foo=bar,var=value '.format(self.WORKFLOW_TEMPLATE,
                                                        self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)

  def testPigJobWithExecute(self):
    workflow_template = self.MakeWorkflowTemplate()
    pig_job = self.PIG_JOB
    pig_job.queryFileUri = None
    pig_job.queryList = self.messages.QueryList(queries=[self.QUERY])
    ordered_job = self.MakeOrderedJob(
        pigJob=pig_job, step_id='XYZ', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job pig --workflow-template {0} '
        '--step-id XYZ --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--params foo=bar,var=value --execute "{1}"'.format(
            self.WORKFLOW_TEMPLATE,
            self.QUERY))

  def testPigJobWithJars(self):
    workflow_template = self.MakeWorkflowTemplate()
    pig_job = self.PIG_JOB
    pig_job.jarFileUris = self.JAR_URIS
    ordered_job = self.MakeOrderedJob(
        pigJob=pig_job, step_id='XYZ', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job pig --workflow-template {0} '
        '--step-id XYZ --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--file {1} --params foo=bar,var=value '
        '--jars {2}'.format(self.WORKFLOW_TEMPLATE,
                            self.SCRIPT_URI,
                            ','.join(self.JAR_URIS)))

  def testPigJobWithContinue(self):
    workflow_template = self.MakeWorkflowTemplate()
    pig_job = self.PIG_JOB
    pig_job.continueOnFailure = True
    ordered_job = self.MakeOrderedJob(
        pigJob=pig_job, step_id='XYZ', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job pig --workflow-template {0} '
        '--step-id XYZ --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value --continue-on-failure '
        '--file {1} --params foo=bar,var=value '.format(self.WORKFLOW_TEMPLATE,
                                                        self.SCRIPT_URI))

  def testPigJobWithLabels(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(
        pigJob=self.PIG_JOB, step_id='ABC', start_after=['XYZ'], labels=labels)
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job pig --workflow-template {0} '
        '--step-id ABC --start-after XYZ '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--labels some_label_key=some_label_value '
        '--properties foo=bar,some.key=some.value '
        '--file {1} --params foo=bar,var=value '.format(self.WORKFLOW_TEMPLATE,
                                                        self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)


class WorkflowTemplatesJobPigUnitTestAlpha(WorkflowTemplatesJobPigUnitTestBeta,
                                           base.DataprocTestBaseAlpha):
  pass
