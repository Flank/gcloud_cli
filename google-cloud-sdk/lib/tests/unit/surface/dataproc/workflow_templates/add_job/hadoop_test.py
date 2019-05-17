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
"""Test of the 'workflow-template add-job hadoop' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope

from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplatesJobHadoopUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc workflow-template add-job hadoop."""
  pass


class WorkflowTemplatesJobHadoopUnitTestBeta(WorkflowTemplatesJobHadoopUnitTest,
                                             base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testHadoopJob(self):
    workflow_template = self.MakeWorkflowTemplate()
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template)
    result = self.RunDataproc(
        'workflow-templates add-job hadoop --workflow-template {0} '
        '--step-id 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--class {1} -- foo --bar baz'.format(self.WORKFLOW_TEMPLATE,
                                              self.CLASS))
    self.AssertMessagesEqual(expected, result)

  def testHadoopJobWithArchivesFilesJars(self):
    hadoop_job = self.HADOOP_JOB
    hadoop_job.archiveUris = self.ARCHIVE_URIS
    hadoop_job.jarFileUris = self.JAR_URIS
    hadoop_job.fileUris = self.FILE_URIS
    ordered_job = self.MakeOrderedJob(
        step_id='001',
        hadoopJob=hadoop_job)
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job hadoop --workflow-template {0} '
        '--step-id 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--class {1} --archives {2} --jars {3} --files {4} '
        '-- foo --bar baz'
        .format(self.WORKFLOW_TEMPLATE, self.CLASS,
                ','.join(self.ARCHIVE_URIS), ','.join(self.JAR_URIS),
                ','.join(self.FILE_URIS)))

  def testHadoopJobWithJar(self):
    hadoop_job = self.HADOOP_JOB
    hadoop_job.mainClass = None
    hadoop_job.mainJarFileUri = self.JAR_URI
    ordered_job = self.MakeOrderedJob(
        step_id='001',
        hadoopJob=hadoop_job)
    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job hadoop --workflow-template {0} '
        '--step-id 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--jar {1} -- foo --bar baz'.format(self.WORKFLOW_TEMPLATE,
                                            self.JAR_URI))

  def testHadoopJobJarClass(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --class: Exactly one of (--class | --jar) '
        'must be specified.'):
      self.RunDataproc(
          'workflow-templates add-job hadoop --workflow-template {0} '
          '--step-id 001 '
          '--driver-log-levels root=INFO,com.example=DEBUG '
          '--properties foo=bar,some.key=some.value '
          '--class {1} --jar {2} -- foo --bar baz '.format(
              self.WORKFLOW_TEMPLATE, self.CLASS, self.JAR_URI))

  def testHadoopJobWithLabels(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(
        step_id='001',
        start_after=['002'],
        hadoopJob=self.HADOOP_JOB,
        labels=labels)
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job hadoop --workflow-template {0} '
        '--step-id 001 --start-after 002 '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--labels some_label_key=some_label_value '
        '--class {1} -- foo --bar baz'.format(self.WORKFLOW_TEMPLATE,
                                              self.CLASS))
    self.AssertMessagesEqual(expected, result)


class WorkflowTemplatesJobHadoopUnitTestAlpha(
    WorkflowTemplatesJobHadoopUnitTestBeta, base.DataprocTestBaseAlpha):
  pass
