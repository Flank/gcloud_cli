# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Test of the 'jobs submit pig' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsSubmitPigUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs submit pig."""

  def testSubmitPigJob(self):
    job = self.MakeJob(pigJob=self.PIG_JOB)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit pig --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--file {2} --params foo=bar,var=value '
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitPigJobWithExecute(self):
    pig_job = self.PIG_JOB
    pig_job.queryFileUri = None
    pig_job.queryList = self.messages.QueryList(queries=[self.QUERY])
    job = self.MakeJob(pigJob=pig_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit pig --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--execute "{2}" --params foo=bar,var=value'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.QUERY))

  def testSubmitPigJobWithJars(self):
    pig_job = self.PIG_JOB
    pig_job.jarFileUris = self.JAR_URIS
    job = self.MakeJob(pigJob=pig_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit pig --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--file {2} --jars {3} --params foo=bar,var=value'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI,
                ','.join(self.JAR_URIS)))

  def testSubmitPigJobWithContinue(self):
    pig_job = self.PIG_JOB
    pig_job.continueOnFailure = True
    job = self.MakeJob(pigJob=pig_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit pig --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--file {2} --continue-on-failure --params foo=bar,var=value'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))

  def testSubmitPigJobWithLabels(self):
    job = self.MakeJob(pigJob=self.PIG_JOB)
    labels = {'some-label-key': 'some-label-value'}
    job.labels = self.ConvertLabels(labels)

    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        command=('jobs submit pig --cluster {0} --id {1} '
                 '--driver-log-levels root=INFO,com.example=DEBUG '
                 '--properties foo=bar,some.key=some.value '
                 '--labels some-label-key=some-label-value '
                 '--file {2} --params foo=bar,var=value ').format(
                     self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitPigJobNoJobGetPermission(self):
    job = self.MakeJob(pigJob=self.PIG_JOB)

    self.ExpectGetCluster()
    self.ExpectSubmitJob(job)
    self.ExpectGetJob(job=job, exception=self.MakeHttpError(403))

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('jobs submit pig --cluster {0} --id {1} '
                       '--driver-log-levels root=INFO,com.example=DEBUG '
                       '--properties foo=bar,some.key=some.value '
                       '--file {2} --params foo=bar,var=value '.format(
                           self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))

  def testSubmitRestartableJob(self):
    job = self.MakeJob(pigJob=self.PIG_JOB)

    scheduling = self.messages.JobScheduling(maxFailuresPerHour=1)
    job.scheduling = scheduling

    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        command=('jobs submit pig --cluster {0} --id {1} '
                 '--driver-log-levels root=INFO,com.example=DEBUG '
                 '--properties foo=bar,some.key=some.value '
                 '--max-failures-per-hour 1 '
                 '--file {2} --params foo=bar,var=value ').format(
                     self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))


class JobsSubmitPigUnitTestBeta(JobsSubmitPigUnitTest,
                                base.DataprocTestBaseBeta):
  """Tests for dataproc jobs submit pig."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


class JobsSubmitPigUnitTestAlpha(
    JobsSubmitPigUnitTestBeta, base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
