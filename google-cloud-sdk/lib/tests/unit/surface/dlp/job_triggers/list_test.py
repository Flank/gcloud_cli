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
"""dlp job-triggers list tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class ListTest(base.DlpUnitTestBase):
  """dlp job-triggers list tests."""

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testListOutput(self, track):
    self.track = track
    list_request = self.MakeJobTriggerListRequest()
    list_response = self.MakeJobTriggerListResponse(count=4)
    self.client.projects_jobTriggers.List.Expect(request=list_request,
                                                 response=list_response)
    result = self.Run('dlp job-triggers list')
    self.assertEqual(list_response.jobTriggers, result)

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testListWithSorting(self, track):
    self.track = track
    list_request = self.MakeJobTriggerListRequest(order_by='status desc')
    list_response = self.MakeJobTriggerListResponse(count=4)
    self.client.projects_jobTriggers.List.Expect(request=list_request,
                                                 response=list_response)

    result = self.Run('dlp job-triggers list --sort-by ~status')
    self.assertEqual(list_response.jobTriggers, result)

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testListDefaultFormat(self, track):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.track = track
    list_request = self.MakeJobTriggerListRequest()
    list_response = self.MakeJobTriggerListResponse(count=4)
    self.client.projects_jobTriggers.List.Expect(request=list_request,
                                                 response=list_response)
    self.Run('dlp job-triggers list')
    self.AssertOutputEquals("""\
    NAME CREATED MIN_LIKELIHOOD INFO_TYPES SCHEDULE UPDATED STATUS
2018-01-01T00:00:00.000000Z POSSIBLE PHONE_NUMBER,PERSON_NAME 4500s 2018-01-01T00:00:00.000000Z HEALTHY
2018-01-01T00:00:00.000000Z POSSIBLE PHONE_NUMBER,PERSON_NAME 4500s 2018-01-01T00:00:00.000000Z HEALTHY
2018-01-01T00:00:00.000000Z POSSIBLE PHONE_NUMBER,PERSON_NAME 4500s 2018-01-01T00:00:00.000000Z HEALTHY
2018-01-01T00:00:00.000000Z POSSIBLE PHONE_NUMBER,PERSON_NAME 4500s 2018-01-01T00:00:00.000000Z HEALTHY
    """, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
