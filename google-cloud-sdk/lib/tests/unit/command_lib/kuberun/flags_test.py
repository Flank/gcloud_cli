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
"""Unit tests for flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.kuberun import flags
from tests.lib import test_case

import mock


class FlagsTest(test_case.TestCase):
  """Unit tests for flags module."""

  def SetUp(self):
    self.parser = mock.Mock()
    self.args = mock.Mock()

  def testStringFlag_AddToParser(self):
    flag_name = '--test-flag'
    help_text = 'some help text'
    string_flag = flags.StringFlag(flag_name, help=help_text)
    string_flag.AddToParser(self.parser)

    self.parser.assert_has_calls(
        [mock.call.add_argument(flag_name, help=help_text)])

  def testStringFlag_FormatFlags_present(self):
    expected_value = 'expected_test_value'
    self.args.test_flag = expected_value
    self.args.IsSpecified.return_value = True

    string_flag = flags.StringFlag('--test-flag')
    actual = string_flag.FormatFlags(self.args)

    self.args.IsSpecified.assert_called_with('test_flag')
    self.assertListEqual(['--test-flag', expected_value], actual)

  def testStringFlag_FormatFlags_missing(self):
    self.args.IsSpecified.return_value = False

    string_flag = flags.StringFlag('--test-flag')
    actual = string_flag.FormatFlags(self.args)

    self.assertListEqual([], actual)

  def testStringFlag_FormatFlags_coerceToString(self):
    integer_value = 10
    self.args.test_flag = integer_value
    self.args.IsSpecified.return_value = True

    string_flag = flags.StringFlag('--test-flag')
    actual = string_flag.FormatFlags(self.args)

    self.args.IsSpecified.assert_called_with('test_flag')
    self.assertListEqual(['--test-flag', str(integer_value)], actual)

  def testBooleanFlag_AddToParser(self):
    flag_name = '--test-boolean-flag'
    boolean_flag = flags.BooleanFlag(flag_name)

    boolean_flag.AddToParser(self.parser)

    self.parser.assert_has_calls([
        mock.call.add_argument(
            flag_name, action=arg_parsers.StoreTrueFalseAction)
    ])

  def testBooleanFlag_FormatFlags_present(self):
    flag_name = '--test-boolean-flag'
    boolean_flag = flags.BooleanFlag(flag_name)

    self.args.GetSpecifiedArgNames.return_value = [flag_name]

    actual = boolean_flag.FormatFlags(self.args)

    self.args.GetSpecifiedArgNames.assert_called()
    self.assertListEqual([flag_name], actual)

  def testBooleanFlag_FormatFlags_missing(self):
    flag_name = '--test-boolean-flag'
    boolean_flag = flags.BooleanFlag(flag_name)

    missing_flag_name = '--no-test-boolean-flag'
    self.args.GetSpecifiedArgNames.return_value = [missing_flag_name]

    actual = boolean_flag.FormatFlags(self.args)

    self.args.GetSpecifiedArgNames.assert_called()
    self.assertListEqual([missing_flag_name], actual)

  def testBasicFlag_AddToParser(self):
    flag_name = '--basic-flag'
    basic_flag = flags.BasicFlag(flag_name)

    basic_flag.AddToParser(self.parser)

    self.parser.assert_has_calls(
        [mock.call.add_argument(flag_name, default=False, action='store_true')])

  def testBasicFlag_FormatFlags_present(self):
    flag_name = '--basic-flag'
    basic_flag = flags.BasicFlag(flag_name)

    self.args.IsSpecified.return_value = True

    actual = basic_flag.FormatFlags(self.args)

    self.args.IsSpecified.assert_called_with('basic_flag')
    self.assertListEqual([flag_name], actual)

  def testBasicFlag_FormatFlags_missing(self):
    flag_name = '--basic-flag'
    basic_flag = flags.BasicFlag(flag_name)

    self.args.IsSpecified.return_value = False

    actual = basic_flag.FormatFlags(self.args)

    self.args.IsSpecified.assert_called_with('basic_flag')
    self.assertListEqual([], actual)

  def testFlagGroup_AddToParser(self):
    flag1 = mock.create_autospec(flags.BinaryCommandFlag)
    flag2 = mock.create_autospec(flags.BinaryCommandFlag)
    flag3 = mock.create_autospec(flags.BinaryCommandFlag)

    flag_group = flags.FlagGroup(flag1, flag2, flag3)

    flag_group.AddToParser(self.parser)

    flag1.assert_has_calls([mock.call.AddToParser(self.parser)])
    flag2.assert_has_calls([mock.call.AddToParser(self.parser)])
    flag3.assert_has_calls([mock.call.AddToParser(self.parser)])

  def testFlagGroup_FormatFlags(self):
    flag1 = mock.create_autospec(flags.BinaryCommandFlag)
    flag2 = mock.create_autospec(flags.BinaryCommandFlag)
    flag3 = mock.create_autospec(flags.BinaryCommandFlag)

    flag_group = flags.FlagGroup(flag1, flag2, flag3)

    flag1.FormatFlags.return_value = ['--flag1']
    flag2.FormatFlags.return_value = ['--flag2', 'blah']
    flag3.FormatFlags.return_value = ['--no-flag3']

    actual = flag_group.FormatFlags(self.args)

    flag1.assert_has_calls([mock.call.FormatFlags(self.args)])
    flag2.assert_has_calls([mock.call.FormatFlags(self.args)])
    flag3.assert_has_calls([mock.call.FormatFlags(self.args)])

    self.assertListEqual(['--flag1', '--flag2', 'blah', '--no-flag3'], actual)

if __name__ == '__main__':
  test_case.main()
