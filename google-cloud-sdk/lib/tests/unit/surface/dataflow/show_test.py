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
"""Test of the 'dataflow jobs show' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID


class ShowUnitTest(
    base.DataflowMockingTestBase, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    env_class = base.MESSAGE_MODULE.Environment
    self.fake_environment = env_class(
        dataset='dataset',
        experiments=['exp1', 'exp2'])
    self.view_all = (
        base.MESSAGE_MODULE.DataflowProjectsLocationsJobsGetRequest.
        ViewValueValuesEnum.JOB_VIEW_ALL)

    word_count_json = self.Resource('tests', 'unit', 'surface', 'dataflow',
                                    'test_data', 'WordCountJob.json')
    with open(word_count_json, 'r') as f:
      self.word_count_job = encoding.JsonToMessage(
          base.MESSAGE_MODULE.Job,
          f.read())

  def testShow(self):
    self.MockGetJob(
        self.SampleJob(JOB_1_ID, environment=self.fake_environment),
        view=self.view_all)

    job = self.Run('beta dataflow jobs show ' + JOB_1_ID)
    self.assertEqual(JOB_1_ID, job.id)
    self.assertFalse(hasattr(job, 'environment'))
    self.assertFalse(hasattr(job, 'steps'))

  def testShowWithRegion(self):
    my_region = 'europe-west1'
    self.MockGetJob(
        self.SampleJob(
            JOB_1_ID, environment=self.fake_environment, region=my_region),
        view=self.view_all,
        location=my_region)

    job = self.Run('beta dataflow jobs show --region=%s %s' % (my_region,
                                                               JOB_1_ID))
    self.assertEqual(JOB_1_ID, job.id)
    self.assertFalse(hasattr(job, 'environment'))
    self.assertFalse(hasattr(job, 'steps'))

  def testShowEnvironment(self):
    self.MockGetJob(
        self.SampleJob(JOB_1_ID, environment=self.fake_environment),
        view=self.view_all)

    job = self.Run('beta dataflow jobs show %s --environment' % JOB_1_ID)
    self.assertEqual(JOB_1_ID, job.id)
    self.assertEqual(self.fake_environment, job.environment)
    self.assertFalse(hasattr(job, 'steps'))

  def testShowSteps(self):
    self.MockGetJob(self.word_count_job, view=self.view_all)
    job = self.Run('beta dataflow jobs show --steps ' + JOB_1_ID)
    self.assertEqual(JOB_1_ID, job.id)
    self.assertFalse(hasattr(job, 'environment'))
    self.assertEqual(7, len(job.steps))

  def testShowMissingJobId(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_ID: Must be specified.'):
      self.Run('beta --format=text dataflow jobs show')

  def testShowNoSuchJob(self):
    self.MockGetJobFailure(JOB_1_ID, view=self.view_all)

    with self.AssertRaisesHttpExceptionRegexp(
        r'Requested entity was not found.'.format(normalize_space=True)):
      self.Run('beta dataflow jobs show ' + JOB_1_ID)

    # Neither stdout nor stderr should contain Http(Exception|Error)
    self.AssertErrNotContains('HttpE')
    self.AssertOutputNotContains('HttpE')


if __name__ == '__main__':
  test_case.main()
