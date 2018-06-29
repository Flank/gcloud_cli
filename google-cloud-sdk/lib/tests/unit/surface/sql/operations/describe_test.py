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


class OperationsDescribeTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def testOperationsDescribe(self):
    # pylint: disable=line-too-long
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='1cb8a924-898d-41ec-b695-39a6dc018d16',
            project=self.Project(),
        ),
        self.messages.Operation(
            insertTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                12,
                672000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                13,
                672000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                16,
                342000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='1cb8a924-898d-41ec-b695-39a6dc018d16',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/1cb8a924-898d-41ec-b695-39a6dc018d16'.
            format(self.Project()),
            operationType='CREATE_USER',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.Run('sql operations describe 1cb8a924-898d-41ec-b695-39a6dc018d16')
    # pylint: disable=line-too-long
    self.AssertOutputContains("""\
endTime: '2014-07-10T17:23:16.342000+00:00'
insertTime: '2014-07-10T17:23:12.672000+00:00'
kind: sql#operation
name: 1cb8a924-898d-41ec-b695-39a6dc018d16
operationType: CREATE_USER
selfLink: https://www.googleapis.com/sql/v1beta4/projects/fake-project/operations/1cb8a924-898d-41ec-b695-39a6dc018d16
startTime: '2014-07-10T17:23:13.672000+00:00'
status: DONE
targetId: integration-test
targetLink: https://www.googleapis.com/sql/v1beta4/projects/fake-project/instances/integration-test
targetProject: fake-project
user: 170350250316@developer.gserviceaccount.com
""", normalize_space=True)

if __name__ == '__main__':
  test_case.main()
