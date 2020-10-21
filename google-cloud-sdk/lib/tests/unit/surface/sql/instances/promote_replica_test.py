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

from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseInstancesPromoteReplicaTest(object):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectInstanceLookup(self, database_version=None):
    database_version = (
        database_version or
        self.messages.DatabaseInstance.DatabaseVersionValueValuesEnum.MYSQL_5_7)
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='replica-1',
            project=self.Project(),
        ), self.messages.DatabaseInstance(databaseVersion=database_version))

  def _ExpectPromoteReplica(self, database_version=None):
    self._ExpectInstanceLookup(database_version)
    self.mocked_client.instances.PromoteReplica.Expect(
        self.messages.SqlInstancesPromoteReplicaRequest(
            instance='replica-1',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                26,
                22,
                6,
                26,
                785000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=None,
            importContext=None,
            targetId='replica-1',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/patch-instance3'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='56dec13c-fe47-449d-9942-921ad3bb8092',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/56dec13c-fe47-449d-9942-921ad3bb8092'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .PROMOTE_REPLICA,
            status=self.messages.Operation.StatusValueValuesEnum.PENDING,
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='56dec13c-fe47-449d-9942-921ad3bb8092',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                26,
                22,
                6,
                26,
                785000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=datetime.datetime(
                2014,
                8,
                26,
                22,
                6,
                27,
                48000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            endTime=datetime.datetime(
                2014,
                8,
                26,
                22,
                6,
                27,
                48000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='replica-1',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/patch-instance3'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='56dec13c-fe47-449d-9942-921ad3bb8092',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/56dec13c-fe47-449d-9942-921ad3bb8092'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .PROMOTE_REPLICA,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='170350250316@developer.gserviceaccount.com',
        ))

  def testSimplePromoteMysql(self):
    self._ExpectPromoteReplica(database_version=self.messages.DatabaseInstance
                               .DatabaseVersionValueValuesEnum.MYSQL_5_7)
    self.WriteInput('y')

    self.Run('sql instances promote-replica replica-1')
    # It should link to the db-specific guidance for promote replica.
    self.AssertErrContains(
        'Learn more:\nhttps://cloud.google.com/sql/docs/mysql/replication/manage-replicas#promote-replica'
    )
    self.AssertErrContains(
        'Promoted [https://sqladmin.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/replica-1].'.format(self.Project()))

  def testSimplePromotePostgres(self):
    self._ExpectPromoteReplica(database_version=self.messages.DatabaseInstance
                               .DatabaseVersionValueValuesEnum.POSTGRES_12)
    self.WriteInput('y')

    self.Run('sql instances promote-replica replica-1')
    # It should link to the db-specific guidance for promote replica.
    self.AssertErrContains(
        'Learn more:\nhttps://cloud.google.com/sql/docs/postgres/replication/manage-replicas#promote-replica'
    )
    self.AssertErrContains(
        'Promoted [https://sqladmin.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/replica-1].'.format(self.Project()))

  def testPromoteAsync(self):
    self._ExpectPromoteReplica()
    self.WriteInput('y')

    self.Run('sql instances promote-replica replica-1 --async')
    self.AssertErrNotContains(
        'Promoted [https://sqladmin.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/replica-1].'.format(self.Project()))

  def testPromoteNoConfirmCancels(self):
    self._ExpectInstanceLookup()
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql instances promote-replica replica-1')


class InstancesPromoteReplicaGATest(_BaseInstancesPromoteReplicaTest,
                                    base.SqlMockTestGA):
  pass


class InstancesPromoteReplicaBetaTest(_BaseInstancesPromoteReplicaTest,
                                      base.SqlMockTestBeta):
  pass


class InstancesPromoteReplicaAlphaTest(_BaseInstancesPromoteReplicaTest,
                                       base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
