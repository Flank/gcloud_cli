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


class _BaseInstancesRestoreBackupTest(object):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectRestoreBackup(self):
    self.mocked_client.instances.RestoreBackup.Expect(
        self.messages.SqlInstancesRestoreBackupRequest(
            # pylint:disable=line-too-long
            instance='clone-instance-7',
            project=self.Project(),
            instancesRestoreBackupRequest=self.messages
            .InstancesRestoreBackupRequest(
                restoreBackupContext=self.messages.RestoreBackupContext(
                    backupRunId=1438876800422,
                    instanceId='clone-instance-7',
                ),),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                415000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='1178746b-14d4-4258-bbdd-52856882c213',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/1178746b-14d4-4258-bbdd-52856882c213'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .RESTORE_VOLUME,
            status=self.messages.Operation.StatusValueValuesEnum.PENDING,
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='1178746b-14d4-4258-bbdd-52856882c213',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                415000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            startTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                525000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            endTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                39,
                26,
                601000,
                tzinfo=protorpc_util.TimeZoneOffset(
                    datetime.timedelta(0))).isoformat(),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='1178746b-14d4-4258-bbdd-52856882c213',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/1178746b-14d4-4258-bbdd-52856882c213'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .RESTORE_VOLUME,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='170350250316@developer.gserviceaccount.com',
        ))

  def testRestoreBackup(self):
    self._ExpectRestoreBackup()

    self.Run('sql instances restore-backup clone-instance-7 '
             '--backup-id=1438876800422')
    self.AssertErrContains(
        'Restored [https://sqladmin.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/clone-instance-7].'.format(self.Project()))

  def testRestoreBackupAsync(self):
    self._ExpectRestoreBackup()

    self.Run('sql instances restore-backup clone-instance-7 '
             '--backup-id=1438876800422 --async')
    self.AssertErrNotContains(
        'Restored [https://sqladmin.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/clone-instance-7].'.format(self.Project()))


class InstancesRestoreBackupGATest(_BaseInstancesRestoreBackupTest,
                                   base.SqlMockTestGA):
  pass


class InstancesRestoreBackupBetaTest(_BaseInstancesRestoreBackupTest,
                                     base.SqlMockTestBeta):
  pass


class InstancesRestoreBackupAlphaTest(_BaseInstancesRestoreBackupTest,
                                      base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
