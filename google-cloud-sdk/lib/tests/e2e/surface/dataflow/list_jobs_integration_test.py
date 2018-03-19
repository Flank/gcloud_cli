# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Integration test for the 'dataflow jobs list' command."""

from tests.lib import test_case
from tests.lib.surface.dataflow import e2e_base

REGION = 'us-central1'


class ListIntegrationTest(e2e_base.DataflowIntegrationTestBase):
  """Integration test for the 'dataflow jobs list' command.

  Dataflow requires the Apache Beam Java (or python) SDK in order to create a
  job and there is no API to create a job. This means for user facing code
  like the UI and the CLI there is no way to create a job; there needs to be a
  project that already has the Dataflow jobs. All jobs are kept in the
  "dataflow-monitoring" project. This is an external project that only the
  Dataflow team has access to this. For every CLI integration test, do a
  "gcloud config set project dataflow-monitoring" to be in the proper project.
  """

  def testListJobs(self):
    jobs = self.ListJobs()
    self.assertGreater(len(jobs), 0)

  def testListJobsTerminated(self):
    jobs = self.ListJobs('terminated')
    self.assertTrue(all([self.IsTerminated(j.state) for j in jobs]))

  def testListJobsWithRegion(self):
    jobs = self.ListJobs(region=REGION)
    self.assertGreater(len(jobs), 0)
    self.assertTrue(all([j.location == REGION for j in jobs]))

  def testListJobsTerminatedWithRegion(self):
    jobs = self.ListJobs('terminated', region=REGION)
    self.assertTrue(all([self.IsTerminated(j.state) for j in jobs]))
    self.assertTrue(all([j.location == REGION for j in jobs]))


if __name__ == '__main__':
  test_case.main()
