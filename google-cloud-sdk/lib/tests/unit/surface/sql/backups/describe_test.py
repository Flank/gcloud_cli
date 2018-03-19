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

import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.sql import base

sqladmin_v1beta3 = core_apis.GetMessagesModule('sqladmin', 'v1beta3')


class BackupsDescribeTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def testBackupsDescribe(self):
    self.mocked_client.backupRuns.Get.Expect(
        self.messages.SqlBackupRunsGetRequest(
            project=self.Project(), instance='clone-instance-7', id=42),
        self.messages.BackupRun(
            id=42,
            windowStartTime=datetime.datetime(
                2014,
                8,
                13,
                23,
                0,
                0,
                802000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                14,
                0,
                27,
                47,
                910000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            enqueuedTime=datetime.datetime(
                2014,
                8,
                14,
                0,
                25,
                12,
                318000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            instance=u'clone-instance-7',
            kind=u'sql#backupRun',
            startTime=datetime.datetime(
                2014,
                8,
                14,
                0,
                25,
                12,
                321000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            status=u'SUCCESSFUL',))

    self.Run('sql backups describe --instance=clone-instance-7 42')

if __name__ == '__main__':
  test_case.main()
