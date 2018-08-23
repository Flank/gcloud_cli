# -*- coding: utf-8 -*-
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
"""Tests for Spanner databases query command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabasesQueryTest(base.SpannerTestBase):
  """Cloud Spanner databases query tests."""

  def SetUp(self):
    self.db_ref = resources.REGISTRY.Parse(
        'mydb',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins',
        },
        collection='spanner.projects.instances.databases')

    self.session_ref = resources.REGISTRY.Parse(
        'mysession',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins',
            'databasesId': 'mydb',
        },
        collection='spanner.projects.instances.databases.sessions')

  def _ExpectSessionCreate(self, session_to_create):
    self.client.projects_instances_databases_sessions.Create.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesSessionsCreateRequest(
            database=self.db_ref.RelativeName()),
        response=session_to_create)

  def _ExpectSessionDelete(self, session_to_delete):
    self.client.projects_instances_databases_sessions.Delete.Expect(
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
            name=session_to_delete.name),
        response=self.msgs.Empty())

  def _GivenQueryResults(self):
    return [
        self.msgs.ResultSet.RowsValueListEntry(entry=[
            extra_types.JsonValue(string_value='A1'),
            extra_types.JsonValue(string_value='B1')
        ]),
        self.msgs.ResultSet.RowsValueListEntry(entry=[
            extra_types.JsonValue(string_value='A2'),
            extra_types.JsonValue(string_value='B2')
        ])
    ]

  def _GivenMetadataProp(self, key, str_val):
    return self.msgs.PlanNode.MetadataValue.AdditionalProperty(
        key=key, value=extra_types.JsonValue(string_value=str_val))

  def _GivenQueryPlan(self, has_aggregate_stats):
    query_stats = None
    if has_aggregate_stats:
      query_stats = self.msgs.ResultSetStats.QueryStatsValue(
          additionalProperties=[
              self.msgs.ResultSetStats.QueryStatsValue.AdditionalProperty(
                  key='elapsed_time',
                  value=extra_types.JsonValue(string_value='1.7 msecs')),
              self.msgs.ResultSetStats.QueryStatsValue.AdditionalProperty(
                  key='cpu_time',
                  value=extra_types.JsonValue(string_value='.3 msecs')),
              self.msgs.ResultSetStats.QueryStatsValue.AdditionalProperty(
                  key='rows_returned',
                  value=extra_types.JsonValue(string_value='9')),
              self.msgs.ResultSetStats.QueryStatsValue.AdditionalProperty(
                  key='rows_scanned',
                  value=extra_types.JsonValue(string_value='2000'))
          ])
    return self.msgs.ResultSetStats(
        queryPlan=self.msgs.QueryPlan(planNodes=[
            self.msgs.PlanNode(
                kind=self.msgs.PlanNode.KindValueValuesEnum('RELATIONAL'),
                displayName='Serialize Result',
                childLinks=[
                    self.msgs.ChildLink(childIndex=1),
                    self.msgs.ChildLink(childIndex=3)
                ]),
            self.msgs.PlanNode(
                kind=self.msgs.PlanNode.KindValueValuesEnum('RELATIONAL'),
                displayName='Enumerate Rows',
                childLinks=[
                    self.msgs.ChildLink(childIndex=2),
                    self.msgs.ChildLink(childIndex=3)
                ],
                metadata=self.msgs.PlanNode.MetadataValue(
                    additionalProperties=[
                        self._GivenMetadataProp('iterator_type', 'stream'),
                        self._GivenMetadataProp('scan_target', 'TableScan')
                    ]),
                index=1),
            self.msgs.PlanNode(
                kind=self.msgs.PlanNode.KindValueValuesEnum('SCALAR'),
                displayName='Constant',
                shortRepresentation=self.msgs.ShortRepresentation(
                    description='<null>'),
                index=2),
            self.msgs.PlanNode(
                kind=self.msgs.PlanNode.KindValueValuesEnum('SCALAR'),
                displayName='Constant',
                shortRepresentation=self.msgs.ShortRepresentation(
                    description='1'),
                index=3),
        ]),
        queryStats=query_stats)

  def _GivenQueryMetadata(self):
    return self.msgs.ResultSetMetadata(rowType=self.msgs.StructType(
        fields=[self.msgs.Field(name='colA'),
                self.msgs.Field(name='colB')]))

  def _GivenExecuteRequest(self, sql, query_mode):
    return self.msgs.SpannerProjectsInstancesDatabasesSessionsExecuteSqlRequest(
        session=self.session_ref.RelativeName(),
        executeSqlRequest=self.msgs.ExecuteSqlRequest(
            sql=sql,
            queryMode=self.msgs.ExecuteSqlRequest.QueryModeValueValuesEnum(
                query_mode)))

  def testNormalQuery(self):
    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self._ExpectSessionCreate(session)

    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self._GivenExecuteRequest('SELECT 1', 'NORMAL'),
        response=self.msgs.ResultSet(
            metadata=self._GivenQueryMetadata(),
            rows=self._GivenQueryResults()))

    self._ExpectSessionDelete(session)

    self.Run(
        'spanner databases execute-sql mydb --instance myins --sql "SELECT 1"')

    self.AssertOutputEquals('colA  colB\n' 'A1    B1\n' 'A2    B2\n')

  def testUnicodeQuery(self):
    self.SetEncoding('utf8')
    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self._ExpectSessionCreate(session)

    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self._GivenExecuteRequest('SELECT Ṳᾔḯ¢◎ⅾℯ', 'NORMAL'),
        response=self.msgs.ResultSet(
            metadata=self._GivenQueryMetadata(),
            rows=self._GivenQueryResults()))

    self._ExpectSessionDelete(session)

    self.Run(
        'spanner databases execute-sql mydb --instance myins --sql "SELECT '
        'Ṳᾔḯ¢◎ⅾℯ"'
    )

    self.AssertOutputEquals('colA  colB\n'
                            'A1    B1\n'
                            'A2    B2\n')

  def testPlanQuery(self):
    session = self.msgs.Session(name=self.session_ref.RelativeName())
    has_aggregate_stats = False
    self._ExpectSessionCreate(session)

    query_response = self.msgs.ResultSet(
        metadata=self._GivenQueryMetadata(),
        stats=self._GivenQueryPlan(has_aggregate_stats))
    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self._GivenExecuteRequest('SELECT 1', 'PLAN'),
        response=query_response)

    self._ExpectSessionDelete(session)

    query_request = self.Run("""
        spanner databases execute-sql mydb --instance myins
        --query-mode=PLAN --sql 'SELECT 1'
        """)
    self.assertEqual(query_request, query_response)

    query_plan = r""" RELATIONAL Serialize Result
    |
    +- RELATIONAL Enumerate Rows
    |  iterator_type: stream, scan_target: TableScan
    |   |
    |   +- SCALAR Constant
    |   |  <null>
    |   |
    |   \- SCALAR Constant
    |      1
    |
    \- SCALAR Constant
       1"""
    self.AssertOutputContains(query_plan)

  def testProfileQuery(self):
    session = self.msgs.Session(name=self.session_ref.RelativeName())
    has_aggregate_stats = True
    self._ExpectSessionCreate(session)

    query_response = self.msgs.ResultSet(
        metadata=self._GivenQueryMetadata(),
        rows=self._GivenQueryResults(),
        stats=self._GivenQueryPlan(has_aggregate_stats))
    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self._GivenExecuteRequest('SELECT 1', 'PROFILE'),
        response=query_response)

    self._ExpectSessionDelete(session)

    query_request = self.Run("""
        spanner databases execute-sql mydb --instance myins
        --query-mode=PROFILE --sql 'SELECT 1'
        """)
    self.assertEqual(query_request, query_response)

    # Check that the query results are written to stderr.
    self.AssertErrContains('colA  colB\n' 'A1    B1\n' 'A2    B2\n')

    self.AssertOutputContains(
        'ELAPSED_TIME | CPU_TIME | ROWS_RETURNED | ROWS_SCANNED',
        normalize_space=True)
    # 1.7 msecs         |  .3 msecs    | 9    | 2000
    self.AssertOutputMatches(r'1\.7 msecs[\s|]+\.3 msecs[\s|]+9[\s|]+2000',
                             normalize_space=True)

    query_plan = r""" RELATIONAL Serialize Result
    |
    +- RELATIONAL Enumerate Rows
    |  iterator_type: stream, scan_target: TableScan
    |   |
    |   +- SCALAR Constant
    |   |  <null>
    |   |
    |   \- SCALAR Constant
    |      1
    |
    \- SCALAR Constant
       1"""
    self.AssertOutputContains(query_plan)
