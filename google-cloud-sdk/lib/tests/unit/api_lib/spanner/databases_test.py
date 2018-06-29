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
"""Tests for Spanner databases library."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabasesClientTest(base.SpannerTestBase):

  def testCreate(self):
    response = self.msgs.Operation()
    extra_ddl = ['a', 'b']
    ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.client.projects_instances_databases.Create.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesCreateRequest(
            parent=ref.RelativeName(),
            createDatabaseRequest=self.msgs.CreateDatabaseRequest(
                createStatement='CREATE DATABASE `dbId`',
                extraStatements=extra_ddl)),
        response=response)
    self.assertEqual(response, databases.Create(ref, 'dbId', extra_ddl))

  def testDelete(self):
    response = self.msgs.Empty()
    ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'instancesId': 'insId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases.DropDatabase.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesDropDatabaseRequest(
            database=ref.RelativeName()),
        response=response)
    self.assertEqual(response, databases.Delete(ref))

  def testGet(self):
    response = self.msgs.Database()
    ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'instancesId': 'insId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEqual(response, databases.Get(ref))

  def testGetDdl(self):
    statements = ['a', 'b']
    response = self.msgs.GetDatabaseDdlResponse(statements=statements)
    ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'instancesId': 'insId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases.GetDdl.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetDdlRequest(
            database=ref.RelativeName()),
        response=response)
    self.assertCountEqual(statements, databases.GetDdl(ref))

  def testList(self):
    database_list = [self.msgs.Database()]
    response = self.msgs.ListDatabasesResponse(databases=database_list)
    ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.client.projects_instances_databases.List.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesListRequest(
            parent=ref.RelativeName(), pageSize=100),
        response=response)
    self.assertCountEqual(database_list, databases.List(ref))

  def testUpdateDdl(self):
    statements = ['a', 'b']
    response = self.msgs.Operation()
    ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'instancesId': 'insId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases.UpdateDdl.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesUpdateDdlRequest(
            database=ref.RelativeName(),
            updateDatabaseDdlRequest=self.msgs.UpdateDatabaseDdlRequest(
                statements=statements)),
        response=response)
    self.assertEqual(response, databases.UpdateDdl(ref, statements))
