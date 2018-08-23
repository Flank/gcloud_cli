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
"""Test of the 'dataflow logs list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import iso_duration
from googlecloudsdk.core.util import times
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID


class LogsListUnitTest(base.DataflowMockingTestBase,
                       sdk_test_base.WithOutputCapture):
  """Test of the 'dataflow logs list' command."""

  def SetUp(self):
    self.job_id = JOB_1_ID
    self.job_message = base.MESSAGE_MODULE.JobMessage
    self.debug = (
        self.job_message.MessageImportanceValueValuesEnum.JOB_MESSAGE_DEBUG)
    self.detailed = (
        self.job_message.MessageImportanceValueValuesEnum.JOB_MESSAGE_DETAILED)
    self.warning = (
        self.job_message.MessageImportanceValueValuesEnum.JOB_MESSAGE_WARNING)

  def testLogs(self):
    self._MockRequest(responses=[
        self._JobMsg(0, self.warning, '(id1): Worker pool stopped.'),
        self._JobMsg(1, self.warning, '(id2): Worker pool stopped.'),
    ])

    self.Run('beta dataflow logs list ' + self.job_id)
    self.AssertOutputContains('(id1): Worker pool stopped.')
    self.AssertOutputContains('(id1): Worker pool stopped.')

  def testLogsWithRegion(self):
    my_region = 'europe-west1'
    self._MockRequest(
        responses=[
            self._JobMsg(0, self.warning, '(id1): Worker pool stopped.'),
            self._JobMsg(1, self.warning, '(id2): Worker pool stopped.'),
        ],
        region=my_region)

    self.Run('beta dataflow logs list --region=%s %s' % (my_region,
                                                         self.job_id))
    self.AssertOutputContains('(id1): Worker pool stopped.')
    self.AssertOutputContains('(id1): Worker pool stopped.')

  def testLogs_Unknown(self):
    self._MockRequest(responses=[
        self._JobMsg(0, None, '(id1): Worker pool stopped.'),
    ])

    self.Run('beta dataflow logs list ' + self.job_id)
    self.AssertOutputContains('{0}_0 (id1): Worker pool stopped.'.format(
        self.job_id, normalize_space=True))

  def testLogs_Filtering(self):
    self._MockRequest(
        responses=[
            self._JobMsg(0, self.warning, '(id1): Worker pool stopped.'),
            self._JobMsg(1, self.warning, '(id2): Worker pool stopped.')
        ],
        minimum_importance=(base.MESSAGE_MODULE.
                            DataflowProjectsLocationsJobsMessagesListRequest.
                            MinimumImportanceValueValuesEnum.JOB_MESSAGE_DEBUG),
        end_time=times.FormatDateTime(
            times.ParseDateTime('2015-01-15 12:31:08')),
        start_time=times.FormatDateTime(
            times.ParseDateTime('2015-01-15 12:31:07')))
    self.Run(('beta dataflow logs list --importance=debug {0} '
              '--after="2015-01-15 12:31:07" '
              '--before="2015-01-15 12:31:08"').format(
                  self.job_id, normalize_space=True))
    self.AssertOutputEquals("""\
W 2015-01-15T12:31:07 {0}_0 (id1): Worker pool stopped.
W 2015-01-15T12:31:08 {0}_1 (id2): Worker pool stopped.
""".format(self.job_id, normalize_space=True))

  def testLogs_Paging(self):
    self._MockRequest(
        responses=[
            self._JobMsg(0, self.warning, '(id1): Worker pool stopped.'),
            self._JobMsg(1, self.warning, '(id2): Worker pool stopped.'),
        ],
        next_page_token='page_token')
    self._MockRequest(
        responses=[
            self._JobMsg(2, self.warning, '(id3): Worker pool stopped.'),
            self._JobMsg(3, self.warning, '(id4): Worker pool stopped.'),
        ],
        page_token='page_token')

    self.Run('beta dataflow logs list ' + self.job_id)
    self.AssertOutputEquals("""\
W 2015-01-15T12:31:07 {0}_0 (id1): Worker pool stopped.
W 2015-01-15T12:31:08 {0}_1 (id2): Worker pool stopped.
W 2015-01-15T12:31:09 {0}_2 (id3): Worker pool stopped.
W 2015-01-15T12:31:10 {0}_3 (id4): Worker pool stopped.
""".format(self.job_id, normalize_space=True))

  def _MockRequest(self,
                   minimum_importance=None,
                   responses=None,
                   page_token=None,
                   next_page_token=None,
                   start_time=None,
                   end_time=None,
                   region=None):
    region = region or base.DEFAULT_REGION
    request_class = (
        base.MESSAGE_MODULE.DataflowProjectsLocationsJobsMessagesListRequest)
    request = request_class(
        projectId=self.Project(),
        jobId=self.job_id,
        location=region,
        minimumImportance=(
            minimum_importance or
            request_class.MinimumImportanceValueValuesEnum.JOB_MESSAGE_WARNING),
        startTime=start_time,
        endTime=end_time,
        pageToken=page_token)
    response = base.MESSAGE_MODULE.ListJobMessagesResponse(
        jobMessages=responses or [], nextPageToken=next_page_token)
    self.mocked_client.projects_locations_jobs_messages.List.Expect(
        request=request, response=response)

  def _JobMsg(self, idx, importance, text):
    start_time = times.ParseDateTime('2015-01-15 12:31:07')
    time = times.FormatDateTime(
        iso_duration.Duration(seconds=idx).GetRelativeDateTime(start_time))

    return self.job_message(
        id='{0}_{1}'.format(
            self.job_id, idx, normalize_space=True),
        messageImportance=importance,
        messageText=text,
        time=time)


if __name__ == '__main__':
  test_case.main()
