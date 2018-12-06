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
"""Test of the 'workflow-template add-job sparksql' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk import calliope

from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplatesJobSparkSqlUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for workflow-template add-job sparksql."""
  pass


class WorkflowTemplatesJobSparkSqlUnitTestBeta(
    WorkflowTemplatesJobSparkSqlUnitTest, base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope.base.ReleaseTrack.BETA)

  def testSparkSqlJob(self):
    workflow_template = self.MakeWorkflowTemplate()
    ordered_job = self.MakeOrderedJob(
        sparkSqlJob=self.SPARK_SQL_JOB, step_id='002', start_after=['001'])
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job spark-sql --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG --file {1} '
        '--properties foo=bar,some.key=some.value '.format(
            self.WORKFLOW_TEMPLATE, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)

  def testSparkSqlJobWithExecute(self):
    workflow_template = self.MakeWorkflowTemplate()
    spark_sql_job = self.SPARK_SQL_JOB
    spark_sql_job.queryFileUri = None
    spark_sql_job.queryList = self.messages.QueryList(queries=[self.QUERY])
    ordered_job = self.MakeOrderedJob(
        sparkSqlJob=spark_sql_job, step_id='002', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job spark-sql --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG --execute "{1}" '
        '--properties foo=bar,some.key=some.value'.format(
            self.WORKFLOW_TEMPLATE, self.QUERY))

  def testSparkSqlJobWithParams(self):
    workflow_template = self.MakeWorkflowTemplate()
    spark_sql_job = self.SPARK_SQL_JOB
    spark_sql_job.scriptVariables = encoding.DictToAdditionalPropertyMessage(
        self.PARAMS, self.messages.SparkSqlJob.ScriptVariablesValue)
    ordered_job = self.MakeOrderedJob(
        sparkSqlJob=spark_sql_job, step_id='002', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job spark-sql --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG --file {1} '
        '--properties foo=bar,some.key=some.value '
        '--params foo=bar,var=value'.format(
            self.WORKFLOW_TEMPLATE, self.SCRIPT_URI))

  def testSparkSqlJobWithJars(self):
    workflow_template = self.MakeWorkflowTemplate()
    spark_sql_job = self.SPARK_SQL_JOB
    spark_sql_job.jarFileUris = self.JAR_URIS
    ordered_job = self.MakeOrderedJob(
        sparkSqlJob=spark_sql_job, step_id='002', start_after=['001'])
    self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    self.RunDataproc(
        'workflow-templates add-job spark-sql --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG --file {1} '
        '--properties foo=bar,some.key=some.value --jars {2}'.format(
            self.WORKFLOW_TEMPLATE, self.SCRIPT_URI, ','.join(self.JAR_URIS)))

  def testSparkSqlJobWithLabels(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(
        sparkSqlJob=self.SPARK_SQL_JOB,
        step_id='002',
        start_after=['001'],
        labels=labels)
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job])
    result = self.RunDataproc(
        'workflow-templates add-job spark-sql --workflow-template {0} '
        '--step-id 002 --start-after 001 '
        '--driver-log-levels root=INFO,com.example=DEBUG --file {1} '
        '--labels some_label_key=some_label_value '
        '--properties foo=bar,some.key=some.value '.format(
            self.WORKFLOW_TEMPLATE, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
