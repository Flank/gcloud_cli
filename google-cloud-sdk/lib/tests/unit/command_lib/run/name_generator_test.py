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
"""Tests for name_generator.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.run import name_generator
from tests.lib import parameterized
from tests.lib import test_case


class NameGeneratorTest(test_case.TestCase, parameterized.TestCase):

  @parameterized.parameters(
      (1, '-', None, False, 'abc'),
      (2, '-', None, True, 'abc-abc'),
      (3, 'bla', None, False, 'abcblaabcblaabc'),
      (2, '/', 'prefix', True, 'prefix/abc/abc'),
      (2, '', None, False, 'abcabc'),
      (1, '', 'prefix', True, 'prefixabc'),
      (1, '-', '', True, '-abc'))
  def testGenerateNames(self, sections, separator, prefix, validate,
                        expected_name):
    gen = self.StartObjectPatch(
        name_generator,
        '_ThreeLetterGenerator',
        return_value='abc')
    self.assertEqual(
        expected_name, name_generator.GenerateName(
            sections, separator, prefix, validate))
    self.assertEqual(sections, gen.call_count)
    gen.assert_called_with(validate)

  def testGenerateNamesRequiresAtLeastOneSection(self):
    with self.assertRaises(AssertionError):
      name_generator.GenerateName(sections=0)

  def testThreeLetterGeneratorGenerates(self):
    validator = self.StartObjectPatch(name_generator, 'IsValidWord')
    for _ in range(10):
      self.assertEqual(3, len(name_generator._ThreeLetterGenerator(False)))
    self.assertEqual(0, validator.call_count)

  @parameterized.parameters(
      ([True], 1),
      ([False, False, False, True], 1),
      ([True, False, False, True], 2),
      ([False, False, True, True, True, False, True], 4))
  def testThreeLetterGeneratorGeneratesAndValidates(self, validations, calls):
    validator = self.StartObjectPatch(
        name_generator, 'IsValidWord', side_effect=validations)
    for _ in range(calls):
      self.assertEqual(3, len(name_generator._ThreeLetterGenerator(True)))
    self.assertEqual(len(validations), validator.call_count)

  @parameterized.parameters(
      ('', True),
      ('a', True),
      ('abc', True),
      ('big', True),
      ('toolong', True),
      ('coq', False),
      ('jew', False))
  def testIsValidWord(self, word, is_valid):
    """Test a very small sample of words."""
    self.assertEqual(is_valid, name_generator.IsValidWord(word))
