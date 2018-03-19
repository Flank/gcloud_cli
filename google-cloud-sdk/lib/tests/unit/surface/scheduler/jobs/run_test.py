# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud scheduler jobs run`."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.scheduler import base


@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,))
class JobsRunTest(base.SchedulerTestBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def _ExpectRun(self, job_name):
    self.client.projects_locations_jobs.Run.Expect(
        self.messages.CloudschedulerProjectsLocationsJobsRunRequest(
            name=job_name,
            runJobRequest=self.messages.RunJobRequest()),
        self.messages.Empty())

  def testRun(self, track):
    relative_name = ('projects/{}/locations'
                     '/us-central1/jobs/my-job').format(self.Project())
    self.track = track
    self._ExpectGetApp()
    self._ExpectRun(relative_name)

    self.Run('scheduler jobs run my-job')

    self.AssertOutputEquals('')

  def testRun_RelativeName(self, track):
    relative_name = ('projects/{}/locations'
                     '/us-central1/jobs/my-job').format(self.Project())
    self.track = track
    self._ExpectRun(relative_name)

    self.Run('scheduler jobs run ' + relative_name)
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_case.main()
