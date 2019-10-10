# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""dlp jobs delete tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class DeleteTest(base.DlpUnitTestBase):
  """dlp jobs delete tests."""

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testDelete(self, track):
    self.track = track
    self.StartPatch('time.sleep')
    job_ref = resources.REGISTRY.Parse(
        'myjob', params={'projectsId': self.Project()},
        collection='dlp.projects.dlpJobs')
    delete_request = self.msg.DlpProjectsDlpJobsDeleteRequest(
        name=job_ref.RelativeName())
    self.client.projects_dlpJobs.Delete.Expect(
        request=delete_request, response=self.msg.GoogleProtobufEmpty())
    self.WriteInput('y')
    self.Run('dlp jobs delete myjob')


if __name__ == '__main__':
  test_case.main()
