# -*- coding: utf-8 -*- #
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
"""Tests for `gcloud scheduler jobs delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.scheduler import base


@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,))
class JobsDeleteTest(base.SchedulerTestBase):

  def SetUp(self):
    self.StartPatch('time.sleep')
    properties.VALUES.core.user_output_enabled.Set(True)

  def _ExpectDelete(self, job_name):
    self.client.projects_locations_jobs.Delete.Expect(
        self.messages.CloudschedulerProjectsLocationsJobsDeleteRequest(
            name=job_name),
        self.messages.Empty())

  def testDelete(self, track):
    relative_name = ('projects/{}/locations'
                     '/us-central1/jobs/my-job').format(self.Project())
    self.track = track
    self._ExpectGetApp()
    self._ExpectDelete(relative_name)
    self.WriteInput('y')

    self.Run('scheduler jobs delete my-job')

    self.AssertOutputEquals('')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_NoConfirm(self, track):
    self.track = track
    self.WriteInput('n')
    self._ExpectGetApp()

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('scheduler jobs delete my-job')

    self.AssertOutputEquals('')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_RelativeName(self, track):
    relative_name = ('projects/{}/locations'
                     '/us-central1/jobs/my-job').format(self.Project())
    self.track = track
    self._ExpectDelete(relative_name)
    self.WriteInput('y')

    self.Run('scheduler jobs delete ' + relative_name)

    self.AssertOutputEquals('')
    self.AssertErrContains('PROMPT_CONTINUE')


if __name__ == '__main__':
  test_case.main()
