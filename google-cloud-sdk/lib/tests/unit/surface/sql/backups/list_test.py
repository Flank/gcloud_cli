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
"""Tests that exercise operations listing and executing."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime

from apitools.base.protorpclite import util as protorpc_util

from tests.lib import test_case
from tests.lib.surface.sql import base


class BackupsListTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def testBackupsList(self):
    self.mocked_client.backupRuns.List.Expect(
        self.messages.SqlBackupRunsListRequest(
            pageToken=None,
            project=self.Project(),
            instance='integration-test',
            maxResults=100,
        ),
        self.messages.BackupRunsListResponse(
            kind='sql#backupRunsList',
            items=[
                self.messages.BackupRun(
                    id=1,
                    windowStartTime=datetime.datetime(
                        2014,
                        7,
                        8,
                        2,
                        0,
                        0,
                        623000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    error=None,
                    instance='integration-test',
                    endTime=None,
                    kind='sql#backupRun',
                    startTime=None,
                    enqueuedTime=datetime.datetime(
                        2014,
                        7,
                        8,
                        2,
                        57,
                        4,
                        555000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    status='SKIPPED',
                ),
                self.messages.BackupRun(
                    id=2,
                    windowStartTime=datetime.datetime(
                        2014,
                        3,
                        29,
                        2,
                        0,
                        0,
                        451000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    error=None,
                    instance='integration-test',
                    endTime=None,
                    kind='sql#backupRun',
                    startTime=None,
                    enqueuedTime=datetime.datetime(
                        2014,
                        3,
                        29,
                        2,
                        11,
                        7,
                        464000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    status='SKIPPED',
                ),
            ],
            nextPageToken='1396059067464',
        ),
    )
    self.mocked_client.backupRuns.List.Expect(
        self.messages.SqlBackupRunsListRequest(
            instance='integration-test',
            project=self.Project(),
            maxResults=100,
            pageToken='1396059067464',
        ),
        self.messages.BackupRunsListResponse(
            kind='sql#backupRunsList',
            items=[
                self.messages.BackupRun(
                    id=3,
                    windowStartTime=datetime.datetime(
                        2015,
                        7,
                        8,
                        2,
                        0,
                        0,
                        623000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    error=None,
                    instance='integration-test',
                    endTime=None,
                    kind='sql#backupRun',
                    startTime=datetime.datetime(
                        2015,
                        3,
                        29,
                        2,
                        0,
                        0,
                        451000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    enqueuedTime=datetime.datetime(
                        2015,
                        7,
                        8,
                        2,
                        57,
                        4,
                        555000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    status='SKIPPED',
                ),
                self.messages.BackupRun(
                    id=4,
                    windowStartTime=datetime.datetime(
                        2015,
                        3,
                        29,
                        2,
                        0,
                        0,
                        451000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    error=None,
                    instance='integration-test',
                    endTime=None,
                    kind='sql#backupRun',
                    startTime=None,
                    enqueuedTime=datetime.datetime(
                        2015,
                        3,
                        29,
                        2,
                        11,
                        7,
                        464000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    status='SKIPPED',
                ),
            ],
            nextPageToken=None,
        ),
    )

    self.Run('sql backups list --instance=integration-test')
    self.AssertOutputContains(
        """\
ID  WINDOW_START_TIME              ERROR  STATUS
1   2014-07-08T02:00:00.623+00:00  -      SKIPPED
2   2014-03-29T02:00:00.451+00:00  -      SKIPPED
3   2015-07-08T02:00:00.623+00:00  -      SKIPPED
4   2015-03-29T02:00:00.451+00:00  -      SKIPPED
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
