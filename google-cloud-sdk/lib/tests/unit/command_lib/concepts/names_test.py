# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for the names module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.concepts import names
from tests.lib import parameterized
from tests.lib import test_case


class NamesTest(parameterized.TestCase):

  @parameterized.named_parameters(
      ('HasPrefix', '--foo', 'foo'),
      ('HasMoreDashes', '---foo', '-foo'),
      ('HasOneDash', '-foo', '-foo'),
      ('HasNoPrefix', 'foo', 'foo'))
  def testStripFlagPrefix(self, input_val, expected):
    self.assertEqual(
        expected,
        names.StripFlagPrefix(input_val))

  @parameterized.named_parameters(
      ('HasPrefix', '--foo', '--foo'),
      ('HasMoreDashes', '---foo', '---foo'),
      ('HasOneDash', '-foo', '---foo'),
      ('HasNoPrefix', 'foo', '--foo'))
  def testAddFlagPrefix(self, input_val, expected):
    self.assertEqual(
        expected,
        names.AddFlagPrefix(input_val))

  @parameterized.named_parameters(
      ('', 'foo', '--foo'),
      ('HasPrefix', '--foo', '--foo'),
      ('Underscores', 'foo_bar', '--foo-bar'),
      ('PrefixUnderscores', '--foo_bar', '--foo-bar'),
      ('Dashes', 'foo-bar', '--foo-bar'),
      ('PrefixDashes', '--foo-bar', '--foo-bar'),
      ('Uppercase', 'FOO', '--foo'),
      ('UppercaseUnderscores', 'FOO_BAR', '--foo-bar'),
      ('UppercasePrefix', '--FOO', '--foo'),
      ('UppercasePrefixUnderscores', '--FOO_BAR', '--foo-bar'),
      ('UppercaseDashes', 'FOO-BAR', '--foo-bar'),
      ('UppercasePrefixDashes', '--FOO-BAR', '--foo-bar'))
  def testConvertToFlagName(self, input_val, expected):
    self.assertEqual(
        expected,
        names.ConvertToFlagName(input_val))

  @parameterized.named_parameters(
      ('', 'foo', 'FOO'),
      ('HasPrefix', '--foo', 'FOO'),
      ('Underscores', 'foo_bar', 'FOO_BAR'),
      ('PrefixUnderscores', '--foo_bar', 'FOO_BAR'),
      ('Dashes', 'foo-bar', 'FOO_BAR'),
      ('PrefixDashes', '--foo-bar', 'FOO_BAR'),
      ('Uppercase', 'FOO', 'FOO'),
      ('UppercaseUnderscores', 'FOO_BAR', 'FOO_BAR'),
      ('UppercasePrefix', '--FOO', 'FOO'),
      ('UppercasePrefixUnderscores', '--FOO_BAR', 'FOO_BAR'),
      ('UppercaseDashes', 'FOO-BAR', 'FOO_BAR'),
      ('UppercasePrefixDashes', '--FOO-BAR', 'FOO_BAR'))
  def testConvertToPositionalName(self, input_val, expected):
    self.assertEqual(
        expected,
        names.ConvertToPositionalName(input_val))

  @parameterized.named_parameters(
      ('', 'foo', 'foo'),
      ('HasPrefix', '--foo', 'foo'),
      ('Underscores', 'foo_bar', 'foo_bar'),
      ('PrefixUnderscores', '--foo_bar', 'foo_bar'),
      ('Dashes', 'foo-bar', 'foo_bar'),
      ('PrefixDashes', '--foo-bar', 'foo_bar'),
      ('Uppercase', 'FOO', 'foo'),
      ('UppercaseUnderscores', 'FOO_BAR', 'foo_bar'),
      ('UppercasePrefix', '--FOO', 'foo'),
      ('UppercasePrefixUnderscores', '--FOO_BAR', 'foo_bar'),
      ('UppercaseDashes', 'FOO-BAR', 'foo_bar'),
      ('UppercasePrefixDashes', '--FOO-BAR', 'foo_bar'))
  def testConvertToNamespaceName(self, input_val, expected):
    self.assertEqual(
        expected,
        names.ConvertToNamespaceName(input_val))


if __name__ == '__main__':
  test_case.main()
