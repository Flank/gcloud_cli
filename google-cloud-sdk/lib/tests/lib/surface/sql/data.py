# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Provides sample messages for SQL tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from apitools.base.protorpclite import util as protorpc_util
from googlecloudsdk.api_lib.util import apis as core_apis

sqladmin_v1beta4 = core_apis.GetMessagesModule('sqladmin', 'v1beta4')

DEFAULT_INSTANCE_NAME = 'test-instance'
DEFAULT_INSTANCE_DATABASE_VERSION = 'MYSQL_5_7'
DEFAULT_BACKUP_ID = 1234

DEFAULT_CERT_CREATE_TIME = datetime.datetime(
    2024,
    1,
    28,
    1,
    55,
    28,
    96000,
    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0)))

# Factory functions to generate sample DatabaseInstance instances.


def GetDatabaseInstancesListOfTwo():
  """Returns a list of two sample DatabaseInstance instances."""
  return [
      sqladmin_v1beta4.DatabaseInstance(
          currentDiskSize=52690837,
          databaseVersion='MYSQL_5_5',
          etag='"DExdZ69FktjWMJ-ohD1vLZW9pnk/MQ"',
          name='testinstance',
          ipAddresses=[],
          ipv6Address='2001:4860:4864:1:df7c:6a7a:d107:ab9d',
          kind='sql#instance',
          maxDiskSize=268435456000,
          project='testproject',
          region='us-central',
          serverCaCert=None,
          settings=sqladmin_v1beta4.Settings(
              activationPolicy='ON_DEMAND',
              authorizedGaeApplications=[],
              backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
                  binaryLogEnabled=False,
                  enabled=True,
                  kind='sql#backupConfiguration',
                  startTime='11:54'),
              databaseFlags=[],
              ipConfiguration=sqladmin_v1beta4.IpConfiguration(
                  authorizedNetworks=[],
                  ipv4Enabled=False,
                  requireSsl=None,
              ),
              kind='sql#settings',
              locationPreference=None,
              pricingPlan='PER_USE',
              replicationType='SYNCHRONOUS',
              settingsVersion=1,
              tier='D0',
          ),
          state='RUNNABLE',
          instanceType='CLOUD_SQL_INSTANCE',
      ),
      sqladmin_v1beta4.DatabaseInstance(
          currentDiskSize=287571860,
          databaseVersion='MYSQL_5_5',
          etag='"yGhHGJDUk5hWK-gppo_8C-KD7iU/QWyUhySo75iWP2WEOzCGc"',
          gceZone='us-central1-a',
          name='backupless-instance1',
          ipAddresses=[],
          ipv6Address='2001:4860:4864:1:df7c:6a7a:d107:aaaa',
          kind='sql#instance',
          maxDiskSize=268435456000,
          project='testproject',
          region='us-central1',
          serverCaCert=sqladmin_v1beta4.SslCert(
              cert='-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAg',
              certSerialNumber='0',
              commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL ',
              createTime=datetime.datetime(
                  2014,
                  8,
                  12,
                  19,
                  43,
                  9,
                  329000,
                  tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
              expirationTime=datetime.datetime(
                  2024,
                  8,
                  9,
                  19,
                  43,
                  9,
                  329000,
                  tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
              instance='backupless-instance1',
              kind='sql#sslCert',
              sha1Fingerprint='70bd50bd905e822ce428b8a1345ffc68d5aa',
          ),
          settings=sqladmin_v1beta4.Settings(
              activationPolicy='ON_DEMAND',
              authorizedGaeApplications=[],
              backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
                  binaryLogEnabled=True,
                  enabled=True,
                  kind='sql#backupConfiguration',
                  startTime='12:00'),
              databaseFlags=[],
              ipConfiguration=sqladmin_v1beta4.IpConfiguration(
                  authorizedNetworks=[],
                  ipv4Enabled=False,
                  requireSsl=None,
              ),
              kind='sql#settings',
              locationPreference=None,
              pricingPlan='PER_USE',
              replicationType='SYNCHRONOUS',
              settingsVersion=1,
              tier='D1',
          ),
          state='RUNNABLE',
          instanceType='CLOUD_SQL_INSTANCE',
      )
  ]


def GetDatabaseInstancesListOfOne():
  """Returns a list of one sample DatabaseInstance instance."""
  return [
      sqladmin_v1beta4.DatabaseInstance(
          currentDiskSize=287571860,
          databaseVersion='MYSQL_5_5',
          etag='"yGhHGJDUk5hWK-gppo_8C-KD7iU/nbMj8WWUtdJPpSjOHUxEh"',
          name='backupless-instance2',
          ipAddresses=[],
          ipv6Address='2001:4860:4864:1:df7c:6a7a:d107:aaaa',
          kind='sql#instance',
          maxDiskSize=268435456000,
          project='testproject',
          region='us-central',
          serverCaCert=sqladmin_v1beta4.SslCert(
              cert='-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAg',
              certSerialNumber='0',
              commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL ',
              createTime=datetime.datetime(
                  2014,
                  8,
                  11,
                  21,
                  47,
                  10,
                  788000,
                  tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
              expirationTime=datetime.datetime(
                  2024,
                  8,
                  8,
                  21,
                  47,
                  10,
                  788000,
                  tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
              instance='backupless-instance',
              kind='sql#sslCert',
              sha1Fingerprint='a691db45f7dee0827650fd2eb277d2ca81b9',
          ),
          settings=sqladmin_v1beta4.Settings(
              activationPolicy='NEVER',
              authorizedGaeApplications=[],
              backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
                  binaryLogEnabled=False,
                  enabled=False,
                  kind='sql#backupConfiguration',
                  startTime='00:00'),
              databaseFlags=[],
              databaseReplicationEnabled=None,
              ipConfiguration=sqladmin_v1beta4.IpConfiguration(
                  authorizedNetworks=[],
                  ipv4Enabled=False,
                  requireSsl=None,
              ),
              kind='sql#settings',
              locationPreference=sqladmin_v1beta4.LocationPreference(
                  followGaeApplication=None,
                  kind='sql#locationPreference',
                  zone=None,
              ),
              pricingPlan='PER_USE',
              replicationType='SYNCHRONOUS',
              settingsVersion=1,
              tier='D1',
          ),
          state='RUNNABLE',
          instanceType='CLOUD_SQL_INSTANCE',
      )
  ]


def GetRequestInstance(project, instance_name):
  """Returns a sample DatabaseInstance named instance_name, to use in CREATE."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType=None,
      connectionName=None,
      currentDiskSize=None,
      databaseVersion=None,
      etag=None,
      failoverReplica=None,
      instanceType=None,
      ipAddresses=[],
      ipv6Address=None,
      kind='sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region='us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink=None,
      serverCaCert=None,
      serviceAccountEmailAddress=None,
      settings=sqladmin_v1beta4.Settings(
          activationPolicy=None,
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=None,
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=None,
          dataDiskType=None,
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=None,
          kind='sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan='PER_USE',
          replicationType='SYNCHRONOUS',
          settingsVersion=None,
          storageAutoResize=None,
          storageAutoResizeLimit=None,
          tier='db-n1-standard-1',
          userLabels=None,
      ),
      state=None,
      suspensionReason=[],
  )


def GetExternalMasterRequestInstance(project, instance_name):
  """Returns an empty external master instance for making create requests."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType=None,
      connectionName=None,
      currentDiskSize=None,
      databaseVersion=None,
      etag=None,
      failoverReplica=None,
      gceZone=None,
      instanceType=None,
      ipAddresses=[],
      ipv6Address=None,
      kind='sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=sqladmin_v1beta4.OnPremisesConfiguration(
          hostPort=None,
          kind='sql#onPremisesConfiguration',
      ),
      project=project,
      region='us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink=None,
      serverCaCert=None,
      serviceAccountEmailAddress=None,
      settings=None,
      state=None,
      suspensionReason=[],
  )


def GetPatchRequestInstance(project, instance_name):
  """Returns a sample DatabaseInstance named instance_name, to use in PATCH."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType=None,
      connectionName=None,
      currentDiskSize=None,
      databaseVersion=None,
      etag=None,
      failoverReplica=None,
      instanceType=None,
      ipAddresses=[],
      ipv6Address=None,
      kind='sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region=None,
      replicaConfiguration=None,
      replicaNames=[],
      selfLink=None,
      serverCaCert=None,
      serviceAccountEmailAddress=None,
      settings=sqladmin_v1beta4.Settings(
          activationPolicy=None,
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=None,
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=None,
          dataDiskType=None,
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=None,
          kind='sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan=None,
          replicationType=None,
          settingsVersion=None,
          storageAutoResize=None,
          storageAutoResizeLimit=None,
          tier=None,
          userLabels=None,
      ),
      state=None,
      suspensionReason=[],
  )


def GetV1Instance(project, instance_name):
  """Returns a sample MySQL V1 DatabaseInstance named instance_name."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType='FIRST_GEN',
      connectionName='test-connection-name',
      currentDiskSize=281811817,
      databaseVersion=DEFAULT_INSTANCE_DATABASE_VERSION,
      etag='"7nzH-h2yIa307nzH-h2nzH-h2g/MQ"',
      failoverReplica=None,
      instanceType='CLOUD_SQL_INSTANCE',
      ipAddresses=[],
      ipv6Address='2000:3000:4000:1:92cd:7afd:2e22:9fa3',
      kind='sql#instance',
      masterInstanceName=None,
      maxDiskSize=268435456000,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region='us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink='https://www.googleapis.com/sql/v1beta4/projects/sample-link',
      serverCaCert=sqladmin_v1beta4.SslCert(
          cert='-----BEGIN CERTIFICATE-----\ntestcert',
          certSerialNumber='0',
          commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL Server CA',
          createTime=datetime.datetime(
              2017,
              7,
              19,
              13,
              0,
              0,
              92000,
              tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
          expirationTime=datetime.datetime(
              2019,
              7,
              19,
              13,
              1,
              0,
              92000,
              tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
          instance='create-instance1',
          kind='sql#sslCert',
          selfLink=None,
          sha1Fingerprint='d89219c0742139ae46a580742139ae8fd1cf6d30',
      ),
      serviceAccountEmailAddress=None,
      settings=sqladmin_v1beta4.Settings(
          activationPolicy='ON_DEMAND',
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
              binaryLogEnabled=None,
              enabled=False,
              kind='sql#backupConfiguration',
              startTime='06:00',
          ),
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=None,
          dataDiskType=None,
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=sqladmin_v1beta4.IpConfiguration(
              authorizedNetworks=[],
              ipv4Enabled=False,
              requireSsl=None,
          ),
          kind='sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan='PER_USE',
          replicationType='SYNCHRONOUS',
          settingsVersion=1,
          storageAutoResize=None,
          storageAutoResizeLimit=None,
          tier='D1',
          userLabels=None,
      ),
      state='RUNNABLE',
      suspensionReason=[],
  )


def GetV2Instance(project, instance_name):
  """Returns a sample MySQL V2 DatabaseInstance named instance_name."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType='SECOND_GEN',
      connectionName='test-connection-name',
      currentDiskSize=None,
      databaseVersion=DEFAULT_INSTANCE_DATABASE_VERSION,
      etag='"7nzH-h2yIa30FGKFRs9YFu88s0g/MQ"',
      failoverReplica=None,
      instanceType='CLOUD_SQL_INSTANCE',
      ipAddresses=[
          sqladmin_v1beta4.IpMapping(
              ipAddress='0.0.0.0',
              timeToRetire=None,
              type='PRIMARY',
          ),
      ],
      ipv6Address=None,
      kind='sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region='us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink='https://www.googleapis.com/sql/v1beta4/projects/sample-link',
      serverCaCert=sqladmin_v1beta4.SslCert(
          cert='-----BEGIN CERTIFICATE-----\ntestcert',
          certSerialNumber='0',
          commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL Server CA',
          createTime=datetime.datetime(
              2017,
              7,
              19,
              14,
              11,
              41,
              694000,
              tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
          expirationTime=datetime.datetime(
              2019,
              7,
              19,
              14,
              12,
              41,
              694000,
              tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
          instance='create-instance1-v1',
          kind='sql#sslCert',
          selfLink=None,
          sha1Fingerprint='4d18ed6c0742139a14caa988e04cd3ad6e9a9bfc',
      ),
      serviceAccountEmailAddress='test@sample.iam.gserviceaccount.com',
      settings=sqladmin_v1beta4.Settings(
          activationPolicy='ALWAYS',
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
              binaryLogEnabled=None,
              enabled=False,
              kind='sql#backupConfiguration',
              startTime='14:00',
          ),
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=10,
          dataDiskType='PD_SSD',
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=sqladmin_v1beta4.IpConfiguration(
              authorizedNetworks=[],
              ipv4Enabled=True,
              requireSsl=None,
          ),
          kind='sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan='PER_USE',
          replicationType='SYNCHRONOUS',
          settingsVersion=1,
          storageAutoResize=True,
          storageAutoResizeLimit=0,
          tier='db-n1-standard-1',
          userLabels=None,
      ),
      state='RUNNABLE',
      suspensionReason=[],
  )


def GetPostgresInstance(project, instance_name):
  """Returns a sample Postgres DatabaseInstance named instance_name."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType='SECOND_GEN',
      connectionName='test-connection-name',
      currentDiskSize=None,
      databaseVersion='POSTGRES_9_6',
      etag='"7nzH-7nzH-h2yIKFRs9YFu88s0g/MA"',
      failoverReplica=None,
      instanceType='CLOUD_SQL_INSTANCE',
      ipAddresses=[
          sqladmin_v1beta4.IpMapping(
              ipAddress='0.0.0.0',
              timeToRetire=None,
              type='PRIMARY',
          ),
      ],
      ipv6Address=None,
      kind='sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region='us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink='https://www.googleapis.com/sql/v1beta4/projects/sample-link',
      serverCaCert=None,
      serviceAccountEmailAddress='test@sample.iam.gserviceaccount.com',
      settings=sqladmin_v1beta4.Settings(
          activationPolicy='ALWAYS',
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
              binaryLogEnabled=None,
              enabled=False,
              kind='sql#backupConfiguration',
              startTime='06:00',
          ),
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=10,
          dataDiskType='PD_SSD',
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=sqladmin_v1beta4.IpConfiguration(
              authorizedNetworks=[],
              ipv4Enabled=True,
              requireSsl=None,
          ),
          kind='sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan='PER_USE',
          replicationType='SYNCHRONOUS',
          settingsVersion=0,
          storageAutoResize=True,
          storageAutoResizeLimit=0,
          tier='db-custom-1-3840',
          userLabels=None,
      ),
      state='RUNNABLE',
      suspensionReason=[],
  )


def GetSqlServerInstance(project, instance_name):
  """Returns a sample SQL Server DatabaseInstance named instance_name."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType='SECOND_GEN',
      connectionName='test-connection-name',
      currentDiskSize=None,
      databaseVersion='SQLSERVER_2017_STANDARD',
      etag='"7nzH-7nzH-h2yIKFRs9YFu88s0g/MA"',
      failoverReplica=None,
      instanceType='CLOUD_SQL_INSTANCE',
      ipAddresses=[
          sqladmin_v1beta4.IpMapping(
              ipAddress='0.0.0.0',
              timeToRetire=None,
              type='PRIMARY',
          ),
      ],
      ipv6Address=None,
      kind='sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region='us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink='https://www.googleapis.com/sql/v1beta4/projects/sample-link',
      serverCaCert=None,
      serviceAccountEmailAddress='test@sample.iam.gserviceaccount.com',
      settings=sqladmin_v1beta4.Settings(
          activationPolicy='ALWAYS',
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
              binaryLogEnabled=None,
              enabled=False,
              kind='sql#backupConfiguration',
              startTime='06:00',
          ),
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=10,
          dataDiskType='PD_SSD',
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=sqladmin_v1beta4.IpConfiguration(
              authorizedNetworks=[],
              ipv4Enabled=True,
              requireSsl=None,
          ),
          kind='sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan='PER_USE',
          replicationType='SYNCHRONOUS',
          settingsVersion=0,
          storageAutoResize=True,
          storageAutoResizeLimit=0,
          tier='db-custom-1-3840',
          userLabels=None,
      ),
      state='RUNNABLE',
      suspensionReason=[],
  )


def GetExternalMasterInstance(project, instance_name):
  """Returns a sample external master DatabaseInstance named instance_name."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType='EXTERNAL',
      connectionName=None,
      currentDiskSize=None,
      databaseVersion=DEFAULT_INSTANCE_DATABASE_VERSION,
      etag='"7nzH-7nzH-h2yIKFRs9YFu88s0g/MA"',
      failoverReplica=None,
      gceZone=None,
      instanceType='ON_PREMISES_INSTANCE',
      ipAddresses=[],
      ipv6Address=None,
      kind='sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=sqladmin_v1beta4.OnPremisesConfiguration(
          hostPort='127.0.0.1:3306',
          kind='sql#onPremisesConfiguration',
      ),
      project=project,
      region='us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink=None,
      serverCaCert=None,
      serviceAccountEmailAddress=None,
      settings=None,
      state=None,
      suspensionReason=[],
  )


def GetInstanceGetRequest(project, instance):
  """Returns a sample SqlInstancesGetRequest to GET instance."""
  return sqladmin_v1beta4.SqlInstancesGetRequest(
      instance=instance.name, project=project)


def GetInstancePatchRequest(project, instance):
  """Returns a sample SqlInstancesPatchRequest to PATCH instance."""
  return sqladmin_v1beta4.SqlInstancesPatchRequest(
      project=project, instance=instance.name, databaseInstance=instance)


# Factory functions to generate sample BackupRun instances.


def GetBackup(instance, backup_id, status):
  """Returns a sample BackupRun w/ id backup_id and the given status."""
  return sqladmin_v1beta4.BackupRun(
      id=backup_id,
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
      instance=instance.name,
      kind='sql#backupRun',
      startTime=datetime.datetime(
          2014,
          8,
          14,
          0,
          25,
          12,
          321000,
          tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
      status=status,
  )


def GetBackupDeleteRequest(project, backup):
  """Returns a sample SqlBackupRunsDeleteRequest to DELETE backup."""
  return sqladmin_v1beta4.SqlBackupRunsDeleteRequest(
      project=project,
      id=backup.id,
      instance=backup.instance,)


# Factory functions to generate sample Operation instances.


def GetOperation(project, instance, op_type, op_status, error=None):
  """Returns a sample Operation of op_type and op_status acting on instance."""
  return sqladmin_v1beta4.Operation(
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
      error=error,
      exportContext=None,
      importContext=None,
      targetId=instance.name,
      targetLink='https://www.googleapis.com/sql/v1beta4/projects/{0}'.format(
          project),
      targetProject=project,
      kind='sql#operation',
      name='344acb84-0000-1111-2222-1e71c6077b34',
      selfLink='https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/sample'
      .format(project),
      operationType=op_type,
      status=op_status,
      user='test@sample.gserviceaccount.com',
  )


def GetOperationGetRequest(project):
  """Returns a sample SqlOperationsGetRequest."""
  return sqladmin_v1beta4.SqlOperationsGetRequest(
      operation='344acb84-0000-1111-2222-1e71c6077b34', project=project)


def GetSslCert(instance,
               fingerprint,
               create_time=DEFAULT_CERT_CREATE_TIME,
               common_name=None):
  """Returns a sample SslCert."""
  return sqladmin_v1beta4.SslCert(
      cert='-----BEGIN CERTIFICATE-----\nMIICzAwIA\n-----END CERTIFICATE-----',
      certSerialNumber='1',
      commonName=common_name,
      createTime=create_time,
      expirationTime=create_time,
      instance=instance,
      sha1Fingerprint=fingerprint)
