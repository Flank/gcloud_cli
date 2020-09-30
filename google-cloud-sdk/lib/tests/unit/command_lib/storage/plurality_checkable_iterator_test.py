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
"""Unit tests for PluralityCheckableIterator."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from tests.lib import test_case


def _exception_iterator():
  yield 0
  raise ValueError


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class PluralityCheckableIteratorTest(test_case.TestCase):

  def test_iteration_terminates(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([])

    with self.assertRaises(StopIteration):
      next(test_iter)

  def test_iteration_yields_correct_values(self):
    expected_list = [0, 1, 2]
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator(
        expected_list)

    self.assertEqual(list(test_iter), expected_list)

  def test_iteration_raises_exception(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator(
        _exception_iterator())

    self.assertEqual(next(test_iter), 0)
    with self.assertRaises(ValueError):
      next(test_iter)

  def test_multiply_wrapped_iterator_raises_exception(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator(
        plurality_checkable_iterator.PluralityCheckableIterator(
            _exception_iterator()))

    self.assertEqual(next(test_iter), 0)
    with self.assertRaises(ValueError):
      next(test_iter)

  def test_plural_iterator(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([0, 1])
    self.assertTrue(test_iter.is_plural())

  def test_singular_iterator_not_plural(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([0])
    self.assertFalse(test_iter.is_plural())

  def test_exceptions_count_toward_plurality(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator(
        _exception_iterator())
    self.assertTrue(test_iter.is_plural())

  def test_initially_plural_iterator_becomes_singular_is_not_plural(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([0, 1])

    self.assertTrue(test_iter.is_plural())
    next(test_iter)
    self.assertFalse(test_iter.is_plural())

  def test_empty_iterator_is_empty(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([])
    self.assertTrue(test_iter.is_empty())

  def test_non_empty_iterator_is_not_empty(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([0])
    self.assertFalse(test_iter.is_empty())

  def test_non_empty_iterator_becomes_empty(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([0])

    self.assertFalse(test_iter.is_empty())
    next(test_iter)
    self.assertTrue(test_iter.is_empty())

  def test_peeking_returns_first_iterator_item(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([0])
    self.assertEqual(test_iter.peek(), 0)
    # Call again to confirm the first item in the iterator isn't consumed.
    self.assertEqual(test_iter.peek(), 0)

  def test_peeking_returns_none_for_empty_iterator(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator([])
    self.assertIsNone(test_iter.peek())

  def test_peeking_handles_buffered_error(self):
    test_iter = plurality_checkable_iterator.PluralityCheckableIterator(
        _exception_iterator())

    next(test_iter)
    with self.assertRaises(ValueError):
      next(test_iter)


if __name__ == '__main__':
  test_case.main()
