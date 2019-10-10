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

"""Test of the 'jobs wait' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import textwrap

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_attr
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsWaitUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs wait."""

  def testWaitJob(self):
    expected = self.ExpectWaitCalls()
    result = self.RunDataproc('jobs wait ' + self.JOB_ID)
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testWaitCompletedJob(self):
    expected = self.MakeCompletedJob()
    self.ExpectGetJob(job=expected)
    self.ExpectGetJob(job=expected)
    result = self.RunDataproc('jobs wait ' + self.JOB_ID)
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testWaitCompletedJobLateOutput(self):
    job = self.MakeJob(state=self.STATE_ENUM.DONE)
    self.ExpectGetJob(job=job)
    self.ExpectGetJob(job=job)
    self.ExpectGetJob(job=job)
    self.ExpectGetJob(job=job)
    self.ExpectGetJob(job=job)
    self.ExpectGetJob(job=job)
    expected = self.MakeCompletedJob()
    self.ExpectGetJob(job=expected)
    result = self.RunDataproc('jobs wait ' + self.JOB_ID)
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testWaitJobFailure(self):
    self.ExpectWaitCalls(final_state=self.STATE_ENUM.ERROR)
    with self.AssertRaisesExceptionMatches(
        exceptions.JobError, 'Job [{0}] failed.'.format(self.JOB_ID)):
      self.RunDataproc('jobs wait ' + self.JOB_ID)
    self.AssertErrContains(textwrap.dedent("""\
      First line of job output.
      Next line of job output.
      Yet another line of job output.
      Last line of job output."""))

  def testSubmitJobFailureWithDetails(self):
    self.ExpectWaitCalls(
        final_state=self.STATE_ENUM.ERROR,
        details='Something bad')
    with self.AssertRaisesExceptionMatches(
        exceptions.JobError,
        textwrap.dedent("""\
          Job [{0}] failed with error:
          Something bad""".format(self.JOB_ID))):
      self.RunDataproc('jobs wait ' + self.JOB_ID)
    self.AssertErrContains(textwrap.dedent("""\
      First line of job output.
      Next line of job output.
      Yet another line of job output.
      Last line of job output."""))

  def testWaitJobNotFound(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)
    self.ExpectGetJob(job, exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(' not found.'):
      self.RunDataproc('jobs wait ' + self.JOB_ID)
    self.AssertErrNotContains(textwrap.dedent("""\
      First line of job output.
      Next line of job output.
      Yet another line of job output.
      Last line of job output."""))

  def testWaitRestartableJob(self):
    self.StartObjectPatch(console_attr.ConsoleAttr, 'GetTermSize',
                          return_value=(80, 100))
    job = self.ExpectWaitCalls(final_state=self.STATE_ENUM.RUNNING)
    job = copy.deepcopy(job)
    job.driverOutputResourceUri = self.DRIVER_URI + '2'
    self.ExpectGetJob(job=job)
    job = copy.deepcopy(job)
    job.driverOutputResourceUri = self.DRIVER_URI + '3'
    self.ExpectGetJob(job=job)
    job = copy.deepcopy(job)
    job.status.state = self.STATE_ENUM.DONE
    self.ExpectGetJob(job=job)
    result = self.RunDataproc('jobs wait ' + self.JOB_ID)
    self.AssertMessagesEqual(job, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        ================================================================================
        WARNING: Job attempt failed. Streaming new attempt's output.
        ================================================================================
        Oops let's try that again.
        This time for sure.
        ================================================================================
        WARNING: Job attempt failed. Streaming new attempt's output.
        ================================================================================
        Why is this happening?!?
        All done :D
        Job [{0}] finished successfully.""").format(self.JOB_ID))

  def testWaitJobNoGetJobPermissions(self):
    job = self.MakeSubmittedJob()

    self.ExpectGetJob(
        job=job,
        exception=self.MakeHttpError(403))

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('jobs wait ' + self.JOB_ID)


class JobsWaitUnitTestBeta(JobsWaitUnitTest, base.DataprocTestBaseBeta):
  """Tests for dataproc jobs wait."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)


class JobsWaitUnitTestAlpha(JobsWaitUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  sdk_test_base.main()
