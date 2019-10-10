# -*- coding: utf-8 -*- #

# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for parameterized testing class."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class SanityCheckTest(parameterized.TestCase):

  @parameterized.parameters(1, 2, 3)
  def testParameters(self, number):
    self.assertGreater(number, 0)
    self.assertLess(number, 4)

  @parameterized.named_parameters(
      ('one', 1),
      ('two', 2),
      ('three', 3),
  )
  def testNamedParameters(self, number):
    self.assertGreater(number, 0)
    self.assertLess(number, 4)


class ParameterizedWithOutputCaptureTest(parameterized.TestCase,
                                         sdk_test_base.WithOutputCapture):

  @parameterized.parameters(
      ('This is a test string.', 'test', 'string'),
      ('Another test string.', 'st st'),
  )
  def testOutputContains(self, output, *args):
    sys.stdout.write(output)
    for expected_str in args:
      self.AssertOutputContains(expected_str)


class ParameterizedTestCaseBaseTest(parameterized.TestCase, test_case.Base):
  """Parameterized version of _StripLongestCommonSpaceSuffix test."""

  @parameterized.named_parameters(
      ('Empty', '', '', '', ''),
      ('One', 'a', 'z', 'a', 'z'),
      ('AGtB', 'abc', 'z', 'abc', 'z'),
      ('ALtB', 'a', 'xyz', 'a', 'xyz'),
      ('OneLine', '\n', '\n', '', ''),
      ('UnequalLines', '\n\n\n', '\n', '\n\n', ''),
      ('DiffSpace', 'a \t ', 'xyz\t \t', 'a \t ', 'xyz\t \t'),
      ('DiffAndSameSpace', 'a\t \t ', 'xyz  \t ', 'a\t', 'xyz '),
  )
  def testStripLongestCommonSpaceSuffix(self,
                                        str_a,
                                        str_b,
                                        expected_a,
                                        expected_b):
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)


if __name__ == '__main__':
  test_case.main()
