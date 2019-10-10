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

"""Unit tests for monitoring flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.monitoring import flags
from tests.lib import test_case


class IfComparatorTest(test_case.TestCase):

  def testValidComparator(self):
    c, v = flags.ComparisonValidator('<0.5')
    self.assertEqual(c, 'COMPARISON_LT')
    self.assertEqual(v, 0.5)

    c, v = flags.ComparisonValidator('> 0.7')
    self.assertEqual(c, 'COMPARISON_GT')
    self.assertEqual(v, 0.7)

    c, v = flags.ComparisonValidator('< 42')
    self.assertEqual(c, 'COMPARISON_LT')
    self.assertEqual(v, 42)

    c, v = flags.ComparisonValidator('> -1')
    self.assertEqual(c, 'COMPARISON_GT')
    self.assertEqual(v, -1)

  def testInvalidComparator(self):
    with self.assertRaises(exceptions.BadArgumentException):
      flags.ComparisonValidator('=')
    with self.assertRaises(exceptions.BadArgumentException):
      flags.ComparisonValidator('0')
    with self.assertRaises(exceptions.BadArgumentException):
      flags.ComparisonValidator('=0.5')
    with self.assertRaises(exceptions.BadArgumentException):
      flags.ComparisonValidator('<ten')
    with self.assertRaises(exceptions.BadArgumentException):
      flags.ComparisonValidator('<=1')
    with self.assertRaises(exceptions.BadArgumentException):
      flags.ComparisonValidator('>=1')
    with self.assertRaises(exceptions.BadArgumentException):
      flags.ComparisonValidator('==1')
    with self.assertRaises(exceptions.BadArgumentException):
      flags.ComparisonValidator('!=1')


if __name__ == '__main__':
  IfComparatorTest.main()
