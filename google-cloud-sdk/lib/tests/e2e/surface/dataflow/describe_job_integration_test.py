# -*- coding: utf-8 -*- #
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
"""Integration test for the 'dataflow jobs describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.command_lib.dataflow import dataflow_util
from tests.lib import test_case
from tests.lib.surface.dataflow import e2e_base


class DescribeJobIntegrationTest(e2e_base.DataflowIntegrationTestBase):
  """Integration test for the 'dataflow jobs describe' command.

  Dataflow requires the Apache Beam Java (or python) SDK in order to create a
  job and there is no API to create a job. This means for user facing code
  like the UI and the CLI there is no way to create a job; thre needs to be a
  project that already has the Dataflow jobs. All jobs are kept in the
  'dataflow-monitoring' project. This is an external project that only the
  Dataflow team has access to this. For every CLI integration test, do a
  'gcloud config set project dataflow-monitoring' to be in the proper project.
  """

  def SetUp(self):
    state_enum = apis.GetMessagesModule().Job.CurrentStateValueValuesEnum
    self.terminated_states = [state_enum.JOB_STATE_CANCELLED,
                              state_enum.JOB_STATE_DONE,
                              state_enum.JOB_STATE_FAILED,
                              state_enum.JOB_STATE_STOPPED,
                              state_enum.JOB_STATE_UPDATED]
    type_enum = apis.GetMessagesModule().Job.TypeValueValuesEnum
    self.valid_types = [type_enum.JOB_TYPE_BATCH,
                        type_enum.JOB_TYPE_STREAMING]

  def testDescribeJobWithRegion(self):
    try:
      old_job = self.FindOldTerminatedJob(region='europe-west1')
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')

    job_id = old_job.id
    job = self.DescribeJob(job_id, region='europe-west1')

    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertIn(job.currentState, self.terminated_states)

    # Does the job have a valid type?
    self.assertIn(job.type, self.valid_types)

    # Are the timestamps in the correct format?
    self.assertIsNotNone(job.currentStateTime)
    self.assertIsNotNone(job.createTime)

  def testDescribeJob(self):
    try:
      old_job = self.FindOldTerminatedJob()
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')

    job_id = old_job.id
    job = self.DescribeJob(job_id)

    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertIn(job.currentState, self.terminated_states)

    # Does the job have a valid type?
    self.assertIn(job.type, self.valid_types)

    # Are the timestamps in the correct format?
    self.assertIsNotNone(job.currentStateTime)
    self.assertIsNotNone(job.createTime)

  def testShowJobWithUri(self):
    try:
      old_job = self.FindOldTerminatedJob()
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')

    resource_uri = dataflow_util.JobsUriFromId(old_job.id, 'us-central1')
    job = self.DescribeJob(resource_uri)

    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertIn(job.currentState, self.terminated_states)

    # Does the job have a valid type?
    self.assertIn(job.type, self.valid_types)

    # Are the timestamps in the correct format?
    self.assertIsNotNone(job.currentStateTime)
    self.assertIsNotNone(job.createTime)

  def testShowJobWithUriWithRegion(self):
    try:
      old_job = self.FindOldTerminatedJob(region='europe-west1')
    except ValueError:
      self.skipTest('No jobs in terminated state. Skipping test.')

    resource_uri = dataflow_util.JobsUriFromId(old_job.id, 'europe-west1')
    # Note that the region is inferred from the URI
    job = self.DescribeJob(resource_uri)

    self.assertIsNotNone(job)

    # Does the job id match the expected?
    self.assertRegexpMatches(job.id, e2e_base.JOB_ID_PATTERN)
    self.assertIsNotNone(job.name)
    self.assertIn(job.currentState, self.terminated_states)

    # Does the job have a valid type?
    self.assertIn(job.type, self.valid_types)

    # Are the timestamps in the correct format?
    self.assertIsNotNone(job.currentStateTime)
    self.assertIsNotNone(job.createTime)


if __name__ == '__main__':
  test_case.main()
