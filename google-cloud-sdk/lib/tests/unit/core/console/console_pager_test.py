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

# Tests for the console_pager module.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_pager
from tests.lib import test_case


class ConsolePagerTests(test_case.WithOutputCapture):

  def SetUp(self):
    self.StartObjectPatch(console_attr.ConsoleAttr,
                          'GetFontCode').side_effect = self.MockGetFontCode
    self.StartObjectPatch(console_attr.ConsoleAttr,
                          'GetRawKey').side_effect = self.MockGetRawKey
    self.StartObjectPatch(console_attr.ConsoleAttr,
                          'GetTermSize').side_effect = self.MockGetTermSize
    self.raw_keys = None
    self.term_size = (20, 10)

  def MockGetFontCode(self, bold=False):
    return '<B>' if bold else '</B>'

  def MockGetRawKey(self):
    return self.raw_keys.pop(0) if self.raw_keys else None

  def MockGetTermSize(self):
    return self.term_size

  def SetRawKeys(self, keys):
    self.raw_keys = keys

  def Prompt(self, percent=100):
    return ('<B>--({percent}%)--</B>'
            '\r                 \r'.format(percent=percent))

  def testPagerBlankQuit(self):
    self.SetRawKeys(['q'])
    contents = '1\n2\n\n3\n4\n\n5\n'
    expected = contents
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual(['q'], self.raw_keys)

  def testPagerUnderQuit(self):
    self.SetRawKeys(['q'])
    contents = '1\n2\n3\n4\n5\n'
    expected = contents
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual(['q'], self.raw_keys)

  def testPagerAtQuit(self):
    self.SetRawKeys(['q'])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n'
    expected = contents
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual(['q'], self.raw_keys)

  def testPagerOverQuit(self):
    self.SetRawKeys(['q'])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n'
    expected = '1\n2\n3\n4\n5\n6\n7\n8\n9\n%s' % self.Prompt(81)
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerOverHelpQuit(self):
    self.SetRawKeys(['h', 'X', 'q'])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n'
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '%s\n'
                '1\n2\n3\n4\n5\n6\n7\n8\n9\n%s' % (
                    self.Prompt(81),
                    console_pager.Pager.HELP_TEXT,
                    self.Prompt(81)))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerOverNextQuit(self):
    self.SetRawKeys([' ', 'q'])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n'
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '10\n11\n%s') % (self.Prompt(81),
                                 self.Prompt(100))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerOverNextBoundaryQuit(self):
    self.SetRawKeys([' ', ' ', 'q'])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n'
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '10\n11\n%s'
                '%s') % (self.Prompt(81), self.Prompt(100), self.Prompt(100))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerThreePagesBackAndForthBoundary(self):
    self.SetRawKeys([' ', ' ', ' ', 'b', 'b', 'b', ' ', ' ', ' ', 'q'])
    contents = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n'
                '11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n'
                '21\n22\n23\n24\n25\n26\n27\n')
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '10\n11\n12\n13\n14\n15\n16\n17\n18\n%s'
                '19\n20\n21\n22\n23\n24\n25\n26\n27\n%s'
                '%s'
                '10\n11\n12\n13\n14\n15\n16\n17\n18\n%s'
                '1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '%s'
                '10\n11\n12\n13\n14\n15\n16\n17\n18\n%s'
                '19\n20\n21\n22\n23\n24\n25\n26\n27\n%s'
                '%s') % (self.Prompt(33),
                         self.Prompt(66),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(66),
                         self.Prompt(33),
                         self.Prompt(33),
                         self.Prompt(66),
                         self.Prompt(100),
                         self.Prompt(100))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerThreePagesForwardSearch(self):
    self.SetRawKeys(['/', '^', '.', '1', '\n', '/', '\n', 'n', 'n', 'N', 'N',
                     'N', 'q'])
    contents = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n'
                '11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n'
                '21\n22\n23\n24\n25\n26\n27\n')
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '/^.1\r   \r'
                '11\n12\n13\n14\n15\n16\n17\n18\n19\n%s'
                '/\r\r'
                '20\n21\n22\n23\n24\n25\n26\n27\n%s'
                '%s'
                '%s'
                '11\n12\n13\n14\n15\n16\n17\n18\n19\n%s'
                '%s'
                '%s') % (self.Prompt(33),
                         self.Prompt(70),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(70),
                         self.Prompt(70),
                         self.Prompt(70))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerThreePagesBackwardSearch(self):
    self.SetRawKeys(['G', '?', '^', '.', '1', '\n', '?', '\n', 'n', 'n', 'N',
                     'N', 'N', 'q'])
    contents = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n'
                '11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n'
                '21\n22\n23\n24\n25\n26\n27\n')
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '19\n20\n21\n22\n23\n24\n25\n26\n27\n%s'
                '?^.1\r   \r'
                '11\n12\n13\n14\n15\n16\n17\n18\n19\n%s'
                '?\r\r%s'
                '%s'
                '%s'
                '20\n21\n22\n23\n24\n25\n26\n27\n%s'
                '%s'
                '%s') % (self.Prompt(33),
                         self.Prompt(100),
                         self.Prompt(70),
                         self.Prompt(70),
                         self.Prompt(70),
                         self.Prompt(70),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(100))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerOnePagePlusTwoLinesBoundaryBanger(self):
    self.SetRawKeys(['f', 'f', 'j', 'j', 'j', 'k', 'k', 'k', 'b', 'f', 'f',
                     'q'])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n'
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '10\n11\n%s'
                '%s'
                '%s'
                '%s'
                '%s'
                '2\n3\n4\n5\n6\n7\n8\n9\n10\n%s'
                '1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '%s'
                '%s'
                '10\n11\n%s'
                '%s') % (self.Prompt(81),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(90),
                         self.Prompt(81),
                         self.Prompt(81),
                         self.Prompt(81),
                         self.Prompt(100),
                         self.Prompt(100))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerOnePagePlusTwoLinesBoundaryBangerViaFunctionKeys(self):
    self.SetRawKeys(['<PAGE-DOWN>', '<PAGE-DOWN>', '<DOWN-ARROW>',
                     '<DOWN-ARROW>', '<DOWN-ARROW>', '<UP-ARROW>',
                     '<UP-ARROW>', '<UP-ARROW>', '<PAGE-UP>', '<PAGE-DOWN>',
                     '<PAGE-DOWN>', None])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n'
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '10\n11\n%s'
                '%s'
                '%s'
                '%s'
                '%s'
                '2\n3\n4\n5\n6\n7\n8\n9\n10\n%s'
                '1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '%s'
                '%s'
                '10\n11\n%s'
                '%s') % (self.Prompt(81),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(100),
                         self.Prompt(90),
                         self.Prompt(81),
                         self.Prompt(81),
                         self.Prompt(81),
                         self.Prompt(100),
                         self.Prompt(100))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerOnePagePlusTwoWithWidesLines(self):
    self.SetRawKeys(['f', 'f', 'k', 'k', 'k', 'k', 'q'])
    contents = (
        'A2345678901234567890abcdef\n'
        'B2345678901234567890abcdef\n'
        'C2345678901234567890abcdef\n'
        'D2345678901234567890abcdef\n'
        'E2345678901234567890abcdef\n'
        'F2345678901234567890abcdef\n'
        'G2345678901234567890abcdef\n'
        'H2345678901234567890abcdef\n'
        'I2345678901234567890abcdef\n'
        )
    expected = (
        'A2345678901234567890\nabcdef\n'
        'B2345678901234567890\nabcdef\n'
        'C2345678901234567890\nabcdef\n'
        'D2345678901234567890\nabcdef\n'
        'E2345678901234567890\n'
        '%s'
        'abcdef\n'
        'F2345678901234567890\nabcdef\n'
        'G2345678901234567890\nabcdef\n'
        'H2345678901234567890\nabcdef\n'
        'I2345678901234567890\nabcdef\n'
        '%s'
        '%s'
        'E2345678901234567890\nabcdef\n'
        'F2345678901234567890\nabcdef\n'
        'G2345678901234567890\nabcdef\n'
        'H2345678901234567890\nabcdef\n'
        'I2345678901234567890\n'
        '%s'
        'abcdef\n'
        'E2345678901234567890\nabcdef\n'
        'F2345678901234567890\nabcdef\n'
        'G2345678901234567890\nabcdef\n'
        'H2345678901234567890\nabcdef\n'
        '%s'
        'D2345678901234567890\nabcdef\n'
        'E2345678901234567890\nabcdef\n'
        'F2345678901234567890\nabcdef\n'
        'G2345678901234567890\nabcdef\n'
        'H2345678901234567890\n'
        '%s'
        'abcdef\n'
        'D2345678901234567890\nabcdef\n'
        'E2345678901234567890\nabcdef\n'
        'F2345678901234567890\nabcdef\n'
        'G2345678901234567890\nabcdef\n'
        '%s') % (self.Prompt(50),
                 self.Prompt(100),
                 self.Prompt(100),
                 self.Prompt(94),
                 self.Prompt(88),
                 self.Prompt(83),
                 self.Prompt(77))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerBadSearchPattern(self):
    self.SetRawKeys(['/', '*', '1', '\n', 'q'])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n'
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '/*1\r  \r%s') % (
                    self.Prompt(81),
                    self.Prompt(81))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)

  def testPagerCountPosition(self):
    self.SetRawKeys(['1', '0', 'g', 'q'])
    contents = '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n'
    expected = ('1\n2\n3\n4\n5\n6\n7\n8\n9\n%s'
                '%s'
                '%s'
                '10\n11\n'
                '%s') % (
                    self.Prompt(81),
                    self.Prompt(81),
                    self.Prompt(81),
                    self.Prompt(100))
    console_pager.Pager(contents).Run()
    self.AssertOutputEquals(expected)
    self.assertEqual([], self.raw_keys)


if __name__ == '__main__':
  test_case.main()
