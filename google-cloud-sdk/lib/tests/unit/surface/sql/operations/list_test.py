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

from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseOperationsListTest(object):
  # pylint:disable=g-tzinfo-datetime

  def testOperationsList(self):
    # pylint: disable=line-too-long
    self.mocked_client.operations.List.Expect(
        self.messages.SqlOperationsListRequest(
            instance='integration-test',
            maxResults=10,
            pageToken=None,
            project=self.Project(),
        ),
        self.messages.OperationsListResponse(items=[
            self.messages.Operation(
                insertTime=datetime.datetime(
                    2014,
                    7,
                    10,
                    17,
                    23,
                    12,
                    672000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(
                        0))).isoformat(),
                startTime=datetime.datetime(
                    2014,
                    7,
                    10,
                    17,
                    23,
                    13,
                    672000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(
                        0))).isoformat(),
                endTime=datetime.datetime(
                    2014,
                    7,
                    10,
                    17,
                    23,
                    16,
                    342000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(
                        0))).isoformat(),
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
                operationType=self.messages.Operation
                .OperationTypeValueValuesEnum.CREATE_USER,
                status=self.messages.Operation.StatusValueValuesEnum.DONE,
                user='170350250316@developer.gserviceaccount.com',
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
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(
                        0))).isoformat(),
                startTime=datetime.datetime(
                    2014,
                    7,
                    10,
                    17,
                    23,
                    2,
                    165000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(
                        0))).isoformat(),
                endTime=datetime.datetime(
                    2014,
                    7,
                    10,
                    17,
                    23,
                    3,
                    165000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(
                        0))).isoformat(),
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
                operationType=self.messages.Operation
                .OperationTypeValueValuesEnum.RESTART,
                status=self.messages.Operation.StatusValueValuesEnum.DONE,
                user='1@developer.gserviceaccount.com',
            ),
        ]))
    self.Run('sql operations list -i=integration-test --limit=10')
    # pylint: disable=line-too-long
    self.AssertOutputContains("""\
NAME                                  TYPE         START                             END                               ERROR  STATUS
1cb8a924-898d-41ec-b695-39a6dc018d16  CREATE_USER  2014-07-10T17:23:13.672+00:00  2014-07-10T17:23:16.342+00:00  -      DONE
27e060bf-4e4b-4fbb-b451-a9ee6c8a433a  RESTART      2014-07-10T17:23:02.165+00:00  2014-07-10T17:23:03.165+00:00  -      DONE
""", normalize_space=True)

  def testOperationsListWithErrors(self):
    self.instance = self.GetV2Instance('some-instance')
    first_op = self.GetOperation(
        self.messages.Operation.OperationTypeValueValuesEnum.CREATE,
        self.messages.Operation.StatusValueValuesEnum.DONE,
        self.messages.OperationErrors(
            kind='sql#operationErrors',
            errors=[
                self.messages.OperationError(
                    kind='sql#operationError', code='problem')
            ]))
    first_op.name = 'operation-1'
    second_op = self.GetOperation(
        self.messages.Operation.OperationTypeValueValuesEnum.EXPORT,
        self.messages.Operation.StatusValueValuesEnum.DONE,
        self.messages.OperationErrors(
            kind='sql#operationErrors',
            errors=[
                self.messages.OperationError(
                    kind='sql#operationError', code='badbadnotgood')
            ]))
    second_op.name = 'operation-2'
    self.mocked_client.operations.List.Expect(
        self.messages.SqlOperationsListRequest(
            instance=self.instance.name,
            maxResults=10,
            pageToken=None,
            project=self.Project(),
        ), self.messages.OperationsListResponse(items=[first_op, second_op]))
    self.Run('sql operations list -i=some-instance --limit=10')
    # pylint: disable=line-too-long
    self.AssertOutputContains(
        """\
NAME         TYPE    START                          END                            ERROR          STATUS
operation-1  CREATE  2014-08-12T19:38:39.525+00:00  2014-08-12T19:39:26.601+00:00  problem        DONE
operation-2  EXPORT  2014-08-12T19:38:39.525+00:00  2014-08-12T19:39:26.601+00:00  badbadnotgood  DONE
""",
        normalize_space=True)


class OperationsListGATest(_BaseOperationsListTest, base.SqlMockTestGA):
  pass


class OperationsListBetaTest(_BaseOperationsListTest, base.SqlMockTestBeta):
  pass


class OperationsListAlphaTest(_BaseOperationsListTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
