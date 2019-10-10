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
"""Tests of the 'update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class UpdateCommandTestAlpha(base.BigtableV2TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.svc = self.client.projects_instances_clusters_backups.Patch

  def testUpdate(self):
    self.svc.Expect(
        request=
        self.msgs.BigtableadminProjectsInstancesClustersBackupsPatchRequest(
            backup=self.msgs.Backup(
                expireTime=u'2019-06-05T00:00:00Z',),
            name=('projects/{0}/instances/theinstance/clusters/'
                  'thecluster/backups/thebackup'.format(self.Project())),
            updateMask=u'expire_time'),
        response=self.msgs.Backup(
            name=('projects/theproject/instances/theinstance/clusters/'
                  'thecluster/backups/thebackup'),
            sourceTable=('projects/theproject/instances/theinstance/'
                         'tables/mytable'),
            expireTime='2019-06-05T00:00:00Z',
            startTime='2019-05-28T18:19:16.792310Z',
            endTime='2019-05-28T18:20:19.470575Z',
            sizeBytes=3187,
            state=self.msgs.Backup.StateValueValuesEnum.READY))
    self.Run('bigtable backups update thebackup --instance theinstance '
             '--cluster thecluster --expiration-date 2019-06-05T00:00:00Z')

  def testArgumentError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--expiration-date | --retention-period) must be '
        'specified.'):
      self.Run('bigtable backups update thebackup --instance theinstance '
               '--cluster thecluster')

  def testMutexArgumentsError(self):
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'argument --expiration-date: '
                                           'Exactly one of (--expiration-date |'
                                           ' --retention-period) must be '
                                           'specified.'):
      self.Run('bigtable backups update thebackup --instance theinstance '
               '--cluster thecluster '
               '--expiration-date 2019-06-01T00:00:00Z --retention-period 5d')


if __name__ == '__main__':
  test_case.main()
