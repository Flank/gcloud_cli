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
"""Tests of the 'list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.command_lib.util.concepts import resource_completer_test_base
from tests.lib.surface.bigtable import base


class ListCommandTestAlpha(base.BigtableV2TestBase, cli_test_base.CliTestBase,
                           resource_completer_test_base.ResourceCompleterBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.backups_list_mock = self.client.projects_instances_clusters_backups.List
    self.instance_ref = util.GetInstanceRef('theinstance')
    self.cluster_ref1 = util.GetClusterRef('theinstance', 'cluster1')
    self.cluster_ref2 = util.GetClusterRef('theinstance', 'cluster2')
    self.table_ref = util.GetTableRef('theinstance', 'thetable')

  def expectBackupList(self, cluster_ref, backup_name):
    self.backups_list_mock.Expect(
        request=
        self.msgs.BigtableadminProjectsInstancesClustersBackupsListRequest(
            parent=cluster_ref.RelativeName()),
        response=self.msgs.ListBackupsResponse(backups=[
            self.msgs.Backup(
                name=('{}/backups/{}'.format(
                    cluster_ref.RelativeName(), backup_name)),
                sourceTable=self.table_ref.RelativeName(),
                expireTime='2019-06-01T00:00:00Z',
                startTime='2019-05-28T18:19:16.792310Z',
                endTime='2019-05-28T18:20:19.470575Z',
                sizeBytes=3187,
                state=self.msgs.Backup.StateValueValuesEnum.READY)
        ]))

  def testListCluster(self):
    self.expectBackupList(self.cluster_ref1, 'thebackup')
    self.Run('bigtable backups list --instance theinstance --cluster cluster1')
    self.AssertOutputContains('thebackup')
    self.AssertOutputContains('cluster1')
    self.AssertOutputContains('thetable')
    self.AssertOutputContains('2019-06-01T00:00:00Z')
    self.AssertOutputContains('READY')

  def testListInstance(self):
    self.backups_list_mock.Expect(
        request=
        self.msgs.BigtableadminProjectsInstancesClustersBackupsListRequest(
            parent=self.instance_ref.RelativeName()+'/clusters/-'),
        response=self.msgs.ListBackupsResponse(backups=[
            self.msgs.Backup(
                name=('{}/backups/{}'.format(
                    self.cluster_ref1.RelativeName(), 'thebackup1')),
                sourceTable=self.table_ref.RelativeName(),
                expireTime='2019-06-01T00:00:00Z',
                startTime='2019-05-28T18:19:16.792310Z',
                endTime='2019-05-28T18:20:19.470575Z',
                sizeBytes=3187,
                state=self.msgs.Backup.StateValueValuesEnum.READY),
            self.msgs.Backup(
                name=('{}/backups/{}'.format(
                    self.cluster_ref2.RelativeName(), 'thebackup2')),
                sourceTable=self.table_ref.RelativeName(),
                expireTime='2019-06-10T00:00:00Z',
                startTime='2019-05-29T15:26:55.081381Z',
                endTime='2019-05-29T15:26:56.093891Z',
                sizeBytes=3187,
                state=self.msgs.Backup.StateValueValuesEnum.READY),
        ]))
    self.Run('bigtable backups list --instance theinstance')
    self.AssertOutputContains('thebackup1')
    self.AssertOutputContains('thebackup2')
    self.AssertOutputContains('cluster1')
    self.AssertOutputContains('cluster2')
    self.AssertOutputContains('thetable')
    self.AssertOutputContains('2019-06-01T00:00:00Z')
    self.AssertOutputContains('2019-06-10T00:00:00Z')
    self.AssertOutputContains('READY')

if __name__ == '__main__':
  test_case.main()
