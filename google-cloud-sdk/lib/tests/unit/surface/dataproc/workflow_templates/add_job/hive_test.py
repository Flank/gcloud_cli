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
"""Test of the 'workflow-template add-job hive' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk import calliope

from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplatesJobHiveUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for workflow-template add-job hive."""
  pass


class WorkflowTemplatesJobHiveUnitTestBeta(WorkflowTemplatesJobHiveUnitTest,
                                           base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testHiveJob(self):
    workflow_template = self.MakeWorkflowTemplate()
    ordered_job = self.MakeOrderedJob(
        hiveJob=self.HIVE_JOB, step_id='012', start_after=['011'])
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job hive --workflow-template {0} '
        '--step-id 012 --start-after 011 '
        '--file {1} --params foo=bar,var=value '
        '--properties foo=bar,some.key=some.value '.format(
            self.WORKFLOW_TEMPLATE, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)

  def testHiveJobWithExecute(self):
    workflow_template = self.MakeWorkflowTemplate()
    hive_job = self.HIVE_JOB
    hive_job.queryFileUri = None
    hive_job.queryList = self.messages.QueryList(queries=[self.QUERY])
    ordered_job = self.MakeOrderedJob(
        hiveJob=hive_job, step_id='012', start_after=['011'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job hive --workflow-template {0} '
        '--step-id 012 --start-after 011 '
        '--execute "{1}" --params foo=bar,var=value '
        '--properties foo=bar,some.key=some.value '.format(
            self.WORKFLOW_TEMPLATE, self.QUERY))

  def testHiveJobWithJars(self):
    workflow_template = self.MakeWorkflowTemplate()
    hive_job = self.HIVE_JOB
    hive_job.jarFileUris = self.JAR_URIS
    ordered_job = self.MakeOrderedJob(
        hiveJob=hive_job, step_id='012', start_after=['011'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job hive --workflow-template {0} '
        '--step-id 012 --start-after 011 '
        '--file {1} --jars {2} --params foo=bar,var=value '
        '--properties foo=bar,some.key=some.value '.format(
            self.WORKFLOW_TEMPLATE, self.SCRIPT_URI, ','.join(self.JAR_URIS)))

  def testHiveJobWithContinue(self):
    workflow_template = self.MakeWorkflowTemplate()
    hive_job = self.HIVE_JOB
    hive_job.continueOnFailure = True
    ordered_job = self.MakeOrderedJob(
        hiveJob=hive_job, step_id='012', start_after=['011'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job hive --workflow-template {0} '
        '--step-id 012 --start-after 011 '
        '--file {1} --params foo=bar,var=value '
        '--properties foo=bar,some.key=some.value --continue-on-failure'.format(
            self.WORKFLOW_TEMPLATE, self.SCRIPT_URI))

  def testHiveJobWithLabels(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(
        hiveJob=self.HIVE_JOB,
        step_id='ABC',
        start_after=['AAA'],
        labels=labels)
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job hive --workflow-template {0} '
        '--step-id ABC --start-after AAA '
        '--file {1} --params foo=bar,var=value '
        '--labels some_label_key=some_label_value '
        '--properties foo=bar,some.key=some.value '.format(
            self.WORKFLOW_TEMPLATE, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
