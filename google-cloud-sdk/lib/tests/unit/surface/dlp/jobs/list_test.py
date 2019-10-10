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
"""dlp jobs list tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class ListTest(base.DlpUnitTestBase):
  """dlp jobs list tests."""

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testListOutput(self, track):
    self.track = track
    list_request = self.MakeJobListRequest()
    list_response = self.MakeJobListResponse()
    self.client.projects_dlpJobs.List.Expect(request=list_request,
                                             response=list_response)
    result = self.Run('dlp jobs list')
    self.assertEqual(list_response.jobs, result)

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testListDefaultFormat(self, track):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.track = track
    list_request = self.MakeJobListRequest()
    list_response = self.MakeJobListResponse()
    self.client.projects_dlpJobs.List.Expect(request=list_request,
                                             response=list_response)
    self.Run('dlp jobs list')
    self.AssertOutputContains("""\
NAME CREATED MIN_LIKELIHOOD INFO_TYPES JOB_TYPE STATUS
Job_0 2018-01-01T00:00:00.0000Z POSSIBLE LAST_NAME,EMAIL_ADDRESS INSPECT_JOB DONE
Job_1 2018-01-01T00:00:00.0000Z POSSIBLE LAST_NAME,EMAIL_ADDRESS INSPECT_JOB DONE
Job_2 2018-01-01T00:00:00.0000Z POSSIBLE LAST_NAME,EMAIL_ADDRESS INSPECT_JOB DONE
Job_3 2018-01-01T00:00:00.0000Z POSSIBLE LAST_NAME,EMAIL_ADDRESS INSPECT_JOB DONE
Job_4 2018-01-01T00:00:00.0000Z POSSIBLE LAST_NAME,EMAIL_ADDRESS INSPECT_JOB DONE
    """, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
