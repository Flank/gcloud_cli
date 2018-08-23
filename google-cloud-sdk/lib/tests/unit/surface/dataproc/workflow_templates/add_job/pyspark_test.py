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
"""Test of the 'workflow-template add-job pyspark' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope

from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplatesJobPySparkUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for workflow-template add-job pyspark."""
  pass


class WorkflowTemplatesJobPySparkUnitTestBeta(
    WorkflowTemplatesJobPySparkUnitTest, base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testPysparkJob(self):
    workflow_template = self.MakeWorkflowTemplate()
    ordered_job = self.MakeOrderedJob(
        pysparkJob=self.PYSPARK_JOB, step_id='002', start_after=['001'])
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job pyspark --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--jars {1} {2} -- foo --bar baz '.format(
            self.WORKFLOW_TEMPLATE, ','.join(self.JAR_URIS), self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)

  def testPysparkJobWithPyfilesFilesArchives(self):
    workflow_template = self.MakeWorkflowTemplate()
    pyspark_job = self.PYSPARK_JOB
    pyspark_job.pythonFileUris = self.PYFILE_URIS
    pyspark_job.archiveUris = self.ARCHIVE_URIS
    pyspark_job.fileUris = self.FILE_URIS
    ordered_job = self.MakeOrderedJob(
        pysparkJob=pyspark_job, step_id='002', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job pyspark --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--jars {1} {2} --archives {3} --files {4} --py-files {5} '
        '-- foo --bar baz '.format(
            self.WORKFLOW_TEMPLATE, ','.join(self.JAR_URIS), self.SCRIPT_URI,
            ','.join(self.ARCHIVE_URIS), ','.join(self.FILE_URIS),
            ','.join(self.PYFILE_URIS)))

  def testPysparkJobWithLabels(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(
        pysparkJob=self.PYSPARK_JOB,
        step_id='002',
        start_after=['001'],
        labels=labels)
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job pyspark --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--labels some_label_key=some_label_value '
        '--properties foo=bar,some.key=some.value '
        '--jars {1} {2} -- foo --bar baz '.format(
            self.WORKFLOW_TEMPLATE, ','.join(self.JAR_URIS), self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
