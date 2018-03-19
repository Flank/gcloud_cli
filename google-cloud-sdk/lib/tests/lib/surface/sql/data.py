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
"""Provides sample messages for SQL tests."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
from apitools.base.protorpclite import util as protorpc_util
from googlecloudsdk.api_lib.util import apis as core_apis

sqladmin_v1beta4 = core_apis.GetMessagesModule('sqladmin', 'v1beta4')

DEFAULT_INSTANCE_NAME = 'test-instance'
DEFAULT_BACKUP_ID = 1234

# Factory functions to generate sample DatabaseInstance instances.


def GetDatabaseInstancesListOfTwo():
  """Returns a list of two sample DatabaseInstance instances."""
  return [
      sqladmin_v1beta4.DatabaseInstance(
          currentDiskSize=52690837,
          databaseVersion=u'MYSQL_5_5',
          etag=u'"DExdZ69FktjWMJ-ohD1vLZW9pnk/MQ"',
          name=u'testinstance',
          ipAddresses=[],
          ipv6Address=u'2001:4860:4864:1:df7c:6a7a:d107:ab9d',
          kind=u'sql#instance',
          maxDiskSize=268435456000,
          project=u'testproject',
          region=u'us-central',
          serverCaCert=None,
          settings=sqladmin_v1beta4.Settings(
              activationPolicy=u'ON_DEMAND',
              authorizedGaeApplications=[],
              backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
                  binaryLogEnabled=False,
                  enabled=True,
                  kind=u'sql#backupConfiguration',
                  startTime=u'11:54'),
              databaseFlags=[],
              ipConfiguration=sqladmin_v1beta4.IpConfiguration(
                  authorizedNetworks=[],
                  ipv4Enabled=False,
                  requireSsl=None,),
              kind=u'sql#settings',
              locationPreference=None,
              pricingPlan=u'PER_USE',
              replicationType=u'SYNCHRONOUS',
              settingsVersion=1,
              tier=u'D0',),
          state=u'RUNNABLE',
          instanceType=u'CLOUD_SQL_INSTANCE',),
      sqladmin_v1beta4.DatabaseInstance(
          currentDiskSize=287571860,
          databaseVersion=u'MYSQL_5_5',
          etag=u'"yGhHGJDUk5hWK-gppo_8C-KD7iU/QWyUhySo75iWP2WEOzCGc"',
          gceZone='us-central1-a',
          name=u'backupless-instance1',
          ipAddresses=[],
          ipv6Address=u'2001:4860:4864:1:df7c:6a7a:d107:aaaa',
          kind=u'sql#instance',
          maxDiskSize=268435456000,
          project=u'testproject',
          region=u'us-central1',
          serverCaCert=sqladmin_v1beta4.SslCert(
              cert=u'-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAg',
              certSerialNumber=u'0',
              commonName=u'C=US,O=Google\\, Inc,CN=Google Cloud SQL ',
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
              instance=u'backupless-instance1',
              kind=u'sql#sslCert',
              sha1Fingerprint=u'70bd50bd905e822ce428b8a1345ffc68d5aa',),
          settings=sqladmin_v1beta4.Settings(
              activationPolicy=u'ON_DEMAND',
              authorizedGaeApplications=[],
              backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
                  binaryLogEnabled=True,
                  enabled=True,
                  kind=u'sql#backupConfiguration',
                  startTime=u'12:00'),
              databaseFlags=[],
              ipConfiguration=sqladmin_v1beta4.IpConfiguration(
                  authorizedNetworks=[],
                  ipv4Enabled=False,
                  requireSsl=None,),
              kind=u'sql#settings',
              locationPreference=None,
              pricingPlan=u'PER_USE',
              replicationType=u'SYNCHRONOUS',
              settingsVersion=1,
              tier=u'D1',),
          state=u'RUNNABLE',
          instanceType=u'CLOUD_SQL_INSTANCE',)
  ]


def GetDatabaseInstancesListOfOne():
  """Returns a list of one sample DatabaseInstance instance."""
  return [
      sqladmin_v1beta4.DatabaseInstance(
          currentDiskSize=287571860,
          databaseVersion=u'MYSQL_5_5',
          etag=u'"yGhHGJDUk5hWK-gppo_8C-KD7iU/nbMj8WWUtdJPpSjOHUxEh"',
          name=u'backupless-instance2',
          ipAddresses=[],
          ipv6Address=u'2001:4860:4864:1:df7c:6a7a:d107:aaaa',
          kind=u'sql#instance',
          maxDiskSize=268435456000,
          project=u'testproject',
          region=u'us-central',
          serverCaCert=sqladmin_v1beta4.SslCert(
              cert=u'-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAg',
              certSerialNumber=u'0',
              commonName=u'C=US,O=Google\\, Inc,CN=Google Cloud SQL ',
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
              instance=u'backupless-instance',
              kind=u'sql#sslCert',
              sha1Fingerprint=u'a691db45f7dee0827650fd2eb277d2ca81b9',),
          settings=sqladmin_v1beta4.Settings(
              activationPolicy=u'NEVER',
              authorizedGaeApplications=[],
              backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
                  binaryLogEnabled=False,
                  enabled=False,
                  kind=u'sql#backupConfiguration',
                  startTime=u'00:00'),
              databaseFlags=[],
              databaseReplicationEnabled=None,
              ipConfiguration=sqladmin_v1beta4.IpConfiguration(
                  authorizedNetworks=[],
                  ipv4Enabled=False,
                  requireSsl=None,),
              kind=u'sql#settings',
              locationPreference=sqladmin_v1beta4.LocationPreference(
                  followGaeApplication=None,
                  kind=u'sql#locationPreference',
                  zone=None,),
              pricingPlan=u'PER_USE',
              replicationType=u'SYNCHRONOUS',
              settingsVersion=1,
              tier=u'D1',),
          state=u'RUNNABLE',
          instanceType=u'CLOUD_SQL_INSTANCE',)
  ]


def GetRequestInstance(project, instance_name):
  """Returns a sample DatabaseInstance named instance_name, to use in CREATE."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType=None,
      connectionName=None,
      currentDiskSize=None,
      databaseVersion='MYSQL_5_6',
      etag=None,
      failoverReplica=None,
      instanceType=None,
      ipAddresses=[],
      ipv6Address=None,
      kind=u'sql#instance',
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
          kind=u'sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan='PER_USE',
          replicationType='SYNCHRONOUS',
          settingsVersion=None,
          storageAutoResize=None,
          storageAutoResizeLimit=None,
          tier='db-n1-standard-1',
          userLabels=None,),
      state=None,
      suspensionReason=[],)


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
      kind=u'sql#instance',
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
          kind=u'sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan=None,
          replicationType=None,
          settingsVersion=None,
          storageAutoResize=None,
          storageAutoResizeLimit=None,
          tier=None,
          userLabels=None,),
      state=None,
      suspensionReason=[],)


def GetV1Instance(project, instance_name):
  """Returns a sample MySQL V1 DatabaseInstance named instance_name."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType=u'FIRST_GEN',
      connectionName=u'test-connection-name',
      currentDiskSize=281811817,
      databaseVersion=u'MYSQL_5_6',
      etag=u'"7nzH-h2yIa307nzH-h2nzH-h2g/MQ"',
      failoverReplica=None,
      instanceType=u'CLOUD_SQL_INSTANCE',
      ipAddresses=[],
      ipv6Address=u'2000:3000:4000:1:92cd:7afd:2e22:9fa3',
      kind=u'sql#instance',
      masterInstanceName=None,
      maxDiskSize=268435456000,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region=u'us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink=u'https://www.googleapis.com/sql/v1beta4/projects/sample-link',
      serverCaCert=sqladmin_v1beta4.SslCert(
          cert=u'-----BEGIN CERTIFICATE-----\ntestcert',
          certSerialNumber=u'0',
          commonName=u'C=US,O=Google\\, Inc,CN=Google Cloud SQL Server CA',
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
          instance=u'create-instance1',
          kind=u'sql#sslCert',
          selfLink=None,
          sha1Fingerprint=u'd89219c0742139ae46a580742139ae8fd1cf6d30',),
      serviceAccountEmailAddress=None,
      settings=sqladmin_v1beta4.Settings(
          activationPolicy=u'ON_DEMAND',
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
              binaryLogEnabled=None,
              enabled=False,
              kind=u'sql#backupConfiguration',
              startTime=u'06:00',),
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=None,
          dataDiskType=None,
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=sqladmin_v1beta4.IpConfiguration(
              authorizedNetworks=[],
              ipv4Enabled=False,
              requireSsl=None,),
          kind=u'sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan=u'PER_USE',
          replicationType=u'SYNCHRONOUS',
          settingsVersion=1,
          storageAutoResize=None,
          storageAutoResizeLimit=None,
          tier=u'D1',
          userLabels=None,),
      state=u'RUNNABLE',
      suspensionReason=[],)


def GetV2Instance(project, instance_name):
  """Returns a sample MySQL V2 DatabaseInstance named instance_name."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType=u'SECOND_GEN',
      connectionName=u'test-connection-name',
      currentDiskSize=None,
      databaseVersion=u'MYSQL_5_6',
      etag=u'"7nzH-h2yIa30FGKFRs9YFu88s0g/MQ"',
      failoverReplica=None,
      instanceType=u'CLOUD_SQL_INSTANCE',
      ipAddresses=[
          sqladmin_v1beta4.IpMapping(
              ipAddress=u'0.0.0.0',
              timeToRetire=None,
              type=u'PRIMARY',),
      ],
      ipv6Address=None,
      kind=u'sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region=u'us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink=u'https://www.googleapis.com/sql/v1beta4/projects/sample-link',
      serverCaCert=sqladmin_v1beta4.SslCert(
          cert=u'-----BEGIN CERTIFICATE-----\ntestcert',
          certSerialNumber=u'0',
          commonName=u'C=US,O=Google\\, Inc,CN=Google Cloud SQL Server CA',
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
          instance=u'create-instance1-v1',
          kind=u'sql#sslCert',
          selfLink=None,
          sha1Fingerprint=u'4d18ed6c0742139a14caa988e04cd3ad6e9a9bfc',),
      serviceAccountEmailAddress=u'test@sample.iam.gserviceaccount.com',
      settings=sqladmin_v1beta4.Settings(
          activationPolicy=u'ALWAYS',
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
              binaryLogEnabled=None,
              enabled=False,
              kind=u'sql#backupConfiguration',
              startTime=u'14:00',),
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=10,
          dataDiskType=u'PD_SSD',
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=sqladmin_v1beta4.IpConfiguration(
              authorizedNetworks=[],
              ipv4Enabled=True,
              requireSsl=None,),
          kind=u'sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan=u'PER_USE',
          replicationType=u'SYNCHRONOUS',
          settingsVersion=1,
          storageAutoResize=True,
          storageAutoResizeLimit=0,
          tier=u'db-n1-standard-1',
          userLabels=None,),
      state=u'RUNNABLE',
      suspensionReason=[],)


def GetPostgresInstance(project, instance_name):
  """Returns a sample Postgres DatabaseInstance named instance_name."""
  return sqladmin_v1beta4.DatabaseInstance(
      backendType=u'SECOND_GEN',
      connectionName=u'test-connection-name',
      currentDiskSize=None,
      databaseVersion=u'POSTGRES_9_6',
      etag=u'"7nzH-7nzH-h2yIKFRs9YFu88s0g/MA"',
      failoverReplica=None,
      instanceType=u'CLOUD_SQL_INSTANCE',
      ipAddresses=[
          sqladmin_v1beta4.IpMapping(
              ipAddress=u'0.0.0.0',
              timeToRetire=None,
              type=u'PRIMARY',),
      ],
      ipv6Address=None,
      kind=u'sql#instance',
      masterInstanceName=None,
      maxDiskSize=None,
      name=instance_name,
      onPremisesConfiguration=None,
      project=project,
      region=u'us-central',
      replicaConfiguration=None,
      replicaNames=[],
      selfLink=u'https://www.googleapis.com/sql/v1beta4/projects/sample-link',
      serverCaCert=None,
      serviceAccountEmailAddress=u'test@sample.iam.gserviceaccount.com',
      settings=sqladmin_v1beta4.Settings(
          activationPolicy=u'ALWAYS',
          authorizedGaeApplications=[],
          availabilityType=None,
          backupConfiguration=sqladmin_v1beta4.BackupConfiguration(
              binaryLogEnabled=None,
              enabled=False,
              kind=u'sql#backupConfiguration',
              startTime=u'06:00',),
          crashSafeReplicationEnabled=None,
          dataDiskSizeGb=10,
          dataDiskType=u'PD_SSD',
          databaseFlags=[],
          databaseReplicationEnabled=None,
          ipConfiguration=sqladmin_v1beta4.IpConfiguration(
              authorizedNetworks=[],
              ipv4Enabled=True,
              requireSsl=None,),
          kind=u'sql#settings',
          locationPreference=None,
          maintenanceWindow=None,
          pricingPlan=u'PER_USE',
          replicationType=u'SYNCHRONOUS',
          settingsVersion=0,
          storageAutoResize=True,
          storageAutoResizeLimit=0,
          tier=u'db-custom-1-3840',
          userLabels=None,),
      state=u'RUNNABLE',
      suspensionReason=[],)


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
      status=status,)


def GetBackupDeleteRequest(project, backup):
  """Returns a sample SqlBackupRunsDeleteRequest to DELETE backup."""
  return sqladmin_v1beta4.SqlBackupRunsDeleteRequest(
      project=project,
      id=backup.id,
      instance=backup.instance,)


# Factory functions to generate sample Operation instances.


def GetOperation(project, instance, op_type, op_status):
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
      error=None,
      exportContext=None,
      importContext=None,
      targetId=instance.name,
      targetLink=u'https://www.googleapis.com/sql/v1beta4/projects/{0}'.format(
          project),
      targetProject=project,
      kind=u'sql#operation',
      name=u'344acb84-0000-1111-2222-1e71c6077b34',
      selfLink=
      u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/sample'.
      format(project),
      operationType=op_type,
      status=op_status,
      user=u'test@sample.gserviceaccount.com',)


def GetOperationGetRequest(project):
  """Returns a sample SqlOperationsGetRequest."""
  return sqladmin_v1beta4.SqlOperationsGetRequest(
      operation=u'344acb84-0000-1111-2222-1e71c6077b34', project=project)
