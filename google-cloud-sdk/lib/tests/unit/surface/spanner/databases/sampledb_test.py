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
"""Tests for Spanner databases create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import textwrap

from apitools.base.py import extra_types
from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import resources
from tests.lib.apitools import http_error
from tests.lib.surface.spanner import base
import mock


class DatabasesSampleDBTest(base.SpannerTestBase):
  """Cloud Spanner databases sampledb tests."""

  def SetUp(self):

    self.ins_ref = resources.REGISTRY.Parse(
        'myins',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')

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

    self.schema_statements = [
        'CREATE TABLE comments ( '
        'comments_id INT64, author STRING(MAX), `by` '
        'STRING(MAX), dead BOOL, deleted BOOL, stories_id INT64, ranking '
        'INT64, text STRING(MAX), time INT64, time_ts TIMESTAMP,) PRIMARY '
        'KEY(stories_id, comments_id)',
        'CREATE INDEX CommentsByAuthor ON comments(author)',
        'CREATE INDEX CommentsByTimeText ON comments(time_ts) STORING (text)',
        'CREATE TABLE stories ( stories_id INT64, author STRING(MAX), `by` '
        'STRING(MAX), dead BOOL, deleted BOOL, descendants INT64, score INT64,'
        ' text STRING(MAX), time INT64, time_ts TIMESTAMP, title STRING(MAX), '
        'url STRING(MAX),) PRIMARY KEY(stories_id)',
        'CREATE INDEX StoriesByAuthor ON stories(author)',
        'CREATE INDEX StoriesByScoreURL ON stories(score, url)',
        'CREATE INDEX StoriesByTitleTimeScore ON stories(title) STORING '
        '(time_ts, score)',
    ]

    self.schema = textwrap.dedent(
        ('CREATE TABLE comments ( '
         'comments_id INT64, author STRING(MAX), `by` '
         'STRING(MAX), dead BOOL, deleted BOOL, stories_id INT64, ranking '
         'INT64, text STRING(MAX), time INT64, time_ts TIMESTAMP,) PRIMARY '
         'KEY(stories_id, comments_id);'
         'CREATE INDEX CommentsByAuthor ON comments(author);'
         'CREATE INDEX CommentsByTimeText ON comments(time_ts) STORING (text);'
         'CREATE TABLE stories ( stories_id INT64, author STRING(MAX), `by` '
         'STRING(MAX), dead BOOL, deleted BOOL, descendants INT64, score INT64,'
         ' text STRING(MAX), time INT64, time_ts TIMESTAMP, title STRING(MAX), '
         'url STRING(MAX),) PRIMARY KEY(stories_id);'
         'CREATE INDEX StoriesByAuthor ON stories(author);'
         'CREATE INDEX StoriesByScoreURL ON stories(score, url);'
         'CREATE INDEX StoriesByTitleTimeScore ON stories(title) STORING '
         '(time_ts, score);'))

    self.comments_data = ','.join([
        '454528', 'Arrington', 'Arrington', 'true', 'NULL', '99', '0',
        "This is why we can't have nice things.", '1233175417',
        '2009-01-28T20:43:37Z'
    ])
    self.stories_data = ','.join([
        '99', 'pg', 'pg', 'NULL', 'NULL', '0', '5', 'NULL', '1171910249',
        '2007-02-19T18:37:29Z', 'The Google-Powered Business',
        'http://blog.radioactiveyak.com/2006/07/googleoffice-beta-google-powered.html'
    ])

    self.return_list = [
        io.BytesIO(self.schema.encode()),
        io.BytesIO(self.comments_data.encode()),
        io.BytesIO(self.stories_data.encode())
    ]
    self.comments_columns = [
        'comments_id',
        'author',
        'by',
        'dead',
        'deleted',
        'stories_id',
        'ranking',
        'text',
        'time',
        'time_ts',
    ]

    self.comments_mutation = [
        extra_types.JsonValue(string_value='454528'),
        extra_types.JsonValue(string_value='Arrington'),
        extra_types.JsonValue(string_value='Arrington'),
        extra_types.JsonValue(boolean_value=True),
        extra_types.JsonValue(is_null=True),
        extra_types.JsonValue(string_value='99'),
        extra_types.JsonValue(string_value='0'),
        extra_types.JsonValue(
            string_value="This is why we can't have nice things."),
        extra_types.JsonValue(string_value='1233175417'),
        extra_types.JsonValue(string_value='2009-01-28T20:43:37Z')
    ]

    self.stories_columns = [
        'stories_id', 'author', 'by', 'dead', 'deleted', 'descendants', 'score',
        'text', 'time', 'time_ts', 'title', 'url'
    ]

    self.stories_mutations = [
        extra_types.JsonValue(string_value='99'),
        extra_types.JsonValue(string_value='pg'),
        extra_types.JsonValue(string_value='pg'),
        extra_types.JsonValue(is_null=True),
        extra_types.JsonValue(is_null=True),
        extra_types.JsonValue(string_value='0'),
        extra_types.JsonValue(string_value='5'),
        extra_types.JsonValue(is_null=True),
        extra_types.JsonValue(string_value='1171910249'),
        extra_types.JsonValue(string_value='2007-02-19T18:37:29Z'),
        extra_types.JsonValue(string_value='The Google-Powered Business'),
        extra_types.JsonValue(
            string_value='http://blog.radioactiveyak.com/2006/07/googleoffice-beta-google-powered.html'
        )
    ]

    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)

  def _ExpectDatabaseCreation(self):
    op_ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins',
            'databasesId': 'mydb'
        },
        collection='spanner.projects.instances.databases.operations')

    self.client.projects_instances_databases.Create.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesCreateRequest(
            parent=self.ins_ref.RelativeName(),
            createDatabaseRequest=self.msgs.CreateDatabaseRequest(
                createStatement='CREATE DATABASE `mydb`',
                extraStatements=self.schema_statements)),
        response=self.msgs.Operation(name=op_ref.RelativeName()))

    self.client.projects_instances_databases_operations.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesOperationsGetRequest(
            name=op_ref.RelativeName()),
        response=self.msgs.Operation(
            name=op_ref.RelativeName(),
            done=True,
            response=self.msgs.Operation.ResponseValue()))

  def _ExpectDdl(self):

    self.client.projects_instances_databases.GetDdl.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetDdlRequest(
            database=self.db_ref.RelativeName()),
        response=self.msgs.GetDatabaseDdlResponse(
            statements=self.schema_statements))

  def _ExpectSessionCreate(self, session_to_create):
    self.client.projects_instances_databases_sessions.Create.Expect(
        request=self.msgs
        .SpannerProjectsInstancesDatabasesSessionsCreateRequest(
            database=self.db_ref.RelativeName()),
        response=session_to_create)

  def _ExpectSessionDelete(self, session_to_delete):
    self.client.projects_instances_databases_sessions.Delete.Expect(
        request=self.msgs
        .SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
            name=session_to_delete.name),
        response=self.msgs.Empty())

  def _ExpectSessionCommit(self, session_to_commit, table_name, columns,
                           values):
    mutations = [
        self.msgs.Mutation(
            insert=self.msgs.Write(
                columns=columns,
                table=table_name,
                values=[self.msgs.Write.ValuesValueListEntry(entry=values)]))
    ]
    self.client.projects_instances_databases_sessions.Commit.Expect(
        request=self.msgs
        .SpannerProjectsInstancesDatabasesSessionsCommitRequest(
            session=session_to_commit,
            commitRequest=self.msgs.CommitRequest(
                mutations=mutations,
                singleUseTransaction=self.msgs.TransactionOptions(
                    readWrite=self.msgs.ReadWrite()))),
        response=self.msgs.CommitResponse())

  def testSampleDB(self):
    self._ExpectDatabaseCreation()

    self._ExpectDdl()

    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self._ExpectSessionCreate(session)
    self._ExpectSessionCommit(self.session_ref.RelativeName(), 'comments',
                              self.comments_columns, self.comments_mutation)
    self._ExpectSessionDelete(session)
    self._ExpectDdl()
    self._ExpectSessionCreate(session)
    self._ExpectSessionCommit(self.session_ref.RelativeName(), 'stories',
                              self.stories_columns, self.stories_mutations)
    self._ExpectSessionDelete(session)

    #  Currently gcloud does not support download/upload from an
    #  mocked apitools client (b/33202933)
    with mock.patch.object(storage_api.StorageClient,
                           'ReadObject') as mock_read:
      mock_read.side_effect = self.return_list
      self.Run('alpha spanner databases sampledb mydb --instance=myins')

  def testExistingDBError(self):
    self.client.projects_instances_databases.Create.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesCreateRequest(
            parent=self.ins_ref.RelativeName(),
            createDatabaseRequest=self.msgs.CreateDatabaseRequest(
                createStatement='CREATE DATABASE `mydb`',
                extraStatements=self.schema_statements)),
        exception=http_error.MakeHttpError(
            code=404, message='Database already exists'))

    with self.AssertRaisesHttpExceptionMatches(
        'Database already exists'), mock.patch.object(
            storage_api.StorageClient, 'ReadObject') as mock_read:
      #  Currently gcloud does not support download/upload from an
      #  mocked apitools client (b/33202933)
      mock_read.side_effect = self.return_list
      self.Run('alpha spanner databases sampledb mydb --instance=myins')

  def testSampleDBWithDefaultInstance(self):
    self.Run('config set spanner/instance myins')
    self._ExpectDatabaseCreation()

    self._ExpectDdl()

    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self._ExpectSessionCreate(session)
    self._ExpectSessionCommit(self.session_ref.RelativeName(), 'comments',
                              self.comments_columns, self.comments_mutation)
    self._ExpectSessionDelete(session)
    self._ExpectDdl()
    self._ExpectSessionCreate(session)
    self._ExpectSessionCommit(self.session_ref.RelativeName(), 'stories',
                              self.stories_columns, self.stories_mutations)
    self._ExpectSessionDelete(session)

    #  Currently gcloud does not support download/upload from an
    #  mocked apitools client (b/33202933)
    with mock.patch.object(storage_api.StorageClient,
                           'ReadObject') as mock_read:
      mock_read.side_effect = self.return_list
      self.Run('alpha spanner databases sampledb mydb')

    self.AssertErrContains('--instance=myins')
