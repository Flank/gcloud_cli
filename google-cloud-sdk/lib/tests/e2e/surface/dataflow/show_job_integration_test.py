# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Integration test for the 'dataflow jobs show' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from tests.lib import test_case
from tests.lib.surface.dataflow import e2e_base


def CheckTimestampIsValid(timestamp):
  datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')


class ShowJobIntegrationTest(e2e_base.DataflowIntegrationTestBase):
  """Integration test for the 'dataflow jobs show' command.

  Dataflow requires the Apache Beam Java (or python) SDK in order to create a
  job and there is no API to create a job. This means for user facing code
  like the UI and the CLI there is no way to create a job; thre needs to be a
  project that already has the Dataflow jobs. All jobs are kept in the
  'dataflow-monitoring' project. This is an external project that only the
  Dataflow team has access to this. For every CLI integration test, do a
  'gcloud config set project dataflow-monitoring' to be in the proper project.
  """

  def testShowJob(self):
    try:
      test_job = self.GetOldTerminatedJobFromList()
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')
      return

    job = self.ShowJob(test_job.id, test_job.location)

    # Both jobs should exist
    self.assertIsNotNone(test_job)
    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertTrue(self.IsTerminated(job.state))

    # Does the job have a valid type?
    self.assertTrue(job.type == 'Streaming' or job.type == 'Batch')

    # Are the timestamps valid
    CheckTimestampIsValid(job.stateTime)
    CheckTimestampIsValid(job.creationTime)

    # Make sure that the jobs are similar
    self.assertEqual(test_job.type, job.type)
    self.assertEqual(test_job.creationTime, job.creationTime)

  def testShowJobWithRegion(self):
    try:
      test_job = self.GetOldTerminatedJobFromList()
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')
      return

    job = self.ShowJob(test_job.id, test_job.location)

    # Both jobs should exist
    self.assertIsNotNone(test_job)
    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertTrue(self.IsTerminated(job.state))

    # Does the job have a valid type?
    self.assertTrue(job.type == 'Streaming' or job.type == 'Batch')

    # Are the timestamps valid
    CheckTimestampIsValid(job.stateTime)
    CheckTimestampIsValid(job.creationTime)

    # Make sure that the jobs are similar
    self.assertEqual(test_job.type, job.type)
    self.assertEqual(test_job.creationTime, job.creationTime)

  def testShowJobWithUri(self):
    try:
      test_job = self.GetOldTerminatedJobFromList()
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')
      return

    job = self.ShowJob(test_job.id, test_job.location)

    # Make sure we successfully retrieved a job via the URI
    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertTrue(self.IsTerminated(job.state))

    # Does the job have a valid type?
    self.assertTrue(job.type == 'Streaming' or job.type == 'Batch')

    # Are the timestamps valid
    CheckTimestampIsValid(job.stateTime)
    CheckTimestampIsValid(job.creationTime)

  def testShowJobWithUriWithRegion(self):
    try:
      test_job = self.GetOldTerminatedJobFromList()
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')
      return

    # Note that the region is inferred from the URI
    job = self.ShowJob(test_job.id, test_job.location)

    # Make sure we successfully retrieved a job via the URI
    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertTrue(self.IsTerminated(job.state))

    # Does the job have a valid type?
    self.assertTrue(job.type == 'Streaming' or job.type == 'Batch')

    # Are the timestamps valid
    CheckTimestampIsValid(job.stateTime)
    CheckTimestampIsValid(job.creationTime)


if __name__ == '__main__':
  test_case.main()
