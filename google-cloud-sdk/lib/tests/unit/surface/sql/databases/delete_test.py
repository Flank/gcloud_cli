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
"""Tests that exercise operations listing and executing."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.sql import base


class DatabasesDeleteTest(base.SqlMockTestBeta):

  def testDelete(self):
    sqladmin = core_apis.GetMessagesModule('sqladmin', 'v1beta4')
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self.mocked_client.databases.Delete.Expect(
        sqladmin.SqlDatabasesDeleteRequest(
            database='mock-db-name',
            instance='mock-instance',
            project=self.Project(),
        ),
        sqladmin.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                415000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=None,
            importContext=None,
            targetId='mock-instance',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='56282116-8e0d-43d4-85d1-692b1f0cf044',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/56282116-8e0d-43d4-85d1-692b1f0cf044'.
            format(self.Project()),
            operationType='DELETE_DATABASE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.operations.Get.Expect(
        sqladmin.SqlOperationsGetRequest(
            operation='56282116-8e0d-43d4-85d1-692b1f0cf044',
            project=self.Project(),
        ),
        sqladmin.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                415000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                525000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                39,
                26,
                601000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='mock-instance',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='56282116-8e0d-43d4-85d1-692b1f0cf044',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/56282116-8e0d-43d4-85d1-692b1f0cf044'.
            format(self.Project()),
            operationType='DELETE_DATABASE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.Run('sql databases delete mock-db-name --instance=mock-instance')
    self.AssertErrContains('Deleted database [{0}].'.format('mock-db-name'))
    self.assertEqual(prompt_mock.call_count, 1)

  def testDeleteNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql databases delete mock-db-name --instance=mock-instance')

  def testDeleteNotExist(self):
    # TODO(b/36051029): implement this test.
    pass


if __name__ == '__main__':
  test_case.main()
