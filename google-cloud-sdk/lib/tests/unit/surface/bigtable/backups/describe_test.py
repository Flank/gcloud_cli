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
"""Tests of the 'describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class DescribeCommandTest(base.BigtableV2TestBase,
                          sdk_test_base.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.svc = self.client.projects_instances_clusters_backups.Get
    self.msg = self.msgs.BigtableadminProjectsInstancesClustersBackupsGetRequest(
        name='projects/{0}/instances/theinstance/clusters/thecluster/'
        'backups/thebackup'.format(self.Project()))
    self.cluster_ref = util.GetClusterRef('theinstance', 'thecluster')
    self.table_ref = util.GetTableRef('theinstance', 'thetable')

  def _RunSuccessTest(self, cmd):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.Backup(
            name=('{}/backups/{}'.format(
                self.cluster_ref.RelativeName(), 'thebackup')),
            sourceTable=self.table_ref.RelativeName(),
            expireTime='2019-06-01T00:00:00Z',
            startTime='2019-05-28T18:19:16.792310Z',
            endTime='2019-05-28T18:20:19.470575Z',
            sizeBytes=3187,
            state=self.msgs.Backup.StateValueValuesEnum.READY))
    self.Run(cmd)
    self.AssertOutputContains('thebackup')
    self.AssertOutputContains('2019-06-01T00:00:00Z')
    self.AssertOutputContains('READY')

  def testDescribe(self):
    self._RunSuccessTest(
        'bigtable backups describe thebackup --instance=theinstance '
        '--cluster=thecluster')

  def testDescribeByUri(self):
    cmd = ('bigtable backups describe projects/{0}/instances/theinstance/'
           'clusters/thecluster/backups/thebackup'.format(self.Project()))
    self._RunSuccessTest(cmd)


if __name__ == '__main__':
  test_case.main()
