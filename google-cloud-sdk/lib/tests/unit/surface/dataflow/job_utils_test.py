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
"""Tests for the job_utils."""

from __future__ import absolute_import
from __future__ import unicode_literals
import shlex

from googlecloudsdk.command_lib.dataflow import job_utils
from tests.lib import test_case
from tests.lib.calliope import util
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID
JOB_2_ID = base.JOB_2_ID

REGION = 'europe-west1'


class _BaseJobHelpersTest(base.DataflowMockingTestBase):

  def SetUp(self):
    self.parser = util.ArgumentParser()

  def ParseArgs(self, cmdline):
    return self.parser.parse_args(args=shlex.split(cmdline, comments=True))

  def AssertJobRef(self, job_ref, job_id, project_id=None, location=None):
    location = location or base.DEFAULT_REGION

    self.assertEqual(
        project_id or self.Project(), job_ref.projectId)
    self.assertEqual(location, job_ref.location)
    self.assertEqual(job_id, job_ref.jobId)


class OneJobHelperTest(_BaseJobHelpersTest):

  def SetUp(self):
    job_utils.ArgsForJobRef(self.parser)

  def testExtractJobRef(self):
    self.AssertJobRef(
        job_utils.ExtractJobRef(self.ParseArgs(JOB_1_ID)), job_id=JOB_1_ID)

  def testExtractJobRefAndRegion(self):
    self.AssertJobRef(
        job_utils.ExtractJobRef(
            self.parser.parse_args(['--region=%s' % REGION, JOB_1_ID])),
        job_id=JOB_1_ID,
        location=REGION)

  def testExtractJobRefMissingRequiredArg(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_ID: Must be specified.'):
      self.parser.parse_args([])

  def testExtractJobRefMissingRequiredArgButHasRegion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_ID: Must be specified.'):
      job_utils.ExtractJobRef(self.parser.parse_args(
          ['--region=%s' % (REGION)]))


class MultiJobHelperTest(_BaseJobHelpersTest):

  def testExtractJobRefsNone(self):
    job_utils.ArgsForJobRefs(self.parser, nargs='+')
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_ID [JOB_ID ...]: Must be specified.'):
      job_utils.ExtractJobRef(self.parser.parse_args([]))

  def testExtractJobRefsNoneButHasRegion(self):
    job_utils.ArgsForJobRefs(self.parser, nargs='+')
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_ID [JOB_ID ...]: Must be specified.'):
      job_utils.ExtractJobRef(
          self.parser.parse_args(['--region=%s' % (REGION)]))

  def testExtractJobRefsNoneOptional(self):
    job_utils.ArgsForJobRefs(self.parser, nargs='*')
    self.assertEqual([], job_utils.ExtractJobRefs(self.parser.parse_args([])))

  def testExtractJobRefsOne(self):
    job_utils.ArgsForJobRefs(self.parser, nargs='+')
    jobs = job_utils.ExtractJobRefs(self.parser.parse_args([JOB_1_ID]))
    self.assertEqual(1, len(jobs))
    self.AssertJobRef(jobs[0], JOB_1_ID)

  def testExtractJobRefsTwo(self):
    job_utils.ArgsForJobRefs(self.parser, nargs='+')
    jobs = job_utils.ExtractJobRefs(
        self.ParseArgs('%s %s' % (JOB_1_ID, JOB_2_ID)))
    self.assertEqual(2, len(jobs))
    self.AssertJobRef(jobs[0], JOB_1_ID)
    self.AssertJobRef(jobs[1], JOB_2_ID)

  def testExtractJobRefsOneWithRegion(self):
    job_utils.ArgsForJobRefs(self.parser, nargs='+')
    jobs = job_utils.ExtractJobRefs(
        self.ParseArgs('--region=%s %s' % (REGION, JOB_1_ID)))
    self.assertEqual(1, len(jobs))
    self.AssertJobRef(jobs[0], JOB_1_ID, location=REGION)

  def testExtractJobRefsTwoWithRegion(self):
    job_utils.ArgsForJobRefs(self.parser, nargs='+')
    jobs = job_utils.ExtractJobRefs(
        self.ParseArgs('--region=%s %s %s' % (REGION, JOB_1_ID, JOB_2_ID)))
    self.assertEqual(2, len(jobs))
    self.AssertJobRef(jobs[0], JOB_1_ID, location=REGION)
    self.AssertJobRef(jobs[1], JOB_2_ID, location=REGION)


if __name__ == '__main__':
  test_case.main()
