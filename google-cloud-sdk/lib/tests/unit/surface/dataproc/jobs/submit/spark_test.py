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

"""Test of the 'jobs submit spark' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_attr
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsSubmitSparkUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs submit spark."""

  def testSubmitSparkJob(self):
    job = self.MakeJob(sparkJob=self.SPARK_JOB)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit spark --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--class {2} -- foo --bar baz '
        .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitSparkJobJarClass(self):
    job = self.MakeJob(sparkJob=copy.deepcopy(self.SPARK_JOB))
    job.sparkJob.jarFileUris = [self.JAR_URI]
    with self.AssertRaisesArgumentErrorMatches(
        'argument --class: Exactly one of (--class | --jar) '
        'must be specified.'):
      self.RunDataproc(
          'jobs submit spark --cluster {0} --id {1} '
          '--driver-log-levels root=INFO,com.example=DEBUG '
          '--properties foo=bar,some.key=some.value '
          '--class {2} --jar {3} -- foo --bar baz '
          .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS, self.JAR_URI))

  def testSubmitSparkJobWithJarsFilesArchives(self):
    spark_job = self.SPARK_JOB
    spark_job.fileUris = self.FILE_URIS
    spark_job.jarFileUris = self.JAR_URIS
    spark_job.archiveUris = self.ARCHIVE_URIS
    job = self.MakeJob(sparkJob=spark_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit spark --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--jars {3} --files {4} --archives {5} '
        '--class {2} -- foo --bar baz'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS,
                ','.join(self.JAR_URIS), ','.join(self.FILE_URIS),
                ','.join(self.ARCHIVE_URIS)))

  def testSubmitSparkJobWithJar(self):
    spark_job = self.SPARK_JOB
    spark_job.mainClass = None
    spark_job.mainJarFileUri = self.JAR_URI
    job = self.MakeJob(sparkJob=spark_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit spark --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--jar {2} -- foo --bar baz'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.JAR_URI))

  def testSubmitSparkJobWithLabels(self):
    job = self.MakeJob(sparkJob=self.SPARK_JOB)
    labels = {'some-label-key': 'some-label-value'}
    job.labels = self.ConvertLabels(labels)

    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc('jobs submit spark --cluster {0} --id {1} '
                              '--driver-log-levels root=INFO,com.example=DEBUG '
                              '--properties foo=bar,some.key=some.value '
                              '--labels some-label-key=some-label-value '
                              '--class {2} -- foo --bar baz '.format(
                                  self.CLUSTER_NAME, self.JOB_ID, self.CLASS))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitSparkJobNoJobGetPermission(self):
    job = self.MakeJob(sparkJob=self.SPARK_JOB)
    self.ExpectGetCluster()
    self.ExpectSubmitJob(job)
    self.ExpectGetJob(job=job, exception=self.MakeHttpError(403))

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('jobs submit spark --cluster {0} --id {1} '
                       '--driver-log-levels root=INFO,com.example=DEBUG '
                       '--properties foo=bar,some.key=some.value '
                       '--class {2} -- foo --bar baz '.format(
                           self.CLUSTER_NAME, self.JOB_ID, self.CLASS))

  def testSubmitRestartableJob(self):
    self.StartObjectPatch(console_attr.ConsoleAttr, 'GetTermSize',
                          return_value=(80, 100))
    job = self.MakeJob(sparkJob=self.SPARK_JOB)
    scheduling = self.messages.JobScheduling(maxFailuresPerHour=1)
    job.scheduling = scheduling

    job = self.ExpectSubmitCalls(job, final_state=self.STATE_ENUM.RUNNING)
    job = copy.deepcopy(job)
    job.driverOutputResourceUri = self.DRIVER_URI + '2'
    self.ExpectGetJob(job=job)
    job = copy.deepcopy(job)
    job.driverOutputResourceUri = self.DRIVER_URI + '3'
    self.ExpectGetJob(job=job)
    job = copy.deepcopy(job)
    job.status.state = self.STATE_ENUM.DONE
    self.ExpectGetJob(job=job)
    result = self.RunDataproc('jobs submit spark --cluster {0} --id {1} '
                              '--driver-log-levels root=INFO,com.example=DEBUG '
                              '--properties foo=bar,some.key=some.value '
                              '--max-failures-per-hour 1 '
                              '--class {2} -- foo --bar baz '.format(
                                  self.CLUSTER_NAME, self.JOB_ID, self.CLASS))
    self.AssertMessagesEqual(job, result)
    self.AssertErrMatches(
        r"""First line of job output\.
        Next line of job output\.
        Yet another line of job output\.
        =+
        WARNING: Job attempt failed\. Streaming new attempt's output\.
        =+
        Oops let's try that again\.
        This time for sure\.
        =+
        WARNING: Job attempt failed\. Streaming new attempt's output\.
        =+
        Why is this happening\?!\?
        All done :D
        Job \[{0}\] finished successfully\.""".format(self.JOB_ID),
        normalize_space=True)


class JobsSubmitSparkUnitTestBeta(JobsSubmitSparkUnitTest,
                                  base.DataprocTestBaseBeta):
  """Tests for dataproc jobs submit spark."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

  def testSubmitSparkJobJarClass(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --class: Exactly one of (--class | --jar) must be '
        'specified.'):
      self.RunDataproc('jobs submit spark --cluster {0} --id {1} '
                       '--driver-log-levels root=INFO,com.example=DEBUG '
                       '--properties foo=bar,some.key=some.value '
                       '--class {2} --jar {3} -- foo --bar baz '.format(
                           self.CLUSTER_NAME, self.JOB_ID, self.CLASS,
                           self.JAR_URI))


class JobsSubmitSparkUnitTestAlpha(
    JobsSubmitSparkUnitTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
