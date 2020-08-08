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

"""Test of the 'restore' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.bigtable import base


class RestoreTestGA(base.BigtableV2TestBase,
                    waiter_test_base.CloudOperationsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.svc = self.client.projects_instances_tables.Restore

  def buildRequest(self, backup, table):
    return self.msgs.BigtableadminProjectsInstancesTablesRestoreRequest(
        parent='projects/{0}/instances/{1}'
        .format(self.Project(), 'theinstance'),
        restoreTableRequest=self.msgs.RestoreTableRequest(
            backup='projects/{0}/instances/{1}/clusters/{2}/backups/{3}'
            .format(self.Project(), 'theinstance', 'thecluster', backup),
            tableId=table))

  def testSourceIdError(self):
    with self.assertRaises(handlers.ParseError):
      self.Run('bigtable instances tables restore --source thebackup '
               '--destination projects/theproject/instances/theinstance/'
               'tables/newtable')

  def testRestoreAsync(self):
    self.svc.Expect(
        request=self.buildRequest('thebackup', 'newtable'),
        response=self.msgs.Operation(name='operations/theoperation'))
    self.Run('bigtable instances tables restore --source thebackup '
             '--source-instance theinstance --source-cluster thecluster '
             '--destination newtable --async')
    self.AssertErrContains('Create in progress for bigtable table newtable')

  def testRestoreWait_Uri(self):
    self.svc.Expect(request=self.buildRequest('thebackup', 'newtable'),
                    response=self.msgs.Operation(
                        name='operations/theoperation', done=False))
    self.ExpectOperation(
        self.client.operations, 'operations/theoperation',
        self.client.projects_instances_tables,
        'projects/{0}/instances/{1}/tables/{2}'
        .format(self.Project(), 'theinstance', 'newtable'))

    self.Run('bigtable instances tables restore --source '
             'projects/{0}/instances/theinstance/clusters/thecluster/'
             'backups/thebackup --destination projects/{0}/instances/'
             'theinstance/tables/newtable'.format(self.Project()))

    self.AssertErrContains('Creating bigtable table newtable')

  def testRestoreWait(self):
    self.svc.Expect(request=self.buildRequest('thebackup', 'newtable'),
                    response=self.msgs.Operation(
                        name='operations/theoperation', done=False))
    self.ExpectOperation(
        self.client.operations, 'operations/theoperation',
        self.client.projects_instances_tables,
        'projects/{0}/instances/{1}/tables/{2}'
        .format(self.Project(), 'theinstance', 'newtable'))

    self.Run('bigtable instances tables restore --source thebackup '
             '--source-instance theinstance --source-cluster thecluster '
             '--destination newtable')

    self.AssertErrContains('Creating bigtable table newtable')


class RestoreTestBeta(RestoreTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class RestoreTestAlpha(RestoreTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
