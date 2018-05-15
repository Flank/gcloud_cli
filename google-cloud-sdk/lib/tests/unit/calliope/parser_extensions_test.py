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

"""Unit tests for the parser_extensions module."""

from __future__ import absolute_import
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import parser_errors
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import parameterized_line_no
from tests.lib.calliope import util as calliope_test_util

import mock


T = parameterized_line_no.LineNo


class SpecifiedArgsTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()

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


class SpecifiedGroupsTest(cli_test_base.CliTestBase, parameterized.TestCase):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()

  @parameterized.parameters(
      T(
          [],
          None,
      ),
      T(
          ['--inner-1'],
          'argument --outer-1 --outer-2: Must be specified.',
      ),
      T(
          ['--inner-2'],
          'argument --outer-1 --outer-2: Must be specified.',
      ),
      T(
          ['--inner-1', '--inner-2'],
          'argument --inner-1: At most one of (--inner-1 | --inner-2) '
          'may be specified.',
      ),
      T(
          ['--outer-1'],
          'argument --outer-2 (--inner-1 | --inner-2): Must be specified.',
      ),
      T(
          ['--outer-1', '--inner-1'],
          'argument --outer-2: Must be specified.',
      ),
      T(
          ['--outer-1', '--inner-2'],
          'argument --outer-2: Must be specified.',
      ),
      T(
          ['--outer-1', '--inner-1', '--inner-2'],
          'argument --inner-1: At most one of (--inner-1 | --inner-2) '
          'may be specified.',
      ),
      T(
          ['--outer-2'],
          'argument --outer-1 (--inner-1 | --inner-2): Must be specified.',
      ),
      T(
          ['--outer-2', '--inner-1'],
          'argument --outer-1: Must be specified.',
      ),
      T(
          ['--outer-2', '--inner-2'],
          'argument --outer-1: Must be specified.',
      ),
      T(
          ['--outer-2', '--inner-1', '--inner-2'],
          'argument --inner-1: At most one of (--inner-1 | --inner-2) '
          'may be specified.',
      ),
      T(
          ['--outer-1', '--outer-2'],
          'argument (--inner-1 | --inner-2): Must be specified.',
      ),
      T(
          ['--outer-1', '--outer-2', '--inner-1'],
          None,
      ),
      T(
          ['--outer-1', '--outer-2', '--inner-2'],
          None,
      ),
      T(
          ['--outer-1', '--outer-2', '--inner-1', '--inner-2'],
          'argument --inner-1: At most one of (--inner-1 | --inner-2) '
          'may be specified.',
      ),
  )
  def testRequiredInOptionalGroup(self, line, args, error):
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

  @parameterized.parameters(
      T(
          [],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          ['--inner-1'],
          'argument --outer-1 --outer-2: Must be specified.',
      ),
      T(
          ['--inner-2'],
          'argument --outer-1 --outer-2: Must be specified.',
      ),
      T(
          ['--inner-1', '--inner-2'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          ['--outer-1'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          ['--outer-1', '--inner-1'],
          'argument --outer-2: Must be specified.',
      ),
      T(
          ['--outer-1', '--inner-2'],
          'argument --outer-2: Must be specified.',
      ),
      T(
          ['--outer-1', '--inner-1', '--inner-2'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          ['--outer-2'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          ['--outer-2', '--inner-1'],
          'argument --outer-1: Must be specified.',
      ),
      T(
          ['--outer-2', '--inner-2'],
          'argument --outer-1: Must be specified.',
      ),
      T(
          ['--outer-2', '--inner-1', '--inner-2'],
          'argument --inner-1: Exactly one of (--inner-1 | --inner-2) '
          'must be specified.',
      ),
      T(
          ['--outer-1', '--outer-2'],
          'Exactly one of (--inner-1 | --inner-2) must be specified.',
      ),
      T(
          ['--outer-1', '--outer-2', '--inner-1'],
          None,
      ),
      T(
          ['--outer-1', '--outer-2', '--inner-2'],
          None,
      ),
      T(
          ['--outer-1', '--outer-2', '--inner-1', '--inner-2'],
          'argument --inner-1: Exactly one of (--inner-1 | --inner-2) '
          'must be specified.',
      ),
  )
  def testRequiredInRequiredGroup(self, line, args, error):
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


if __name__ == '__main__':
  cli_test_base.main()
