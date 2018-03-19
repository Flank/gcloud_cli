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
            maxResults=100,),
        self.messages.InstancesListResponse(
            items=[
                self.messages.DatabaseInstance(
                    currentDiskSize=287571860,
                    databaseVersion=u'MYSQL_5_5',
                    etag=u'"yGhHGJDUk5hWK-gppo_8C-KD7iU/nbMj8WWUtdJPpSjOHUxEh"',
                    name=u'backupless-instance',
                    instanceType=u'CLOUD_SQL_INSTANCE',
                    ipAddresses=[],
                    ipv6Address=u'2001:4860:4864:1:df7c:6a7a:d107:ab9d',
                    kind=u'sql#instance',
                    masterInstanceName=None,
                    maxDiskSize=268435456000,
                    project=self.Project(),
                    region=u'us-central',
                    replicaNames=[],
                    serverCaCert=self.messages.SslCert(
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
                            tzinfo=protorpc_util.TimeZoneOffset(
                                datetime.timedelta(0))),
                        expirationTime=datetime.datetime(
                            2024,
                            8,
                            8,
                            21,
                            47,
                            10,
                            788000,
                            tzinfo=protorpc_util.TimeZoneOffset(
                                datetime.timedelta(0))),
                        instance=u'backupless-instance',
                        kind=u'sql#sslCert',
                        sha1Fingerprint=u'a691db45f7dee0827650fd2eb277d2ca81b9',
                    ),
                    settings=self.messages.Settings(
                        activationPolicy=u'ON_DEMAND',
                        authorizedGaeApplications=[],
                        backupConfiguration=self.messages.BackupConfiguration(
                            binaryLogEnabled=False,
                            enabled=False,
                            kind=u'sql#backupConfiguration',
                            startTime=u'00:00',),
                        databaseFlags=[],
                        databaseReplicationEnabled=None,
                        ipConfiguration=self.messages.IpConfiguration(
                            authorizedNetworks=[],
                            ipv4Enabled=False,
                            requireSsl=False,),
                        kind=u'sql#settings',
                        locationPreference=self.messages.LocationPreference(
                            followGaeApplication=None,
                            kind=u'sql#locationPreference',
                            zone=None,),
                        pricingPlan=u'PER_USE',
                        replicationType=u'SYNCHRONOUS',
                        settingsVersion=1,
                        tier=u'db-n1-standard-1',),
                    state=u'RUNNABLE',),
            ],
            kind=u'sql#instancesList',
            nextPageToken=None,))

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
