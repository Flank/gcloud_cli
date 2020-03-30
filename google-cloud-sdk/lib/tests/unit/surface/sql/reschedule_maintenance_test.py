# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests that exercise reschedule maintenance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import exceptions as sql_exceptions
from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.sql import base


class RescheduleMaintenanceGATest(base.SqlMockTestGA):

  def GetScheduledMaintenance(self, can_reschedule):
    """Create a mock SqlScheduledMaintenance message.

    Args:
      can_reschedule: bool, Supplies the value of the canReschedule field of the
        message.

    Returns:
      The created SqlScheduledMaintenance message.
    """
    return self.messages.SqlScheduledMaintenance(
        startTime='2019-11-10T04:00:00Z', canReschedule=can_reschedule)

  def ExpectInstanceGet(self, scheduled_maintenance):
    """Mock an instance GET request that returns an instance.

    Args:
      scheduled_maintenance: SqlScheduledMaintenance, Supplies the value of the
        scheduled_maintenance field of the instance.

    Returns:
      None
    """
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='testinstance',
            project=self.Project(),
        ),
        self.messages.DatabaseInstance(
            # pylint:disable=line-too-long
            backendType=self.messages.DatabaseInstance
            .BackendTypeValueValuesEnum.SECOND_GEN,
            connectionName='{0}:us-central1:testinstance'.format(
                self.Project()),
            databaseVersion=self.messages.DatabaseInstance
            .DatabaseVersionValueValuesEnum.MYSQL_5_7,
            etag='9c6aef2ac3aa816fffbdbaf0514443464e116d59bb0052b4f43f404970f1464',
            gceZone='us-central1-c',
            instanceType=self.messages.DatabaseInstance
            .InstanceTypeValueValuesEnum.CLOUD_SQL_INSTANCE,
            ipAddresses=[
                self.messages.IpMapping(
                    ipAddress='104.154.166.249',
                    type=self.messages.IpMapping.TypeValueValuesEnum.PRIMARY,
                ),
            ],
            kind='sql#instance',
            name='testinstance',
            project=self.Project(),
            region='us-central1',
            scheduledMaintenance=scheduled_maintenance,
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'
            .format(self.Project()),
            serviceAccountEmailAddress='vxmlqos47zbmzgjppv2ued6e74@speckle-umbrella-5.iam.gserviceaccount.com',
            serverCaCert=self.messages.SslCert(
                cert='-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAgIBADANBgkqhkiG9w0BAQUFADBIMSMwIQYDVQQDExpHb29n\nbGUgQ2x',
                certSerialNumber='0',
                commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL Server CA',
                createTime='2017-05-12T21:33:04.844Z',
                expirationTime='2019-05-12T21:34:04.844Z',
                instance='testinstance',
                kind='sql#sslCert',
                sha1Fingerprint='fcddb49c4a00ff8796ba099933dbeb208b8599bd',
            ),
            settings=self.messages.Settings(
                activationPolicy=self.messages.Settings
                .ActivationPolicyValueValuesEnum.ALWAYS,
                authorizedGaeApplications=[],
                availabilityType=self.messages.Settings
                .AvailabilityTypeValueValuesEnum.ZONAL,
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=True,
                    enabled=False,
                    kind='sql#backupConfiguration',
                    startTime='03:00',
                ),
                dataDiskSizeGb=10,
                dataDiskType=self.messages.Settings.DataDiskTypeValueValuesEnum
                .PD_SSD,
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=True,
                ),
                kind='sql#settings',
                locationPreference=self.messages.LocationPreference(
                    kind='sql#locationPreference', zone='us-central1-c'),
                maintenanceWindow=self.messages.MaintenanceWindow(
                    day=2, hour=5, kind='sql#maintenanceWindow'),
                pricingPlan=self.messages.Settings.PricingPlanValueValuesEnum
                .PER_USE,
                replicationType=self.messages.Settings
                .ReplicationTypeValueValuesEnum.SYNCHRONOUS,
                settingsVersion=1,
                storageAutoResize=True,
                storageAutoResizeLimit=0,
                tier='db-n1-standard-1'),
            state=self.messages.DatabaseInstance.StateValueValuesEnum.RUNNABLE,
        ))

  def ExpectRescheduleMaintenance(self, reschedule_type, schedule_time=None):
    """Mocks a successful reschedule maintenance request.

    Args:
      reschedule_type: Reschedule.RescheduleTypeValueValuesEnum, The
        rescheduleType field of the reschedule maintenance request.
      schedule_time: string, The scheduleTime field of the reschedule
        maintenance request.

    Returns:
      None
    """
    self.mocked_client.projects_instances.RescheduleMaintenance.Expect(
        self.messages.SqlProjectsInstancesRescheduleMaintenanceRequest(
            instance='testinstance',
            project=self.Project(),
            sqlInstancesRescheduleMaintenanceRequestBody=self.messages
            .SqlInstancesRescheduleMaintenanceRequestBody(
                reschedule=self.messages.Reschedule(
                    rescheduleType=reschedule_type,
                    scheduleTime=schedule_time))),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime='2014-08-13T20:50:43.963Z',
            startTime=None,
            endTime=None,
            error=None,
            targetId='testinstance',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='af859489-ca9c-470f-8340-86da167b368f',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/af859489-ca9c-470f-8340-86da167b368f'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .RESCHEDULE_MAINTENANCE,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='af859489-ca9c-470f-8340-86da167b368f',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime='2014-08-13T20:50:43.963Z',
            startTime='2014-08-13T20:50:44.130Z',
            endTime='2014-08-13T20:50:49.639Z',
            error=None,
            targetId='testinstance',
            targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='af859489-ca9c-470f-8340-86da167b368f',
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/af859489-ca9c-470f-8340-86da167b368f'
            .format(self.Project()),
            operationType=self.messages.Operation.OperationTypeValueValuesEnum
            .RESCHEDULE_MAINTENANCE,
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            user='170350250316@developer.gserviceaccount.com',
        ))

  def ExpectInstanceGetMissing(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='missinginstance',
            project=self.Project(),
        ),
        exception=http_error.MakeHttpError(
            code=404,
            reason='notFound',
        ))

  def testRescheduleMaintenanceMissingInstance(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument INSTANCE --reschedule-type: Must be specified.'):
      self.Run('sql reschedule-maintenance')

  def testRescheduleMaintenanceInvalidInstance(self):
    with self.assertRaisesRegex(exceptions.ToolException,
                                'Instance names cannot contain the'):
      self.Run(
          'sql reschedule-maintenance invalid:instance '
          '--reschedule-type=IMMEDIATE'
      )

  def testRescheduleMaintenanceMissingRescheduleType(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --reschedule-type: Must be specified.'):
      self.Run('sql reschedule-maintenance testinstance')

  def testRescheduleMaintenanceInvalidRescheduleType(self):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'argument --reschedule-type: Invalid choice'):
      self.Run('sql reschedule-maintenance testinstance --reschedule-type=abc')

  def testRescheduleMaintenanceSpecificTimeMissingScheduleTime(self):
    with self.assertRaisesRegex(
        sql_exceptions.ArgumentError,
        r'argument \-\-schedule\-time\: Must be specified for SPECIFIC_TIME\.'):
      self.Run(
          'sql reschedule-maintenance testinstance '
          '--reschedule-type=SPECIFIC_TIME'
      )

  def testRescheduleMaintenanceSpecificTimeInvalidScheduleTimeFormat(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument \-\-schedule\-time\: Failed to parse date/time'):
      self.Run(
          'sql reschedule-maintenance testinstance '
          '--reschedule-type=SPECIFIC_TIME --schedule-time=abc123'
      )

  def testRescheduleMaintenanceInstanceError(self):
    self.ExpectInstanceGetMissing()
    with self.AssertRaisesHttpExceptionRegexp('notFound: Resource not found.'):
      self.Run(
          'sql reschedule-maintenance missinginstance '
          '--reschedule-type=IMMEDIATE'
      )

  def testRescheduleMaintenanceNoneScheduled(self):
    self.ExpectInstanceGet(None)
    with self.assertRaisesRegex(
        sql_exceptions.InvalidStateError,
        'This instance does not have any scheduled maintenance at this time.'):
      self.Run(
          'sql reschedule-maintenance testinstance --reschedule-type=IMMEDIATE')

  def testRescheduleMaintenanceCantReschedule(self):
    self.ExpectInstanceGet(self.GetScheduledMaintenance(False))
    with self.assertRaisesRegex(
        sql_exceptions.InvalidStateError,
        'Cannot reschedule this instance\'s maintenance.'):
      self.Run(
          'sql reschedule-maintenance testinstance --reschedule-type=IMMEDIATE')

  def testRescheduleMaintenanceSpecificTimeInvalidScheduleTimePast(self):
    self.ExpectInstanceGet(self.GetScheduledMaintenance(True))
    with self.assertRaisesRegex(
        sql_exceptions.ArgumentError,
        r'argument --schedule-time: Must be after original scheduled time.'):
      self.Run(
          'sql reschedule-maintenance testinstance '
          '--reschedule-type=SPECIFIC_TIME --schedule-time=2019-11-09T04:15Z'
      )

  def testRescheduleMaintenanceSpecificTimeInvalidScheduleTimeFuture7(self):
    self.ExpectInstanceGet(self.GetScheduledMaintenance(True))
    with self.assertRaisesRegex(
        sql_exceptions.ArgumentError,
        r'argument --schedule-time: Must be no more than 7 days after original '
        'scheduled time.'
    ):
      self.Run(
          'sql reschedule-maintenance testinstance '
          '--reschedule-type=SPECIFIC_TIME --schedule-time=2019-11-18T04:15Z'
      )

  def testRescheduleMaintenanceImmediate(self):
    self.ExpectInstanceGet(self.GetScheduledMaintenance(True))
    self.ExpectRescheduleMaintenance(
        self.messages.Reschedule.RescheduleTypeValueValuesEnum.IMMEDIATE)
    self.Run(
        'sql reschedule-maintenance testinstance --reschedule-type=IMMEDIATE')
    self.AssertErrContains('Rescheduling maintenance.')
    self.AssertErrContains('Maintenance rescheduled.')

  def testRescheduleMaintenanceNext(self):
    self.ExpectInstanceGet(self.GetScheduledMaintenance(True))
    self.ExpectRescheduleMaintenance(
        self.messages.Reschedule.RescheduleTypeValueValuesEnum
        .NEXT_AVAILABLE_WINDOW)
    self.Run(
        'sql reschedule-maintenance testinstance '
        '--reschedule-type=NEXT_AVAILABLE_WINDOW'
    )
    self.AssertErrContains('Rescheduling maintenance.')
    self.AssertErrContains('Maintenance rescheduled.')

  def testRescheduleMaintenanceSpecific(self):
    self.ExpectInstanceGet(self.GetScheduledMaintenance(True))
    self.ExpectRescheduleMaintenance(
        self.messages.Reschedule.RescheduleTypeValueValuesEnum.SPECIFIC_TIME,
        '2019-11-16T04:15:00Z')
    self.Run(
        'sql reschedule-maintenance testinstance '
        '--reschedule-type=SPECIFIC_TIME --schedule-time=2019-11-16T04:15Z'
    )
    self.AssertErrContains('Rescheduling maintenance.')
    self.AssertErrContains('Maintenance rescheduled.')

  def testRescheduleMaintenanceSpecificNonUtc(self):
    self.ExpectInstanceGet(self.GetScheduledMaintenance(True))
    self.ExpectRescheduleMaintenance(
        self.messages.Reschedule.RescheduleTypeValueValuesEnum.SPECIFIC_TIME,
        '2019-11-16T04:15:00Z')
    self.Run(
        'sql reschedule-maintenance testinstance '
        '--reschedule-type=SPECIFIC_TIME --schedule-time=2019-11-16T02:15-02:00'
    )
    self.AssertErrContains('Rescheduling maintenance.')
    self.AssertErrContains('Maintenance rescheduled.')


class RescheduleMaintenanceBetaTest(RescheduleMaintenanceGATest,
                                    base.SqlMockTestBeta):
  pass


class RescheduleMaintenanceAlphaTest(RescheduleMaintenanceBetaTest,
                                     base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
