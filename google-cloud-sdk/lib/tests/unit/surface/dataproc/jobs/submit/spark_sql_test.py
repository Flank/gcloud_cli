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

"""Test of the 'jobs submit spark_sql' command."""
import textwrap

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsSubmitSparkSqlUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs submit spark_sql."""

  def testSubmitSparkSqlJob(self):
    job = self.MakeJob(sparkSqlJob=self.SPARK_SQL_JOB)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit spark-sql --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG --file {2} '
        '--properties foo=bar,some.key=some.value '
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitSparkSqlJobWithParams(self):
    spark_sql_job = self.SPARK_SQL_JOB
    spark_sql_job.scriptVariables = encoding.PyValueToMessage(
        self.messages.SparkSqlJob.ScriptVariablesValue,
        {'var': 'value', 'foo': 'bar'})
    job = self.MakeJob(sparkSqlJob=spark_sql_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit spark-sql --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG --file {2} '
        '--properties foo=bar,some.key=some.value '
        '--params foo=bar,var=value'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))

  def testSubmitSparkSqlJobWithExecute(self):
    spark_sql_job = self.SPARK_SQL_JOB
    spark_sql_job.queryFileUri = None
    spark_sql_job.queryList = self.messages.QueryList(queries=[self.QUERY])
    job = self.MakeJob(sparkSqlJob=spark_sql_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit spark-sql --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG --execute "{2}" '
        '--properties foo=bar,some.key=some.value'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.QUERY))

  def testSubmitSparkSqlJobWithJars(self):
    spark_sql_job = self.SPARK_SQL_JOB
    spark_sql_job.jarFileUris = self.JAR_URIS
    job = self.MakeJob(sparkSqlJob=spark_sql_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit spark-sql --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG --file {2} '
        '--properties foo=bar,some.key=some.value --jars {3}'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI,
                ','.join(self.JAR_URIS)))

  def testSubmitSparkSqlJobWithLabels(self):
    job = self.MakeJob(sparkSqlJob=self.SPARK_SQL_JOB)
    labels = {'some-label-key': 'some-label-value'}
    job.labels = self.ConvertLabels(labels)

    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        command=('jobs submit spark-sql --cluster {0} --id {1} '
                 '--driver-log-levels root=INFO,com.example=DEBUG --file {2} '
                 '--labels some-label-key=some-label-value '
                 '--properties foo=bar,some.key=some.value ').format(
                     self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitSparkSqlJobNoJobGetPermission(self):
    job = self.MakeJob(sparkSqlJob=self.SPARK_SQL_JOB)
    self.ExpectGetCluster()
    self.ExpectSubmitJob(job)
    self.ExpectGetJob(job=job, exception=self.MakeHttpError(403))

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc(
          'jobs submit spark-sql --cluster {0} --id {1} '
          '--driver-log-levels root=INFO,com.example=DEBUG --file {2} '
          '--properties foo=bar,some.key=some.value '.format(
              self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))

  def testSubmitRestartableJob(self):
    job = self.MakeJob(sparkSqlJob=self.SPARK_SQL_JOB)

    scheduling = self.messages.JobScheduling(maxFailuresPerHour=1)
    job.scheduling = scheduling

    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        command=('jobs submit spark-sql --cluster {0} --id {1} '
                 '--file {2} '
                 '--driver-log-levels root=INFO,com.example=DEBUG '
                 '--max-failures-per-hour 1 '
                 '--properties foo=bar,some.key=some.value ').format(
                     self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))


class JobsSubmitSparkSqlUnitTestBeta(JobsSubmitSparkSqlUnitTest,
                                     base.DataprocTestBaseBeta):
  """Tests for dataproc jobs submit spark_sql."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


if __name__ == '__main__':
  sdk_test_base.main()
