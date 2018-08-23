# -*- coding: utf-8 -*- #
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

"""Tests for googlecloudsdk.core.util.peek_iterable."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import peek_iterable
from tests.lib import test_case

from six.moves import range  # pylint: disable=redefined-builtin


class PeekTest(test_case.TestCase):

  def testPeekScalar(self):
    expected = [1]
    iterable = peek_iterable.Peeker(1)
    self.assertTrue(iterable.Peek() == 1)
    actual = list(iterable)
    self.assertEqual(expected, actual)

  def testPeekList(self):
    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Peeker([1, 2, 3, 4])
    self.assertTrue(iterable.Peek() == 1)
    actual = list(iterable)
    self.assertEqual(expected, actual)

  def testPeekIterator(self):
    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Peeker(iter(expected))
    self.assertTrue(iterable.Peek() == 1)
    actual = list(iterable)
    self.assertEqual(expected, actual)

  def testPeekGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Peeker(Generate(4))
    self.assertTrue(iterable.Peek() == 1)
    actual = list(iterable)
    self.assertEqual(expected, actual)

  def testPeekEmptyGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected = [None]
    iterable = peek_iterable.Peeker(Generate(0))
    self.assertTrue(iterable.Peek() is None)
    actual = list(iterable)
    self.assertEqual(expected, actual)


class TapTest(test_case.TestCase):

  class Accumulator(peek_iterable.Tap):

    def __init__(self):
      self._items = []

    def Tap(self, item):
      self._items.append(item)
      return True

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def SetUp(self):
    self.accumulate = self.Accumulator()

  def testTapScalar(self):
    expected = [1]
    iterable = peek_iterable.Tapper(1, self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testTapList(self):
    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Tapper([1, 2, 3, 4], self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testTapIterator(self):
    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Tapper(iter(expected), self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testTapGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Tapper(Generate(4), self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())


class TapLimitTest(test_case.TestCase):

  class Limiter(peek_iterable.Tap):

    def __init__(self, limit):
      self._items = []
      self._limit = limit

    def Tap(self, item):
      if len(self._items) >= self._limit:
        return None
      self._items.append(item)
      return True

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def SetUp(self):
    self.limiter = self.Limiter(2)

  def testTapLimitScalar(self):
    expected = [1]
    iterable = peek_iterable.Tapper(1, self.limiter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())

  def testTapLimitList(self):
    expected = [1, 2]
    iterable = peek_iterable.Tapper([1, 2, 3, 4], self.limiter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())

  def testTapLimitIterator(self):
    expected = [1, 2]
    iterable = peek_iterable.Tapper(iter([1, 2, 3, 4]), self.limiter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())

  def testTapLimitGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected = [1, 2]
    iterable = peek_iterable.Tapper(Generate(4), self.limiter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())


class TapCountLimitTest(test_case.TestCase):

  class Counter(peek_iterable.Tap):

    def __init__(self):
      self._count = 0
      self._total = 0

    def Tap(self, unused_item):
      self._count += 1
      return True

    def Done(self):
      self._total = self._count

    def Total(self):
      return self._total

  class Limiter(peek_iterable.Tap):

    def __init__(self, limit):
      self._items = []
      self._limit = limit

    def Tap(self, item):
      if len(self._items) >= self._limit:
        return None
      self._items.append(item)
      return True

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def SetUp(self):
    self.counter = self.Counter()
    self.limiter = self.Limiter(2)

  def testTapCountLimitScalar(self):
    expected = [1]
    iterable = peek_iterable.Tapper(1, self.limiter)
    iterable = peek_iterable.Tapper(iterable, self.counter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())
    self.assertEqual(1, self.counter.Total())

  def testTapCountLimitList(self):
    expected = [1, 2]
    iterable = peek_iterable.Tapper([1, 2, 3, 4], self.limiter)
    iterable = peek_iterable.Tapper(iterable, self.counter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())
    self.assertEqual(2, self.counter.Total())

  def testTapCountLimitIterator(self):
    expected = [1, 2]
    iterable = peek_iterable.Tapper(iter([1, 2, 3, 4]), self.limiter)
    iterable = peek_iterable.Tapper(iterable, self.counter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())
    self.assertEqual(2, self.counter.Total())

  def testTapCountLimitGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected = [1, 2]
    iterable = peek_iterable.Tapper(Generate(4), self.limiter)
    iterable = peek_iterable.Tapper(iterable, self.counter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())
    self.assertEqual(2, self.counter.Total())


class TapLimitCountTest(test_case.TestCase):

  class Counter(peek_iterable.Tap):

    def __init__(self):
      self._count = 0
      self._total = 0

    def Tap(self, unused_item):
      self._count += 1
      return True

    def Done(self):
      self._total = self._count

    def Total(self):
      return self._total

  class Limiter(peek_iterable.Tap):

    def __init__(self, limit):
      self._items = []
      self._limit = limit

    def Tap(self, item):
      if len(self._items) >= self._limit:
        return None
      self._items.append(item)
      return True

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def SetUp(self):
    self.counter = self.Counter()
    self.limiter = self.Limiter(2)

  def testTapLimitCountScalar(self):
    expected = [1]
    iterable = peek_iterable.Tapper(1, self.counter)
    iterable = peek_iterable.Tapper(iterable, self.limiter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())
    self.assertEqual(1, self.counter.Total())

  def testTapLimitCountList(self):
    expected = [1, 2]
    iterable = peek_iterable.Tapper([1, 2, 3, 4], self.counter)
    iterable = peek_iterable.Tapper(iterable, self.limiter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())
    self.assertEqual(0, self.counter.Total())

  def testTapLimitCountIterator(self):
    expected = [1, 2]
    iterable = peek_iterable.Tapper(iter([1, 2, 3, 4]), self.counter)
    iterable = peek_iterable.Tapper(iterable, self.limiter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())
    self.assertEqual(0, self.counter.Total())

  def testTapLimitCountGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected = [1, 2]
    iterable = peek_iterable.Tapper(Generate(4), self.counter)
    iterable = peek_iterable.Tapper(iterable, self.limiter)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.limiter.Actual())
    self.assertEqual(0, self.counter.Total())


class TapInjectorTest(test_case.TestCase):

  class Injector(peek_iterable.Tap):

    def __init__(self, index):
      self._index = index
      self._items = []

    def Tap(self, item):
      if len(self._items) == self._index:
        item = 'marker'
        self._items.append(item)
        return peek_iterable.TapInjector(item)
      self._items.append(item)
      return True

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def testTapScalar1Inject0(self):
    inject = self.Injector(0)
    expected = ['marker', 1]
    iterable = peek_iterable.Tapper(1, inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapScalar1Inject1(self):
    inject = self.Injector(1)
    expected = [1]
    iterable = peek_iterable.Tapper(1, inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapList4Inject2(self):
    inject = self.Injector(2)
    expected = [1, 2, 'marker', 3, 4]
    iterable = peek_iterable.Tapper([1, 2, 3, 4], inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapIterator4Inject3(self):
    inject = self.Injector(3)
    expected = [1, 2, 3, 'marker', 4]
    iterable = peek_iterable.Tapper(iter([1, 2, 3, 4]), inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapGenerator4Inject0(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    inject = self.Injector(0)
    expected = ['marker', 1, 2, 3, 4]
    iterable = peek_iterable.Tapper(Generate(4), inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapGenerator4Inject1(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    inject = self.Injector(1)
    expected = [1, 'marker', 2, 3, 4]
    iterable = peek_iterable.Tapper(Generate(4), inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())


class TapInjectorReplaceTest(test_case.TestCase):

  class InjectorReplace(peek_iterable.Tap):

    def __init__(self, index):
      self._index = index
      self._items = []

    def Tap(self, item):
      if len(self._items) == self._index:
        item = 'marker'
        self._items.append(item)
        return peek_iterable.TapInjector(item, replace=True)
      self._items.append(item)
      return True

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def testTapScalar1InjectReplace0(self):
    inject = self.InjectorReplace(0)
    expected = ['marker']
    iterable = peek_iterable.Tapper(1, inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapScalar1InjectReplace1(self):
    inject = self.InjectorReplace(1)
    expected = [1]
    iterable = peek_iterable.Tapper(1, inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapList4InjectReplace2(self):
    inject = self.InjectorReplace(2)
    expected = [1, 2, 'marker', 4]
    iterable = peek_iterable.Tapper([1, 2, 3, 4], inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapIterator4InjectReplace3(self):
    inject = self.InjectorReplace(3)
    expected = [1, 2, 3, 'marker']
    iterable = peek_iterable.Tapper(iter([1, 2, 3, 4]), inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapGenerator4InjectReplace0(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    inject = self.InjectorReplace(0)
    expected = ['marker', 2, 3, 4]
    iterable = peek_iterable.Tapper(Generate(4), inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())

  def testTapGenerator4InjectReplace1(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    inject = self.InjectorReplace(1)
    expected = [1, 'marker', 3, 4]
    iterable = peek_iterable.Tapper(Generate(4), inject)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, inject.Actual())


class TapOddTest(test_case.TestCase):

  class Accumulator(peek_iterable.Tap):

    def __init__(self):
      self._items = []
      # False to skip the even items, True to skip the odd.
      self._skip = False

    def Tap(self, item):
      self._items.append(item)
      # This skips every other item.
      self._skip = not self._skip
      return self._skip

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def SetUp(self):
    self.accumulate = self.Accumulator()

  def testTapOddScalar(self):
    expected_all = [1, 1]
    expected_odd = [1]
    iterable = peek_iterable.Tapper(1, self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected_odd, actual)
    self.assertEqual(expected_all, self.accumulate.Actual())

  def testTapOddList(self):
    expected_all = [4, 1, 2, 3, 4]
    expected_odd = [1, 3]
    iterable = peek_iterable.Tapper([1, 2, 3, 4], self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected_odd, actual)
    self.assertEqual(expected_all, self.accumulate.Actual())

  def testTapOddIterator(self):
    expected_all = [4, 1, 2, 3, 4]
    expected_odd = [1, 3]
    iterable = peek_iterable.Tapper(iter([1, 2, 3, 4]), self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected_odd, actual)
    self.assertEqual(expected_all, self.accumulate.Actual())

  def testTapOddGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected_all = [4, 1, 2, 3, 4]
    expected_odd = [1, 3]
    iterable = peek_iterable.Tapper(Generate(4), self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected_odd, actual)
    self.assertEqual(expected_all, self.accumulate.Actual())


class PeekTapTest(test_case.TestCase):

  class Accumulator(peek_iterable.Tap):

    def __init__(self):
      self._items = []

    def Tap(self, item):
      self._items.append(item)
      return True

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def SetUp(self):
    self.accumulate = self.Accumulator()

  def testPeekTapScalar(self):
    expected = [1]
    iterable = peek_iterable.Peeker(1)
    self.assertTrue(iterable.Peek() == 1)
    iterable = peek_iterable.Tapper(iterable, self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testPeekTapList(self):
    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Peeker([1, 2, 3, 4])
    self.assertTrue(iterable.Peek() == 1)
    iterable = peek_iterable.Tapper(iterable, self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testPeekTapIterator(self):
    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Peeker(iter(expected))
    self.assertTrue(iterable.Peek() == 1)
    iterable = peek_iterable.Tapper(iterable, self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testPeekTapGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Peeker(Generate(4))
    self.assertTrue(iterable.Peek() == 1)
    iterable = peek_iterable.Tapper(iterable, self.accumulate)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())


class TapPeekTest(test_case.TestCase):

  class Accumulator(peek_iterable.Tap):

    def __init__(self):
      self._items = []

    def Tap(self, item):
      self._items.append(item)
      return True

    def Done(self):
      self._items.insert(0, len(self._items))

    def Actual(self):
      return self._items

  def SetUp(self):
    self.accumulate = self.Accumulator()

  def testTapPeekScalar(self):
    expected = [1]
    iterable = peek_iterable.Tapper(1, self.accumulate)
    iterable = peek_iterable.Peeker(iterable)
    self.assertTrue(iterable.Peek() == 1)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testTapPeekList(self):
    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Tapper([1, 2, 3, 4], self.accumulate)
    iterable = peek_iterable.Peeker(iterable)
    self.assertTrue(iterable.Peek() == 1)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testTapPeekIterator(self):
    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Tapper(iter(expected), self.accumulate)
    iterable = peek_iterable.Peeker(iterable)
    self.assertTrue(iterable.Peek() == 1)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())

  def testTapPeekGenerator(self):

    def Generate(n):
      for i in range(1, n + 1):
        yield i

    expected = [1, 2, 3, 4]
    iterable = peek_iterable.Tapper(Generate(4), self.accumulate)
    iterable = peek_iterable.Peeker(iterable)
    self.assertTrue(iterable.Peek() == 1)
    actual = list(iterable)
    self.assertEqual(expected, actual)
    self.assertEqual([len(expected)] + expected, self.accumulate.Actual())


if __name__ == '__main__':
  test_case.main()
