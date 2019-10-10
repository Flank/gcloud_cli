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

"""Unit tests for the parser_extensions module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import cli
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.calliope import util as calliope_test_util
from tests.lib.parameterized_line_no import LabelLineNo as T

import mock
import six


class SpecifiedArgsTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()

  def testNoneSpecified(self):
    self.parser.parse_args()

  def testSpecifiedArgs(self):
    self.parser.add_argument(
        '--flag', default='DEFAULT-FLAG', help='Auxilio aliis.')
    self.parser.add_argument(
        'positional', nargs='?', default='DEFAULT-POSITIONAL',
        help='Auxilio aliis.')

    args = self.parser.parse_args([])
    self.assertEqual('DEFAULT-FLAG', args.flag)
    self.assertEqual('DEFAULT-POSITIONAL', args.positional)
    self.assertEqual({}, args._specified_args)
    if not args.IsSpecified('flag'):
      args.flag = 'RUN-FLAG'
    if not args.IsSpecified('positional'):
      args.positional = 'RUN-POSITIONAL'
    self.assertEqual('RUN-FLAG', args.flag)
    self.assertEqual('RUN-POSITIONAL', args.positional)

    args = self.parser.parse_args(['--flag=CMD-FLAG'])
    self.assertEqual('CMD-FLAG', args.flag)
    self.assertEqual('DEFAULT-POSITIONAL', args.positional)
    self.assertEqual({'flag': '--flag'}, args._specified_args)
    if not args.IsSpecified('flag'):
      args.flag = 'RUN-FLAG'
    if not args.IsSpecified('positional'):
      args.positional = 'RUN-POSITIONAL'
    self.assertEqual('CMD-FLAG', args.flag)
    self.assertEqual('RUN-POSITIONAL', args.positional)

    args = self.parser.parse_args(['CMD-POSITIONAL'])
    self.assertEqual('DEFAULT-FLAG', args.flag)
    self.assertEqual('CMD-POSITIONAL', args.positional)
    self.assertEqual({'positional': 'POSITIONAL'}, args._specified_args)
    if not args.IsSpecified('flag'):
      args.flag = 'RUN-FLAG'
    if not args.IsSpecified('positional'):
      args.positional = 'RUN-POSITIONAL'
    self.assertEqual('RUN-FLAG', args.flag)
    self.assertEqual('CMD-POSITIONAL', args.positional)

    args = self.parser.parse_args(['--flag=CMD-FLAG', 'CMD-POSITIONAL'])
    self.assertEqual('CMD-FLAG', args.flag)
    self.assertEqual('CMD-POSITIONAL', args.positional)
    self.assertEqual({'flag': '--flag', 'positional': 'POSITIONAL'},
                     args._specified_args)
    if not args.IsSpecified('flag'):
      args.flag = 'RUN-FLAG'
    if not args.IsSpecified('positional'):
      args.positional = 'RUN-POSITIONAL'
    self.assertEqual('CMD-FLAG', args.flag)
    self.assertEqual('CMD-POSITIONAL', args.positional)

  def testSpecifiedArgsPositionalZeroOrMore(self):
    self.parser.add_argument(
        'positional', nargs='*', default=['DEFAULT-POSITIONAL'],
        help='Auxilio aliis.')

    args = self.parser.parse_args([])
    self.assertEqual(['DEFAULT-POSITIONAL'], args.positional)
    self.assertEqual({}, args._specified_args)
    if not args.IsSpecified('positional'):
      args.positional = ['RUN-POSITIONAL']
    self.assertEqual(['RUN-POSITIONAL'], args.positional)

    args = self.parser.parse_args(['CMD-POSITIONAL-1'])
    self.assertEqual(['CMD-POSITIONAL-1'], args.positional)
    self.assertEqual({'positional': 'POSITIONAL:1'}, args._specified_args)
    if not args.IsSpecified('positional'):
      args.positional = ['RUN-POSITIONAL']
    self.assertEqual(['CMD-POSITIONAL-1'], args.positional)

    args = self.parser.parse_args(['CMD-POSITIONAL-1', 'CMD-POSITIONAL-2'])
    self.assertEqual(['CMD-POSITIONAL-1', 'CMD-POSITIONAL-2'], args.positional)
    self.assertEqual({'positional': 'POSITIONAL:2'}, args._specified_args)
    if not args.IsSpecified('positional'):
      args.positional = ['RUN-POSITIONAL']
    self.assertEqual(['CMD-POSITIONAL-1', 'CMD-POSITIONAL-2'], args.positional)

  def testSetIfNotSpecifiedUnknown(self):
    args = self.parser.parse_args([])
    with self.AssertRaisesExceptionMatches(
        parser_errors.UnknownDestinationException,
        'No registered arg for destination [foo].'):
      args.IsSpecified('foo')

  def testMakeGetOrFail(self):
    self.parser.add_argument(
        '--default-flag', default='DEFAULT-FLAG', help='Auxilio aliis.')
    self.parser.add_argument('--special-flag', help='Auxilio aliis.')
    self.parser.add_argument('--helper-flag', help='Auxilio aliis.')
    self.parser.add_argument(
        'positional', nargs='?', default='DEFAULT-POSITIONAL',
        help='Auxilio aliis.')

    args = self.parser.parse_args(['--special-flag', 'value'])

    self.assertFalse(args.IsSpecified('default_flag'))
    flag_func = args.MakeGetOrRaise('default_flag')
    self.assertEqual('DEFAULT-FLAG', flag_func())

    self.assertTrue(args.IsSpecified('special_flag'))
    flag_func = args.MakeGetOrRaise('special_flag')
    self.assertEqual('value', flag_func())

    self.assertFalse(args.IsSpecified('helper_flag'))
    helper_flag_func = args.MakeGetOrRaise('--helper_flag')
    with self.AssertRaisesExceptionMatches(
        parser_errors.RequiredError,
        'argument --helper_flag: Must be specified.'):
      helper_flag_func()

  def testAddGroupInvalidKwargs(self):
    self.parser.add_group(help='Test group.')

    with self.AssertRaisesExceptionMatches(
        parser_errors.ArgumentException,
        'parser.add_group(): description or title kwargs not supported '
        '-- use help=... instead.'):
      self.parser.add_group(title='Invalid title.')

    with self.AssertRaisesExceptionMatches(
        parser_errors.ArgumentException,
        'parser.add_group(): description or title kwargs not supported '
        '-- use help=... instead.'):
      self.parser.add_group(description='Invalid description.')

  def testConcepts(self):
    handler = mock.MagicMock()
    self.parser.add_concepts(handler)
    with self.assertRaisesRegex(AttributeError, 'two runtime handlers'):
      self.parser.add_concepts(handler)
    args = self.parser.parse_args([])
    concepts = args.CONCEPTS
    # Assert the handler was returned by CONCEPTS.
    self.assertEqual(handler, concepts)
    # Assert the parsed namespace was correctly added to the concept handler.
    self.assertEqual(args, concepts.parsed_args)

  def testRemainderRequiredOmitted(self):
    self.parser.add_argument('--project', help='The project.')
    self.parser.add_argument('host', help='The host.')
    self.parser.add_argument('passthrough', nargs=argparse.REMAINDER,
                             help='The passthrough args.')

    with self.AssertRaisesArgumentErrorMatches(
        'argument HOST: Must be specified.'):
      self.parser.parse_args(['--', 'echo', 'hey'])

    with self.AssertRaisesArgumentErrorMatches(
        'argument HOST: Must be specified.'):
      self.parser.parse_args(['--project', 'proj', '--', 'echo', 'hey'])


class OriginalArgsTest(cli_test_base.CliTestBase):

  def SetUp(self):
    command = calliope_test_util.MockCommand('test')
    self.parser = parser_extensions.ArgumentParser(calliope_command=command)

  def testOriginalArgsSetAndCleared(self):
    original_args = ['original', 'args']
    self.parser._SaveOriginalArgs(original_args)
    self.assertEqual(original_args, self.parser._args)
    self.parser._ClearOriginalArgs()
    self.assertEqual(None, self.parser._args)


class SpecifiedGroupsTest(cli_test_base.CliTestBase, parameterized.TestCase):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()

  @parameterized.named_parameters(
      T(
          'None',
          [],
          None,
      ),
      T(
          'Inner_1',
          ['--inner-1'],
          'argument --outer-1 --outer-2: Must be specified.',
      ),
      T(
          'Inner_2',
          ['--inner-2'],
          'argument --outer-1 --outer-2: Must be specified.',
      ),
      T(
          'Inner_12',
          ['--inner-1', '--inner-2'],
          'argument --inner-1: At most one of (--inner-1 | --inner-2) '
          'may be specified.',
      ),
      T(
          'Outer_1',
          ['--outer-1'],
          'argument --outer-2 (--inner-1 | --inner-2): Must be specified.',
      ),
      T(
          'Outer_1_Inner_1',
          ['--outer-1', '--inner-1'],
          'argument --outer-2: Must be specified.',
      ),
      T(
          'Outer_1_Inner_2',
          ['--outer-1', '--inner-2'],
          'argument --outer-2: Must be specified.',
      ),
      T(
          'Outer_1_Inner_12',
          ['--outer-1', '--inner-1', '--inner-2'],
          'argument --inner-1: At most one of (--inner-1 | --inner-2) '
          'may be specified.',
      ),
      T(
          'Outer_2',
          ['--outer-2'],
          'argument --outer-1 (--inner-1 | --inner-2): Must be specified.',
      ),
      T(
          'Outer_2_Inner_1',
          ['--outer-2', '--inner-1'],
          'argument --outer-1: Must be specified.',
      ),
      T(
          'Outer_2_Inner_2',
          ['--outer-2', '--inner-2'],
          'argument --outer-1: Must be specified.',
      ),
      T(
          'Outer_2_Inner_12',
          ['--outer-2', '--inner-1', '--inner-2'],
          'argument --inner-1: At most one of (--inner-1 | --inner-2) '
          'may be specified.',
      ),
      T(
          'Outer_12',
          ['--outer-1', '--outer-2'],
          'argument (--inner-1 | --inner-2): Must be specified.',
      ),
      T(
          'Outer_12_Inner_1',
          ['--outer-1', '--outer-2', '--inner-1'],
          None,
      ),
      T(
          'Outer_12_Inner_2',
          ['--outer-1', '--outer-2', '--inner-2'],
          None,
      ),
      T(
          'Outer_12_Inner_12',
          ['--outer-1', '--outer-2', '--inner-1', '--inner-2'],
          'argument --inner-1: At most one of (--inner-1 | --inner-2) '
          'may be specified.',
      ),
  )
  def testRequiredInOptionalGroup(self, args, error):
    outer_group = self.parser.add_group(
        required=False, mutex=False, help='Outer.')
    outer_group.add_argument(
        '--outer-1', action='store_true', required=True, help='Outer 1.')
    outer_group.add_argument(
        '--outer-2', action='store_true', required=True, help='Outer 1.')
    inner_group = outer_group.add_group(
        required=True, mutex=True, help='Inner.')
    inner_group.add_argument(
        '--inner-1', action='store_true', required=False, help='Inner 1.')
    inner_group.add_argument(
        '--inner-2', action='store_true', required=False, help='Inner 1.')

    if error:
      with self.AssertRaisesArgumentErrorMatches(error):
        self.parser.parse_args(args)
    else:
      self.parser.parse_args(args)

  @parameterized.named_parameters(
      T(
          'None',
          [],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          'Inner_1',
          ['--inner-1'],
          'argument --outer-1 --outer-2: Must be specified.',
      ),
      T(
          'Inner_2',
          ['--inner-2'],
          'argument --outer-1 --outer-2: Must be specified.',
      ),
      T(
          'Inner_12',
          ['--inner-1', '--inner-2'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          'Outer_1',
          ['--outer-1'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          'Outer_1_Inner_1',
          ['--outer-1', '--inner-1'],
          'argument --outer-2: Must be specified.',
      ),
      T(
          'Outer_1_Inner_2',
          ['--outer-1', '--inner-2'],
          'argument --outer-2: Must be specified.',
      ),
      T(
          'Outer_1_Inner_12',
          ['--outer-1', '--inner-1', '--inner-2'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          'Outer_2',
          ['--outer-2'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          'Outer_2_Inner_1',
          ['--outer-2', '--inner-1'],
          'argument --outer-1: Must be specified.',
      ),
      T(
          'Outer_2_Inner_2',
          ['--outer-2', '--inner-2'],
          'argument --outer-1: Must be specified.',
      ),
      T(
          'Outer_2_Inner_12',
          ['--outer-2', '--inner-1', '--inner-2'],
          'argument --inner-1: Exactly one of (--inner-1 | --inner-2) '
          'must be specified.',
      ),
      T(
          'Outer_1_Inner_2',
          ['--outer-1', '--outer-2'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          'Outer_12_Inner_1',
          ['--outer-1', '--outer-2', '--inner-1'],
          None,
      ),
      T(
          'Outer_12_Inner_2',
          ['--outer-1', '--outer-2', '--inner-2'],
          None,
      ),
      T(
          'Outer_12_Inner_12',
          ['--outer-1', '--outer-2', '--inner-1', '--inner-2'],
          'argument --inner-1: Exactly one of (--inner-1 | --inner-2) '
          'must be specified.',
      ),
  )
  def testRequiredInRequiredGroup(self, args, error):
    # required=True is the only change from testRequiredInOptionalGroup.
    outer_group = self.parser.add_group(
        required=True, mutex=False, help='Outer.')
    outer_group.add_argument(
        '--outer-1', action='store_true', required=True, help='Outer 1.')
    outer_group.add_argument(
        '--outer-2', action='store_true', required=True, help='Outer 2.')
    inner_group = outer_group.add_group(
        required=True, mutex=True, help='Inner.')
    inner_group.add_argument(
        '--inner-1', action='store_true', required=False, help='Inner 1.')
    inner_group.add_argument(
        '--inner-2', action='store_true', required=False, help='Inner 2.')

    if error:
      with self.AssertRaisesArgumentErrorMatches(error):
        self.parser.parse_args(args)
    else:
      self.parser.parse_args(args)


_FLAGS_1 = """\
--boolean:
--string:
  xyz
--integer:
  123
--floating:
  987.321
"""

_FLAGS_2 = """\
--foo:
--bar:
  huh
"""

_FLAGS_3 = """\
--unknown:
  1
--oops:
  rats
"""

_FLAGS_4 = """\
--this:
  mine
--or-that:
  no-its-mine
"""

_FLAGS_5 = """\
--boolean:
--string:
  xyz
--flags-file: flags-2.yaml
"""

_FLAGS_6 = """\
--integer:
  123
--floating:
  987.321
"""

_FLAGS_7 = """\
--boolean:
--flags-file: flags-1.yaml
"""

_FLAGS_8 = """\
--boolean:
--string:
  xyz
"""

_FLAGS_9 = """\
--flags-file:
  - flags-2.yaml
  - flags-3.yaml
"""

_FLAGS_10 = """\
- - --abc: xyz
"""

_FLAGS_11 = """\
- --integer: 123
  --floating: 456.789
- --integer: 321
"""


class FlagsFileTest(cli_test_base.CliTestBase, parameterized.TestCase):

  @parameterized.named_parameters(
      T(
          'Nothing',
          [],
          [],
          False,
          'DEFAULT-FLAG',
          0,
          -0.9,
      ),
      T(
          'NoFile',
          [],
          ['--boolean', '--string=abc', '--integer=456', '--floating=3.14'],
          True,
          'abc',
          456,
          3.14,
      ),
      T(
          'FileNoArgs',
          [_FLAGS_1],
          ['--flags-file=flags-1.yaml'],
          True,
          'xyz',
          123,
          987.321,
          argv=[
              '---flag-file-line-',
              '--boolean flags-1.yaml:2',
              '--boolean',
              '---flag-file-line-',
              '--string=xyz flags-1.yaml:3',
              '--string=xyz',
              '---flag-file-line-',
              '--integer=123 flags-1.yaml:5',
              '--integer=123',
              '---flag-file-line-',
              '--floating=987.321 flags-1.yaml:7',
              '--floating=987.321',
          ],
      ),
      T(
          'FileInFile',
          [_FLAGS_5, _FLAGS_6],
          ['--flags-file=flags-1.yaml'],
          True,
          'xyz',
          123,
          987.321,
          argv=[
              '---flag-file-line-',
              '--boolean flags-1.yaml:2',
              '--boolean',
              '---flag-file-line-',
              '--string=xyz flags-1.yaml:3',
              '--string=xyz',
              '---flag-file-line-',
              '--integer=123 flags-1.yaml:4;'
              'flags-2.yaml:2',
              '--integer=123',
              '---flag-file-line-',
              '--floating=987.321 flags-1.yaml:4;'
              'flags-2.yaml:4',
              '--floating=987.321'
          ],
      ),
      T(
          'FileInFileUnknown',
          [_FLAGS_5, _FLAGS_2],
          ['--flags-file=flags-1.yaml'],
          True,
          'xyz',
          123,
          987.321,
          argv=[
              '---flag-file-line-',
              '--boolean flags-1.yaml:2',
              '--boolean',
              '---flag-file-line-',
              '--string=xyz flags-1.yaml:3',
              '--string=xyz',
              '---flag-file-line-',
              '--foo flags-1.yaml:4;flags-2.yaml:2',
              '--foo',
              '---flag-file-line-',
              '--bar=huh flags-1.yaml:4;flags-2.yaml:3',
              '--bar=huh',
          ],
          exception=Exception,
          exception_regex=(r'unrecognized arguments:'
                           '\n'
                           r'  --foo \(flags-1.yaml:4;flags-2.yaml:2\)'
                           '\n'
                           r'  --bar=huh \(flags-1.yaml:4;flags-2.yaml:3\)'),
      ),
      T(
          'FileArgsWin',
          [_FLAGS_1],
          ['--flags-file=flags-1.yaml', '--string=abc', '--no-boolean'],
          False,
          'abc',
          123,
          987.321,
          argv=[
              '---flag-file-line-',
              '--boolean flags-1.yaml:2',
              '--boolean',
              '---flag-file-line-',
              '--string=xyz flags-1.yaml:3',
              '--string=xyz',
              '---flag-file-line-',
              '--integer=123 flags-1.yaml:5',
              '--integer=123',
              '---flag-file-line-',
              '--floating=987.321 flags-1.yaml:7',
              '--floating=987.321',
              '--string=abc',
              '--no-boolean',
          ],
      ),
      T(
          'FileReplacedByContent1',
          [_FLAGS_1],
          ['--string=abc', '--no-boolean', '--flags-file=flags-1.yaml'],
          True,
          'xyz',
          123,
          987.321,
          argv=[
              '--string=abc',
              '--no-boolean',
              '---flag-file-line-',
              '--boolean flags-1.yaml:2',
              '--boolean',
              '---flag-file-line-',
              '--string=xyz flags-1.yaml:3',
              '--string=xyz',
              '---flag-file-line-',
              '--integer=123 flags-1.yaml:5',
              '--integer=123',
              '---flag-file-line-',
              '--floating=987.321 flags-1.yaml:7',
              '--floating=987.321',
          ],
      ),
      T(
          'FileReplacedByContent2',
          [_FLAGS_1],
          ['--string=abc', '--flags-file=flags-1.yaml', '--no-boolean'],
          False,
          'xyz',
          123,
          987.321,
          argv=[
              '--string=abc',
              '---flag-file-line-',
              '--boolean flags-1.yaml:2',
              '--boolean',
              '---flag-file-line-',
              '--string=xyz flags-1.yaml:3',
              '--string=xyz',
              '---flag-file-line-',
              '--integer=123 flags-1.yaml:5',
              '--integer=123',
              '---flag-file-line-',
              '--floating=987.321 flags-1.yaml:7',
              '--floating=987.321',
              '--no-boolean',
          ],
      ),
      T(
          'FileUnknown_2',
          [_FLAGS_2],
          ['--flags-file=flags-1.yaml'],
          False,
          'abc',
          123,
          987.321,
          argv=[
              '---flag-file-line-',
              '--foo flags-1.yaml:2',
              '--foo',
              '---flag-file-line-',
              '--bar=huh flags-1.yaml:3',
              '--bar=huh',
          ],
          exception=Exception,
          exception_regex=(r'unrecognized arguments:'
                           '\n'
                           r'  --foo \(flags-1.yaml:2\)'
                           '\n'
                           r'  --bar=huh \(flags-1.yaml:3\)'),
      ),
      T(
          'FileUnknown_23',
          [_FLAGS_2, _FLAGS_3],
          ['--flags-file=flags-1.yaml', '--flags-file=flags-2.yaml'],
          False,
          'abc',
          123,
          987.321,
          argv=[
              '---flag-file-line-',
              '--foo flags-1.yaml:2',
              '--foo',
              '---flag-file-line-',
              '--bar=huh flags-1.yaml:3',
              '--bar=huh',
              '---flag-file-line-',
              '--unknown=1 flags-2.yaml:2',
              '--unknown=1',
              '---flag-file-line-',
              '--oops=rats flags-2.yaml:4',
              '--oops=rats',
          ],
          exception=Exception,
          exception_regex=(r'unrecognized arguments:'
                           '\n'
                           r'  --foo \(flags-1.yaml:2\)'
                           '\n'
                           r'  --bar=huh \(flags-1.yaml:3\)'
                           '\n'
                           r'  --unknown=1 \(flags-2.yaml:2\)'
                           '\n'
                           r'  --oops=rats \(flags-2.yaml:4\)'),
      ),
      T(
          'SelfRef',
          [_FLAGS_7],
          ['--flags-file=flags-1.yaml'],
          False,
          'abc',
          123,
          987.321,
          exception=parser_errors.ArgumentError,
          exception_regex=(r'--flags-file recursive reference '
                           r'\(flags-1.yaml:2\).'),
      ),
      T(
          'FileNotFound',
          [],
          ['--flags-file=flags-0.yaml'],
          False,
          'abc',
          123,
          987.321,
          exception=parser_errors.ArgumentError,
          exception_regex=(r'--flags-file \[flags-0.yaml\] not found.'),
      ),
      T(
          'Header',
          [_FLAGS_9, _FLAGS_6, _FLAGS_8],
          ['--flags-file=flags-1.yaml'],
          True,
          'xyz',
          123,
          987.321,
          argv=[
              '---flag-file-line-',
              '--integer=123 flags-1.yaml:2;flags-2.yaml:2',
              '--integer=123',
              '---flag-file-line-',
              '--floating=987.321 '
              'flags-1.yaml:2;flags-2.yaml:4',
              '--floating=987.321',
              '---flag-file-line-',
              '--boolean flags-1.yaml:2;flags-3.yaml:2',
              '--boolean',
              '---flag-file-line-',
              '--string=xyz flags-1.yaml:2;flags-3.yaml:3',
              '--string=xyz',
          ],
      ),
      T(
          'YamlGoodContentsBad',
          [_FLAGS_10],
          ['--flags-file=flags-1.yaml'],
          None,
          None,
          None,
          None,
          exception=parser_errors.ArgumentError,
          exception_regex=(r'flags-1.yaml:1: --flags-file file must contain a '
                           r'dictionary or list of dictionaries of flags.'),
      ),
      T(
          'RepeatedFlag',
          [_FLAGS_11],
          ['--flags-file=flags-1.yaml'],
          False,
          'DEFAULT-FLAG',
          321,
          456.789,
          argv=[
              '---flag-file-line-',
              '--integer=123 flags-1.yaml:1',
              '--integer=123',
              '---flag-file-line-',
              '--floating=456.789 flags-1.yaml:2',
              '--floating=456.789',
              '---flag-file-line-',
              '--integer=321 flags-1.yaml:3',
              '--integer=321',
          ],
      ),
  )
  def testApplyFlagsFile(self, contents, argv, boolean_value, string_value,
                         integer_value, floating_value, kwargs=None):

    if not kwargs:
      kwargs = {}
    expected_argv = kwargs.get('argv')
    exception = kwargs.get('exception')
    exception_regex = kwargs.get('exception_regex')

    parser = calliope_test_util.ArgumentParser()
    cli.FLAG_INTERNAL_FLAG_FILE_LINE.AddToParser(parser)
    parser.add_argument(
        '--boolean', action='store_true', help='Auxilio aliis I.')
    parser.add_argument(
        '--string', default='DEFAULT-FLAG', help='Auxilio aliis II.')
    parser.add_argument(
        '--integer', type=int, default=0, help='Auxilio aliis III.')
    parser.add_argument(
        '--floating', type=float, default=-0.9, help='Auxilio aliis IV.')

    with files.TemporaryDirectory(change_to=True):

      for index, content in enumerate(contents):
        name = 'flags-{}.yaml'.format(index + 1)
        files.WriteFileContents(name, content)

      if not exception:
        argv = cli._ApplyFlagsFile(argv)
        if expected_argv is not None:
          self.assertEqual(
              expected_argv,
              ['{} {}'.format(a.arg, six.text_type(a))
               if hasattr(a, 'arg') else a for a in argv])
        args = parser.parse_args(argv)
        self.assertEqual(boolean_value, args.boolean)
        self.assertEqual(string_value, args.string)
        self.assertEqual(integer_value, args.integer)
        self.assertEqual(floating_value, args.floating)
      elif not exception_regex:
        with self.assertRaises(exception):
          argv = cli._ApplyFlagsFile(argv)
          parser.parse_args(argv)
      else:
        with self.assertRaisesRegex(exception, exception_regex):
          argv = cli._ApplyFlagsFile(argv)
          parser.parse_args(argv)


class FlagsFileCommandTest(calliope_test_util.WithTestTool,
                           cli_test_base.CliTestBase,
                           sdk_test_base.WithOutputCapture,
                           parameterized.TestCase):

  @parameterized.named_parameters(
      T(
          'MinimalArgs',
          [],
          [
              '--or-that=maybe',
          ],
          out="""\
{
  "boolean": false,
  "dict": null,
  "floating": -0.9,
  "integer": 0,
  "list": null,
  "or_that": "maybe",
  "string": "DEFAULT-FLAG",
  "this": null
}
""",
          err='',
      ),
      T(
          'AllArgs',
          [],
          [
              '--boolean',
              '--string=abc',
              '--integer=123',
              '--floating=3.14',
              '--list=a,2,bcd,456',
              '--dict=abc=123,xyz=789',
              '--this=one',
          ],
          out="""\
{
  "boolean": true,
  "dict": {
    "abc": "123",
    "xyz": "789"
  },
  "floating": 3.14,
  "integer": 123,
  "list": [
    "a",
    "2",
    "bcd",
    "456"
  ],
  "or_that": null,
  "string": "abc",
  "this": "one"
}
""",
          err='',
      ),
      T(
          'Unknown_2',
          [_FLAGS_2],
          ['--flags-file=flags-1.yaml'],
          out='',
          exception=Exception,
          exception_regex=(r"unrecognized arguments:"
                           "\n"
                           r"  --foo \(flags-1.yaml:2\) "
                           r"\(did you mean '--format'\?\)"
                           "\n"
                           r"  --bar=huh \(flags-1.yaml:3\) "
                           r"\(did you mean '--uri'\?\)"),
      ),
      T(
          'Mutex_4',
          [_FLAGS_4],
          ['--flags-file=flags-1.yaml'],
          out='',
          exception=Exception,
          exception_regex=(r'argument --or-that=no-its-mine '
                           r'\(flags-1.yaml:4\): Exactly one of \(--or-that \| '
                           r'--this\) must be specified.'),
      ),
  )
  def testFlagsFile(self, contents, argv, kwargs=None):

    if not kwargs:
      kwargs = {}
    out = kwargs.get('out')
    err = kwargs.get('err')
    exception = kwargs.get('exception')
    exception_regex = kwargs.get('exception_regex')

    command = [
        'sdk7',
        'sdk',
        'flags-file',
        '--format=json(boolean,string,integer,floating,list,dict,this,or_that)',
    ] + argv

    with files.TemporaryDirectory(change_to=True):

      for index, content in enumerate(contents):
        name = 'flags-{}.yaml'.format(index + 1)
        files.WriteFileContents(name, content)

      if not exception:
        self.cli.Execute(command)
      elif not exception_regex:
        with self.assertRaises(exception):
          self.cli.Execute(command)
      else:
        with self.assertRaisesRegex(exception, exception_regex):
          self.cli.Execute(command)
      if out:
        self.AssertOutputEquals(out)
      if err:
        self.AssertErrEquals(err)


if __name__ == '__main__':
  cli_test_base.main()
