# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for none_printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_printer
from tests.lib import test_case
from tests.lib.core.resource import resource_printer_test_base

from six.moves import range  # pylint: disable=redefined-builtin


class Iterator(object):

  def __init__(self, n):
    self.i = 0
    self.n = n

  def __iter__(self):
    return self

  def next(self):
    return self.__next__()

  def __next__(self):
    if self.i < self.n:
      i = self.i
      self.i += 1
      return i
    else:
      raise StopIteration()


class NoneAttributeTest(resource_printer_test_base.Base):

  def testNoneIterator(self):
    resource = Iterator(4)
    resource_printer.Print(resource, 'none')
    self.AssertOutputEquals('')
    self.assertEqual(list(resource), [])

  def testNoneIteratorDisable(self):
    resource = Iterator(4)
    resource_printer.Print(resource, 'disable')
    self.AssertOutputEquals('')
    self.assertEqual(list(resource), [0, 1, 2, 3])

  def testNoneIteratorDisableAttributeBackwardsCompatibility(self):
    resource = Iterator(4)
    resource_printer.Print(resource, 'none[disable]')
    self.AssertOutputEquals('')
    self.assertEqual(list(resource), [0, 1, 2, 3])

  def testNoneRange(self):
    resource = list(range(4))
    resource_printer.Print(resource, 'none')
    self.AssertOutputEquals('')
    self.assertEqual(list(resource), [0, 1, 2, 3])

  def testNoneRangeDisable(self):
    resource = list(range(4))
    resource_printer.Print(resource, 'disable')
    self.AssertOutputEquals('')
    self.assertEqual(list(resource), [0, 1, 2, 3])

  def testNoneXrange(self):
    resource = range(4)
    resource_printer.Print(resource, 'none')
    self.AssertOutputEquals('')
    self.assertEqual(list(resource), [0, 1, 2, 3])

  def testNoneXrangeDisable(self):
    resource = range(4)
    resource_printer.Print(resource, 'disable')
    self.AssertOutputEquals('')
    self.assertEqual(list(resource), [0, 1, 2, 3])


if __name__ == '__main__':
  test_case.main()
