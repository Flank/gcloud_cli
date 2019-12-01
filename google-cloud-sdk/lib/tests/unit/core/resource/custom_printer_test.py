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

"""Unit tests for the custom printer base."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import textwrap

from googlecloudsdk.core.resource import custom_printer_base as cp
from tests.lib import test_case


class MockPrinter(cp.CustomPrinterBase):

  def Transform(self, record):
    return record


class CustomPrinterTest(test_case.TestCase):

  def testCalculateColumn(self):
    p = MockPrinter()
    self.assertEqual(p._CalculateColumn(''), 0)
    self.assertEqual(p._CalculateColumn('asdfadsfasdf'), 0)
    self.assertEqual(p._CalculateColumn(cp.Lines([
        'asdfadfsadfadsf', 'asdfasdfweee', 'sdf'])), 0)
    self.assertEqual(p._CalculateColumn(cp.Labeled(
        [('a', 'asdf'), ('aa', 'asdf'), ('aaa', 'asdf')])), 4)
    self.assertEqual(p._CalculateColumn(cp.Mapped(
        [('a', 'asdf'), ('aa', 'asdf'), ('aaa', 'asdf')])), 3)
    self.assertEqual(p._CalculateColumn(cp.Mapped(
        [('a', 'asdf'), ('aa', 'asdf'), ('aaa', '')])), 2)
    self.assertEqual(p._CalculateColumn(cp.Mapped(
        [('a', 'asdf'), ('aa', 'asdf'), ('aaa', cp.Labeled([
            ('a', 'a')]))])), 4)

  def testPrinter(self):
    case = cp.Lines([
        'this is a header',
        cp.Labeled([
            ('Foo', 'carrot'),
            ('Bar', 12),
            ('Baz', cp.Labeled([
                ('Fun', 'doooodles'),
                ('Sun', cp.Lines(['toot', 'taaat', 3]))])),
            ('Quux', cp.Mapped([
                ('hundred', 'lots'),
                ('two', 'few')]))])])
    s = io.StringIO()
    p = MockPrinter(out=s)
    p.AddRecord(case)
    self.assertEqual(s.getvalue(), textwrap.dedent("""\
    this is a header
    Foo:      carrot
    Bar:      12
    Baz:
      Fun:    doooodles
      Sun:
        toot
        taaat
        3
    Quux:
      hundred lots
      two     few
    ------
    """))

if __name__ == '__main__':
  test_case.main()
