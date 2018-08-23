# -*- coding: utf-8 -*- #
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
"""Tests for Spanner databases ddl update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabasesDdlUpdateTest(base.SpannerTestBase):
  """Cloud Spanner databases ddl update tests."""

  def SetUp(self):
    self.db_ref = resources.REGISTRY.Parse(
        'mydb',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins'
        },
        collection='spanner.projects.instances.databases')

  def testUpdateAsync(self):
    self.client.projects_instances_databases.UpdateDdl.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesUpdateDdlRequest(
            database=self.db_ref.RelativeName(),
            updateDatabaseDdlRequest=self.msgs.UpdateDatabaseDdlRequest(
                statements=['A', 'B', 'C'])),
        response=self.msgs.Operation())
    self.Run('beta spanner databases ddl update mydb --instance myins --async '
             '--ddl A --ddl "B;C"')

  def testUpdateSync(self):
    op_ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
            'databasesId': 'dbId',
        },
        collection='spanner.projects.instances.databases.operations')
    self.client.projects_instances_databases.UpdateDdl.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesUpdateDdlRequest(
            database=self.db_ref.RelativeName(),
            updateDatabaseDdlRequest=self.msgs.UpdateDatabaseDdlRequest(
                statements=['A', 'B', 'C'])),
        response=self.msgs.Operation(name=op_ref.RelativeName()))
    self.client.projects_instances_databases_operations.Get.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsGetRequest(
            name=op_ref.RelativeName()),
        response=self.msgs.Operation(
            name=op_ref.RelativeName(), done=True,
            response=self.msgs.Operation.ResponseValue()))
    self.Run('spanner databases ddl update mydb --instance myins '
             '--ddl A --ddl "B;C"')
