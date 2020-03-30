# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.core.util import retry
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseOperationsWaitTest(object):
  # pylint:disable=g-tzinfo-datetime

  def testOperationsWait(self):
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
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                13,
                672000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                16,
                342000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='1cb8a924-898d-41ec-b695-39a6dc018d16',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/1cb8a924-898d-41ec-b695-39a6dc018d16'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .CREATE_USER,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='170350250316@developer.gserviceaccount.com',
        ))
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
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                13,
                672000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                16,
                342000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='1cb8a924-898d-41ec-b695-39a6dc018d16',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/1cb8a924-898d-41ec-b695-39a6dc018d16'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .CREATE_USER,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='170350250316@developer.gserviceaccount.com',
        ))

    # pylint: disable=line-too-long
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='27e060bf-4e4b-4fbb-b451-a9ee6c8a433a',
            project=self.Project(),
        ),
        self.messages.Operation(
            insertTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                1,
                104000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                2,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                3,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='27e060bf-4e4b-4fbb-b451-a9ee6c8a433a',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/27e060bf-4e4b-4fbb-b451-a9ee6c8a433a'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .RESTART,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='1@developer.gserviceaccount.com',
        ))
    # pylint: disable=line-too-long
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='27e060bf-4e4b-4fbb-b451-a9ee6c8a433a',
            project=self.Project(),
        ),
        self.messages.Operation(
            insertTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                1,
                104000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                2,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                3,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='27e060bf-4e4b-4fbb-b451-a9ee6c8a433a',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/27e060bf-4e4b-4fbb-b451-a9ee6c8a433a'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .RESTART,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='1@developer.gserviceaccount.com',
        ))

    self.Run('sql operations wait 1cb8a924-898d-41ec-b695-39a6dc018d16 '
             '27e060bf-4e4b-4fbb-b451-a9ee6c8a433a')
    # pylint: disable=line-too-long
    self.AssertOutputContains("""\
NAME                                  TYPE         START                          END                               ERROR  STATUS
1cb8a924-898d-41ec-b695-39a6dc018d16  CREATE_USER  2014-07-10T17:23:13.672+00:00  2014-07-10T17:23:16.342+00:00  -      DONE
27e060bf-4e4b-4fbb-b451-a9ee6c8a433a  RESTART      2014-07-10T17:23:02.165+00:00  2014-07-10T17:23:03.165+00:00  -      DONE
""", normalize_space=True)

  def testWaitForOperationWithTimeout(self):
    # Test that WaitForOperation is called with the correct timeout kwarg.
    wait_mock = self.StartPatch(
        'googlecloudsdk.api_lib.sql.operations.OperationsV1Beta4.'
        'WaitForOperation')
    op_ref = (
        'https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/'
        '1cb8a924-898d-41ec-b695-39a6dc018d16'.format(self.Project()))

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
                1,
                104000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                2,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                3,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink=(
                'https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/'
                'integration-test').format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='1cb8a924-898d-41ec-b695-39a6dc018d16',
            selfLink=op_ref,
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .RESTART,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='1@developer.gserviceaccount.com',
        ))

    self.Run('sql operations wait 1cb8a924-898d-41ec-b695-39a6dc018d16 '
             '--timeout=400')

    call_args = wait_mock.call_args
    kwargs = call_args[1] if call_args else {}

    # Assert that WaitForOperation was called with timeout specified.
    self.assertEquals(kwargs.get('max_wait_seconds'), 400)

  def testWaitForOperationWithUnlimitedTimeout(self):
    # Test that WaitForOperation is called with the correct timeout kwarg.
    wait_mock = self.StartPatch(
        'googlecloudsdk.api_lib.sql.operations.OperationsV1Beta4.'
        'WaitForOperation')
    op_ref = (
        'https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/'
        '1cb8a924-898d-41ec-b695-39a6dc018d16'.format(self.Project()))

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
                1,
                104000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                2,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                3,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink=(
                'https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/'
                'integration-test').format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='1cb8a924-898d-41ec-b695-39a6dc018d16',
            selfLink=op_ref,
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .RESTART,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='1@developer.gserviceaccount.com',
        ))

    self.Run('sql operations wait 1cb8a924-898d-41ec-b695-39a6dc018d16 '
             '--timeout=unlimited')

    call_args = wait_mock.call_args
    kwargs = call_args[1] if call_args else {}

    # Assert that WaitForOperation was called with timeout disabled.
    self.assertEquals(kwargs.get('max_wait_seconds'), None)

  def testOperationsWaitExceptionMessage(self):
    self.StartPatch('googlecloudsdk.core.util.retry.Retryer.RetryOnResult',
                    side_effect=retry.WaitException('forced timeout',
                                                    False, None))
    with self.assertRaisesRegex(
        exceptions.OperationError,
        'Operation .* is taking longer than expected. You can continue waiting '
        'for the operation by running `gcloud beta sql operations wait .*`'):
      self.Run('sql operations wait 1cb8a924-898d-41ec-b695-39a6dc018d16')


class OperationsWaitGATest(_BaseOperationsWaitTest, base.SqlMockTestGA):
  pass


class OperationsWaitBetaTest(_BaseOperationsWaitTest, base.SqlMockTestBeta):
  pass


class OperationsWaitAlphaTest(_BaseOperationsWaitTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
