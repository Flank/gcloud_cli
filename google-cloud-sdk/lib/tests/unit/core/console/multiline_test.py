# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests of the progress_tracker module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import multiline
from tests.lib import parameterized
from tests.lib import test_case


class SimpleSuffixConsoleOutputTest(test_case.TestCase):

  def SetUp(self):
    self.console_size_mock = self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize')
    self.console_size = self.SetConsoleSize(15)

  def SetConsoleSize(self, size):
    self.console_size_mock.return_value = (size + 1, 'unused size')
    return size

  def testUpdateNoMessages(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    ssco.UpdateConsole()
    self.assertEqual('', stream.getvalue())

  def testAddAndUpdateConsole(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    ssco.AddMessage('message')
    self.assertEqual('', stream.getvalue())
    ssco.UpdateConsole()
    self.assertEqual(
        # Update 1
        '\r' + ' ' * self.console_size + '\r' +
        'message',
        stream.getvalue())

  def testAddAndUpdateMessage(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    message = ssco.AddMessage('message')
    ssco.UpdateConsole()
    ssco.UpdateMessage(message, 'suffix')
    ssco.UpdateConsole()
    self.assertEqual(
        # Update 1
        '\r' + ' ' * self.console_size + '\r' +
        'message' +
        # Update 2
        '\r' + ' ' * self.console_size + '\r' +
        'messagesuffix',
        stream.getvalue())

  def testUpdateMessageAddMessageUpdateConsole(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    message = ssco.AddMessage('message')
    ssco.UpdateConsole()
    ssco.UpdateMessage(message, 'suffix')
    ssco.AddMessage('new message')
    ssco.UpdateConsole()
    self.assertEqual(
        # Update 1
        '\r' + ' ' * self.console_size + '\r' +
        'message' +
        # Update 2
        '\r' + ' ' * self.console_size + '\r' +
        'messagesuffix' + '\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'new message',
        stream.getvalue())

  def testMultipleAddsAndUpdateConsoles(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    ssco.AddMessage('message')
    ssco.UpdateConsole()
    ssco.AddMessage('egassem')
    ssco.UpdateConsole()
    ssco.UpdateConsole()
    self.assertEqual(
        # Update 1
        '\r' + ' ' * self.console_size + '\r' +
        'message' +
        # Update 2
        '\r' + ' ' * self.console_size + '\r' +
        'message' +
        '\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'egassem' +
        # Update 2
        '\r' + ' ' * self.console_size + '\r' +
        'egassem',
        stream.getvalue())

  def testMultipleAddsThenUpdateConsole(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    ssco.AddMessage('message1')
    self.assertEqual('', stream.getvalue())
    ssco.AddMessage('message2')
    self.assertEqual('', stream.getvalue())
    ssco.AddMessage('message3')
    self.assertEqual('', stream.getvalue())
    ssco.UpdateConsole()
    self.assertEqual(
        # Update 1
        '\r' + ' ' * self.console_size + '\r' +
        'message1' +
        '\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'message2' +
        '\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'message3',
        stream.getvalue())

  def testUpdateMessageInvalidMessage(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    stray_message = multiline.SuffixConsoleMessage('asdf', stream)
    with self.assertRaisesRegex(
        ValueError,
        'The given message does not belong to this output object.'):
      ssco.UpdateMessage(stray_message, 'fdsa')

  def testUpdateMessageNoMessage(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    with self.assertRaisesRegex(ValueError, 'A message must be passed.'):
      ssco.UpdateMessage(None, 'fdsa')

  def testUpdateMessageUpdatingOldMessage(self):
    stream = io.StringIO()
    ssco = multiline.SimpleSuffixConsoleOutput(stream)
    msg1 = ssco.AddMessage('Im a little ')
    ssco.AddMessage('I make soup in the ')
    with self.assertRaisesRegex(
        ValueError,
        'Only the last added message can be updated.'):
      ssco.UpdateMessage(msg1, 'teapot')


class SuffixConsoleMessageTest(test_case.TestCase, parameterized.TestCase):

  def SetUp(self):
    self.console_size_mock = self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize')
    self.SetConsoleSize(15)

  def SetConsoleSize(self, size):
    self.console_size_mock.return_value = (size + 1, 'unused size')
    return size

  @parameterized.parameters(0, 1)
  def testSingleLine(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage(
        'My message', stream, indentation_level=indentation_level)
    scm.Print()
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'My message' +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'My message',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testSingleLinePrintExactConsoleWidth(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage(
        'a' * 15, stream, indentation_level=indentation_level)
    scm.Print()
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 15 +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 15,
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testMultiline(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage(
        'a' * 20, stream, indentation_level=indentation_level)
    scm.Print()
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 15 + '\n' +
        indentation + 'a' * 5 +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 5,
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testSingleLineBecomesMultiline(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage(
        'a' * 13, stream, indentation_level=indentation_level)
    scm.Print()
    scm._UpdateSuffix('b' * 5)
    scm.Print()
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 13 +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 13 + 'b' * 2 + '\n' +
        indentation + 'bbb' +
        # Print 3
        '\r' + ' ' * console_size + '\r' +
        indentation + 'bbb',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testSinglineBecomesMultilineViaCallback(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    msg = None
    scm = multiline.SuffixConsoleMessage(
        'a' * 13,
        stream,
        detail_message_callback=lambda: msg,
        indentation_level=indentation_level)
    scm.Print()
    msg = 'b' * 5
    scm.Print()
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 13 +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 13 + 'b' * 2 + '\n' +
        indentation + 'bbb' +
        # Print 3
        '\r' + ' ' * console_size + '\r' +
        indentation + 'bbb',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testMultilineBecomesSingleline(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage('a' * 5,
                                         stream,
                                         suffix='b' * 15,
                                         indentation_level=indentation_level)
    scm.Print()
    # This makes the output single line.
    scm._UpdateSuffix('b' * 5)
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 5 + 'b' * 10 + '\n' +
        indentation + 'bbbbb' +
        # Print 2
        '\n' +
        indentation + 'a' * 5 + 'b' * 5,
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testsingleLinePrefixWithDiffMultilineSuffix(self, indentation_level):
    console_size = self.SetConsoleSize(5 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage('a' * 5,
                                         stream,
                                         suffix='b' * 10,
                                         indentation_level=indentation_level)
    scm.Print()
    # In this case the multiline print can't do better and is forced to reprint
    # everything.
    scm._UpdateSuffix('c' * 10)
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'aaaaa\n' +
        indentation + 'bbbbb\n' +
        indentation + 'bbbbb' +
        # Print 2
        '\n' +
        indentation + 'aaaaa\n' +
        indentation + 'ccccc\n' +
        indentation + 'ccccc',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testMultilineBecomesShorterMultiline(self, indentation_level):
    console_size = self.SetConsoleSize(5 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage('a' * 5,
                                         stream,
                                         suffix='b' * 10,
                                         indentation_level=indentation_level)
    scm.Print()
    # In this case the multiline print can't do better and is forced to reprint
    # everything.
    scm._UpdateSuffix('b' * 5)
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'aaaaa\n' +
        indentation + 'bbbbb\n' +
        indentation + 'bbbbb' +
        # Print 2
        '\n' +
        indentation + 'aaaaa\n' +
        indentation + 'bbbbb',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testTwoDiffMultiThenSingle(self, indentation_level):
    """Tests transition from multiline to different multiline to single line."""
    console_size = self.SetConsoleSize(5 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage('a' * 5,
                                         stream,
                                         suffix='b' * 10,
                                         indentation_level=indentation_level)
    scm.Print()
    scm._UpdateSuffix('c' * 15)
    scm.Print()
    scm._UpdateSuffix('')
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'aaaaa\n' +
        indentation + 'bbbbb\n' +
        indentation + 'bbbbb' +
        # Print 2
        '\n' +
        indentation + 'aaaaa\n' +
        indentation + 'ccccc\n' +
        indentation + 'ccccc\n' +
        indentation + 'ccccc' +
        '\n' +
        indentation + 'aaaaa',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testGraduallyIncreasingLines(self, indentation_level):
    console_size = self.SetConsoleSize(5 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage('The',
                                         stream,
                                         indentation_level=indentation_level)
    scm.Print()
    scm._UpdateSuffix(' quick')
    scm.Print()
    scm._UpdateSuffix(' quick brown')
    scm.Print()
    scm._UpdateSuffix(' quick brown fox')
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'The' +
        '\r' + ' ' * console_size + '\r' +
        indentation + 'The q\n' +
        indentation + 'uick' +
        '\r' + ' ' * console_size + '\r' +
        indentation + 'uick \n' +
        indentation + 'brown' +
        '\r' + ' ' * console_size + '\r' +
        indentation + 'brown\n' +
        indentation + ' fox',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testPrintAll(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage(
        'a' * 20, stream, indentation_level=indentation_level)
    scm.Print()
    scm.Print()
    scm.Print(print_all=True)
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 15 + '\n' +
        indentation + 'a' * 5 +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 5 +
        # Print 3 with print_all set to True
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 15 + '\n' +
        indentation + 'a' * 5,
        stream.getvalue())

  def testNoMessage(self):
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage('', stream)
    scm.Print()
    scm.Print()
    self.assertEqual('', stream.getvalue())

  def testNoMessageUpdateNoMessage(self):
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage('', stream)
    scm.Print()
    scm._UpdateSuffix('')
    scm.Print()
    self.assertEqual('', stream.getvalue())

  # One level of indentation is equal to two spaces.
  @parameterized.parameters((0, 0), (2, 1), (2, 2))
  def testConsoleTooSmall(self, console_width, indentation):
    self.SetConsoleSize(console_width)
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage(
        'a', stream, indentation_level=indentation)
    scm.Print()
    scm.Print()
    self.assertEqual('', stream.getvalue())

  # One level of indentation is equal to two spaces.
  @parameterized.parameters(1, None, ([],))
  def testUpdateWithInvalidMessage(self, new_suffix):
    stream = io.StringIO()
    scm = multiline.SuffixConsoleMessage('', stream)
    with self.assertRaisesRegex(
        TypeError, 'expected a string or other character buffer object'):
      scm._UpdateSuffix(new_suffix)


class MultilineConsoleMessageTest(test_case.TestCase, parameterized.TestCase):

  def SetUp(self):
    self.console_size_mock = self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize')
    self.SetConsoleSize(15)

  def SetConsoleSize(self, size):
    self.console_size_mock.return_value = (size + 1, 'unused size')
    return size

  @parameterized.parameters(0, 1)
  def testPrintAddsNewlineToLastLine(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.MultilineConsoleMessage(
        'My message', stream, indentation_level=indentation_level)
    scm.Print()
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'My message\n' +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'My message\n',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testPrintAddsNewlineToLastLineMultipleLines(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.MultilineConsoleMessage(
        'a' * 20, stream, indentation_level=indentation_level)
    scm.Print()
    scm.Print()
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 15 + '\n' +
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 5 + '\n' +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 15 + '\n' +
        '\r' + ' ' * console_size + '\r' +
        indentation + 'a' * 5 + '\n',
        stream.getvalue())

  @parameterized.parameters(0, 1)
  def testHasUpdate(self, indentation_level):
    console_size = self.SetConsoleSize(15 + 2 * indentation_level)
    indentation = ' ' * 2 * indentation_level
    stream = io.StringIO()
    scm = multiline.MultilineConsoleMessage(
        'My message', stream, indentation_level=indentation_level)
    self.assertTrue(scm.has_update)
    scm.Print()
    self.assertFalse(scm.has_update)
    scm._UpdateMessage('egassem yM')
    self.assertTrue(scm.has_update)
    scm.Print()
    self.assertFalse(scm.has_update)
    self.assertEqual(
        # Print 1
        '\r' + ' ' * console_size + '\r' +
        indentation + 'My message\n' +
        # Print 2
        '\r' + ' ' * console_size + '\r' +
        indentation + 'egassem yM\n',
        stream.getvalue())


class MultilineConsoleOutputTest(test_case.WithOutputCapture):

  def SetUp(self):
    self.console_size_mock = self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize')
    self.console_size = self.SetConsoleSize(15)
    self.ansi_cursor_up = '\x1b[{}A'

  def SetConsoleSize(self, size):
    self.console_size_mock.return_value = (size + 1, 'unused size')
    return size

  def testUpdateNoMessages(self):
    stream = io.StringIO()
    mco = multiline.MultilineConsoleOutput(stream)
    mco.UpdateConsole()
    self.assertEqual('', stream.getvalue())

  def testAddAndUpdateConsole(self):
    stream = io.StringIO()
    mco = multiline.MultilineConsoleOutput(stream)
    mco.AddMessage('message')
    self.assertEqual('', stream.getvalue())
    mco.UpdateConsole()
    mco.UpdateConsole()
    self.assertEqual(
        # Update 1 (Update 2 is empty as no update necessary)
        '\r' + ' ' * self.console_size + '\r' +
        'message\n',
        stream.getvalue())

  def testAddAndUpdateMessage(self):
    stream = io.StringIO()
    mco = multiline.MultilineConsoleOutput(stream)
    message = mco.AddMessage('message')
    mco.UpdateConsole()
    mco.UpdateMessage(message, 'egassem')
    mco.UpdateConsole()
    self.assertEqual(
        # Update 1
        '\r' + ' ' * self.console_size + '\r' +
        'message\n' +
        # Update 2
        self.ansi_cursor_up.format(1) +
        '\r' + ' ' * self.console_size + '\r' +
        'egassem\n',
        stream.getvalue())

  def testAddUpdateAddMessage(self):
    stream = io.StringIO()
    mco = multiline.MultilineConsoleOutput(stream)
    message = mco.AddMessage('message')
    mco.UpdateConsole()
    mco.UpdateMessage(message, 'egassem')
    mco.AddMessage('asdf')
    mco.UpdateConsole()
    self.assertEqual(
        # Update 1
        '\r' + ' ' * self.console_size + '\r' +
        'message\n' +
        # Update 2
        self.ansi_cursor_up.format(1) +
        '\r' + ' ' * self.console_size + '\r' +
        'egassem\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'asdf\n',
        stream.getvalue())

  def testMessagesGetShorter(self):
    stream = io.StringIO()
    mco = multiline.MultilineConsoleOutput(stream)
    message1 = mco.AddMessage('a' * 20)
    message2 = mco.AddMessage('b' * 20)
    mco.UpdateConsole()
    mco.UpdateMessage(message1, 'c' * 5)
    mco.UpdateMessage(message2, 'd' * 5)
    mco.UpdateConsole()
    self.assertEqual(
        # Update 1
        '\r' + ' ' * self.console_size + '\r' +
        'a' * 15 + '\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'a' * 5 + '\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'b' * 15 + '\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'b' * 5 + '\n' +
        # Update 2
        self.ansi_cursor_up.format(4) +
        '\r' + ' ' * self.console_size + '\r' +
        'c' * 5 + '\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'd' * 5 + '\n',
        stream.getvalue())

  def testUpdateMessageInvalidMessage(self):
    stream = io.StringIO()
    mco = multiline.MultilineConsoleOutput(stream)
    stray_message = multiline.MultilineConsoleMessage('asdf', stream)
    with self.assertRaisesRegex(
        ValueError,
        'The given message does not belong to this output object.'):
      mco.UpdateMessage(stray_message, 'fdsa')

  def testUpdateMessageNoMessage(self):
    stream = io.StringIO()
    mco = multiline.MultilineConsoleOutput(stream)
    with self.assertRaisesRegex(ValueError, 'A message must be passed.'):
      mco.UpdateMessage(None, 'fdsa')

  def testMessageContainsAnsiCodes(self):
    self.StartEnvPatch({'TERM': 'screen'})
    self.SetEncoding('utf-8')
    self.console_size = self.SetConsoleSize(20)
    message = ('This is a line constructed from \x1b[31;1mcolorized\x1b[39;0m '
               'parts and long enough to be split into \x1b[34;1m'
               'multiple\x1b[39;0m lines at \x1b[32mwidth=20\x1b[39;0m.')
    stream = io.StringIO()
    mco = multiline.MultilineConsoleOutput(stream)
    mco.AddMessage(message)
    mco.UpdateConsole()
    self.assertEqual(
        '\r' + ' ' * self.console_size + '\r' +
        'This is a line const\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'ructed from \x1b[31;1mcolorize\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'd\x1b[39;0m parts and long eno\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'ugh to be split into\n' +
        '\r' + ' ' * self.console_size + '\r' +
        ' \x1b[34;1mmultiple\x1b[39;0m lines at \x1b[32mw\n' +
        '\r' + ' ' * self.console_size + '\r' +
        'idth=20\x1b[39;0m.\n',
        stream.getvalue())


if __name__ == '__main__':
  test_case.main()
