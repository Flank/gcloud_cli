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
from tests.lib import parameterized
from tests.lib import test_case


class MockPrinter(cp.CustomPrinterBase):

  def Transform(self, record):
    return record


@parameterized.named_parameters(('Table', cp.Table), ('Mapped', cp.Mapped))
class TableAndMappedTest(test_case.TestCase, parameterized.TestCase):

  def testCalculateColumnWidthsComputesColumnWidths(self, constructor):
    marker = constructor([('aaa', 'aa', 'a'), ('bbbb', 'b', 'bb')])
    column_widths = marker.CalculateColumnWidths()
    self.assertEqual(column_widths.widths, [4, 2, 0])

  def testCalculateColumnWidthsDoesNotSkipEmpty(self, constructor):
    marker = constructor([('aaa', 'aa', ''), ('bbbb', 'b', 'bb')])
    column_widths = marker.CalculateColumnWidths()
    self.assertEqual(column_widths.widths, [4, 2, 0])

  def testCalculateColumnWidthsRestrictsToMaxColumnWidth(self, constructor):
    marker = constructor([('aaa', 'aa', 'a'), ('bbbb', 'b', 'bb')])
    column_widths = marker.CalculateColumnWidths(3)
    self.assertEqual(column_widths.widths, [3, 2, 0])

  def testCalculateColumnWidthsIncludesIndentLength(self, constructor):
    marker = constructor([('aaa', 'aa', 'a'), ('bbbb', 'b', 'bb')])
    column_widths = marker.CalculateColumnWidths(indent_length=2)
    self.assertEqual(column_widths.widths, [6, 2, 0])

  def testPrintBasic(self, constructor):
    marker = constructor([
        ('aa', 'aaa', 'a'),
        ('bbbb', 'bb', 'bb'),
        ('cc',),
        ('ddd', 'dd', 'dd', 'dd'),
    ])
    with io.StringIO() as out:
      marker.Print(out, 0, cp.ColumnWidths(row=('4444', '333', '22', '22')))
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      aa   aaa a
      bbbb bb  bb
      cc
      ddd  dd  dd dd
      """))

  def testPrintOverflowingLastColumn(self, constructor):
    marker = constructor([
        ('aa', 'aaa', 'a'),
        ('bbbb', 'bb', 'bb'),
        ('ccccccccccccccccccccccccccc',),
        ('ddd', 'dd', 'dd', 'dd'),
    ])
    with io.StringIO() as out:
      marker.Print(out, 0, cp.ColumnWidths(row=('4444', '333', '22', '22')))
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      aa   aaa a
      bbbb bb  bb
      ccccccccccccccccccccccccccc
      ddd  dd  dd dd
      """))

  def testPrintSkipsEmpty(self, constructor):
    marker = constructor([
        ('aa', 'aaa', 'a'),
        ('bbbb', 'bb', 'bb'),
        (),
        ('ddd', 'dd', 'dd', 'dd'),
    ])
    with io.StringIO() as out:
      marker.Print(out, 0, cp.ColumnWidths(row=('4444', '333', '22', '22')))
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      aa   aaa a
      bbbb bb  bb
      ddd  dd  dd dd
      """))

  def testPrintIndents(self, constructor):
    marker = constructor([
        ('aa', 'aaa', 'a'),
        ('bbbb', 'bb', 'bb'),
        ('cc',),
        ('ddd', 'dd', 'dd', 'dd'),
    ])
    with io.StringIO() as out:
      out.write('prefix\n')
      marker.Print(
          out, 2,
          cp.ColumnWidths(row=('4444', '333', '22', '22'), indent_length=2))
      out.write('suffix\n')
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      prefix
        aa   aaa a
        bbbb bb  bb
        cc
        ddd  dd  dd dd
      suffix
      """))

  def testPrintRejectsMarkerNotInLastColumn(self, constructor):
    marker = constructor([
        ('aa', 'aaa', 'a'),
        ('bbbb', constructor([('ab', 'cd')]), 'bb'),
    ])
    with io.StringIO() as out, self.assertRaises(TypeError):
      marker.Print(out, 0, cp.ColumnWidths(row=('4444', '333', '22')))

  def testPrintNestedMarker(self, constructor):
    marker = constructor([
        ('aa', 'aaa', 'a'),
        ('bbbb', 'bb', 'bb'),
        ('cc', constructor([
            ('xxx', 'xx', 'x'),
            ('yyyy', 'yy', 'yyy')
        ])),
        ('ddd', 'dd', 'dd', 'dd'),
    ])
    with io.StringIO() as out:
      marker.Print(out, 0, cp.ColumnWidths(row=('666666', '333', '22', '22')))
      self.assertEqual(out.getvalue(), textwrap.dedent("""\
      aa     aaa a
      bbbb   bb  bb
      cc
        xxx  xx  x
        yyyy yy  yyy
      ddd    dd  dd dd
      """))


class LabeledTest(test_case.TestCase):

  def testCalculateColumnWidthsComputesColumnWidths(self):
    labeled = cp.Labeled([('aaa', 'aa', 'a'), ('bbbb', 'b', 'bb')])
    column_widths = labeled.CalculateColumnWidths()
    self.assertEqual(column_widths.widths, [5, 3, 0])

  def testCalculateColumnWidthsSkipsEmpty(self):
    labeled = cp.Labeled([('aaa', 'aa', ''), ('bbbb', 'b', 'bb')])
    column_widths = labeled.CalculateColumnWidths()
    self.assertEqual(column_widths.widths, [5, 2, 0])

  def testCalculateColumnWidthsRestrictsToMaxColumnWidth(self):
    labeled = cp.Labeled([('aaa', 'aa', 'a'), ('bbbb', 'b', 'bb')])
    column_widths = labeled.CalculateColumnWidths(3)
    self.assertEqual(column_widths.widths, [3, 3, 0])

  def testCalculateColumnWidthsIncludesIndentLength(self):
    labeled = cp.Labeled([('aaa', 'aa', 'a'), ('bbbb', 'b', 'bb')])
    column_widths = labeled.CalculateColumnWidths(indent_length=2)
    self.assertEqual(column_widths.widths, [7, 3, 0])

  def testPrintIncludesSeparator(self):
    labeled = cp.Labeled([
        ('aa', 'aaa'),
        ('bbbb', 'bb'),
        ('ccc', 'cc'),
    ])
    with io.StringIO() as out:
      labeled.Print(out, 0, cp.ColumnWidths(row=('55555', '333')))
      self.assertEqual(out.getvalue(), textwrap.dedent("""\
      aa:   aaa
      bbbb: bb
      ccc:  cc
      """))

  def testPrintSkipsSingleColumnRow(self):
    labeled = cp.Labeled([
        ('aa', 'aaa'),
        ('bbbb', 'bb'),
        ('cc',),
        ('ddd', 'dd'),
    ])
    with io.StringIO() as out:
      labeled.Print(out, 0, cp.ColumnWidths(row=('55555', '333')))
      self.assertEqual(out.getvalue(), textwrap.dedent("""\
      aa:   aaa
      bbbb: bb
      ddd:  dd
      """))

  def testPrintSkipsFollowedByEmpty(self):
    labeled = cp.Labeled([
        ('aa', 'aaa'),
        ('bbbb', 'bb'),
        ('cc', ''),
        ('ddd', 'dd'),
    ])
    with io.StringIO() as out:
      labeled.Print(out, 0, cp.ColumnWidths(row=('55555', '333')))
      self.assertEqual(out.getvalue(), textwrap.dedent("""\
      aa:   aaa
      bbbb: bb
      ddd:  dd
      """))


@parameterized.named_parameters(
    ('Lines', cp.Lines, lambda lines, cw: cw.widths),
    ('Section', cp.Section, lambda section, cw: section._column_widths.widths))
class LinesAndSectionCalculateColumnWidthsTest(test_case.TestCase,
                                               parameterized.TestCase):

  def testNoMarkers(self, constructor, column_widths_getter):
    marker = constructor(['line1', 'line2'])
    column_widths = marker.CalculateColumnWidths()
    self.assertEqual(column_widths_getter(marker, column_widths), [])

  def testMarkers(self, constructor, column_widths_getter):
    marker = constructor(
        [cp.Table([('aaa', 'aa', 'a')]),
         cp.Table([('bb', 'bbbb', 'b')])])
    column_widths = marker.CalculateColumnWidths()
    self.assertEqual(column_widths_getter(marker, column_widths), [3, 4, 0])

  def testMarkersAndNonMarkers(self, constructor, column_widths_getter):
    marker = constructor([
        cp.Table([('aaa', 'aa', 'a')]), 'line2',
        cp.Table([('bb', 'bbbb', 'b')])
    ])
    column_widths = marker.CalculateColumnWidths()
    self.assertEqual(column_widths_getter(marker, column_widths), [3, 4, 0])

  def testRestrictsToMaxColumnWidth(self, constructor, column_widths_getter):
    marker = constructor(
        [cp.Table([('aaa', 'aa', 'a')]),
         cp.Table([('bb', 'bbbb', 'b')])])
    column_widths = marker.CalculateColumnWidths(3)
    self.assertEqual(column_widths_getter(marker, column_widths), [3, 3, 0])

  def testIncludesIndentLength(self, constructor, column_widths_getter):
    marker = constructor(
        [cp.Table([('aaa', 'aa', 'a')]),
         cp.Table([('bb', 'bbbb', 'b')])])
    column_widths = marker.CalculateColumnWidths(indent_length=2)
    self.assertEqual(column_widths_getter(marker, column_widths), [5, 4, 0])


class SectionCalculateColumnWidthsTest(test_case.TestCase):

  def testReturnsEmptyColumnWidths(self):
    section = cp.Section(
        [cp.Table([('aaa', 'aa', 'a')]),
         cp.Table([('bb', 'bbbb', 'b')])])
    column_widths = section.CalculateColumnWidths()
    self.assertEqual(column_widths.widths, [])

  def testOverridesMaxColumnWidth(self):
    section = cp.Section(
        [cp.Table([('aaa', 'aa', 'a')]),
         cp.Table([('bb', 'bbbb', 'b')])],
        max_column_width=3)
    section.CalculateColumnWidths(2)
    self.assertEqual(section._column_widths.widths, [3, 3, 0])


@parameterized.named_parameters(('Lines', cp.Lines), ('Section', cp.Section))
class LinesAndSectionPrintTest(test_case.TestCase, parameterized.TestCase):

  def testPrintWithNonMarkerValues(self, constructor):
    marker = constructor([
        'line 1',
        'line 2',
        'line 3',
    ])
    with io.StringIO() as out:
      marker.Print(out, 0, cp.ColumnWidths())
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      line 1
      line 2
      line 3
      """))

  def testPrintWithMarkerValues(self, constructor):
    marker = constructor([
        'line 1',
        'line 2',
        cp.Table([
            ('a', 'aaa', 'a'),
            ('bb', 'bb', 'b'),
        ]),
        'line 3',
    ])
    with io.StringIO() as out:
      marker.Print(out, 0, cp.ColumnWidths(row=('22', '333', '1')))
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      line 1
      line 2
      a  aaa a
      bb bb  b
      line 3
      """))

  def testPrintWithIndentation(self, constructor):
    marker = constructor([
        'line 1',
        'line 2',
        'line 3',
    ])
    with io.StringIO() as out:
      out.write('prefix\n')
      marker.Print(out, 2, cp.ColumnWidths())
      out.write('suffix\n')
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      prefix
        line 1
        line 2
        line 3
      suffix
      """))

  def testPrintSkipsEmptyLines(self, constructor):
    marker = constructor([
        'line 1',
        'line 2',
        '',
        'line 3',
    ])
    with io.StringIO() as out:
      marker.Print(out, 0, cp.ColumnWidths())
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      line 1
      line 2
      line 3
      """))


class SectionPrintTest(test_case.TestCase):

  def testOverridesColumnWidths(self):
    section = cp.Section([
        'line 1',
        'line 2',
        cp.Table([
            ('a', 'aaa', 'a'),
            ('bb', 'bb', 'b'),
        ]),
        'line 3',
    ])
    with io.StringIO() as out:
      section.Print(out, 0, cp.ColumnWidths(row=('1', '1', '1')))
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      line 1
      line 2
      a  aaa a
      bb bb  b
      line 3
      """))


class ColumnWidthsTest(test_case.TestCase):

  def testWidthsDefaultsToEmpty(self):
    self.assertEqual(cp.ColumnWidths().widths, [])

  def testReprIncludesWidths(self):
    column_widths = cp.ColumnWidths(row=('bb', 'bbb'))
    self.assertEqual(repr(column_widths), '<widths: [2, 0]>')

  def testComputesWidthsIgnoringLastColumn(self):
    column_widths = cp.ColumnWidths(row=('aaa', 'aa', 'aaaa', 'a'))
    self.assertEqual(column_widths.widths, [3, 2, 4, 0])

  def testIgnoresEmptyRow(self):
    column_widths = cp.ColumnWidths(row=())
    self.assertEqual(column_widths.widths, [])

  def testHandlesEmptyInteriorColumn(self):
    column_widths = cp.ColumnWidths(row=('aaa', '', 'bbbbb', 'c'))
    self.assertEqual(column_widths.widths, [3, 0, 5, 0])

  def testHandlesEmptyLastColumn(self):
    column_widths = cp.ColumnWidths(row=('aaa', 'bbbbb', 'c', ''))
    self.assertEqual(column_widths.widths, [3, 5, 1, 0])

  def testIncludesSeparatorWidth(self):
    column_widths = cp.ColumnWidths(row=('aaa', 'aa'), separator=':')
    self.assertEqual(column_widths.widths, [4, 0])

  def testSkipsEmptyLastColumnWhenSpecified(self):
    column_widths = cp.ColumnWidths(row=('aaa', 'bbbbb', ''), skip_empty=True)
    self.assertEqual(column_widths.widths, [3, 0, 0])

  def testSkipsMultipleEmptyEndingColumnsWhenSpecified(self):
    column_widths = cp.ColumnWidths(
        row=('aaa', 'bbbbb', '', ''), skip_empty=True)
    self.assertEqual(column_widths.widths, [3, 0, 0, 0])

  def testIncludesEmptyInteriorColumnsWhenSkipEmptySpecified(self):
    column_widths = cp.ColumnWidths(
        row=('aaa', '', 'bbbbb', 'c'), skip_empty=True)
    self.assertEqual(column_widths.widths, [3, 0, 5, 0])

  def testRestrictsWidthsToMaxColumnWidth(self):
    column_widths = cp.ColumnWidths(
        row=('a', 'aa', 'aaaa', 'a'), max_column_width=2)
    self.assertEqual(column_widths.widths, [1, 2, 2, 0])

  def testRejectsNestedNotLastColumn(self):
    with self.assertRaises(TypeError):
      cp.ColumnWidths(row=('aaaa', cp.Table([('1', '2')]), 'bb'))

  def testAddsIndentLengthToFirstColumnWidth(self):
    column_widths = cp.ColumnWidths(row=('a', 'aa', 'aaaa'), indent_length=2)
    self.assertEqual(column_widths.widths, [3, 2, 0])

  def testRestrictsIndentLengthToMaxColumnWidth(self):
    column_widths = cp.ColumnWidths(
        row=('a', 'aa', 'aaaa'), indent_length=10, max_column_width=4)
    self.assertEqual(column_widths.widths, [4, 2, 0])

  def testComputesNestedColumnWidthsNestedColumnsLarger(self):
    column_widths = cp.ColumnWidths(
        row=('bb', 'bbb', 'bb', cp.Table([('ccc', 'cccc', 'c')])))
    self.assertEqual(column_widths.widths, [5, 4, 0])

  def testComputesNestedColumnWidthsNestedColumnsSmaller(self):
    column_widths = cp.ColumnWidths(
        row=('bbbb', 'bbbbbb', 'bb', cp.Table([('c', 'cc', 'c')])))
    self.assertEqual(column_widths.widths, [4, 6, 0])

  def testComputesNestedColumnWidthsNestedMoreColumns(self):
    column_widths = cp.ColumnWidths(
        row=('bb', 'bbbbbb', cp.Table([('ccc', 'cc', 'c')])))
    self.assertEqual(column_widths.widths, [5, 2, 0])

  def testComputesNestedColumnWidthsNestedLessColumns(self):
    column_widths = cp.ColumnWidths(
        row=('bb', 'bbbbbb', 'bb', cp.Table([('ccc', 'cc')])))
    self.assertEqual(column_widths.widths, [5, 6, 0])

  def testPassesMaxColumnWidthToNestedTables(self):
    column_widths = cp.ColumnWidths(
        row=('b', 'bbbb', 'bb', cp.Table([('c', 'c', 'cc')])),
        max_column_width=2)
    self.assertEqual(column_widths.widths, [2, 2, 0])

  def testMergeTakesMaxWidthInEachColumn(self):
    widths1 = cp.ColumnWidths(row=('aaa', 'aaaa', 'a'))
    widths2 = cp.ColumnWidths(row=('bb', 'bbbbb', 'bb'))
    merged = widths1.Merge(widths2)
    self.assertEqual(merged.widths, [3, 5, 0])

  def testMergeRetrictsToLargerMaxColumnWidth(self):
    widths1 = cp.ColumnWidths(row=('aaa', 'aaaa', 'a'), max_column_width=3)
    widths2 = cp.ColumnWidths(row=('bb', 'bbbbb', 'bb'), max_column_width=2)
    merged = widths1.Merge(widths2)
    self.assertEqual(merged.widths, [3, 3, 0])

  def testMergeSetsMaxColumnWidthToUnlimitedIfOneUnlimited(self):
    widths1 = cp.ColumnWidths(row=('aaa', 'aaaa', 'a'))
    widths2 = cp.ColumnWidths(row=('bb', 'bbbbb', 'bb'), max_column_width=2)
    merged = widths1.Merge(widths2)
    self.assertEqual(merged.widths, [3, 4, 0])

  def testMergeHandlesReceiverMoreColumns(self):
    widths1 = cp.ColumnWidths(row=('aaa', 'aaaa', 'aaaaaa', 'aa'))
    widths2 = cp.ColumnWidths(row=('bb', 'bbbbb', 'bb'))
    merged = widths1.Merge(widths2)
    self.assertEqual(merged.widths, [3, 5, 6, 0])

  def testMergeHandlesArgumentMoreColumns(self):
    widths1 = cp.ColumnWidths(row=('aaa', 'aaaa', 'aa'))
    widths2 = cp.ColumnWidths(row=('bb', 'bbbbb', 'bbbbbb', 'bb'))
    merged = widths1.Merge(widths2)
    self.assertEqual(merged.widths, [3, 5, 6, 0])


class CustomPrinterTest(test_case.TestCase):

  def testPrinter(self):
    case = cp.Lines([
        'this is a header',
        cp.Labeled([('Foo', 'carrot'), ('Bar', 12),
                    ('Baz',
                     cp.Labeled([('Fun', 'doooodles'),
                                 ('Sun', cp.Lines(['toot', 'taaat', 3]))])),
                    ('Quux', cp.Mapped([('hundred', 'lots'), ('two', 'few')]))])
    ])
    s = io.StringIO()
    p = MockPrinter(out=s)
    p.AddRecord(case)
    self.assertEqual(
        s.getvalue(),
        textwrap.dedent("""\
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

  def testPrinterNonMarkerRecord(self):
    with io.StringIO() as out:
      p = MockPrinter(out=out)
      p.AddRecord('test record')
      self.assertEqual(out.getvalue(), textwrap.dedent("""\
      test record
      ------
      """))

  def testPrinterNoDelimit(self):
    with io.StringIO() as out:
      p = MockPrinter(out=out)
      p.AddRecord('test record', delimit=False)
      self.assertEqual(out.getvalue(), textwrap.dedent("""\
      test record
      """))

  def testPrinterSkipsEmpty(self):
    with io.StringIO() as out:
      p = MockPrinter(out=out)
      p.AddRecord('')
      self.assertEqual(out.getvalue(),
                       textwrap.dedent("""\
      ------
      """))

  def testPrinterAlignsTablesInLines(self):
    case = cp.Lines([
        'title',
        cp.Table([
            ('aaa', 'bbbbbbbb', 'c'),
            ('a', 'bb', 'ccc'),
        ]),
        'middle',
        cp.Table([
            ('a', 'b', 'c'),
            ('a', 'b', 'c'),
        ]),
        'end',
    ])
    with io.StringIO() as out:
      p = MockPrinter(out=out)
      p.AddRecord(case)
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      title
      aaa bbbbbbbb c
      a   bb       ccc
      middle
      a   b        c
      a   b        c
      end
      ------
      """))

  def testPrinterLocallyAlignsTablesWithinSections(self):
    case = cp.Lines([
        'title',
        cp.Table([
            ('aaa', 'bbbbbbbb', 'c'),
            ('a', 'bb', 'ccc'),
        ]),
        'middle',
        cp.Table([
            ('a', 'b', 'c'),
            ('a', 'b', 'c'),
        ]),
        'section',
        cp.Section([cp.Table([
            ('a', 'b', 'c'),
            ('a', 'b', 'c'),
        ])]),
        'end',
    ])
    with io.StringIO() as out:
      p = MockPrinter(out=out)
      p.AddRecord(case)
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      title
      aaa bbbbbbbb c
      a   bb       ccc
      middle
      a   b        c
      a   b        c
      section
      a b c
      a b c
      end
      ------
      """))

  def testPrinterIsolatesTableAlignmentInSections(self):
    case = cp.Lines([
        'title',
        cp.Section([cp.Table([
            ('aaa', 'bbbbbbbb', 'c'),
            ('a', 'bb', 'ccc'),
        ])]),
        'middle',
        cp.Table([
            ('a', 'b', 'c'),
            ('a', 'b', 'c'),
        ]),
        'end',
    ])
    with io.StringIO() as out:
      p = MockPrinter(out=out)
      p.AddRecord(case)
      self.assertEqual(
          out.getvalue(),
          textwrap.dedent("""\
      title
      aaa bbbbbbbb c
      a   bb       ccc
      middle
      a b c
      a b c
      end
      ------
      """))


if __name__ == '__main__':
  test_case.main()
