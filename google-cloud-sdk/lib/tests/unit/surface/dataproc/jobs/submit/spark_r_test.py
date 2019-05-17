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
"""Test of the 'jobs submit spark-r command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsSubmitSparkRUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs submit spark-r."""
  pass


class JobsSubmitSparkRUnitTestBeta(JobsSubmitSparkRUnitTest,
                                   base.DataprocTestBaseBeta):
  """Tests for dataproc jobs submit spark-r."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

  def testSubmitSparkRJob(self):
    job = self.MakeJob(sparkRJob=self.SPARK_R_JOB)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc('jobs submit spark-r --cluster {0} --id {1} '
                              '--driver-log-levels root=INFO,com.example=DEBUG '
                              '--properties foo=bar,some.key=some.value '
                              '{2} -- foo --bar baz '.format(
                                  self.CLUSTER_NAME, self.JOB_ID,
                                  self.R_SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(
        textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains('Job [{0}] finished successfully.'.format(
        self.JOB_ID))

  def testSubmitSparkRJobWithFilesArchives(self):
    spark_r_job = self.SPARK_R_JOB
    spark_r_job.fileUris = self.FILE_URIS
    spark_r_job.archiveUris = self.ARCHIVE_URIS
    job = self.MakeJob(sparkRJob=spark_r_job)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc('jobs submit spark-r --cluster {0} --id {1} '
                              '--driver-log-levels root=INFO,com.example=DEBUG '
                              '--properties foo=bar,some.key=some.value '
                              '{2} --files {3} --archives {4} '
                              '-- foo --bar baz '.format(
                                  self.CLUSTER_NAME, self.JOB_ID,
                                  self.R_SCRIPT_URI, ','.join(self.FILE_URIS),
                                  ','.join(self.ARCHIVE_URIS)))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(
        textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains('Job [{0}] finished successfully.'.format(
        self.JOB_ID))

  def testSubmitSparkRJobWithLabels(self):
    job = self.MakeJob(sparkRJob=self.SPARK_R_JOB)
    labels = {'some-label-key': 'some-label-value'}
    job.labels = self.ConvertLabels(labels)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        command=('jobs submit spark-r --cluster {0} --id {1} '
                 '--driver-log-levels root=INFO,com.example=DEBUG '
                 '--properties foo=bar,some.key=some.value '
                 '--labels some-label-key=some-label-value '
                 '{2} -- foo --bar baz '
                ).format(self.CLUSTER_NAME, self.JOB_ID, self.R_SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(
        textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains('Job [{0}] finished successfully.'.format(
        self.JOB_ID))

  def testSubmitSparkRJobNoJobGetPermission(self):
    job = self.MakeJob(sparkRJob=self.SPARK_R_JOB)
    self.ExpectGetCluster()
    self.ExpectSubmitJob(job)
    self.ExpectGetJob(job=job, exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('jobs submit spark-r --cluster {0} --id {1} '
                       '--driver-log-levels root=INFO,com.example=DEBUG '
                       '--properties foo=bar,some.key=some.value '
                       '{2} -- foo --bar baz '.format(
                           self.CLUSTER_NAME, self.JOB_ID, self.R_SCRIPT_URI))


class JobsSubmitSparkRUnitTestAlpha(
    JobsSubmitSparkRUnitTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
