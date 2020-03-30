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
"""Test of the 'describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.spanner import base


class BackupsDescribeTest(base.SpannerTestBeta):

  def SetUp(self):
    self.svc = self.client.projects_instances_backups.Get
    self.msg = self.msgs.SpannerProjectsInstancesBackupsGetRequest(
        name='projects/{0}/instances/theinstance/backups/thebackup'.format(
            self.Project()))
    self.backup_ref = resources.REGISTRY.Parse(
        'thebackup',
        params={
            'projectsId': self.Project(),
            'instancesId': 'theinstance',
        },
        collection='spanner.projects.instances.backups')
    self.database_ref = resources.REGISTRY.Parse(
        'thedatabase',
        params={
            'projectsId': self.Project(),
            'instancesId': 'theinstance',
        },
        collection='spanner.projects.instances.databases')

  def _RunSuccessTest(self, cmd):
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.Backup(
            name=('{}/backups/{}'.format(
                self.backup_ref.RelativeName(), 'thebackup')),
            database=self.database_ref.RelativeName(),
            expireTime='2019-06-01T00:00:00Z',
            createTime='2019-05-28T18:19:16.792310Z',
            sizeBytes=3187,
            state=self.msgs.Backup.StateValueValuesEnum.READY))
    self.Run(cmd)
    self.AssertOutputContains('createTime: \'2019-05-28T18:19:16.792310Z\'')
    self.AssertOutputContains(
        'database: projects/{0}/instances/theinstance/databases/thedatabase'
        .format(self.Project()))
    self.AssertOutputContains('expireTime: \'2019-06-01T00:00:00Z\'')
    self.AssertOutputContains(
        'name: projects/{0}/instances/theinstance/backups/thebackup/'
        'backups/thebackup'.format(self.Project()))
    self.AssertOutputContains('sizeBytes: \'3187\'')
    self.AssertOutputContains('state: READY')

  def testDescribe(self):
    self._RunSuccessTest(
        'spanner backups describe thebackup --instance=theinstance')

  def testDescribeByUri(self):
    cmd = ('spanner backups describe projects/{0}/instances/theinstance/'
           'backups/thebackup'.format(self.Project()))
    self._RunSuccessTest(cmd)


if __name__ == '__main__':
  test_case.main()
