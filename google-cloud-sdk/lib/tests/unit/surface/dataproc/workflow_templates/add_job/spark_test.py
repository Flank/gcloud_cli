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
"""Test of the 'workflow-template add-job spark' command."""

from googlecloudsdk import calliope

from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplatesJobSparkUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for workflow-template add-job spark."""
  pass


class WorkflowTemplatesJobSparkUnitTestBeta(WorkflowTemplatesJobSparkUnitTest,
                                            base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testSparkJob(self):
    workflow_template = self.MakeWorkflowTemplate()
    ordered_job = self.MakeOrderedJob(
        sparkJob=self.SPARK_JOB, step_id='002', start_after=['001'])
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job spark --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--class {1} -- foo --bar baz '.format(self.WORKFLOW_TEMPLATE,
                                               self.CLASS))
    self.AssertMessagesEqual(expected, result)

  def testSparkJobWithJarsFilesArchives(self):
    workflow_template = self.MakeWorkflowTemplate()
    spark_job = self.SPARK_JOB
    spark_job.jarFileUris = self.JAR_URIS
    spark_job.archiveUris = self.ARCHIVE_URIS
    spark_job.fileUris = self.FILE_URIS
    ordered_job = self.MakeOrderedJob(
        sparkJob=spark_job, step_id='002', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job spark --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--class {1} --jars {2} --archives {3} --files {4} '
        '-- foo --bar baz '.format(self.WORKFLOW_TEMPLATE,
                                   self.CLASS,
                                   ','.join(self.JAR_URIS),
                                   ','.join(self.ARCHIVE_URIS),
                                   ','.join(self.FILE_URIS)))

  def testSparkJobWithJar(self):
    workflow_template = self.MakeWorkflowTemplate()
    spark_job = self.SPARK_JOB
    spark_job.mainClass = None
    spark_job.mainJarFileUri = self.JAR_URI
    ordered_job = self.MakeOrderedJob(
        sparkJob=spark_job, step_id='002', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job spark --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--jar {1} -- foo --bar baz '.format(self.WORKFLOW_TEMPLATE,
                                             self.JAR_URI))

  def testSparkJobWithLabels(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(
        sparkJob=self.SPARK_JOB,
        step_id='002',
        start_after=['001'],
        labels=labels)
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job spark --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--labels some_label_key=some_label_value '
        '--properties foo=bar,some.key=some.value '
        '--class {1} -- foo --bar baz '.format(self.WORKFLOW_TEMPLATE,
                                               self.CLASS))
    self.AssertMessagesEqual(expected, result)
