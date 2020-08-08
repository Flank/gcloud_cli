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
"""Test of the 'create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.bigtable import base


class CreateCommandTestGA(base.BigtableV2TestBase,
                          waiter_test_base.CloudOperationsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.svc = self.client.projects_instances_clusters_backups.Create

  def buildRequest(self,
                   backup):
    return self.msgs.BigtableadminProjectsInstancesClustersBackupsCreateRequest(
        backup=self.msgs.Backup(
            sourceTable='projects/{0}/instances/{1}/tables/{2}'
            .format(self.Project(), 'theinstance', 'thetable'),
            expireTime='2019-06-01T00:00:00Z'),
        backupId=backup,
        parent='projects/{0}/instances/{1}/clusters/{2}'
        .format(self.Project(), 'theinstance', 'thecluster'))

  def testCreateAsync(self):
    self.svc.Expect(
        request=self.buildRequest('thebackup1'),
        response=self.msgs.Operation(name='operations/theoperation'))
    self.Run('bigtable backups create thebackup1 --instance theinstance '
             '--cluster thecluster --table thetable '
             '--expiration-date 2019-06-01T00:00:00Z --async')

  def testCreateWait(self):
    self.svc.Expect(
        request=self.buildRequest('thebackup2'),
        response=self.msgs.Operation(
            name='operations/theoperation', done=False))
    result = self.ExpectOperation(
        self.client.operations, 'operations/theoperation',
        self.client.projects_instances_clusters_backups,
        'projects/{0}/instances/{1}/clusters/{2}/backups/{3}'
        .format(self.Project(), 'theinstance', 'thecluster', 'thebackup2'))
    result.state = self.msgs.Backup.StateValueValuesEnum.READY

    self.Run('bigtable backups create thebackup2 --instance theinstance '
             '--cluster thecluster --table thetable '
             '--expiration-date 2019-06-01T00:00:00Z')

    self.AssertErrContains('Created backup [thebackup2]')

  def testMissingExpireTimeError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--expiration-date | --retention-period) must be '
        'specified.'):
      self.Run('bigtable backups create thebackup --instance theinstance '
               '--cluster thecluster --async')

  def testMissingTableError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --table: Must be specified.'):
      self.Run('bigtable backups create thebackup --instance theinstance '
               '--cluster thecluster --retention-period 2w')

  def testMutexArgumentsError(self):
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'argument --expiration-date: '
                                           'Exactly one of (--expiration-date |'
                                           ' --retention-period) must be '
                                           'specified.'):
      self.Run('bigtable backups create thebackup --instance theinstance '
               '--cluster thecluster --table thetable '
               '--expiration-date 2019-06-01T00:00:00Z --retention-period 5d')


class CreateCommandTestBeta(CreateCommandTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CreateCommandTestAlpha(CreateCommandTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
