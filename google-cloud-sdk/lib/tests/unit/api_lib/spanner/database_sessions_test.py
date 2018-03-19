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
"""Tests for Spanner database sessions library."""

from googlecloudsdk.api_lib.spanner import database_sessions
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabaseSessionsClientTest(base.SpannerTestBase):

  def SetUp(self):
    self.instance_id = 'myins'
    self.database_id = 'mydb'
    self.session_id = 'mysession'

  def testCreate(self):
    response = self.msgs.Session()
    ref = resources.REGISTRY.Parse(
        self.database_id,
        params={
            'instancesId': self.instance_id,
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases_sessions.Create.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesSessionsCreateRequest(
            database=ref.RelativeName()),
        response=response)
    self.assertEquals(database_sessions.Create(ref), response)

  def testList(self):
    session = self.msgs.Session()
    response = self.msgs.ListSessionsResponse(sessions=[session])
    ref = resources.REGISTRY.Parse(
        self.database_id,
        params={
            'instancesId': self.instance_id,
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases_sessions.List.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSessionsListRequest(
            database=ref.RelativeName()),
        response=response)
    self.assertEquals(database_sessions.List(ref).next(), session)

  def testListWithFilter(self):
    session = self.msgs.Session(
        labels=self.msgs.Session.LabelsValue(additionalProperties=[
            self.msgs.Session.LabelsValue.AdditionalProperty(
                key='aLabel', value='stuff')
        ]))
    response = self.msgs.ListSessionsResponse(sessions=[session])
    ref = resources.REGISTRY.Parse(
        self.database_id,
        params={
            'instancesId': self.instance_id,
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    server_filter = 'labels.aLabel:*'
    self.client.projects_instances_databases_sessions.List.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSessionsListRequest(
            database=ref.RelativeName(), filter=server_filter),
        response=response)
    self.assertEquals(
        database_sessions.List(ref, server_filter).next(), session)

  def testDelete(self):
    response = self.msgs.Empty()
    ref = resources.REGISTRY.Parse(
        self.session_id,
        params={
            'projectsId': self.Project(),
            'instancesId': self.instance_id,
            'databasesId': self.database_id,
        },
        collection='spanner.projects.instances.databases.sessions')
    self.client.projects_instances_databases_sessions.Delete.Expect(
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEquals(database_sessions.Delete(ref), response)

  def testExecuteSql(self):
    response = self.msgs.ResultSet()
    ref = resources.REGISTRY.Parse(
        self.session_id,
        params={
            'projectsId': self.Project(),
            'instancesId': self.instance_id,
            'databasesId': self.database_id,
        },
        collection='spanner.projects.instances.databases.sessions')

    execute_sql_request = self.msgs.ExecuteSqlRequest(
        sql='sql',
        queryMode=self.msgs.ExecuteSqlRequest.QueryModeValueValuesEnum.NORMAL)
    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsExecuteSqlRequest(
            session=ref.RelativeName(), executeSqlRequest=execute_sql_request),
        response=response)
    self.assertEquals(
        database_sessions.ExecuteSql(ref, 'sql', 'NORMAL'), response)
