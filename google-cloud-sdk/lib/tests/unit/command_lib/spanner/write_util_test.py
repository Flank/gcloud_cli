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
"""Tests for Spanner write util lib."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from collections import OrderedDict
import re
from apitools.base.py import extra_types
from googlecloudsdk.command_lib.spanner import write_util as util
from tests.lib import parameterized
from tests.lib.surface.spanner import base

_DATABASE_DDL = [
    'CREATE TABLE Singers (  SingerId INT64 NOT NULL,  FirstName '
    'STRING(MAX),  LastName STRING(MAX),) PRIMARY KEY(SingerId)',
    'CREATE TABLE Songs (  SingerId INT64,  AlbumName STRING(MAX),  '
    'Genre BYTES(MAX),  Modification ARRAY<BOOL>,) PRIMARY KEY(SingerId, '
    'AlbumName)',
    'CREATE TABLE Users (  Id INT64 NOT NULL,  Key BYTES(MAX) NOT NULL,'
    '  Message STRING(MAX),) PRIMARY KEY(Id, Key)',
    'CREATE TABLE bytesTable (  id INT64,  name BYTES(MAX),) PRIMARY '
    'KEY(id)',
    'CREATE TABLE checkbox (  llll BOOL,  b INT64,) PRIMARY KEY(llll)',
    'CREATE INDEX aaaa ON checkbox(llll)',
    'CREATE UNIQUE INDEX testIndex ON dfafdas(fdsafasd)',
    'CREATE TABLE events (  eventId STRING(MAX),  userId INT64,  Name '
    'STRING(MAX),  Duration INT64,  date ARRAY<TIMESTAMP>,) PRIMARY '
    'KEY(eventId, userId)',
    'CREATE TABLE media (  id INT64 NOT NULL,  data BYTES(MAX) NOT NULL,'
    '  filetype STRING(16) NOT NULL,) PRIMARY KEY(id)',
    'CREATE TABLE permissionsTest (  a INT64,) PRIMARY KEY(a)',
    'CREATE TABLE pkTest (  col1 BOOL,  col2 FLOAT64,  col3 '
    'STRING(MAX),  col4 TIMESTAMP,  name STRING(MAX),) PRIMARY KEY(col1,'
    ' col2, col3, col4)',
    'CREATE TABLE queryTest (  id INT64,  name STRING(MAX),  others '
    'STRING(MAX),  arr ARRAY<STRING(MAX)>,) PRIMARY KEY(id, name)',
    'CREATE TABLE strTbl (  id INT64,  col STRING(4),) PRIMARY KEY(id)',
    'CREATE TABLE table (  asdf INT64,  aaa INT64,) PRIMARY KEY(asdf)',
    'CREATE TABLE testTable (  adsfasd INT64,  asdfsdafsad INT64,) '
    'PRIMARY KEY(adsfasd)',
    'CREATE TABLE timestampArr (  id INT64,  col1 TIMESTAMP,  col2 '
    'ARRAY<TIMESTAMP>,) PRIMARY KEY(id)',
    'CREATE TABLE wall_post (  id INT64 NOT NULL,  username STRING(64) NOT'
    ' NULL,  caption STRING(MAX) NOT NULL,  media_ids ARRAY<INT64>,) '
    'PRIMARY KEY(id)',
    'CREATE INDEX PostsByUsername ON wall_post(username) STORING (caption, '
    'media_ids)'
]


class TableTest(base.SpannerTestBase, parameterized.TestCase):

  @classmethod
  def _TableCreatedWithExpectedNamesAndPrimaryKeys(cls, table, name, pks):
    return table.name == name and table._primary_keys == pks

  @classmethod
  def _GivenScalarColumn(cls, name, scalar_type):
    return util._TableColumn(name, util._ScalarColumnType(scalar_type))

  @classmethod
  def _GivenArrayColumn(cls, name, scalar_type):
    return util._TableColumn(name, util._ArrayColumnType(scalar_type))

  def testTableCreationFromSimpleDdl(self):
    database_ddl_singers = [
        'CREATE TABLE Singers (  SingerId INT64 NOT NULL,  FirstName '
        'STRING(MAX),  LastName STRING(MAX),) PRIMARY KEY(SingerId)',
    ]
    table = util.Table.FromDdl(database_ddl_singers, 'Singers')

    self.assertTrue(
        self._TableCreatedWithExpectedNamesAndPrimaryKeys(
            table, 'Singers', ['SingerId']))
    self.assertEqual(['SingerId', 'FirstName', 'LastName'],
                     list(table._columns.keys()))
    self.assertEqual([
        self._GivenScalarColumn('SingerId', 'INT64'),
        self._GivenScalarColumn('FirstName', 'STRING'),
        self._GivenScalarColumn('LastName', 'STRING'),
    ], list(table._columns.values()))

  def testTableCreationWithArrayColumn(self):
    database_ddl_songs = [
        'CREATE TABLE Songs (  SingerId INT64,  AlbumName STRING(MAX),  '
        'Genre BYTES(MAX),  Modification ARRAY<BOOL>,) PRIMARY KEY(SingerId, '
        'AlbumName)'
    ]

    table = util.Table.FromDdl(database_ddl_songs, 'Songs')

    self.assertTrue(
        self._TableCreatedWithExpectedNamesAndPrimaryKeys(
            table, 'Songs', ['SingerId', 'AlbumName']))
    self.assertEqual(['SingerId', 'AlbumName', 'Genre', 'Modification'],
                     list(table._columns.keys()))
    self.assertEqual([
        self._GivenScalarColumn('SingerId', 'INT64'),
        self._GivenScalarColumn('AlbumName', 'STRING'),
        self._GivenScalarColumn('Genre', 'BYTES'),
        self._GivenArrayColumn('Modification', 'BOOL'),
    ], list(table._columns.values()))

  def testTableCreationWithBytesColumn(self):
    database_ddl_bytes = [
        'CREATE TABLE bytesTable (  id INT64,  name BYTES(MAX),) PRIMARY '
        'KEY(id)',
    ]
    table = util.Table.FromDdl(database_ddl_bytes, 'bytesTable')

    self.assertTrue(
        self._TableCreatedWithExpectedNamesAndPrimaryKeys(
            table, 'bytesTable', ['id']))
    self.assertEqual(['id', 'name'], list(table._columns.keys()))
    self.assertEqual([
        self._GivenScalarColumn('id', 'INT64'),
        self._GivenScalarColumn('name', 'BYTES'),
    ], list(table._columns.values()))

  def testTableCreationWithNumericColumns(self):
    database_ddl_numeric = [
        'CREATE TABLE numericTable ( id INT64, numeric NUMERIC, arr_numeric '
        'ARRAY<NUMERIC>) PRIMARY KEY(id)',
    ]
    table = util.Table.FromDdl(database_ddl_numeric, 'numericTable')

    self.assertTrue(
        self._TableCreatedWithExpectedNamesAndPrimaryKeys(
            table, 'numericTable', ['id']))
    self.assertEqual(['id', 'numeric', 'arr_numeric'],
                     list(table._columns.keys()))
    self.assertEqual([
        self._GivenScalarColumn('id', 'INT64'),
        self._GivenScalarColumn('numeric', 'NUMERIC'),
        self._GivenArrayColumn('arr_numeric', 'NUMERIC'),
    ], list(table._columns.values()))

  def testTableCreationWithKeywordColumn(self):
    database_ddl_bytes = [
        'CREATE TABLE keywordTable (  id INT64,  `by` STRING(MAX),) PRIMARY '
        'KEY(id)',
    ]
    table = util.Table.FromDdl(database_ddl_bytes, 'keywordTable')

    self.assertTrue(
        self._TableCreatedWithExpectedNamesAndPrimaryKeys(
            table, 'keywordTable', ['id']))
    self.assertEqual(['id', 'by'], list(table._columns.keys()))
    self.assertEqual([
        self._GivenScalarColumn('id', 'INT64'),
        self._GivenScalarColumn('by', 'STRING'),
    ], list(table._columns.values()))

  def testTableCreationFromComplicatedDdl(self):
    database_ddl_pk = [
        'CREATE TABLE pkTest (  col1 BOOL,  col2 FLOAT64,  col3 '
        'STRING(MAX),  col4 TIMESTAMP,  name STRING(MAX),) PRIMARY KEY(col1,'
        ' col2, col3, col4)'
    ]
    table = util.Table.FromDdl(database_ddl_pk, 'pkTest')

    self.assertTrue(
        self._TableCreatedWithExpectedNamesAndPrimaryKeys(
            table, 'pkTest', ['col1', 'col2', 'col3', 'col4']))
    self.assertEqual(['col1', 'col2', 'col3', 'col4', 'name'],
                     list(table._columns.keys()))
    self.assertEqual([
        self._GivenScalarColumn('col1', 'BOOL'),
        self._GivenScalarColumn('col2', 'FLOAT64'),
        self._GivenScalarColumn('col3', 'STRING'),
        self._GivenScalarColumn('col4', 'TIMESTAMP'),
        self._GivenScalarColumn('name', 'STRING'),
    ], list(table._columns.values()))

  def testTableCreationFromAnotherComplicatedDdl(self):
    database_ddl_events = [
        'CREATE TABLE events (  eventId STRING(MAX),  userId INT64,  Name '
        'STRING(MAX),  Duration INT64,  date ARRAY<TIMESTAMP>,) PRIMARY '
        'KEY(eventId, userId)',
    ]
    table = util.Table.FromDdl(database_ddl_events, 'events')

    self.assertTrue(
        self._TableCreatedWithExpectedNamesAndPrimaryKeys(
            table, 'events', ['eventId', 'userId']))
    self.assertEqual(['eventId', 'userId', 'Name', 'Duration', 'date'],
                     list(table._columns.keys()))
    self.assertEqual([
        self._GivenScalarColumn('eventId', 'STRING'),
        self._GivenScalarColumn('userId', 'INT64'),
        self._GivenScalarColumn('Name', 'STRING'),
        self._GivenScalarColumn('Duration', 'INT64'),
        self._GivenArrayColumn('date', 'TIMESTAMP'),
    ], list(table._columns.values()))

  @parameterized.parameters('singers', 'songs', 'users', 'BytesTable', 'Event',
                            'PostsByUsername')
  def testTableWithInvalidTableName(self, invalid_table_name):
    error_message = re.escape(
        ('Table name [{}] is invalid. Valid table names: [Singers, '
         'Songs, Users, bytesTable, checkbox, events, media, '
         'permissionsTest, pkTest, queryTest, strTbl, table, '
         'testTable, timestampArr, wall_post].').format(invalid_table_name))

    with self.assertRaisesRegex(util.BadTableNameError, error_message):
      util.Table.FromDdl(_DATABASE_DDL, invalid_table_name)

  # TODO(b/143093180): Update test after we support numeric in keys.
  def testTableWithScalarNumericKeyColumn(self):
    database_ddl_numeric_key = [
        'CREATE TABLE numericTable ( id INT64, numeric NUMERIC, arr_numeric '
        'ARRAY<NUMERIC>) PRIMARY KEY(numeric)',
    ]
    error_message = re.escape(
        'Invalid DDL: Column [numeric] is not a valid primary key type.')
    with self.assertRaisesRegex(ValueError, error_message):
      util.Table.FromDdl(database_ddl_numeric_key, 'numericTable')

  # TODO(b/143093180): Update test after we support numeric in keys.
  def testTableWithArrayNumericKeyColumn(self):
    database_ddl_numeric_key = [
        'CREATE TABLE numericTable ( id INT64, numeric NUMERIC, arr_numeric '
        'ARRAY<NUMERIC>) PRIMARY KEY(arr_numeric)',
    ]
    error_message = re.escape(
        'Invalid DDL: Column [arr_numeric] is not a valid primary key type.')
    with self.assertRaisesRegex(ValueError, error_message):
      util.Table.FromDdl(database_ddl_numeric_key, 'numericTable')

  def testTableWithValidDataInput(self):
    table = util.Table.FromDdl(_DATABASE_DDL, 'pkTest')
    data_input = OrderedDict([('col1', 'true'), ('col2', '2.3'),
                              ('col3', 'abc'), ('col4', '2000-10-10'), ('name',
                                                                        'bb')])
    test_data = table.GetJsonData(data_input)
    expected_values = [
        extra_types.JsonValue(boolean_value=True),
        extra_types.JsonValue(double_value=2.3),
        extra_types.JsonValue(string_value='abc'),
        extra_types.JsonValue(string_value='2000-10-10'),
        extra_types.JsonValue(string_value='bb')
    ]
    self.assertEquals(expected_values, [col.col_value for col in test_data])
    self.assertEquals(['col1', 'col2', 'col3', 'col4', 'name'],
                      [col.col_name for col in test_data])

  def testTableWithValidArrayDataInput(self):
    table = util.Table.FromDdl(_DATABASE_DDL, 'events')
    data_input = OrderedDict([('eventId', 'bb'), ('userId', '1'),
                              ('Name', 'apple'), ('Duration', '12'),
                              ('date', ['1001-10-10', '1010-01-01'])])
    test_data = table.GetJsonData(data_input)
    expected_values = [
        extra_types.JsonValue(string_value='bb'),
        extra_types.JsonValue(string_value='1'),
        extra_types.JsonValue(string_value='apple'),
        extra_types.JsonValue(string_value='12'),
        extra_types.JsonValue(
            array_value=extra_types.JsonArray(entries=[
                extra_types.JsonValue(string_value='1001-10-10'),
                extra_types.JsonValue(string_value='1010-01-01')
            ])),
    ]
    self.assertEquals(expected_values, [col.col_value for col in test_data])
    self.assertEquals(['eventId', 'userId', 'Name', 'Duration', 'date'],
                      [col.col_name for col in test_data])

  def testTableWithInvalidColumn(self):
    table = util.Table.FromDdl(_DATABASE_DDL, 'queryTest')
    data = OrderedDict([('ID', '1')])
    error_message = re.escape('Column name [ID] is invalid. '
                              'Valid column names: [id, name, others, arr].')

    with self.assertRaisesRegex(util.BadColumnNameError, error_message):
      table.GetJsonData(data)

  def testTableWithValidKeysInput(self):
    table = util.Table.FromDdl(_DATABASE_DDL, 'pkTest')
    keys = ['true', '2.3', 'ala', '1001-01-10']

    test_keys = table.GetJsonKeys(keys)
    expected_keys = [
        extra_types.JsonValue(boolean_value=True),
        extra_types.JsonValue(double_value=2.3),
        extra_types.JsonValue(string_value='ala'),
        extra_types.JsonValue(string_value='1001-01-10'),
    ]
    self.assertEqual(expected_keys, test_keys)

  @parameterized.parameters(([], 0), (['1'], 1), (['2', '2', '2', '2', '2'], 5))
  def testTableWithInvalidKeysInput(self, invalid_keys, invalid_key_number):
    table = util.Table.FromDdl(_DATABASE_DDL, 'pkTest')
    error_message = re.escape('Invalid keys. There are 4 primary key columns '
                              'in the table [pkTest]. {} are given.'
                              .format(invalid_key_number))

    with self.assertRaisesRegex(util.InvalidKeysError, error_message):
      table.GetJsonKeys(invalid_keys)

  def testGetColumnTypes(self):
    table = util.Table.FromDdl(_DATABASE_DDL, 'queryTest')
    expected_types = OrderedDict([('id', util._ScalarColumnType('INT64')),
                                  ('name', util._ScalarColumnType('STRING')),
                                  ('others', util._ScalarColumnType('STRING')),
                                  ('arr', util._ArrayColumnType('STRING'))])
    self.assertEquals(table.GetColumnTypes(), expected_types)


class JsonConversionTest(base.SpannerTestBase, parameterized.TestCase):

  @parameterized.parameters('BOOL', 'BYTES', 'DATE', 'FLOAT64', 'INT64',
                            'STRING', 'TIMESTAMP', 'NUMERIC')
  def testNullValues(self, scalar_type):
    self.assertEquals(
        extra_types.JsonValue(is_null=True),
        util.ConvertJsonValueForScalarTypes(scalar_type, 'NULL'))

  @parameterized.parameters(('true', True), ('True', True), ('False', False),
                            ('TRUE', True), ('false', False), ('FALSE', False))
  def testBoolValues(self, input_value, expected_value):
    self.assertEquals(
        extra_types.JsonValue(boolean_value=expected_value),
        util.ConvertJsonValueForScalarTypes('BOOL', input_value))

  @parameterized.parameters(('2.3', 2.3), ('1', 1))
  def testFloat64ValuesWithNumber(self, input_value, expected_value):
    self.assertEquals(
        extra_types.JsonValue(double_value=expected_value),
        util.ConvertJsonValueForScalarTypes('FLOAT64', input_value))

  @parameterized.parameters('NaN', 'Infinity', '-Infinity')
  def testFloat64ValuesWithLetter(self, input_value):
    self.assertEquals(
        extra_types.JsonValue(string_value=input_value),
        util.ConvertJsonValueForScalarTypes('FLOAT64', input_value))

  @parameterized.parameters('1', '2', '0')
  def testIntValues(self, input_value):
    self.assertEquals(
        extra_types.JsonValue(string_value=input_value),
        util.ConvertJsonValueForScalarTypes('INT64', input_value))

  @parameterized.parameters('ac', 'bbbbb', '345')
  def testStringValues(self, input_value):
    self.assertEquals(
        extra_types.JsonValue(string_value=input_value),
        util.ConvertJsonValueForScalarTypes('STRING', input_value))

  @parameterized.parameters('2014-09-27T12:30:00.45Z',
                            '2018-04-12T01:02:33.666666666')
  def testTimestampValues(self, input_value):
    self.assertEquals(
        extra_types.JsonValue(string_value=input_value),
        util.ConvertJsonValueForScalarTypes('TIMESTAMP', input_value))

  @parameterized.parameters('2006-09-23', '1009-02-01')
  def testDateValues(self, input_value):
    self.assertEquals(
        extra_types.JsonValue(string_value=input_value),
        util.ConvertJsonValueForScalarTypes('DATE', input_value))

  @parameterized.parameters('-96283295.412871',
                            '99999999999999999999999999999.999999999')
  def testNumericValues(self, input_value):
    self.assertEqual(
        extra_types.JsonValue(string_value=input_value),
        util.ConvertJsonValueForScalarTypes('NUMERIC', input_value))


class ValidateArrayInputTest(base.SpannerTestBase, parameterized.TestCase):

  def testValidInput(self):
    data = OrderedDict([('id', '1'), ('name', 'Cooper Dogerson')])
    table = util.Table.FromDdl(_DATABASE_DDL, 'queryTest')
    self.assertEqual(data, util.ValidateArrayInput(table, data))

  def testValidArrayInput(self):
    data = OrderedDict([('id', '1'), ('name', 'Cooper Dogerson'),
                        ('arr', ['hello, I am valid', 'also valid'])])
    table = util.Table.FromDdl(_DATABASE_DDL, 'queryTest')
    self.assertEqual(data, util.ValidateArrayInput(table, data))

  def testInvalidArrayInput(self):
    data = OrderedDict([('id', '1'), ('name', 'Cooper Dogerson'),
                        ('arr', '[invalid]')])
    table = util.Table.FromDdl(_DATABASE_DDL, 'queryTest')
    error_message = re.escape(
        'Column name [arr] has an invalid array input: [invalid]. '
        '`--flags-file` should be used to specify array values.')
    with self.assertRaisesRegex(util.InvalidArrayInputError, error_message):
      util.ValidateArrayInput(table, data)
