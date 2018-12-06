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
"""Tests for Spanner databases query command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


def SetUp(test_obj):
  test_obj.db_ref = resources.REGISTRY.Parse(
      'mydb',
      params={
          'projectsId': test_obj.Project(),
          'instancesId': 'myins',
      },
      collection='spanner.projects.instances.databases')

  test_obj.session_ref = resources.REGISTRY.Parse(
      'mysession',
      params={
          'projectsId': test_obj.Project(),
          'instancesId': 'myins',
          'databasesId': 'mydb',
      },
      collection='spanner.projects.instances.databases.sessions')


class _BaseDatabasesQueryTest(object):

  def SetUp(self):
    SetUp(self)

  def ExpectSessionCreate(self, session_to_create):
    self.client.projects_instances_databases_sessions.Create.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesSessionsCreateRequest(
            database=self.db_ref.RelativeName()),
        response=session_to_create)

  def ExpectSessionDelete(self, session_to_delete):
    self.client.projects_instances_databases_sessions.Delete.Expect(
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
            name=session_to_delete.name),
        response=self.msgs.Empty())

  def ExpectBeginTransaction(self, transaction_options, transaction_to_create):
    begin_transaction_req = self.msgs.BeginTransactionRequest(
        options=transaction_options)
    req = (
        self.msgs
        .SpannerProjectsInstancesDatabasesSessionsBeginTransactionRequest(
            beginTransactionRequest=begin_transaction_req,
            session=self.session_ref.RelativeName()))
    self.client.projects_instances_databases_sessions.BeginTransaction.Expect(
        request=req, response=transaction_to_create)

  def GivenQueryResults(self):
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

  def GivenMetadataProp(self, key, str_val):
    return self.msgs.PlanNode.MetadataValue.AdditionalProperty(
        key=key, value=extra_types.JsonValue(string_value=str_val))

  def GivenQueryPlan(self, has_aggregate_stats):
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
                metadata=self.msgs.PlanNode.MetadataValue(additionalProperties=[
                    self.GivenMetadataProp('iterator_type', 'stream'),
                    self.GivenMetadataProp('scan_target', 'TableScan')
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

  def GivenQueryMetadata(self, is_dml=False):
    if is_dml:
      return self.msgs.ResultSetMetadata(
          transaction=self.msgs.Transaction(id=bytes(123)),
          rowType=self.msgs.StructType(fields=[]))

    return self.msgs.ResultSetMetadata(rowType=self.msgs.StructType(
        fields=[self.msgs.Field(name='colA'),
                self.msgs.Field(name='colB')]))

  def GivenExecuteRequest(self,
                          sql,
                          query_mode,
                          is_dml=False,
                          enable_partitioned_dml=False):
    return self.msgs.SpannerProjectsInstancesDatabasesSessionsExecuteSqlRequest(
        session=self.session_ref.RelativeName(),
        executeSqlRequest=self.msgs.ExecuteSqlRequest(
            sql=sql,
            queryMode=self.msgs.ExecuteSqlRequest.QueryModeValueValuesEnum(
                query_mode),
            transaction=self.GivenTransaction(is_dml, enable_partitioned_dml)))

  def GivenTransaction(self, is_dml=False, enable_partitioned_dml=False):
    if enable_partitioned_dml is True:
      transaction_options = self.msgs.TransactionOptions(
          partitionedDml=self.msgs.PartitionedDml())
      transaction = self.msgs.Transaction(id=bytes(123))
      self.ExpectBeginTransaction(transaction_options, transaction)
      return self.msgs.TransactionSelector(id=transaction.id)
    elif is_dml is True:
      transaction_options = self.msgs.TransactionOptions(
          readWrite=self.msgs.ReadWrite())
      return self.msgs.TransactionSelector(begin=transaction_options)
    else:
      transaction_options = self.msgs.TransactionOptions(
          readOnly=self.msgs.ReadOnly(strong=True))
      return self.msgs.TransactionSelector(singleUse=transaction_options)

  def GivenCommitRequest(self):
    return self.msgs.SpannerProjectsInstancesDatabasesSessionsCommitRequest(
        commitRequest=self.msgs.CommitRequest(
            mutations=[], transactionId=bytes(123)),
        session=self.session_ref.RelativeName())


class DatabasesQueryTest(_BaseDatabasesQueryTest, base.SpannerTestBase):
  """Cloud Spanner databases query tests."""

  def SetUp(self):
    SetUp(self)

  def testNormalQuery(self):
    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self.ExpectSessionCreate(session)

    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self.GivenExecuteRequest('SELECT 1', 'NORMAL', False),
        response=self.msgs.ResultSet(
            metadata=self.GivenQueryMetadata(), rows=self.GivenQueryResults()))

    self.ExpectSessionDelete(session)

    self.Run(
        'spanner databases execute-sql mydb --instance myins --sql "SELECT 1"')

    self.AssertOutputEquals('colA  colB\n' 'A1    B1\n' 'A2    B2\n')

  def testDmlQuery(self):
    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self.ExpectSessionCreate(session)

    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self.GivenExecuteRequest('INSERT abc (a), VALUES (1)', 'NORMAL',
                                         True),
        response=self.msgs.ResultSet(
            metadata=self.GivenQueryMetadata(True),
            rows=[],
            stats=self.msgs.ResultSetStats(rowCountExact=1)))

    self.client.projects_instances_databases_sessions.Commit.Expect(
        request=self.GivenCommitRequest(), response=self.msgs.CommitResponse())

    self.ExpectSessionDelete(session)

    self.Run('spanner databases execute-sql mydb --instance myins ' +
             '--sql "INSERT abc (a), VALUES (1)"')
    self.AssertOutputEquals('Statement modified 1 row\n')

  def testPartitionedDmlQuery(self):
    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self.ExpectSessionCreate(session)

    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self.GivenExecuteRequest('update abc set d=13 where d=1',
                                         'NORMAL', True, True),
        response=self.msgs.ResultSet(
            metadata=self.GivenQueryMetadata(True),
            rows=[],
            stats=self.msgs.ResultSetStats(rowCountLowerBound=100)))

    self.ExpectSessionDelete(session)

    self.Run('spanner databases execute-sql mydb --instance myins ' +
             '--enable-partitioned-dml --sql "update abc set d=13 where d=1"')

    self.AssertOutputEquals('Statement modified a lower bound of 100 rows\n')

  def testUnicodeQuery(self):
    self.SetEncoding('utf8')
    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self.ExpectSessionCreate(session)

    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self.GivenExecuteRequest('SELECT Ṳᾔḯ¢◎ⅾℯ', 'NORMAL'),
        response=self.msgs.ResultSet(
            metadata=self.GivenQueryMetadata(), rows=self.GivenQueryResults()))

    self.ExpectSessionDelete(session)

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
    self.ExpectSessionCreate(session)

    query_response = self.msgs.ResultSet(
        metadata=self.GivenQueryMetadata(),
        stats=self.GivenQueryPlan(has_aggregate_stats))
    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self.GivenExecuteRequest('SELECT 1', 'PLAN'),
        response=query_response)

    self.ExpectSessionDelete(session)

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
    self.ExpectSessionCreate(session)

    query_response = self.msgs.ResultSet(
        metadata=self.GivenQueryMetadata(),
        rows=self.GivenQueryResults(),
        stats=self.GivenQueryPlan(has_aggregate_stats))
    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=self.GivenExecuteRequest('SELECT 1', 'PROFILE'),
        response=query_response)

    self.ExpectSessionDelete(session)

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


class DatabasesQueryBetaTest(_BaseDatabasesQueryTest, base.SpannerTestBeta):
  pass


class DatabasesQueryAlphaTest(DatabasesQueryBetaTest, base.SpannerTestAlpha):
  pass
