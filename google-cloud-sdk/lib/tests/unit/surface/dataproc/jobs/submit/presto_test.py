# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Test of the 'jobs submit presto' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsSubmitPrestoUnitTest(jobs_unit_base.JobsUnitTestBase):
  pass  # Presto jobs are beta only


class JobsSubmitPrestoUnitTestBeta(jobs_unit_base.JobsUnitTestBase,
                                   base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

  def testSubmitPrestoJob(self):
    job = self.MakeJob(prestoJob=self.PRESTO_JOB)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit presto --cluster {0} --id {1} --file {2} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--query-output-format foo-output '
        '--client-tags foo-tag,bar-tag '
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitPrestoJobWithExecute(self):
    presto_job = self.PRESTO_JOB
    presto_job.queryFileUri = None
    presto_job.queryList = self.messages.QueryList(queries=[self.QUERY])
    job = self.MakeJob(prestoJob=presto_job)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit presto --cluster {0} --id {1} --execute "{2}" '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--query-output-format foo-output '
        '--client-tags foo-tag,bar-tag '
        .format(self.CLUSTER_NAME, self.JOB_ID, self.QUERY))
    self.AssertMessagesEqual(expected, result)

  def testSubmitPrestoJobWithContinue(self):
    presto_job = self.PRESTO_JOB
    presto_job.continueOnFailure = True
    job = self.MakeJob(prestoJob=presto_job)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit presto --cluster {0} --id {1} --file {2} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--query-output-format foo-output '
        '--client-tags foo-tag,bar-tag '
        '--continue-on-failure'
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)

  def testSubmitPrestoJobWithLabels(self):
    job = self.MakeJob(prestoJob=self.PRESTO_JOB)
    labels = {'some-label-key': 'some-label-value'}
    job.labels = self.ConvertLabels(labels)

    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit presto --cluster {0} --id {1} --file {2} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--query-output-format foo-output '
        '--labels some-label-key=some-label-value '
        '--client-tags foo-tag,bar-tag '
        .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))
    self.AssertMessagesEqual(expected, result)

  def testSubmitPrestoJobNoGetPermission(self):
    job = self.MakeJob(prestoJob=self.PRESTO_JOB)

    self.ExpectGetCluster()
    self.ExpectSubmitJob(job)
    self.ExpectGetJob(job=job, exception=self.MakeHttpError(403))

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc(
          'jobs submit presto --cluster {0} --id {1} --file {2} '
          '--driver-log-levels root=INFO,com.example=DEBUG '
          '--properties foo=bar,some.key=some.value '
          '--query-output-format foo-output '
          '--client-tags foo-tag,bar-tag '
          .format(self.CLUSTER_NAME, self.JOB_ID, self.SCRIPT_URI))


class JobsSubmitPrestoUnitTestAlpha(jobs_unit_base.JobsUnitTestBase,
                                    base.DataprocTestBaseAlpha):
  pass

if __name__ == '__main__':
  sdk_test_base.main()
