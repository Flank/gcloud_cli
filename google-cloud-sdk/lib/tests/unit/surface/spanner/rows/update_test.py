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
"""Tests for Spanner rows update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from apitools.base.py import extra_types
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib.surface.spanner import base


@parameterized.named_parameters(('Beta', calliope_base.ReleaseTrack.BETA),
                                ('Alpha', calliope_base.ReleaseTrack.ALPHA))
class RowsUpdateTest(base.SpannerTestBase):
  """Cloud Spanner rows update tests."""

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
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsCreateRequest(
            database=self.db_ref.RelativeName()),
        response=session_to_create)

  def _ExpectSessionDelete(self, session_to_delete):
    self.client.projects_instances_databases_sessions.Delete.Expect(
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
            name=session_to_delete.name),
        response=self.msgs.Empty())

  def _ExpectSessionCommit(self, session_to_commit, table_name, columns,
                           values):
    mutations = [
        self.msgs.Mutation(
            update=self.msgs.Write(
                columns=columns,
                table=table_name,
                values=[self.msgs.Write.ValuesValueListEntry(entry=values)]))
    ]
    self.client.projects_instances_databases_sessions.Commit.Expect(
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsCommitRequest(
            session=session_to_commit,
            commitRequest=self.msgs.CommitRequest(
                mutations=mutations,
                singleUseTransaction=self.msgs.TransactionOptions(
                    readWrite=self.msgs.ReadWrite()))),
        response=self.msgs.Empty())

  def _GivenDdlResponse(self):
    table1_ddl = textwrap.dedent("""
          CREATE TABLE Singers (
          SingerId INT64 NOT NULL,
          FirstName STRING(MAX),
          LastName STRING(MAX),) PRIMARY KEY(SingerId)
        """)

    table2_ddl = textwrap.dedent("""
          CREATE TABLE Songs (
          SingerId INT64,
          AlbumName STRING(MAX),
          Genre BYTES(MAX),
          Modification ARRAY<BOOL>,) PRIMARY KEY(SingerId, AlbumName)
        """)

    self.client.projects_instances_databases.GetDdl.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetDdlRequest(
            database=self.db_ref.RelativeName()),
        response=self.msgs.GetDatabaseDdlResponse(
            statements=[table1_ddl, table2_ddl]))

  def testUpdateWithSimpleTable(self, track):
    self.track = track
    self._GivenDdlResponse()

    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self._ExpectSessionCreate(session)

    self._ExpectSessionCommit(
        self.session_ref.RelativeName(),
        'Singers', ['SingerId', 'FirstName', 'LastName'], [
            extra_types.JsonValue(string_value='2'),
            extra_types.JsonValue(string_value='abc'),
            extra_types.JsonValue(string_value='cab')
        ])
    self._ExpectSessionDelete(session)

    self.Run('spanner rows update --table=Singers --database=mydb '
             '--instance=myins --data=SingerId=2,FirstName=abc,LastName=cab')

  def testUpdateWithComplicatedTable(self, track):
    self.track = track
    self._GivenDdlResponse()

    session = self.msgs.Session(name=self.session_ref.RelativeName())
    self._ExpectSessionCreate(session)
    self._ExpectSessionCommit(
        self.session_ref.RelativeName(),
        'Songs', ['SingerId', 'AlbumName', 'Genre', 'Modification'], [
            extra_types.JsonValue(string_value='2'),
            extra_types.JsonValue(string_value='my-album'),
            extra_types.JsonValue(is_null=True),
            extra_types.JsonValue(
                array_value=extra_types.JsonArray(entries=[
                    extra_types.JsonValue(boolean_value=True),
                ]))
        ])
    self._ExpectSessionDelete(session)

    self.Run(
        'spanner rows update  --table=Songs --database=mydb --instance=myins '
        '--data=SingerId=2,AlbumName=my-album,Genre=NULL,Modification=[True]')
