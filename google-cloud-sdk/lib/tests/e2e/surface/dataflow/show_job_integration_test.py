# Copyright 2016 Google Inc. All Rights Reserved.
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

from googlecloudsdk.command_lib.dataflow import dataflow_util
from tests.lib import test_case
from tests.lib.surface.dataflow import e2e_base


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
      test_job = self.FindOldTerminatedJob()
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')

    job = self.ShowJob(test_job.id)

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
    self.assertGreater(job.stateTime, 0)
    self.assertGreater(job.creationTime, 0)

    # Make sure that the jobs are similar
    self.assertEquals(test_job.type, job.type)
    self.assertEquals(test_job.creationTime, job.creationTime)

  def testShowJobWithRegion(self):
    try:
      test_job = self.FindOldTerminatedJob(region='europe-west1')
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')

    job = self.ShowJob(test_job.id, region='europe-west1')

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
    self.assertGreater(job.stateTime, 0)
    self.assertGreater(job.creationTime, 0)

    # Make sure that the jobs are similar
    self.assertEquals(test_job.type, job.type)
    self.assertEquals(test_job.creationTime, job.creationTime)

  def testShowJobWithUri(self):
    try:
      test_job = self.FindOldTerminatedJob()
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')

    resource_uri = dataflow_util.JobsUriFromId(test_job.id, 'us-central1')
    job = self.ShowJob(resource_uri)

    # Make sure we successfully retrieved a job via the URI
    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertTrue(self.IsTerminated(job.state))

    # Does the job have a valid type?
    self.assertTrue(job.type == 'Streaming' or job.type == 'Batch')

    # Are the timestamps parsable?
    self.assertGreater(job.stateTime, 0)
    self.assertGreater(job.creationTime, 0)

  def testShowJobWithUriWithRegion(self):
    try:
      test_job = self.FindOldTerminatedJob(region='europe-west1')
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')

    resource_uri = dataflow_util.JobsUriFromId(test_job.id, 'europe-west1')
    # Note that the region is inferred from the URI
    job = self.ShowJob(resource_uri)

    # Make sure we successfully retrieved a job via the URI
    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertTrue(self.IsTerminated(job.state))

    # Does the job have a valid type?
    self.assertTrue(job.type == 'Streaming' or job.type == 'Batch')

    # Are the timestamps parsable?
    self.assertGreater(job.stateTime, 0)
    self.assertGreater(job.creationTime, 0)


if __name__ == '__main__':
  test_case.main()
