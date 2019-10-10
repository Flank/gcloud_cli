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
"""Test of the 'dataflow jobs describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID


class DescribeUnitTest(
    base.DataflowMockingTestBase, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    env_class = base.MESSAGE_MODULE.Environment
    self.fake_environment = env_class(
        dataset='dataset',
        experiments=['exp1', 'exp2'])
    self.view_all = (
        base.MESSAGE_MODULE.DataflowProjectsLocationsJobsGetRequest.
        ViewValueValuesEnum.JOB_VIEW_ALL)

  def testDescribe(self):
    self.MockGetJob(self.SampleJob(JOB_1_ID))

    job = self.Run('beta dataflow jobs describe ' + JOB_1_ID)
    self.assertEqual(JOB_1_ID, job.id)
    self.assertIsNone(job.environment)

  def testDescribeRegionSet(self):
    my_region = 'europe-west1'
    self.MockGetJob(
        self.SampleJob(JOB_1_ID, region=my_region), location=my_region)

    job = self.Run('beta dataflow jobs describe --region=' + my_region + ' ' +
                   JOB_1_ID)
    self.assertEqual(JOB_1_ID, job.id)
    self.assertIsNone(job.environment)

  def testDescribeFull(self):
    self.MockGetJob(
        self.SampleJob(JOB_1_ID, environment=self.fake_environment),
        view=self.view_all)

    job = self.Run('beta dataflow jobs describe --full ' + JOB_1_ID)
    self.assertIsNotNone(job.environment)
    self.assertEqual(self.fake_environment, job.environment)

  def testDescribeMissingJobId(self):
    # argparse raises SystemExit rather than ArgumentError for missing
    # required arguments.
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_ID: Must be specified.'):
      self.Run('beta dataflow jobs describe')

  def testDescribeNoSuchJob(self):
    self.MockGetJobFailure(JOB_1_ID)
    with self.AssertRaisesHttpExceptionRegexp(
        r'Requested entity was not found.'.format(normalize_space=True)):
      self.Run('beta dataflow jobs describe ' + JOB_1_ID)

    # Neither stdout nor stderr should contain Http(Exception|Error)
    self.AssertErrNotContains('HttpE')
    self.AssertOutputNotContains('HttpE')


if __name__ == '__main__':
  test_case.main()
