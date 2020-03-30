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

"""Test of the 'jobs describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsDescribeUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs describe."""

  def _testDescribeJob(self, region=None, region_flag=''):
    if region is None:
      region = self.REGION

    expected = self.MakeRunningJob(region=region)
    self.ExpectGetJob(expected, region=region)
    result = self.RunDataproc(
        'jobs describe {0} {1}'.format(self.JOB_ID, region_flag))
    self.AssertMessagesEqual(expected, result)

  def testDescribeJob(self):
    self._testDescribeJob()

  def testDescribeJob_regionProperty(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testDescribeJob(region='global')

  def testDescribeJob_regionFlag(self):
    properties.VALUES.dataproc.region.Set('global')
    self._testDescribeJob(
        region='us-central1', region_flag='--region=us-central1')

  def testDescribeJob_withoutRegionProperty(self):
    # No region is specified via flag or config.
    regex = r'Failed to find attribute \[region\]'
    with self.assertRaisesRegex(handlers.ParseError, regex):
      self.RunDataproc('jobs describe my-job', set_region=False)

  def testDescribeJobNotFound(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)
    self.ExpectGetJob(job, exception=self.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches(' not found.'):
      self.RunDataproc('jobs describe ' + self.JOB_ID)


class JobsDescribeUnitTestBeta(JobsDescribeUnitTest, base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


class JobsDescribeUnitTestAlpha(JobsDescribeUnitTestBeta,
                                base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
