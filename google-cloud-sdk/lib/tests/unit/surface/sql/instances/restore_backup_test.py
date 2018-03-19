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
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.sql import base

sqladmin_v1beta3 = core_apis.GetMessagesModule('sqladmin', 'v1beta3')


class InstancesRestoreBackupTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectRestoreBackup(self):
    self.mocked_client.instances.RestoreBackup.Expect(
        self.messages.SqlInstancesRestoreBackupRequest(
            # pylint:disable=line-too-long
            instance='clone-instance-7',
            project=self.Project(),
            instancesRestoreBackupRequest=self.messages.
            InstancesRestoreBackupRequest(
                restoreBackupContext=self.messages.RestoreBackupContext(
                    backupRunId=1438876800422,
                    instanceId='clone-instance-7',),),),
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
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=None,
            importContext=None,
            targetId=u'clone-instance-7',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'1178746b-14d4-4258-bbdd-52856882c213',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/1178746b-14d4-4258-bbdd-52856882c213'.
            format(self.Project()),
            operationType=u'RESTORE_VOLUME',
            status=u'PENDING',
            user=u'170350250316@developer.gserviceaccount.com',))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation=u'1178746b-14d4-4258-bbdd-52856882c213',
            project=self.Project(),),
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
            targetId=u'clone-instance-7',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'1178746b-14d4-4258-bbdd-52856882c213',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/1178746b-14d4-4258-bbdd-52856882c213'.
            format(self.Project()),
            operationType=u'RESTORE_VOLUME',
            status=u'DONE',
            user=u'170350250316@developer.gserviceaccount.com',))

  def testRestoreBackup(self):
    self._ExpectRestoreBackup()

    self.Run('sql instances restore-backup clone-instance-7 '
             '--backup-id=1438876800422')
    self.AssertErrContains(
        'Restored [https://www.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/clone-instance-7].'.format(self.Project()))

  def testRestoreBackupAsync(self):
    self._ExpectRestoreBackup()

    self.Run('sql instances restore-backup clone-instance-7 '
             '--backup-id=1438876800422 --async')
    self.AssertErrNotContains(
        'Restored [https://www.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/clone-instance-7].'.format(self.Project()))

  def _ExpectRestoreBackupV1Beta3(self):
    self.mocked_client_v1beta3 = mock.Client(
        core_apis.GetClientClass('sql', 'v1beta3'))
    self.mocked_client_v1beta3.Mock()
    self.addCleanup(self.mocked_client_v1beta3.Unmock)
    self.mocked_client_v1beta3.instances.Get.Expect(
        sqladmin_v1beta3.SqlInstancesGetRequest(
            instance='clone-instance-7',
            project=self.Project(),),
        sqladmin_v1beta3.DatabaseInstance(
            currentDiskSize=287592724,
            databaseVersion=u'MYSQL_5_5',
            etag=u'"DExdZ69FktjWMJ-ohD1vLZW9pnk/NA"',
            instance=u'clone-instance-7',
            ipAddresses=[],
            kind=u'sql#instance',
            maxDiskSize=268435456000,
            project=self.Project(),
            region=u'us-central',
            serverCaCert=sqladmin_v1beta3.SslCert(
                cert=u'-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAgIBADANBg',
                certSerialNumber=u'0',
                commonName=u'C=US,O=Google\\, Inc,CN=Google Cloud SQL Server C',
                createTime=datetime.datetime(
                    2014,
                    8,
                    13,
                    21,
                    47,
                    29,
                    512000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
                expirationTime=datetime.datetime(
                    2024,
                    8,
                    10,
                    21,
                    47,
                    29,
                    512000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
                instance=u'clone-instance-7',
                kind=u'sql#sslCert',
                sha1Fingerprint=u'2dbfcefd3c962a284035ffb06dccdd2055d32b46',),
            settings=sqladmin_v1beta3.Settings(
                activationPolicy=u'ON_DEMAND',
                authorizedGaeApplications=[],
                backupConfiguration=[
                    sqladmin_v1beta3.BackupConfiguration(
                        binaryLogEnabled=True,
                        enabled=True,
                        id=u'43ee7461-d2d8-4c5b-8d8e-98fa3f9d2ecc',
                        kind=u'sql#backupConfiguration',
                        startTime=u'23:00',),
                ],
                databaseFlags=[],
                ipConfiguration=sqladmin_v1beta3.IpConfiguration(
                    authorizedNetworks=[],
                    enabled=False,
                    requireSsl=None,),
                kind=u'sql#settings',
                locationPreference=None,
                pricingPlan=u'PER_USE',
                replicationType=u'SYNCHRONOUS',
                settingsVersion=4,
                tier=u'D1',),
            state=u'RUNNABLE',))
    self.mocked_client_v1beta3.instances.RestoreBackup.Expect(
        sqladmin_v1beta3.SqlInstancesRestoreBackupRequest(
            backupConfiguration=u'43ee7461-d2d8-4c5b-8d8e-98fa3f9d2ecc',
            dueTime='2014-08-13T23:00:00.802000+00:00',
            instance='clone-instance-7',
            project=self.Project(),),
        sqladmin_v1beta3.InstancesRestoreBackupResponse(
            kind=u'sql#instancesRestoreBackup',
            operation=u'7e3d8e00-9300-4baa-8f58-5b429b9b5fd1',))
    self.mocked_client_v1beta3.operations.Get.Expect(
        sqladmin_v1beta3.SqlOperationsGetRequest(
            instance='clone-instance-7',
            operation=u'7e3d8e00-9300-4baa-8f58-5b429b9b5fd1',
            project=self.Project(),),
        sqladmin_v1beta3.InstanceOperation(
            endTime=datetime.datetime(
                2014,
                8,
                14,
                21,
                47,
                41,
                505000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            enqueuedTime=datetime.datetime(
                2014,
                8,
                14,
                21,
                46,
                35,
                146000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=[],
            exportContext=None,
            importContext=None,
            instance=u'clone-instance-7',
            kind=u'sql#instanceOperation',
            operation=u'7e3d8e00-9300-4baa-8f58-5b429b9b5fd1',
            operationType=u'RESTORE_VOLUME',
            startTime=datetime.datetime(
                2014,
                8,
                14,
                21,
                46,
                35,
                195000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            state=u'DONE',
            userEmailAddress=u'170350250316@developer.gserviceaccount.com',))


if __name__ == '__main__':
  test_case.main()
