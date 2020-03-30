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

from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.sql import base


class RemoteCompletionTest(base.SqlMockTestBeta,
                           cli_test_base.CliTestBase):
  # pylint:disable=g-tzinfo-datetime

  def SetUp(self):
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            pageToken=None,
            project=self.Project(),
            maxResults=100,
        ),
        self.messages.InstancesListResponse(
            items=[
                self.messages.DatabaseInstance(
                    currentDiskSize=287571860,
                    databaseVersion=self.messages.DatabaseInstance
                    .DatabaseVersionValueValuesEnum.MYSQL_5_5,
                    etag='"yGhHGJDUk5hWK-gppo_8C-KD7iU/nbMj8WWUtdJPpSjOHUxEh"',
                    name='backupless-instance',
                    instanceType=self.messages.DatabaseInstance
                    .InstanceTypeValueValuesEnum.CLOUD_SQL_INSTANCE,
                    ipAddresses=[],
                    ipv6Address='2001:4860:4864:1:df7c:6a7a:d107:ab9d',
                    kind='sql#instance',
                    masterInstanceName=None,
                    maxDiskSize=268435456000,
                    project=self.Project(),
                    region='us-central',
                    replicaNames=[],
                    serverCaCert=self.messages.SslCert(
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
                            tzinfo=protorpc_util.TimeZoneOffset(
                                datetime.timedelta(0))).isoformat(),
                        expirationTime=datetime.datetime(
                            2024,
                            8,
                            8,
                            21,
                            47,
                            10,
                            788000,
                            tzinfo=protorpc_util.TimeZoneOffset(
                                datetime.timedelta(0))).isoformat(),
                        instance='backupless-instance',
                        kind='sql#sslCert',
                        sha1Fingerprint='a691db45f7dee0827650fd2eb277d2ca81b9',
                    ),
                    settings=self.messages.Settings(
                        activationPolicy=self.messages.Settings
                        .ActivationPolicyValueValuesEnum.ON_DEMAND,
                        authorizedGaeApplications=[],
                        backupConfiguration=self.messages.BackupConfiguration(
                            binaryLogEnabled=False,
                            enabled=False,
                            kind='sql#backupConfiguration',
                            startTime='00:00',
                        ),
                        databaseFlags=[],
                        databaseReplicationEnabled=None,
                        ipConfiguration=self.messages.IpConfiguration(
                            authorizedNetworks=[],
                            ipv4Enabled=False,
                            requireSsl=False,
                        ),
                        kind='sql#settings',
                        locationPreference=self.messages.LocationPreference(
                            followGaeApplication=None,
                            kind='sql#locationPreference',
                            zone=None,
                        ),
                        pricingPlan=self.messages.Settings
                        .PricingPlanValueValuesEnum.PER_USE,
                        replicationType=self.messages.Settings
                        .ReplicationTypeValueValuesEnum.SYNCHRONOUS,
                        settingsVersion=1,
                        tier='db-n1-standard-1',
                    ),
                    state=self.messages.DatabaseInstance.StateValueValuesEnum
                    .RUNNABLE,
                ),
            ],
            kind='sql#instancesList',
            nextPageToken=None,
        ))

  def testDescribeCompletion(self):
    self.RunCompletion('sql instances describe ', ['backupless-instance'])

  def testDeleteCompletion(self):
    self.RunCompletion('sql instances delete ', ['backupless-instance'])

  def testCloneCompletion(self):
    self.RunCompletion('sql instances clone ', ['backupless-instance'])

  def testExportCompletion(self):
    self.RunCompletion('sql instances export ', ['backupless-instance'])

  def testImportCompletion(self):
    self.RunCompletion('sql instances import ', ['backupless-instance'])

  def testPatchCompletion(self):
    self.RunCompletion('sql instances patch ', ['backupless-instance'])

  def testRestartCompletion(self):
    self.RunCompletion('sql instances restart ', ['backupless-instance'])

  def testRestoreBackupCompletion(self):
    self.RunCompletion('sql instances restore-backup ', ['backupless-instance'])

  def testResetSslConfigCompletion(self):
    self.RunCompletion('sql instances reset-ssl-config ',
                       ['backupless-instance'])

  def testBackupsCompletion(self):
    self.RunCompletion('sql backups describe --instance  ',
                       ['backupless-instance'])

  def testSslCertsDescribeCompletion(self):
    self.RunCompletion('sql ssl-certs describe --instance  ',
                       ['backupless-instance'])

  def testSslCertsDeleteCompletion(self):
    self.RunCompletion('sql ssl-certs delete --instance  ',
                       ['backupless-instance'])


if __name__ == '__main__':
  test_case.main()
