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
from googlecloudsdk.api_lib.sql import network
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.sql import base

import mock

sqladmin_v1beta4 = core_apis.GetMessagesModule('sql', 'v1beta4')


class _BaseConnectTest(object):
  time_of_connection = network.GetCurrentTime()

  def ExpectInstanceGet(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance=self.instance['id'],
            project=self.Project(),
        ),
        self.messages.DatabaseInstance(
            # pylint:disable=line-too-long
            backendType=self.instance['backendType'],
            connectionName='{0}:us-central1:{1}'.format(self.Project(),
                                                        self.instance['id']),
            currentDiskSize=None,
            databaseVersion=self.instance['databaseVersion'],
            etag='"DlgRosmIegBpXj_rR5uyhdXAbP8/MQ"',
            failoverReplica=None,
            instanceType=self.messages.DatabaseInstance
            .InstanceTypeValueValuesEnum.CLOUD_SQL_INSTANCE,
            ipAddresses=[
                self.messages.IpMapping(
                    ipAddress='104.154.166.249',
                    timeToRetire=None,
                    type=self.messages.IpMapping.TypeValueValuesEnum.PRIMARY,
                ),
            ],
            ipv6Address=None,
            kind='sql#instance',
            masterInstanceName=None,
            maxDiskSize=None,
            name=self.instance['id'],
            onPremisesConfiguration=None,
            project=self.Project(),
            region='us-central1',
            replicaConfiguration=None,
            replicaNames=[],
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/{1}'
            .format(self.Project(), self.instance['id']),
            serverCaCert=self.messages.SslCert(
                cert='-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAgIBADANBgkqhkiG9w0BAQUFADBIMSMwIQYDVQQDExpHb29n\nbGUgQ2x',
                certSerialNumber='0',
                commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL Server CA',
                createTime=datetime.datetime(
                    2017,
                    5,
                    12,
                    21,
                    33,
                    4,
                    844000,
                    tzinfo=protorpc_util.TimeZoneOffset(
                        datetime.timedelta(0))).isoformat(),
                expirationTime=datetime.datetime(
                    2019,
                    5,
                    12,
                    21,
                    34,
                    4,
                    844000,
                    tzinfo=protorpc_util.TimeZoneOffset(
                        datetime.timedelta(0))).isoformat(),
                instance=self.instance['id'],
                kind='sql#sslCert',
                selfLink=None,
                sha1Fingerprint='fcddb49c4a00ff8796ba099933dbeb208b8599bd',
            ),
            serviceAccountEmailAddress='vxmlqos47zbmzgjppv2ued6e74@speckle-umbrella-5.iam.gserviceaccount.com',
            settings=self.messages.Settings(
                activationPolicy=self.messages.Settings
                .ActivationPolicyValueValuesEnum.ALWAYS,
                authorizedGaeApplications=[],
                availabilityType=None,
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=None,
                    enabled=False,
                    kind='sql#backupConfiguration',
                    startTime='10:00',
                ),
                crashSafeReplicationEnabled=None,
                dataDiskSizeGb=10,
                dataDiskType=self.messages.Settings.DataDiskTypeValueValuesEnum
                .PD_SSD,
                databaseFlags=[],
                databaseReplicationEnabled=None,
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=True,
                    requireSsl=None,
                ),
                kind='sql#settings',
                locationPreference=None,
                maintenanceWindow=None,
                pricingPlan=self.messages.Settings.PricingPlanValueValuesEnum
                .PER_USE,
                replicationType=self.messages.Settings
                .ReplicationTypeValueValuesEnum.SYNCHRONOUS,
                settingsVersion=1,
                storageAutoResize=None,
                storageAutoResizeLimit=None,
                tier=self.instance['tier'],
            ),
            state=self.messages.DatabaseInstance.StateValueValuesEnum.RUNNABLE,
            suspensionReason=[],
        ))

  def MockIPWhitelisting(self, error=False):
    # Mock the connection time.
    self.StartPatch(
        'googlecloudsdk.api_lib.sql.network.GetCurrentTime',
        return_value=self.time_of_connection)

    # Mock GET and PATCH endpoints
    self.ExpectInstanceGet()
    patch_request = self.messages.SqlInstancesPatchRequest(
        databaseInstance=self.messages.DatabaseInstance(
            # pylint:disable=line-too-long
            backendType=self.instance['backendType'],
            connectionName='{0}:us-central1:{1}'.format(self.Project(),
                                                        self.instance['id']),
            currentDiskSize=None,
            databaseVersion=self.instance['databaseVersion'],
            etag='"DlgRosmIegBpXj_rR5uyhdXAbP8/MQ"',
            failoverReplica=None,
            instanceType=self.messages.DatabaseInstance
            .InstanceTypeValueValuesEnum.CLOUD_SQL_INSTANCE,
            ipAddresses=[
                self.messages.IpMapping(
                    ipAddress='104.154.166.249',
                    timeToRetire=None,
                    type=self.messages.IpMapping.TypeValueValuesEnum.PRIMARY,
                ),
            ],
            ipv6Address=None,
            kind='sql#instance',
            masterInstanceName=None,
            maxDiskSize=None,
            name=self.instance['id'],
            onPremisesConfiguration=None,
            project=self.Project(),
            region='us-central1',
            replicaConfiguration=None,
            replicaNames=[],
            selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/{1}'
            .format(self.Project(), self.instance['id']),
            serverCaCert=None,
            serviceAccountEmailAddress='vxmlqos47zbmzgjppv2ued6e74@speckle-umbrella-5.iam.gserviceaccount.com',
            settings=self.messages.Settings(
                activationPolicy=self.messages.Settings
                .ActivationPolicyValueValuesEnum.ALWAYS,
                authorizedGaeApplications=[],
                availabilityType=None,
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=None,
                    enabled=False,
                    kind='sql#backupConfiguration',
                    startTime='10:00',
                ),
                crashSafeReplicationEnabled=None,
                dataDiskSizeGb=10,
                dataDiskType=self.messages.Settings.DataDiskTypeValueValuesEnum
                .PD_SSD,
                databaseFlags=[],
                databaseReplicationEnabled=None,
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[
                        self.messages.AclEntry(
                            expirationTime=(
                                self.time_of_connection +
                                datetime.timedelta(minutes=5)).replace(
                                    microsecond=10000).isoformat(),
                            kind='sql#aclEntry',
                            name='sql connect at time {0}'.format(
                                str(self.time_of_connection)),
                            value='CLIENT_IP',
                        ),
                    ],
                    ipv4Enabled=True,
                    requireSsl=None,
                ),
                kind='sql#settings',
                locationPreference=None,
                maintenanceWindow=None,
                pricingPlan=self.messages.Settings.PricingPlanValueValuesEnum
                .PER_USE,
                replicationType=self.messages.Settings
                .ReplicationTypeValueValuesEnum.SYNCHRONOUS,
                settingsVersion=1,
                storageAutoResize=None,
                storageAutoResizeLimit=None,
                tier=self.instance['tier'],
            ),
            state=self.messages.DatabaseInstance.StateValueValuesEnum.RUNNABLE,
            suspensionReason=[],
        ),
        instance=self.instance['id'],
        project=self.Project(),
    )
    if error:
      self.mocked_client.instances.Patch.Expect(
          patch_request,
          exception=http_error.MakeHttpError(
              code=400,
              message='invalidInstanceProperty',
              reason='Invalid instance property.',
          ))
    else:
      self.mocked_client.instances.Patch.Expect(
          patch_request,
          self.messages.Operation(
              # pylint:disable=line-too-long
              endTime=None,
              error=None,
              exportContext=None,
              importContext=None,
              insertTime=datetime.datetime(
                  2017,
                  5,
                  15,
                  23,
                  3,
                  50,
                  514000,
                  tzinfo=protorpc_util.TimeZoneOffset(
                      datetime.timedelta(0))).isoformat(),
              kind='sql#operation',
              name='8b7ffa62-e950-45c0-bdad-1d366ad8b964',
              operationType=self.messages.Operation.OperationTypeValueValuesEnum
              .UPDATE,
              selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/8b7ffa62-e9'
              .format(self.Project()),
              startTime=None,
              status=self.messages.Operation.StatusValueValuesEnum.PENDING,
              targetId=self.instance['id'],
              targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/{1}'
              .format(self.Project(), self.instance['id']),
              targetProject=self.Project(),
              user='462803083913-lak0k1ette3muh3o3kb3pp2im3urj3e9@developer.gserviceaccount.com',
          ))
      self.mocked_client.operations.Get.Expect(
          self.messages.SqlOperationsGetRequest(
              operation='8b7ffa62-e950-45c0-bdad-1d366ad8b964',
              project=self.Project(),
          ),
          self.messages.Operation(
              # pylint:disable=line-too-long
              endTime=datetime.datetime(
                  2017,
                  5,
                  15,
                  23,
                  5,
                  4,
                  809000,
                  tzinfo=protorpc_util.TimeZoneOffset(
                      datetime.timedelta(0))).isoformat(),
              error=None,
              exportContext=None,
              importContext=None,
              insertTime=datetime.datetime(
                  2017,
                  5,
                  15,
                  23,
                  3,
                  50,
                  514000,
                  tzinfo=protorpc_util.TimeZoneOffset(
                      datetime.timedelta(0))).isoformat(),
              kind='sql#operation',
              name='8b7ffa62-e950-45c0-bdad-1d366ad8b964',
              operationType=self.messages.Operation.OperationTypeValueValuesEnum
              .UPDATE,
              selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/8b7ffa62-e9'
              .format(self.Project()),
              startTime=datetime.datetime(
                  2017,
                  5,
                  15,
                  23,
                  3,
                  50,
                  707000,
                  tzinfo=protorpc_util.TimeZoneOffset(
                      datetime.timedelta(0))).isoformat(),
              status=self.messages.Operation.StatusValueValuesEnum.DONE,
              targetId=self.instance['id'],
              targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/{1}'
              .format(self.Project(), self.instance['id']),
              targetProject=self.Project(),
              user='462803083913-lak0k1ette3muh3o3kb3pp2im3urj3e9@developer.gserviceaccount.com',
          ))
      self.mocked_client.instances.Get.Expect(
          self.messages.SqlInstancesGetRequest(
              instance=self.instance['id'],
              project=self.Project(),
          ),
          self.messages.DatabaseInstance(
              # pylint:disable=line-too-long
              backendType=self.instance['backendType'],
              connectionName='{0}:us-central1:{1}'.format(
                  self.Project(), self.instance['id']),
              currentDiskSize=None,
              databaseVersion=self.instance['databaseVersion'],
              etag='"DlgRosmIegBpXj_rR5uyhdXAbP8/Mw"',
              failoverReplica=None,
              instanceType=self.messages.DatabaseInstance
              .InstanceTypeValueValuesEnum.CLOUD_SQL_INSTANCE,
              ipAddresses=[
                  self.messages.IpMapping(
                      ipAddress='104.154.166.249',
                      timeToRetire=None,
                      type=self.messages.IpMapping.TypeValueValuesEnum.PRIMARY,
                  ),
              ],
              ipv6Address=None,
              kind='sql#instance',
              masterInstanceName=None,
              maxDiskSize=None,
              name=self.instance['id'],
              onPremisesConfiguration=None,
              project=self.Project(),
              region='us-central1',
              replicaConfiguration=None,
              replicaNames=[],
              selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/{1}'
              .format(self.Project(), self.instance['id']),
              serverCaCert=self.messages.SslCert(
                  cert='-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAgIBADANBgkqhkiG9w0BAQUFADBIMSMwIQYDVQQDExpHb29n\nbGUgQ2x',
                  certSerialNumber='0',
                  commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL Server CA',
                  createTime=datetime.datetime(
                      2017,
                      5,
                      12,
                      21,
                      33,
                      4,
                      844000,
                      tzinfo=protorpc_util.TimeZoneOffset(
                          datetime.timedelta(0))).isoformat(),
                  expirationTime=datetime.datetime(
                      2019,
                      5,
                      12,
                      21,
                      34,
                      4,
                      844000,
                      tzinfo=protorpc_util.TimeZoneOffset(
                          datetime.timedelta(0))).isoformat(),
                  instance=self.instance['id'],
                  kind='sql#sslCert',
                  selfLink=None,
                  sha1Fingerprint='fcddb49c4a00ff8796ba099933dbeb208b8599bd',
              ),
              serviceAccountEmailAddress='vxmlqos47zbmzgjppv2ued6e74@speckle-umbrella-5.iam.gserviceaccount.com',
              settings=self.messages.Settings(
                  activationPolicy=self.messages.Settings
                  .ActivationPolicyValueValuesEnum.ALWAYS,
                  authorizedGaeApplications=[],
                  availabilityType=None,
                  backupConfiguration=self.messages.BackupConfiguration(
                      binaryLogEnabled=None,
                      enabled=False,
                      kind='sql#backupConfiguration',
                      startTime='10:00',
                  ),
                  crashSafeReplicationEnabled=None,
                  dataDiskSizeGb=10,
                  dataDiskType=self.messages.Settings
                  .DataDiskTypeValueValuesEnum.PD_SSD,
                  databaseFlags=[],
                  databaseReplicationEnabled=None,
                  ipConfiguration=self.messages.IpConfiguration(
                      authorizedNetworks=[
                          self.messages.AclEntry(
                              expirationTime=(
                                  self.time_of_connection +
                                  datetime.timedelta(minutes=5)).isoformat(),
                              kind='sql#aclEntry',
                              name='sql connect at time {0}'.format(
                                  str(self.time_of_connection)),
                              value='192.0.0.1',
                          ),
                      ],
                      ipv4Enabled=True,
                      requireSsl=None,
                  ),
                  kind='sql#settings',
                  locationPreference=None,
                  maintenanceWindow=None,
                  pricingPlan=self.messages.Settings.PricingPlanValueValuesEnum
                  .PER_USE,
                  replicationType=self.messages.Settings
                  .ReplicationTypeValueValuesEnum.SYNCHRONOUS,
                  settingsVersion=3,
                  storageAutoResize=True,
                  storageAutoResizeLimit=0,
                  tier=self.instance['tier'],
              ),
              state=self.messages.DatabaseInstance.StateValueValuesEnum
              .RUNNABLE,
              suspensionReason=[],
          ))

  def MockProxyStartAndInstanceGet(self):
    # Mock checking that the Cloud SQL Proxy binary is installed.
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value='cloud_sql_proxy')
    # Mock starting the proxy.
    self.StartPatch(
        'googlecloudsdk.api_lib.sql.instances.StartCloudSqlProxy',
        return_value=mock.Mock())

    self.ExpectInstanceGet()


class _BaseMysqlConnectTest(_BaseConnectTest):
  instance = {
      'id':
          'mysql-instance',
      'tier':
          'db-n1-standard-2',
      'databaseVersion':
          sqladmin_v1beta4.DatabaseInstance.DatabaseVersionValueValuesEnum
          .MYSQL_5_6,
      'backendType':
          sqladmin_v1beta4.DatabaseInstance.BackendTypeValueValuesEnum
          .SECOND_GEN
  }

  def RunMysqlConnectTest(self, user=None):
    """Base function for connecting to MySQL instance."""
    self.MockConnectionSetup()

    mocked_mysql_path = 'mysql'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_mysql_path)

    # Mock the actual execution of mysql and assert it's called at the end.
    exec_patched = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec', return_value=True)
    # Set up MySQL user config.
    connect_user_flag = '--user {0}'.format(user) if user else ''
    mysql_user = user or 'root'
    self.Run('sql connect {0} {1}'.format(self.instance['id'],
                                          connect_user_flag))
    self.AssertErrContains(
        'Connecting to database with SQL user [{0}]'.format(mysql_user))

    self.assertTrue(exec_patched.called)

    # call_args[0] is the ordered list of args the mock is called with.
    # Exec is called with exactly one arg, the list of subprocess args, so
    # call_args[0][0] gives us subprocess_args.
    exec_ordered_arguments = exec_patched.call_args[0]
    subprocess_args = exec_ordered_arguments[0]
    self.AssertMysqlArgsAreCorrect(subprocess_args, mocked_mysql_path,
                                   mysql_user)

  def MockConnectionSetup(self):
    self.MockIPWhitelisting()

  def AssertMysqlArgsAreCorrect(self, subprocess_args, mocked_mysql_path,
                                mysql_user):
    (actual_mysql_path, actual_host_flag, actual_ip_address, actual_user_flag,
     actual_username, actual_pass_flag) = subprocess_args
    self.assertEqual(mocked_mysql_path, actual_mysql_path)
    self.assertEqual('-h', actual_host_flag)
    # Basic check that it's an IPv4 address. IPv4 uses '.' instead of ':'.
    self.assertIn('.', actual_ip_address)
    self.assertEqual('-u', actual_user_flag)
    self.assertEqual(mysql_user, actual_username)
    self.assertEqual('-p', actual_pass_flag)

  def testMysqlConnectWithNoUser(self):
    self.RunMysqlConnectTest()

  def testMysqlConnectWithUser(self):
    self.RunMysqlConnectTest(user='someone')

  def testOSErrorOnExec(self):
    self.MockConnectionSetup()

    mocked_mysql_path = 'mysql'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_mysql_path)

    # Mock the actual execution of mysql and assert it's called at the end.
    self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec',
        return_value=True,
        side_effect=OSError('Failed to execute.'))

    # Mock the logging after an exception is raised.
    error_patched = self.StartPatch('googlecloudsdk.core.log.error')
    print_patched = self.StartPatch('googlecloudsdk.core.log.Print')

    self.Run('sql connect {0} --user root'.format(self.instance['id']))

    self.assertTrue(error_patched.called)
    self.assertTrue(print_patched.called)


class MysqlConnectGATest(_BaseMysqlConnectTest, base.SqlMockTestGA):

  def testWhitelistError(self):
    self.MockIPWhitelisting(error=True)

    with self.AssertRaisesHttpExceptionRegexp(r'Invalid instance property'):
      self.Run('sql connect {0} --user root'.format(self.instance['id']))

  def testInstanceNotFound(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='nosuchinstance', project=self.Project()),
        exception=http_error.MakeHttpError(
            403,
            'The client is not authorized to make this request.',
            url=('https://sqladmin.googleapis.com/sql/v1beta4/projects'
                 '/google.com%3Acloudsdktest/instances/noinstance?alt=json')))
    with self.assertRaises(exceptions.ResourceNotFoundError):
      self.Run('sql connect nosuchinstance')


class MysqlV2ConnectBetaTest(_BaseMysqlConnectTest, base.SqlMockTestBeta):
  """Mocks out connecting to V2 instances through the proxy."""

  def MockConnectionSetup(self):
    self.MockProxyStartAndInstanceGet()

  def AssertMysqlArgsAreCorrect(self, subprocess_args, mocked_mysql_path,
                                mysql_user):
    (actual_mysql_path, actual_host_flag, actual_ip_address, actual_port_flag,
     actual_port, actual_user_flag, actual_username,
     actual_pass_flag) = subprocess_args
    self.assertEqual(mocked_mysql_path, actual_mysql_path)
    self.assertEqual('-h', actual_host_flag)
    # Basic check that it's an IPv4 address. IPv4 uses '.' instead of ':'.
    self.assertIn('.', actual_ip_address)
    self.assertIn('-P', actual_port_flag)
    self.assertIn('9470', actual_port)
    self.assertEqual('-u', actual_user_flag)
    self.assertEqual(mysql_user, actual_username)
    self.assertEqual('-p', actual_pass_flag)

  def testProxyNotAvailable(self):
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=None)

    self.ExpectInstanceGet()

    with self.assertRaises(exceptions.CloudSqlProxyError):
      self.Run('sql connect {0} --database somedb'.format(self.instance['id']))

  def testDatabaseFlagError(self):
    self.MockConnectionSetup()

    mocked_mysql_path = 'mysql'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_mysql_path)

    # Mock IPv4 connectivity.
    self.StartPatch(
        'googlecloudsdk.api_lib.sql.network.GetIpVersion', return_value=4)

    # Mock the actual execution of mysql and assert it's called at the end.
    self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec',
        return_value=True,
        side_effect=OSError('Failed to execute.'))

    # The --database flag should not work with MySQL instances.
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run('sql connect {0} --database somedb'.format(self.instance['id']))


class MysqlV1ConnectBetaTest(_BaseMysqlConnectTest, base.SqlMockTestBeta):
  """Mocks out connecting to V1 instances with whitelisting."""

  instance = {
      'id':
          'mysql-instance',
      'tier':
          'D1',
      'databaseVersion':
          sqladmin_v1beta4.DatabaseInstance.DatabaseVersionValueValuesEnum
          .MYSQL_5_6,
      'backendType':
          sqladmin_v1beta4.DatabaseInstance.BackendTypeValueValuesEnum.FIRST_GEN
  }

  def MockConnectionSetup(self):
    self.ExpectInstanceGet()
    self.MockIPWhitelisting()


class _BasePsqlConnectTest(_BaseConnectTest):
  base_args_length = 8
  instance = {
      'id':
          'psql-instance',
      'tier':
          'db-custom-1-1024',
      'databaseVersion':
          sqladmin_v1beta4.DatabaseInstance.DatabaseVersionValueValuesEnum
          .POSTGRES_9_6,
      'backendType':
          sqladmin_v1beta4.DatabaseInstance.BackendTypeValueValuesEnum
          .SECOND_GEN
  }

  def RunPsqlConnectTest(self, database=None):
    self.MockConnectionSetup()

    mocked_psql_path = 'psql'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_psql_path)

    # Mock the actual execution of psql and assert it's called at the end.
    exec_patched = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec', return_value=True)
    cmd = 'sql connect {0}'.format(self.instance['id'])
    if database:
      cmd += ' --database={0}'.format(database)
    self.Run(cmd)
    self.AssertErrContains('Connecting to database with SQL user [postgres]')

    self.assertTrue(exec_patched.called)

    # call_args[0] is the ordered list of args the mock is called with.
    # Exec is called with exactly one arg, the list of subprocess args, so
    # call_args[0][0] gives us subprocess_args.
    exec_ordered_arguments = exec_patched.call_args[0]
    subprocess_args = exec_ordered_arguments[0]
    self.AssertPsqlArgsAreCorrect(subprocess_args, mocked_psql_path)

  def MockConnectionSetup(self):
    self.MockIPWhitelisting()

  def AssertPsqlArgsAreCorrect(self, subprocess_args, mocked_psql_path):
    base_args_length = 6
    (actual_psql_path, actual_host_flag, actual_ip_address, actual_user_flag,
     actual_username, actual_pass_flag) = subprocess_args[:base_args_length]
    self.assertEqual(mocked_psql_path, actual_psql_path)
    self.assertEqual('-h', actual_host_flag)
    # Basic check that it's an IPv4 address. IPv4 uses '.' instead of ':'.
    self.assertIn('.', actual_ip_address)
    self.assertEqual('-U', actual_user_flag)
    self.assertEqual('postgres', actual_username)
    self.assertEqual('-W', actual_pass_flag)

    # Check for additional args.
    if len(subprocess_args) > base_args_length:
      (actual_db_flag, actual_db) = subprocess_args[base_args_length:]
      self.assertEqual('-d', actual_db_flag)
      self.assertEqual('somedb', actual_db)

  def testPsqlConnect(self):
    self.RunPsqlConnectTest()


class _BasePsqlConnectBetaTest(_BasePsqlConnectTest):

  def MockConnectionSetup(self):
    self.MockProxyStartAndInstanceGet()

  def AssertPsqlArgsAreCorrect(self, subprocess_args, mocked_psql_path):
    base_args_length = 8
    (actual_psql_path, actual_host_flag, actual_ip_address, actual_port_flag,
     actual_port, actual_user_flag, actual_username,
     actual_pass_flag) = subprocess_args[:base_args_length]
    self.assertEqual(mocked_psql_path, actual_psql_path)
    self.assertEqual('-h', actual_host_flag)
    # Basic check that it's an IPv4 address. IPv4 uses '.' instead of ':'.
    self.assertIn('.', actual_ip_address)
    self.assertIn('-p', actual_port_flag)
    self.assertIn('9470', actual_port)
    self.assertEqual('-U', actual_user_flag)
    self.assertEqual('postgres', actual_username)
    self.assertEqual('-W', actual_pass_flag)

    # Check for additional args.
    if len(subprocess_args) > base_args_length:
      (actual_db_flag, actual_db) = subprocess_args[base_args_length:]
      self.assertEqual('-d', actual_db_flag)
      self.assertEqual('somedb', actual_db)

  def testPsqlConnectWithDatabase(self):
    self.RunPsqlConnectTest('somedb')


class PsqlConnectGATest(_BasePsqlConnectTest, base.SqlMockTestGA):
  pass


class PsqlConnectBetaTest(_BasePsqlConnectBetaTest, base.SqlMockTestBeta):
  pass


class PsqlConnectAlphaTest(_BasePsqlConnectBetaTest, base.SqlMockTestAlpha):
  pass


class MssqlCliConnectGATest(_BaseConnectTest, base.SqlMockTestGA):
  base_args_length = 5
  instance = {
      'id':
          'sqlserver-instance',
      'tier':
          'db-custom-1-1024',
      'databaseVersion':
          sqladmin_v1beta4.DatabaseInstance.DatabaseVersionValueValuesEnum
          .SQLSERVER_2017_STANDARD,
      'backendType':
          sqladmin_v1beta4.DatabaseInstance.BackendTypeValueValuesEnum
          .SECOND_GEN
  }

  def RunMssqlCliConnectTest(self, database=None):
    self.MockConnectionSetup()

    mocked_mssqlcli_path = 'mssql-cli'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_mssqlcli_path)

    # Mock the actual execution of mssqlcli and assert it's called at the end.
    exec_patched = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec', return_value=True)
    cmd = 'sql connect {0}'.format(self.instance['id'])
    if database:
      cmd += ' --database={0}'.format(database)
    self.Run(cmd)
    self.AssertErrContains('Connecting to database with SQL user [sqlserver]')

    self.assertTrue(exec_patched.called)

    # call_args[0] is the ordered list of args the mock is called with.
    # Exec is called with exactly one arg, the list of subprocess args, so
    # call_args[0][0] gives us subprocess_args.
    exec_ordered_arguments = exec_patched.call_args[0]
    subprocess_args = exec_ordered_arguments[0]
    self.AssertMssqlCliArgsAreCorrect(subprocess_args, mocked_mssqlcli_path)

  def MockConnectionSetup(self):
    self.MockIPWhitelisting()

  def AssertMssqlCliArgsAreCorrect(self, subprocess_args, mocked_mssqlcli_path):
    base_args_length = 5
    (actual_mssqlcli_path, actual_host_flag, actual_ip_address,
     actual_user_flag, actual_username) = subprocess_args[:base_args_length]
    self.assertEqual(mocked_mssqlcli_path, actual_mssqlcli_path)
    self.assertEqual('-S', actual_host_flag)
    # Basic check that it's an IPv4 address. IPv4 uses '.' instead of ':'.
    self.assertIn('.', actual_ip_address)
    self.assertEqual('-U', actual_user_flag)
    self.assertEqual('sqlserver', actual_username)

    # Check for additional args.
    if len(subprocess_args) > base_args_length:
      (actual_db_flag, actual_db) = subprocess_args[base_args_length:]
      self.assertEqual('-d', actual_db_flag)
      self.assertEqual('somedb', actual_db)

  def testMssqlCliConnect(self):
    self.RunMssqlCliConnectTest()


class MssqlCliConnectBetaTest(_BaseConnectTest, base.SqlMockTestBeta):
  instance = {
      'id':
          'mssql-instance',
      'tier':
          'db-custom-1-1024',
      'databaseVersion':
          sqladmin_v1beta4.DatabaseInstance.DatabaseVersionValueValuesEnum
          .SQLSERVER_2017_STANDARD,
      'backendType':
          sqladmin_v1beta4.DatabaseInstance.BackendTypeValueValuesEnum
          .SECOND_GEN
  }

  def RunMssqlCliConnectTest(self, database=None):
    self.MockConnectionSetup()

    mocked_mssqlcli_path = 'mssql-cli'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_mssqlcli_path)

    # Mock the actual execution of mssql-cli and assert it's called at the end.
    exec_patched = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec', return_value=True)
    cmd = 'sql connect {0}'.format(self.instance['id'])
    if database:
      cmd += ' --database={0}'.format(database)
    self.Run(cmd)
    self.AssertErrContains('Connecting to database with SQL user [sqlserver]')

    self.assertTrue(exec_patched.called)

    # call_args[0] is the ordered list of args the mock is called with.
    # Exec is called with exactly one arg, the list of subprocess args, so
    # call_args[0][0] gives us subprocess_args.
    exec_ordered_arguments = exec_patched.call_args[0]
    subprocess_args = exec_ordered_arguments[0]
    self.AssertMssqlCliArgsAreCorrect(subprocess_args, mocked_mssqlcli_path)

  def MockConnectionSetup(self):
    self.MockProxyStartAndInstanceGet()

  def AssertMssqlCliArgsAreCorrect(self, subprocess_args, mocked_mssqlcli_path):
    base_args_length = 5
    (actual_mssqlcli_path, actual_host_flag, actual_ip_address,
     actual_user_flag, actual_username) = subprocess_args[:base_args_length]
    self.assertEqual(mocked_mssqlcli_path, actual_mssqlcli_path)
    self.assertEqual('-S', actual_host_flag)
    # Basic check that it's an IPv4 address. IPv4 uses '.' instead of ':'.
    self.assertIn('.', actual_ip_address)
    self.assertEqual('-U', actual_user_flag)
    self.assertEqual('sqlserver', actual_username)

    # Check for additional args.
    if len(subprocess_args) > base_args_length:
      (actual_db_flag, actual_db) = subprocess_args[base_args_length:]
      self.assertEqual('-d', actual_db_flag)
      self.assertEqual('somedb', actual_db)

  def testMssqlCliConnectWithDatabase(self):
    self.RunMssqlCliConnectTest('somedb')


class MssqlCliConnectAlphaTest(MssqlCliConnectBetaTest, base.SqlMockTestAlpha):
  pass

if __name__ == '__main__':
  test_case.main()
