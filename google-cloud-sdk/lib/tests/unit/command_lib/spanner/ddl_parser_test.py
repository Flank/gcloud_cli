# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for spanner ddl parser module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.spanner import ddl_parser
from tests.lib import completer_test_base
from tests.lib.surface.spanner import base


class DDLParserTest(base.SpannerTestBase):

  def testDDLParser(self):
    # Each test case contains an input ddl and a list of expected statements.
    # If no expected statements is present, the ddl is not expected to change.
    ddl_test_cases = [
        [
            'CREATE TABLE T1;',
            ['CREATE TABLE T1'],
        ],
        [
            'CREATE TABLE T1;CREATE TABLE T2',
            ['CREATE TABLE T1', 'CREATE TABLE T2'],
        ],
        [
            '--this is a test table\nCREATE TABLE T1;',
            ['\nCREATE TABLE T1'],
        ],
        [
            'CREATE TABLE T1(\n--comment \n);CREATE T2--this is a test table\n',
            ['CREATE TABLE T1(\n\n)', 'CREATE T2\n'],
        ],
        [
            'CREATE--comment with no newline',
            ['CREATE'],
        ],
        [
            'CREATE--comment with ;no newline',
            ['CREATE'],
        ],
        # Double quote.
        [
            'CREATE "plain double quote;"',
        ],
        [
            'CREATE--\'abc\'"abc\'" + \';--"""abc""" \'\'\'abc\'\'\' ',
            ['CREATE'],
        ],
        [
            'CREATE "\';"',
        ],
        [
            'CREATE "-- comment in double quote;"',
        ],
        [
            'CREATE "-- comment in double quote;"--comment;',
            ['CREATE "-- comment in double quote;"'],
        ],
        # Single quote.
        [
            "CREATE 'plain single quote;'",
        ],
        [
            "CREATE '\";'",
        ],
        [
            "CREATE '-- comment in single quote;'",
        ],
        [
            "CREATE '-- comment in single quote;'--comment;",
            ["CREATE '-- comment in single quote;'"],
        ],
        # Triple double quote.
        [
            'CREATE """basic triple\n double quote;\\""""',
        ],
        [
            'CREATE """--com\n \'--single quote\' "--double quote;";"""--comment',
            ['CREATE """--com\n \'--single quote\' "--double quote;";"""'],
        ],
        # Triple single quote.
        [
            "CREATE '''basic\n triple single quote\\''''",
        ],
        [
            "CREATE '''--comment\n '--single quote' \"--double quote\" "
            "\"\"\"triple double\"\"\" '''-- comment",
            [
                "CREATE '''--comment\n '--single quote' \"--double quote\" "
                "\"\"\"triple double\"\"\" '''"
            ],
        ],
        # Comment within quote.
        [
            "CREATE '''--com\n '--single quote' \"--double quote\" "
            "\"\"\"triple double\"\"\" '''-- com",
            [
                "CREATE '''--com\n '--single quote' \"--double quote\" "
                "\"\"\"triple double\"\"\" '''"
            ],
        ],
        # Single quote raw string, bytes, raw bytes.
        [
            "CREATE r'str;\"a\"--com' b'str;--com' rb'str;--com'",
        ],
        [
            "CREATE R'str;\"a\"--com' B'str;--com' RB'str;--com'",
        ],
        # Double quote raw string, bytes, raw bytes.
        [
            'CREATE r"str;\'a\'--com" b"str;--com" rb"str;--com"',
        ],
        [
            'CREATE R"str;\'a\'--com" B"str;--com" RB"str;--com"',
        ],
        # Triple single quote raw string, bytes, raw bytes.
        [
            "CREATE r'''str;\"a\"--com''' b'''str;--com''' rb'''str;--com'''",
        ],
        [
            "CREATE R'''str;\"a\"--com''' B'''str;--com''' RB'''str;--com'''",
        ],
        # Triple double quote raw string, bytes, raw bytes.
        [
            'CREATE r"""str;\'a\'--com""" b"""str;--com""" rb"""str;--com"""',
        ],
        [
            'CREATE R"""str;\'a\'--com""" B"""str;--com""" RB"""str;--com"""',
        ],
        # Corner cases in raw string and bytes.
        [
            'CREATE r"\\"" rb"\\""',
        ],
        # In case of "\\" if \\ is not treated as escape sequence, \"
        # will be treated as escape sequence, leaving the string unclosed..
        [
            'CREATE "\\\\" ',
        ],
        [
            """SELECT
      'abc',
      'a\\b',
      "def",
      '\\\\x53',
      '\\\\u1235',
      "\\\\U00012346" """
        ],
        [
            """SELECT
      \"""line1\""",
      '''line1''',
      \"\"""a" \""",
      '''abc'\\\\''def''',
      '''abc''\\\\'def''',
      \"""abc"\\\\""def\""",
      \"""abc""\\\\"def\""",
      \"""line1
    line2
    line3\""",
      '--------------------------',
      '''line1
    line2
    line3''',
      \"""a'''a'''a\""",
      '''a\"""a\"""a''' """
        ],
        [
            """SELECT
      b'abc',
      B"def",
      B'"',
      B"'",
      B'`',
      B"`",
      b\"""abc\""",
      B'''def''',
      B\"""'''a'''\""",
      b'''"a"''',
      B'''`''',
      B\"""`\""",
      b'''...
                 ...''',
      b\"""...
                 ...\""" """
        ],
        [
            """SELECT
      r"1",
      r"\\x53",
      r"\\x123",
      r'\\001',
      r'a\\444A',
      r'a\\e',
      r'\\ea',
      r"\\U1234",
      R"\\u",
      r'\\xc2\\\\',
      r'|\\xc2|\\\\',
      r'f\\(abc,(.*),def\\?',
      r'''...
          ...''',
      r\"""'''\\
          '''\""",
      r'''...
          ...''',
      r\"""'''\\
          '''\""" """
        ],
        [
            """SELECT
      rb"1",
      br"\\x53",
      rb"\\x123",
      br'\\001',
      rb'a\\444A',
      br'a\\e',
      rb'\\ea',
      br"\\U1234",
      RB"\\u",
      rb'\\xc2\\\\',
      BR'|\\xc2|\\\\',
      rb'f\\(abc,(.*),def\\?'
      br'''\"""
           \"""''',
      br\"""...\\
           ...\""",
      br'''\"""
           \"""''',
      br\"""...\\
           ...\""" """
        ],
        [
            'SELECT 1 as `ab` `\"a\"` `\'a\'` `\\\\` `\\`` `--alias` --comment',
            ['SELECT 1 as `ab` `\"a\"` `\'a\'` `\\\\` `\\`` `--alias` ']
        ],
    ]

    for test_case in ddl_test_cases:
      test_ddl = test_case[0]
      expected = [test_ddl]
      if len(test_case) == 2:
        expected = test_case[1]
      self.assertEqual(expected, ddl_parser.PreprocessDDLWithParser(test_ddl))

    # Unclosed strings.
    # These show cases that a single unclosed string could mess up the whole
    # ddl splitting.
    unclosed_cases = [
        'CREATE "str; CREATE',
        "CREATE 'str; CREATE",
        'CREATE """str; CREATE',
        "CREATE '''str; CREATE",
        'CREATE `str; CREATE',
        'CREATE `str\\`; CREATE',
    ]
    for except_case in unclosed_cases:
      with self.assertRaises(ddl_parser.DDLSyntaxError):
        ddl_parser.PreprocessDDLWithParser(except_case)


if __name__ == '__main__':
  completer_test_base.main()
