# Copyright 2015 Google Inc. All Rights Reserved.
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

from tests.lib import test_case
from tests.lib.surface.sql import base


class FlagsListsTest(base.SqlMockTestBeta):

  def _setUpFlagsNoFilter(self):
    self.mocked_client.flags.List.Expect(
        self.messages.SqlFlagsListRequest(),
        self.messages.FlagsListResponse(
            items=[
                self.messages.Flag(
                    allowedStringValues=[
                        u'TABLE',
                        u'NONE',
                    ],
                    appliesTo=[
                        u'MYSQL_5_5',
                        u'MYSQL_5_6',
                    ],
                    kind=u'sql#flag',
                    maxValue=None,
                    minValue=None,
                    name=u'log_output',
                    type=u'STRING',),
                self.messages.Flag(
                    allowedStringValues=[
                        u'CRC32',
                        u'NONE',
                    ],
                    appliesTo=[
                        u'MYSQL_5_6',
                    ],
                    kind=u'sql#flag',
                    maxValue=None,
                    minValue=None,
                    name=u'binlog_checksum',
                    type=u'STRING',),
                self.messages.Flag(
                    allowedStringValues=[],
                    appliesTo=[
                        u'MYSQL_5_5',
                        u'MYSQL_5_6',
                    ],
                    kind=u'sql#flag',
                    maxValue=None,
                    minValue=None,
                    name=u'general_log',
                    type=u'BOOLEAN',),
                self.messages.Flag(
                    allowedStringValues=[
                        u'ALLOW_INVALID_DATES',
                        u'ANSI_QUOTES',
                        u'ERROR_FOR_DIVISION_BY_ZERO',
                        u'HIGH_NOT_PRECEDENCE',
                        u'IGNORE_SPACE',
                        u'NO_AUTO_CREATE_USER',
                        u'NO_AUTO_VALUE_ON_ZERO',
                        u'NO_BACKSLASH_ESCAPES',
                        u'NO_FIELD_OPTIONS',
                        u'NO_KEY_OPTIONS',
                        u'NO_TABLE_OPTIONS',
                        u'NO_UNSIGNED_SUBTRACTION',
                        u'NO_ZERO_DATE',
                        u'NO_ZERO_IN_DATE',
                        u'ONLY_FULL_GROUP_BY',
                        u'PIPES_AS_CONCAT',
                        u'REAL_AS_FLOAT',
                        u'STRICT_ALL_TABLES',
                        u'STRICT_TRANS_TABLES',
                        u'ANSI',
                        u'DB2',
                        u'MAXDB',
                        u'MSSQL',
                        u'MYSQL323',
                        u'MYSQL40',
                        u'ORACLE',
                        u'POSTGRESQL',
                        u'TRADITIONAL',
                    ],
                    appliesTo=[
                        u'MYSQL_5_5',
                        u'MYSQL_5_6',
                    ],
                    kind=u'sql#flag',
                    maxValue=None,
                    minValue=None,
                    name=u'sql_mode',
                    type=u'STRING',),
            ],
            kind=u'sql#flagsList',))

  def testFlagsList(self):
    self._setUpFlagsNoFilter()
    self.Run('sql flags list')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME                             TYPE                   DATABASE_VERSION    ALLOWED_VALUES
log_output                       STRING                 MYSQL_5_5,MYSQL_5_6 TABLE,NONE
binlog_checksum                  STRING                 MYSQL_5_6           CRC32,NONE
general_log                      BOOLEAN                MYSQL_5_5,MYSQL_5_6
sql_mode                         STRING                 MYSQL_5_5,MYSQL_5_6 ALLOW_INVALID_DATES,ANSI_QUOTES,ERROR_FOR_DIVISION_BY_ZERO,HIGH_NOT_PRECEDENCE,IGNORE_SPACE,NO_AUTO_CREATE_USER,NO_AUTO_VALUE_ON_ZERO,NO_BACKSLASH_ESCAPES,NO_FIELD_OPTIONS,NO_KEY_OPTIONS,NO_TABLE_OPTIONS,NO_UNSIGNED_SUBTRACTION,NO_ZERO_DATE,NO_ZERO_IN_DATE,ONLY_FULL_GROUP_BY,PIPES_AS_CONCAT,REAL_AS_FLOAT,STRICT_ALL_TABLES,STRICT_TRANS_TABLES,ANSI,DB2,MAXDB,MSSQL,MYSQL323,MYSQL40,ORACLE,POSTGRESQL,TRADITIONAL
""",
        normalize_space=True)

  def _setUpFlagsDatabaseVersionFilter(self):
    self.mocked_client.flags.List.Expect(
        self.messages.SqlFlagsListRequest(databaseVersion=u'MYSQL_5_5'),
        self.messages.FlagsListResponse(
            items=[
                self.messages.Flag(
                    allowedStringValues=[
                        u'TABLE',
                        u'NONE',
                    ],
                    appliesTo=[
                        u'MYSQL_5_5',
                        u'MYSQL_5_6',
                    ],
                    kind=u'sql#flag',
                    maxValue=None,
                    minValue=None,
                    name=u'log_output',
                    type=u'STRING',),
                self.messages.Flag(
                    allowedStringValues=[],
                    appliesTo=[
                        u'MYSQL_5_5',
                        u'MYSQL_5_6',
                    ],
                    kind=u'sql#flag',
                    maxValue=None,
                    minValue=None,
                    name=u'general_log',
                    type=u'BOOLEAN',),
                self.messages.Flag(
                    allowedStringValues=[
                        u'ALLOW_INVALID_DATES',
                        u'ANSI_QUOTES',
                        u'ERROR_FOR_DIVISION_BY_ZERO',
                        u'HIGH_NOT_PRECEDENCE',
                        u'IGNORE_SPACE',
                        u'NO_AUTO_CREATE_USER',
                        u'NO_AUTO_VALUE_ON_ZERO',
                        u'NO_BACKSLASH_ESCAPES',
                        u'NO_FIELD_OPTIONS',
                        u'NO_KEY_OPTIONS',
                        u'NO_TABLE_OPTIONS',
                        u'NO_UNSIGNED_SUBTRACTION',
                        u'NO_ZERO_DATE',
                        u'NO_ZERO_IN_DATE',
                        u'ONLY_FULL_GROUP_BY',
                        u'PIPES_AS_CONCAT',
                        u'REAL_AS_FLOAT',
                        u'STRICT_ALL_TABLES',
                        u'STRICT_TRANS_TABLES',
                        u'ANSI',
                        u'DB2',
                        u'MAXDB',
                        u'MSSQL',
                        u'MYSQL323',
                        u'MYSQL40',
                        u'ORACLE',
                        u'POSTGRESQL',
                        u'TRADITIONAL',
                    ],
                    appliesTo=[
                        u'MYSQL_5_5',
                        u'MYSQL_5_6',
                    ],
                    kind=u'sql#flag',
                    maxValue=None,
                    minValue=None,
                    name=u'sql_mode',
                    type=u'STRING',),
            ],
            kind=u'sql#flagsList',))

  def testFlagsListFilterDatabaseVersion(self):
    self._setUpFlagsDatabaseVersionFilter()
    self.Run('sql flags list --database-version=MYSQL_5_5')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME                             TYPE                   DATABASE_VERSION    ALLOWED_VALUES
log_output                       STRING                 MYSQL_5_5,MYSQL_5_6 TABLE,NONE
general_log                      BOOLEAN                MYSQL_5_5,MYSQL_5_6
sql_mode                         STRING                 MYSQL_5_5,MYSQL_5_6 ALLOW_INVALID_DATES,ANSI_QUOTES,ERROR_FOR_DIVISION_BY_ZERO,HIGH_NOT_PRECEDENCE,IGNORE_SPACE,NO_AUTO_CREATE_USER,NO_AUTO_VALUE_ON_ZERO,NO_BACKSLASH_ESCAPES,NO_FIELD_OPTIONS,NO_KEY_OPTIONS,NO_TABLE_OPTIONS,NO_UNSIGNED_SUBTRACTION,NO_ZERO_DATE,NO_ZERO_IN_DATE,ONLY_FULL_GROUP_BY,PIPES_AS_CONCAT,REAL_AS_FLOAT,STRICT_ALL_TABLES,STRICT_TRANS_TABLES,ANSI,DB2,MAXDB,MSSQL,MYSQL323,MYSQL40,ORACLE,POSTGRESQL,TRADITIONAL
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
