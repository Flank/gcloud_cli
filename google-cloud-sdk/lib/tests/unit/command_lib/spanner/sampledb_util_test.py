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
"""Tests for sampledb_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import textwrap

from apitools.base.py import extra_types
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.command_lib.spanner import sampledb_util
from googlecloudsdk.command_lib.spanner import write_util
from tests.lib.surface.spanner import base
import mock


class SampledbUtilTest(base.SpannerTestBase):

  _DATABASE_DDL = textwrap.dedent("""CREATE TABLE Singers (
      SingerId INT64 NOT NULL,
      FirstName STRING(MAX),
      LastName STRING(MAX),)
      PRIMARY KEY(SingerId);

      CREATE TABLE tester (
      id INT64 NOT NULL,
      Name STRING(MAX),
      Alive BOOL,
      time TIMESTAMP,
      Score FLOAT64,)
      PRIMARY KEY(id);""")

  _SINGERS_DDL = """CREATE TABLE Singers (
      SingerId INT64 NOT NULL,
      FirstName STRING(MAX),
      LastName STRING(MAX),)
      PRIMARY KEY(SingerId)"""
  _TESTER_DDL = """CREATE TABLE tester (
      id INT64 NOT NULL,
      Name STRING(MAX),
      Alive BOOL,
      time TIMESTAMP,
      Score FLOAT64,)
      PRIMARY KEY(id)"""

  _BUCKET = 'gs://mybucket'
  _SCHEMA_FILE = 'schema_file.txt'
  _FILE = 'myfile'
  _FAKE_CSV_FILE = ','.join(['1', 'John', 'D.'])

  @mock.patch.object(storage_api.StorageClient, 'ReadObject')
  def testReadSchemaFromGCS(self, mock_read):
    mock_read.return_value = io.BytesIO(self._DATABASE_DDL.encode())

    schema = sampledb_util.GetSchemaFromGCS(self._BUCKET, self._SCHEMA_FILE)

    self.assertEqual(self._DATABASE_DDL, schema)

  @mock.patch.object(storage_api.StorageClient, 'ReadObject')
  def testReadCSVFileFromGCS(self, mock_read):
    mock_read.return_value = io.BytesIO(self._FAKE_CSV_FILE.encode())

    data = sampledb_util.ReadCSVFileFromGCS(self._BUCKET, self._FILE)

    self.assertEqual([['1', 'John', 'D.']], data)

  @mock.patch.object(storage_api.StorageClient, 'ReadObject')
  def testReadEmptyCSVFileFromGCS(self, mock_read):
    mock_read.return_value = io.BytesIO(''.encode())

    data = sampledb_util.ReadCSVFileFromGCS(self._BUCKET, self._FILE)

    self.assertEqual([], data)

  def testInsertMutationCreation(self):
    table = write_util.Table.FromDdl([
        self._SINGERS_DDL,
    ], 'Singers')
    data = ['1', 'John', 'D.']
    mutation = sampledb_util.CreateInsertMutationFromCSVRow(
        table, data, table.GetColumnTypes())

    self.assertEqual(
        self.msgs.Mutation(
            insert=self.msgs.Write(
                columns=['SingerId', 'FirstName', 'LastName'],
                table='Singers',
                values=[
                    self.msgs.Write.ValuesValueListEntry(entry=[
                        extra_types.JsonValue(string_value='1'),
                        extra_types.JsonValue(string_value='John'),
                        extra_types.JsonValue(string_value='D.'),
                    ])
                ])), mutation)

  def testInsertMutationCreationTwo(self):
    table = write_util.Table.FromDdl([
        self._SINGERS_DDL,
    ], 'Singers')
    data = ['1', 'Adam', 'NULL']
    mutation = sampledb_util.CreateInsertMutationFromCSVRow(
        table, data, table.GetColumnTypes())
    self.assertEqual(
        self.msgs.Mutation(
            insert=self.msgs.Write(
                columns=['SingerId', 'FirstName', 'LastName'],
                table='Singers',
                values=[
                    self.msgs.Write.ValuesValueListEntry(entry=[
                        extra_types.JsonValue(string_value='1'),
                        extra_types.JsonValue(string_value='Adam'),
                        extra_types.JsonValue(is_null=True),
                    ])
                ])), mutation)

  def testInsertMutationCreationThree(self):
    table = write_util.Table.FromDdl([
        self._TESTER_DDL,
    ], 'tester')
    data = ['1', 'Adam', 'False', '2014-09-27T12:30:00.45Z', '234.2']
    mutation = sampledb_util.CreateInsertMutationFromCSVRow(
        table, data, table.GetColumnTypes())
    self.assertEqual(
        self.msgs.Mutation(
            insert=self.msgs.Write(
                columns=['id', 'Name', 'Alive', 'time', 'Score'],
                table='tester',
                values=[
                    self.msgs.Write.ValuesValueListEntry(entry=[
                        extra_types.JsonValue(string_value='1'),
                        extra_types.JsonValue(string_value='Adam'),
                        extra_types.JsonValue(boolean_value=False),
                        extra_types.JsonValue(
                            string_value='2014-09-27T12:30:00.45Z'),
                        extra_types.JsonValue(double_value=234.2)
                    ])
                ])), mutation)

  def testNullValuesInMutation(self):
    table = write_util.Table.FromDdl([
        self._SINGERS_DDL,
    ], 'Singers')
    data = ['1', 'NULL', 'NULL']
    mutation = sampledb_util.CreateInsertMutationFromCSVRow(
        table, data, table.GetColumnTypes())

    self.assertEqual(
        self.msgs.Mutation(
            insert=self.msgs.Write(
                columns=['SingerId', 'FirstName', 'LastName'],
                table='Singers',
                values=[
                    self.msgs.Write.ValuesValueListEntry(entry=[
                        extra_types.JsonValue(string_value='1'),
                        extra_types.JsonValue(is_null=True),
                        extra_types.JsonValue(is_null=True),
                    ])
                ])), mutation)

  def testEmptyStringsInMutation(self):
    table = write_util.Table.FromDdl([
        self._SINGERS_DDL,
    ], 'Singers')
    data = ['1', 'G.', '']
    mutation = sampledb_util.CreateInsertMutationFromCSVRow(
        table, data, table.GetColumnTypes())

    self.assertEqual(
        self.msgs.Mutation(
            insert=self.msgs.Write(
                columns=['SingerId', 'FirstName', 'LastName'],
                table='Singers',
                values=[
                    self.msgs.Write.ValuesValueListEntry(entry=[
                        extra_types.JsonValue(string_value='1'),
                        extra_types.JsonValue(string_value='G.'),
                        extra_types.JsonValue(string_value=''),
                    ])
                ])), mutation)
