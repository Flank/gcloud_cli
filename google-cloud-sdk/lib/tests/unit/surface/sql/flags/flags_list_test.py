# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests that exercise operations listing and executing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseFlagsListSqlTest(object):

  def _SetUpFlagsNoFilter(self):
    self.mocked_client.flags.List.Expect(
        self.messages.SqlFlagsListRequest(),
        self.messages.FlagsListResponse(
            items=[
                self.messages.Flag(
                    allowedStringValues=[
                        'TABLE',
                        'NONE',
                    ],
                    appliesTo=[
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_6,
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_7,
                    ],
                    kind='sql#flag',
                    maxValue=None,
                    minValue=None,
                    name='log_output',
                    type=self.messages.Flag.TypeValueValuesEnum.STRING,
                ),
                self.messages.Flag(
                    allowedStringValues=[
                        'CRC32',
                        'NONE',
                    ],
                    appliesTo=[
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_7,
                    ],
                    kind='sql#flag',
                    maxValue=None,
                    minValue=None,
                    name='binlog_checksum',
                    type=self.messages.Flag.TypeValueValuesEnum.STRING,
                ),
                self.messages.Flag(
                    allowedStringValues=[],
                    appliesTo=[
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_6,
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_7,
                    ],
                    kind='sql#flag',
                    maxValue=None,
                    minValue=None,
                    name='general_log',
                    type=self.messages.Flag.TypeValueValuesEnum.BOOLEAN,
                ),
                self.messages.Flag(
                    allowedStringValues=[
                        'ALLOW_INVALID_DATES',
                        'ANSI_QUOTES',
                        'ERROR_FOR_DIVISION_BY_ZERO',
                        'HIGH_NOT_PRECEDENCE',
                        'IGNORE_SPACE',
                        'NO_AUTO_CREATE_USER',
                        'NO_AUTO_VALUE_ON_ZERO',
                        'NO_BACKSLASH_ESCAPES',
                        'NO_FIELD_OPTIONS',
                        'NO_KEY_OPTIONS',
                        'NO_TABLE_OPTIONS',
                        'NO_UNSIGNED_SUBTRACTION',
                        'NO_ZERO_DATE',
                        'NO_ZERO_IN_DATE',
                        'ONLY_FULL_GROUP_BY',
                        'PIPES_AS_CONCAT',
                        'REAL_AS_FLOAT',
                        'STRICT_ALL_TABLES',
                        'STRICT_TRANS_TABLES',
                        'ANSI',
                        'DB2',
                        'MAXDB',
                        'MSSQL',
                        'MYSQL323',
                        'MYSQL40',
                        'ORACLE',
                        'POSTGRESQL',
                        'TRADITIONAL',
                    ],
                    appliesTo=[
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_6,
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_7,
                    ],
                    kind='sql#flag',
                    maxValue=None,
                    minValue=None,
                    name='sql_mode',
                    type=self.messages.Flag.TypeValueValuesEnum.STRING,
                ),
            ],
            kind='sql#flagsList',
        ))

  def testFlagsList(self):
    self._SetUpFlagsNoFilter()
    self.Run('sql flags list')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME                             TYPE                   DATABASE_VERSION    ALLOWED_VALUES
log_output                       STRING                 MYSQL_5_6,MYSQL_5_7 TABLE,NONE
binlog_checksum                  STRING                 MYSQL_5_7           CRC32,NONE
general_log                      BOOLEAN                MYSQL_5_6,MYSQL_5_7
sql_mode                         STRING                 MYSQL_5_6,MYSQL_5_7 ALLOW_INVALID_DATES,ANSI_QUOTES,ERROR_FOR_DIVISION_BY_ZERO,HIGH_NOT_PRECEDENCE,IGNORE_SPACE,NO_AUTO_CREATE_USER,NO_AUTO_VALUE_ON_ZERO,NO_BACKSLASH_ESCAPES,NO_FIELD_OPTIONS,NO_KEY_OPTIONS,NO_TABLE_OPTIONS,NO_UNSIGNED_SUBTRACTION,NO_ZERO_DATE,NO_ZERO_IN_DATE,ONLY_FULL_GROUP_BY,PIPES_AS_CONCAT,REAL_AS_FLOAT,STRICT_ALL_TABLES,STRICT_TRANS_TABLES,ANSI,DB2,MAXDB,MSSQL,MYSQL323,MYSQL40,ORACLE,POSTGRESQL,TRADITIONAL
""",
        normalize_space=True)

  def _SetUpFlagsDatabaseVersionFilter(self):
    self.mocked_client.flags.List.Expect(
        self.messages.SqlFlagsListRequest(databaseVersion='MYSQL_5_6'),
        self.messages.FlagsListResponse(
            items=[
                self.messages.Flag(
                    allowedStringValues=[
                        'TABLE',
                        'NONE',
                    ],
                    appliesTo=[
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_6,
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_7,
                    ],
                    kind='sql#flag',
                    maxValue=None,
                    minValue=None,
                    name='log_output',
                    type=self.messages.Flag.TypeValueValuesEnum.STRING,
                ),
                self.messages.Flag(
                    allowedStringValues=[],
                    appliesTo=[
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_6,
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_7,
                    ],
                    kind='sql#flag',
                    maxValue=None,
                    minValue=None,
                    name='general_log',
                    type=self.messages.Flag.TypeValueValuesEnum.BOOLEAN,
                ),
                self.messages.Flag(
                    allowedStringValues=[
                        'ALLOW_INVALID_DATES',
                        'ANSI_QUOTES',
                        'ERROR_FOR_DIVISION_BY_ZERO',
                        'HIGH_NOT_PRECEDENCE',
                        'IGNORE_SPACE',
                        'NO_AUTO_CREATE_USER',
                        'NO_AUTO_VALUE_ON_ZERO',
                        'NO_BACKSLASH_ESCAPES',
                        'NO_FIELD_OPTIONS',
                        'NO_KEY_OPTIONS',
                        'NO_TABLE_OPTIONS',
                        'NO_UNSIGNED_SUBTRACTION',
                        'NO_ZERO_DATE',
                        'NO_ZERO_IN_DATE',
                        'ONLY_FULL_GROUP_BY',
                        'PIPES_AS_CONCAT',
                        'REAL_AS_FLOAT',
                        'STRICT_ALL_TABLES',
                        'STRICT_TRANS_TABLES',
                        'ANSI',
                        'DB2',
                        'MAXDB',
                        'MSSQL',
                        'MYSQL323',
                        'MYSQL40',
                        'ORACLE',
                        'POSTGRESQL',
                        'TRADITIONAL',
                    ],
                    appliesTo=[
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_6,
                        self.messages.Flag.AppliesToValueListEntryValuesEnum
                        .MYSQL_5_7,
                    ],
                    kind='sql#flag',
                    maxValue=None,
                    minValue=None,
                    name='sql_mode',
                    type=self.messages.Flag.TypeValueValuesEnum.STRING,
                ),
            ],
            kind='sql#flagsList',
        ))

  def testFlagsListFilterDatabaseVersion(self):
    self._SetUpFlagsDatabaseVersionFilter()
    self.Run('sql flags list --database-version=MYSQL_5_6')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME                             TYPE                   DATABASE_VERSION    ALLOWED_VALUES
log_output                       STRING                 MYSQL_5_6,MYSQL_5_7 TABLE,NONE
general_log                      BOOLEAN                MYSQL_5_6,MYSQL_5_7
sql_mode                         STRING                 MYSQL_5_6,MYSQL_5_7 ALLOW_INVALID_DATES,ANSI_QUOTES,ERROR_FOR_DIVISION_BY_ZERO,HIGH_NOT_PRECEDENCE,IGNORE_SPACE,NO_AUTO_CREATE_USER,NO_AUTO_VALUE_ON_ZERO,NO_BACKSLASH_ESCAPES,NO_FIELD_OPTIONS,NO_KEY_OPTIONS,NO_TABLE_OPTIONS,NO_UNSIGNED_SUBTRACTION,NO_ZERO_DATE,NO_ZERO_IN_DATE,ONLY_FULL_GROUP_BY,PIPES_AS_CONCAT,REAL_AS_FLOAT,STRICT_ALL_TABLES,STRICT_TRANS_TABLES,ANSI,DB2,MAXDB,MSSQL,MYSQL323,MYSQL40,ORACLE,POSTGRESQL,TRADITIONAL
""",
        normalize_space=True)


class FlagsListSqlGATest(_BaseFlagsListSqlTest, base.SqlMockTestGA):
  pass


class FlagsListSqlBetaTest(_BaseFlagsListSqlTest, base.SqlMockTestBeta):
  pass


class FlagsListSqlAlphaTest(_BaseFlagsListSqlTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
