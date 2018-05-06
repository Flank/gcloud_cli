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

"""Tests for the console_attr module."""

from __future__ import absolute_import
from __future__ import unicode_literals
import io
import sys

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_attr_os
from tests.lib import test_case

import mock
import six


class _Object(object):

  def __init__(self, name='abc', value=123):
    self._name = name
    self._value = value

  def __str__(self):
    return '{name}={value}'.format(name=self._name, value=self._value)


_ASCII = 'Unicode'
_ISO_8859_1 = b'\xdc\xf1\xee\xe7\xf2\xd0\xe9'  # ÜñîçòÐé
_UNICODE = 'Ṳᾔḯ¢◎ⅾℯ'
_UTF8 = _UNICODE.encode('utf8')


class ConsoleAttrTestBase(test_case.WithOutputCapture):
  """Save and restore console attributes state."""

  def TearDown(self):
    console_attr.ResetConsoleAttr()


class ConsoleAttrEncodingTests(ConsoleAttrTestBase):

  def testEncodingUnknown(self):
    attr = console_attr.GetConsoleAttr(encoding='unknown', reset=True)
    self.assertEqual(attr.GetEncoding(), 'unknown')

  def testEncodingAscii(self):
    attr = console_attr.GetConsoleAttr(encoding='ascii', reset=True)
    self.assertEqual(attr.GetEncoding(), 'ascii')

  def testResetEncodingAscii(self):
    attr = console_attr.ResetConsoleAttr(encoding='ascii')
    self.assertEqual(attr.GetEncoding(), 'ascii')

  def testEncodingUtf8(self):
    attr = console_attr.GetConsoleAttr(encoding='utf8', reset=True)
    self.assertEqual(attr.GetEncoding(), 'utf8')

  def testResetEncodingUtf8(self):
    attr = console_attr.ResetConsoleAttr(encoding='utf8')
    self.assertEqual(attr.GetEncoding(), 'utf8')

  def testEncodingWin(self):
    attr = console_attr.GetConsoleAttr(encoding='win', reset=True)
    self.assertEqual(attr.GetEncoding(), 'cp437')

    attr = console_attr.GetConsoleAttr(encoding='cp437', reset=True)
    self.assertEqual(attr.GetEncoding(), 'cp437')

  def testResetEncodingWin(self):
    attr = console_attr.ResetConsoleAttr(encoding='win')
    self.assertEqual(attr.GetEncoding(), 'cp437')

    attr = console_attr.ResetConsoleAttr(encoding='cp437')
    self.assertEqual(attr.GetEncoding(), 'cp437')

  def testEncodingStdOutUtf8(self):
    sys.stdout = mock.MagicMock()
    sys.stdout.encoding = 'UTF-8'
    log.Reset()
    attr = console_attr.GetConsoleAttr(reset=True)
    self.assertEqual(attr.GetEncoding(), 'utf8')

  def testEncodingStdOutWin(self):
    sys.stdout = mock.MagicMock()
    sys.stdout.encoding = 'CP437'
    attr = console_attr.GetConsoleAttr(reset=True)
    self.assertEqual(attr.GetEncoding(), 'cp437')


class AsciiConsoleAttrTests(ConsoleAttrTestBase):

  def SetUp(self):
    self.StartEnvPatch({'TERM': 'dumb'})
    self.buf = io.StringIO()
    self._con = console_attr.GetConsoleAttr(encoding='ascii', reset=True)

  def testBoxLineCharactersAscii(self):
    box = self._con.GetBoxLineCharacters()
    self.assertTrue(isinstance(box, console_attr.BoxLineCharactersAscii))

  def testBulletsAscii(self):
    bullets = self._con.GetBullets()
    self.assertEqual(bullets, self._con._BULLETS_ASCII)

  def testFontBoldAscii(self):
    font = self._con.GetFontCode(bold=True)
    self.assertEqual(font, '')

  def testFontItalicAscii(self):
    font = self._con.GetFontCode(italic=True)
    self.assertEqual(font, '')

  def testFontBoldItalicAscii(self):
    font = self._con.GetFontCode(bold=True, italic=True)
    self.assertEqual(font, '')

  def testFontResetAscii(self):
    font = self._con.GetFontCode()
    self.assertEqual(font, '')

  def testGetControlSequenceIndicatorAscii(self):
    self.assertEqual(self._con.GetControlSequenceIndicator(), None)

  def testGetControlSequenceLenAscii(self):
    self.assertEqual(self._con.GetControlSequenceLen('No control.'), 0)

  def testDisplayWidthNoneAscii(self):
    s = 'This is a test.\n'
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthBeginAscii(self):
    s = '{0}This is a test.\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthMiddleAscii(self):
    s = 'This is {0}a test.\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthEndAscii(self):
    s = 'This is a test.{0}\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testColorizeAscii(self):
    s = 'This is a test.'
    self.assertEqual(
        '    This is a test.     ',
        self._con.Colorize(s, 'red', justify=lambda s: s.center(24)))

  def testHomogenizedColorizerSortAscii(self):
    colors = [
        console_attr.Colorizer('RED', 'red'),
        console_attr.Colorizer('GREEN', 'green'),
        console_attr.Colorizer('BLUE', 'blue'),
        console_attr.Colorizer('YELLOW', 'yellow'),
        ]
    expected = [colors[2], colors[1], colors[0], colors[3]]
    actual = sorted(colors)
    self.assertEqual(expected, actual)

  def testMixedColorizerSortAscii(self):
    colors = [
        console_attr.Colorizer('RED', 'red'),
        'GREEN',
        console_attr.Colorizer('BLUE', 'blue'),
        'YELLOW',
        ]
    expected = [colors[2], colors[1], colors[0], colors[3]]
    actual = sorted(colors)
    self.assertEqual(expected, actual)

  def testSplitIntoNormalAndControlAscii(self):
    self.buf.write('This is a line constructed from ')
    console_attr.Colorizer('colorized', 'red').Render(self.buf)
    self.buf.write(' parts and long enough to be split into ')
    console_attr.Colorizer('multiple', 'blue').Render(self.buf)
    self.buf.write(' lines at ')
    console_attr.Colorizer('width=20', 'green').Render(self.buf)
    self.buf.write('.\n')
    line = self.buf.getvalue()

    expected = [
        ('This is a line constructed from colorized parts and long enough to '
         'be split into multiple lines at width=20.\n',
         ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(line)
    self.assertEqual(expected, actual)

  def testSplitLineAscii(self):
    self.buf.write('This is a line constructed from ')
    console_attr.Colorizer('colorized', 'red').Render(self.buf)
    self.buf.write(' parts and long enough to be split into ')
    console_attr.Colorizer('multiple', 'blue').Render(self.buf)
    self.buf.write(' lines at ')
    console_attr.Colorizer('width=32', 'green').Render(self.buf)
    self.buf.write('.\n')
    line = self.buf.getvalue()

    lines = self._con.SplitLine(line, width=32)
    self.assertEqual(4, len(lines))

    expected = [
        ('This is a line constructed from ', ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(lines[0])
    self.assertEqual(expected, actual)

    expected = [
        ('colorized parts and long enough ', ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(lines[1])
    self.assertEqual(expected, actual)

    expected = [
        ('to be split into multiple lines ', ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(lines[2])
    self.assertEqual(expected, actual)

    expected = [
        ('at width=32.\n', ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(lines[3])
    self.assertEqual(expected, actual)


class Utf8ConsoleAttrTests(ConsoleAttrTestBase):

  def SetUp(self):
    self.StartEnvPatch({'TERM': 'dumb'})
    self._con = console_attr.GetConsoleAttr(encoding='utf8', reset=True)

  def testBoxLineCharactersUnicode(self):
    box = self._con.GetBoxLineCharacters()
    self.assertTrue(isinstance(box, console_attr.BoxLineCharactersUnicode))

  def testBulletsUtf8(self):
    bullets = self._con.GetBullets()
    self.assertEqual(bullets, self._con._BULLETS_UNICODE)


class WinConsoleAttrTests(ConsoleAttrTestBase):

  def SetUp(self):
    self.StartEnvPatch({'TERM': 'dumb'})
    self._con = console_attr.GetConsoleAttr(encoding='win', reset=True)

  def testBoxLineCharactersUnicodeWin(self):
    box = self._con.GetBoxLineCharacters()
    self.assertTrue(isinstance(box, console_attr.BoxLineCharactersUnicode))

  def testBulletsWin(self):
    bullets = self._con.GetBullets()
    self.assertEqual(bullets, self._con._BULLETS_WINDOWS)


class ScreenConsoleAttrTests(ConsoleAttrTestBase):

  _TEST = 'This is a test.'

  def SetUp(self):
    self.StartEnvPatch({'TERM': 'screen'})
    self.buf = io.StringIO()
    self._con = console_attr.GetConsoleAttr(encoding='utf8', reset=True)

  def testFontBoldScreen(self):
    font = self._con.GetFontCode(bold=True)
    self.assertEqual(font, '\x1b[1m')

  def testFontItalicScreen(self):
    font = self._con.GetFontCode(italic=True)
    self.assertEqual(font, '\x1b[4m')

  def testFontBoldItalicScreen(self):
    font = self._con.GetFontCode(bold=True, italic=True)
    self.assertEqual(font, '\x1b[1;4m')

  def testFontResetScreen(self):
    font = self._con.GetFontCode()
    self.assertEqual(font, '\x1b[m')

  def testGetControlSequenceIndicatorScreen(self):
    self.assertEqual(self._con.GetControlSequenceIndicator(), '\x1b[')

  def testGetControlSequenceLenSCreen(self):
    self.assertEqual(self._con.GetControlSequenceLen('No control.'), 0)

  def testDisplayWidthBeginScreen(self):
    s = '{0}'.format(self._TEST)
    self.assertEqual(len(self._TEST), self._con.DisplayWidth(s))

  def testDisplayWidthMiddleScreen(self):
    s = 'This is {0}a test.'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(len(self._TEST), self._con.DisplayWidth(s))

  def testDisplayWidthEndScreen(self):
    s = '{0}{1}'.format(self._TEST, self._con.GetFontCode(bold=True))
    self.assertEqual(len(self._TEST), self._con.DisplayWidth(s))

  def testDisplayWidthMiddleUnicodeScreen(self):
    s = u'This is {0}a UÜ車 test.'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(20, self._con.DisplayWidth(s))

  def testColorizeRedCenterScreen(self):
    actual = self._con.Colorize(
        self._TEST, 'red', justify=lambda s: s.center(len(s) + 5))
    self.assertEqual('\x1b[31;1m  {0}   \x1b[39;0m'.format(self._TEST), actual)

  def testColorizeYellowLeftScreen(self):
    actual = self._con.Colorize(
        self._TEST, 'yellow', justify=lambda s: s.ljust(len(s) + 5))
    self.assertEqual('\x1b[33;1m{0}     \x1b[39;0m'.format(self._TEST), actual)

  def testColorizeGreenRightScreen(self):
    actual = self._con.Colorize(
        self._TEST, 'green', justify=lambda s: s.rjust(len(s) + 5))
    self.assertEqual('\x1b[32m     {0}\x1b[39;0m'.format(self._TEST), actual)

  def testColorizeBlueScreen(self):
    actual = self._con.Colorize(self._TEST, 'blue')
    self.assertEqual('\x1b[34;1m{0}\x1b[39;0m'.format(self._TEST), actual)

  def testColorizerRedCenterScreen(self):
    colorize = console_attr.Colorizer(self._TEST, 'red',
                                      justify=lambda s: s.center(len(s) + 5))
    self.assertEqual(self._TEST, str(colorize))
    self.assertEqual(len(self._TEST), len(colorize))
    colorize.Render(self.buf)
    self.assertEqual('\x1b[31;1m  {0}   \x1b[39;0m'.format(self._TEST),
                     self.buf.getvalue())

  def testColorizerYellowLeftScreen(self):
    colorize = console_attr.Colorizer(self._TEST, 'yellow')
    self.assertEqual(self._TEST, str(colorize))
    self.assertEqual(len(self._TEST), len(colorize))
    colorize.Render(self.buf, justify=lambda s: s.ljust(len(s) + 5))
    self.assertEqual('\x1b[33;1m{0}     \x1b[39;0m'.format(self._TEST),
                     self.buf.getvalue())

  def testColorizerGreenRightScreen(self):
    colorize = console_attr.Colorizer(self._TEST, 'green',
                                      justify=lambda s: s.rjust(len(s) + 5))
    self.assertEqual(self._TEST, str(colorize))
    self.assertEqual(len(self._TEST), len(colorize))
    colorize.Render(self.buf)
    self.assertEqual('\x1b[32m     {0}\x1b[39;0m'.format(self._TEST),
                     self.buf.getvalue())

  def testColorizerBlueScreen(self):
    colorize = console_attr.Colorizer(self._TEST, 'blue')
    self.assertEqual(self._TEST, str(colorize))
    self.assertEqual(len(self._TEST), len(colorize))
    colorize.Render(self.buf)
    self.assertEqual('\x1b[34;1m{0}\x1b[39;0m'.format(self._TEST),
                     self.buf.getvalue())

  def testHomogenizedColorizerSortScreen(self):
    colors = [
        console_attr.Colorizer('RED', 'red'),
        console_attr.Colorizer('GREEN', 'green'),
        console_attr.Colorizer('BLUE', 'blue'),
        console_attr.Colorizer('YELLOW', 'yellow'),
        ]
    expected = [colors[2], colors[1], colors[0], colors[3]]
    actual = sorted(colors)
    self.assertEqual(expected, actual)

  def testMixedColorizerSortScreen(self):
    colors = [
        console_attr.Colorizer('RED', 'red'),
        'GREEN',
        console_attr.Colorizer('BLUE', 'blue'),
        'YELLOW',
        ]
    expected = [colors[2], colors[1], colors[0], colors[3]]
    actual = sorted(colors)
    self.assertEqual(expected, actual)

  def testSplitIntoNormalAndControlScreen(self):
    self.buf.write('This is a line constructed from ')
    console_attr.Colorizer('colorized', 'red').Render(self.buf)
    self.buf.write(' parts and long enough to be split into ')
    console_attr.Colorizer('multiple', 'blue').Render(self.buf)
    self.buf.write(' lines at ')
    console_attr.Colorizer('width=20', 'green').Render(self.buf)
    self.buf.write('.\n')
    line = self.buf.getvalue()

    expected = [
        ('This is a line constructed from ', '\x1b[31;1m'),
        ('colorized', '\x1b[39;0m'),
        (' parts and long enough to be split into ', '\x1b[34;1m'),
        ('multiple', '\x1b[39;0m'),
        (' lines at ', '\x1b[32m'),
        ('width=20', '\x1b[39;0m'),
        ('.\n', ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(line)
    self.assertEqual(expected, actual)

  def testSplitLineScreen(self):
    self.buf.write('This is a line constructed from ')
    console_attr.Colorizer('colorized', 'red').Render(self.buf)
    self.buf.write(' parts and long enough to be split into ')
    console_attr.Colorizer('multiple', 'blue').Render(self.buf)
    self.buf.write(' lines at ')
    console_attr.Colorizer('width=32', 'green').Render(self.buf)
    self.buf.write('.\n')
    line = self.buf.getvalue()

    lines = self._con.SplitLine(line, width=32)
    self.assertEqual(4, len(lines))

    expected = [
        ('This is a line constructed from ', '\x1b[31;1m'),
        ]
    actual = self._con.SplitIntoNormalAndControl(lines[0])
    self.assertEqual(expected, actual)

    expected = [
        ('colorized', '\x1b[39;0m'),
        (' parts and long enough ', ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(lines[1])
    self.assertEqual(expected, actual)

    expected = [
        ('to be split into ', '\x1b[34;1m'),
        ('multiple', '\x1b[39;0m'),
        (' lines ', ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(lines[2])
    self.assertEqual(expected, actual)

    expected = [
        ('at ', '\x1b[32m'),
        ('width=32', '\x1b[39;0m'),
        ('.\n', ''),
        ]
    actual = self._con.SplitIntoNormalAndControl(lines[3])
    self.assertEqual(expected, actual)


class ScreenDefaultOutDefaultInitTests(ConsoleAttrTestBase):

  def SetUp(self):
    self.StartEnvPatch({'TERM': 'screen'})

  def testColorizerBlueScreenDefaultOutImplicitInit(self):
    console_attr.ResetConsoleAttr(encoding='UTF-8')
    s = 'Am I blue?'
    colorize = console_attr.Colorizer(s, 'blue')
    colorize.Render(sys.stdout)
    self.AssertOutputEquals('\x1b[34;1m{0}\x1b[39;0m'.format(s))


class XtermConsoleAttrTests(ConsoleAttrTestBase):

  def SetUp(self):
    self.StartEnvPatch({'TERM': 'xterm'})
    self._con = console_attr.GetConsoleAttr(encoding='utf8', reset=True)

  def testFontBoldXterm(self):
    font = self._con.GetFontCode(bold=True)
    self.assertEqual(font, '\x1b[1m')

  def testFontItalicXterm(self):
    font = self._con.GetFontCode(italic=True)
    self.assertEqual(font, '\x1b[4m')

  def testFontBoldItalicXterm(self):
    font = self._con.GetFontCode(bold=True, italic=True)
    self.assertEqual(font, '\x1b[1;4m')

  def testFontResetXterm(self):
    font = self._con.GetFontCode()
    self.assertEqual(font, '\x1b[m')

  def testGetControlSequenceIndicatorXterm(self):
    self.assertEqual(self._con.GetControlSequenceIndicator(), '\x1b[')

  def testGetControlSequenceLenXterm(self):
    self.assertEqual(self._con.GetControlSequenceLen('No control.'), 0)

  def testDisplayWidthNoneXterm(self):
    s = 'This is a test.\n'
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthBeginXterm(self):
    s = '{0}This is a test.\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthMiddleXterm(self):
    s = 'This is {0}a test.\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthEndXterm(self):
    s = 'This is a test.{0}\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthMiddleUnicodeXterm(self):
    s = 'This is {0}a UÜ車 test.'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(20, self._con.DisplayWidth(s))


class Xterm256ConsoleAttrTests(ConsoleAttrTestBase):

  def SetUp(self):
    self.StartEnvPatch({'TERM': 'xterm-256'})
    self._con = console_attr.GetConsoleAttr(encoding='utf8', reset=True)

  def testFontBoldXterm256(self):
    font = self._con.GetFontCode(bold=True)
    self.assertEqual(font, '\x1b[1m')

  def testFontItalicXterm256(self):
    font = self._con.GetFontCode(italic=True)
    self.assertEqual(font, '\x1b[4m')

  def testFontBoldItalicXterm256(self):
    font = self._con.GetFontCode(bold=True, italic=True)
    self.assertEqual(font, '\x1b[1;4m')

  def testFontResetXterm256(self):
    font = self._con.GetFontCode()
    self.assertEqual(font, '\x1b[m')

  def testGetControlSequenceIndicatorXterm256(self):
    self.assertEqual(self._con.GetControlSequenceIndicator(), '\x1b[')

  def testGetControlSequenceLenXterm256(self):
    self.assertEqual(self._con.GetControlSequenceLen('No control.'), 0)

  def testDisplayWidthNoneXterm256(self):
    s = 'This is a test.\n'
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthBeginXterm256(self):
    s = '{0}This is a test.\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthMiddleXterm256(self):
    s = 'This is {0}a test.\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthEndXterm256(self):
    s = 'This is a test.{0}\n'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(15, self._con.DisplayWidth(s))

  def testDisplayWidthMiddleUnicodeXterm256(self):
    s = 'This is {0}a UÜ車 test.'.format(self._con.GetFontCode(bold=True))
    self.assertEqual(20, self._con.DisplayWidth(s))


class ConsoleAttrStateTests(ConsoleAttrTestBase):

  def SetUp(self):
    self._get_raw_key_function_posix_mock = self.StartObjectPatch(
        console_attr_os, '_GetRawKeyFunctionPosix')
    self._get_raw_key_function_posix_mock.side_effect = (
        self._GetRawKeyFunctionPosixMock)
    self._get_raw_key_function_windows_mock = self.StartObjectPatch(
        console_attr_os, '_GetRawKeyFunctionWindows')
    self._get_raw_key_function_windows_mock.side_effect = (
        self._GetRawKeyFunctionWindowsMock)

    self._get_term_size_posix_mock = self.StartObjectPatch(
        console_attr_os, '_GetTermSizePosix')
    self._get_term_size_posix_mock.side_effect = self._GetTermSizePosixMock
    self._get_term_size_windows_mock = self.StartObjectPatch(
        console_attr_os, '_GetTermSizeWindows')
    self._get_term_size_windows_mock.side_effect = self._GetTermSizeWindowsMock

  @staticmethod
  def _GetRawKeyFunctionPosixMock():
    raise ImportError

  @staticmethod
  def _GetRawKeyFunctionWindowsMock():
    return lambda: '?'

  @staticmethod
  def _GetTermSizePosixMock():
    raise ImportError

  @staticmethod
  def _GetTermSizeWindowsMock():
    return (123, 456)

  def testConsoleAttrStateInit(self):
    attr_1 = console_attr.GetConsoleAttr(encoding='mock', reset=True)
    self.assertEqual(attr_1.GetEncoding(), 'mock')
    attr_2 = console_attr.GetConsoleAttr()
    self.assertEqual(attr_2.GetEncoding(), 'mock')

  def testConsoleAttrStateGetRawKey(self):
    attr_1 = console_attr.GetConsoleAttr(encoding='mock', reset=True)
    attr_2 = console_attr.GetConsoleAttr()
    self.assertEqual('?', attr_1.GetRawKey())
    self.assertEqual('?', attr_2.GetRawKey())
    self.assertEqual('?', attr_1.GetRawKey())
    self.assertEqual('?', attr_2.GetRawKey())
    self._get_raw_key_function_posix_mock.assert_called_once_with()

  def testConsoleAttrStateTermSize(self):
    attr_1 = console_attr.GetConsoleAttr(encoding='mock', reset=True)
    self.assertEqual((123, 456), attr_1.GetTermSize())
    attr_2 = console_attr.GetConsoleAttr()
    self.assertEqual((123, 456), attr_2.GetTermSize())
    self._get_term_size_posix_mock.assert_called_once_with()

  def testConsoleAttrStateResetTermSize(self):
    console_attr.ConsoleAttr._CONSOLE_ATTR_STATE = None

    console_attr.GetConsoleAttr()
    self.assertEqual(self._get_term_size_windows_mock.call_count, 1)
    console_attr.GetConsoleAttr()
    self.assertEqual(self._get_term_size_windows_mock.call_count, 1)

    console_attr.GetConsoleAttr(encoding='mock')
    self.assertEqual(self._get_term_size_windows_mock.call_count, 2)
    console_attr.GetConsoleAttr()
    self.assertEqual(self._get_term_size_windows_mock.call_count, 2)

    console_attr.ResetConsoleAttr()
    self.assertEqual(self._get_term_size_windows_mock.call_count, 3)
    console_attr.GetConsoleAttr()
    self.assertEqual(self._get_term_size_windows_mock.call_count, 3)


class GetCharacterDisplayWidthTests(ConsoleAttrTestBase):

  def testGetCharacterDisplayWidth0(self):
    self.assertEqual(0, console_attr.GetCharacterDisplayWidth(
        '\N{ZERO WIDTH SPACE}'))
    self.assertEqual(0, console_attr.GetCharacterDisplayWidth(
        '\N{SOFT HYPHEN}'))

  def testGetCharacterDisplayWidth1(self):
    self.assertEqual(1, console_attr.GetCharacterDisplayWidth('U'))
    self.assertEqual(1, console_attr.GetCharacterDisplayWidth('U'))
    self.assertEqual(1, console_attr.GetCharacterDisplayWidth('Ü'))
    self.assertEqual(1, console_attr.GetCharacterDisplayWidth('Ⓤ'))

  def testGetCharacterDisplayWidth2(self):
    self.assertEqual(2, console_attr.GetCharacterDisplayWidth('車'))


class ConsoleAttrSafeTextTests(ConsoleAttrTestBase):

  def testSafeTextException(self):
    self.assertEqual('\\u1000', console_attr.SafeText(Exception('\u1000')))
    if six.PY2:
      self.assertEqual('\\xff', console_attr.SafeText(Exception(b'\xff')))
      self.assertEqual('\\xff', console_attr.SafeText(Exception(b'\xc3\xbf')))
    else:
      # On Py3, bytes are not treated as strings and the str() of Exception
      # contains the repr(). This should be fine because on Py3 Exceptions
      # should not contain bytes anyway, and if they do, there is no expectation
      # that it can be decoded.
      self.assertEqual(r"b'\xff'", console_attr.SafeText(Exception(b'\xff')))
      self.assertEqual(r"b'\xc3\xbf'",
                       console_attr.SafeText(Exception(b'\xc3\xbf')))

  def testSafeTextAsciiToAscii(self):
    expected = _ASCII
    actual = console_attr.SafeText(_ASCII, encoding='ascii')
    self.assertEqual(expected, actual)

  def testSafeTextIso8859_1ToAsciiEscape(self):
    expected = r'\xdc\xf1\xee\xe7\xf2\xd0\xe9'
    actual = console_attr.SafeText(_ISO_8859_1, encoding='ascii')
    self.assertEqual(expected, actual)

  def testSafeTextIso8859_1ToAsciiUnknown(self):
    expected = '???????'
    actual = console_attr.SafeText(_ISO_8859_1, encoding='ascii', escape=False)
    self.assertEqual(expected, actual)

  def testSafeTextIso8859_1ToIso8859_1(self):
    expected = '\xdc\xf1\xee\xe7\xf2\xd0\xe9'
    actual = console_attr.SafeText(_ISO_8859_1, encoding='iso-8859-1')
    self.assertEqual(expected, actual)

  def testSafeTextUnicodeToAsciiEscape(self):
    expected = '\\u1e72\\u1f94\\u1e2f\\xa2\\u25ce\\u217e\\u212f'
    actual = console_attr.SafeText(_UNICODE, encoding='ascii')
    self.assertEqual(expected, actual)

  def testSafeTextUnicodeToAsciiUnknown(self):
    expected = '???????'
    actual = console_attr.SafeText(
        _UNICODE, encoding='ascii', escape=False)
    self.assertEqual(expected, actual)

  def testSafeTextUnicodeToCp437Escape(self):
    expected = _UNICODE.encode('cp437', 'backslashreplace').decode('cp437')
    actual = console_attr.SafeText(_UNICODE, encoding='cp437')
    self.assertEqual(expected, actual)

  def testSafeTextUnicodeToCp437Unknown(self):
    expected = _UNICODE.encode('cp437', 'replace').decode('cp437')
    actual = console_attr.SafeText(
        _UNICODE, encoding='cp437', escape=False)
    self.assertEqual(expected, actual)

  def testSafeTextUtf8ToAsciiEscape(self):
    expected = '\\u1e72\\u1f94\\u1e2f\\xa2\\u25ce\\u217e\\u212f'
    actual = console_attr.SafeText(_UTF8, encoding='ascii')
    self.assertEqual(expected, actual)

  def testSafeTextUtf8ToAsciiUnknown(self):
    expected = '???????'
    actual = console_attr.SafeText(_UTF8, encoding='ascii', escape=False)
    self.assertEqual(expected, actual)

  def testSafeTextUnicodeToUtf8(self):
    expected = _UNICODE
    actual = console_attr.SafeText(_UNICODE, encoding='utf8')
    self.assertEqual(expected, actual)

  def testSafeTextUtf8ToUtf8(self):
    expected = _UNICODE
    actual = console_attr.SafeText(_UTF8, encoding='utf8')
    self.assertEqual(expected, actual)

  def testSafeTextUtf8ToUtf8DefaultEncoding(self):
    console_attr.GetConsoleAttr(encoding='utf8', reset=True)
    expected = _UNICODE
    actual = console_attr.SafeText(_UTF8)
    self.assertEqual(expected, actual)


class ConsoleAttrEncodeToBytesTests(ConsoleAttrTestBase):

  def testEncodeToBytesAscii(self):
    expected = b'Unicode'
    actual = console_attr.EncodeToBytes(_ASCII)
    self.assertEqual(expected, actual)

  def testEncodeToBytesIso8859_1(self):
    expected = b'\xdc\xf1\xee\xe7\xf2\xd0\xe9'
    actual = console_attr.EncodeToBytes(_ISO_8859_1)
    self.assertEqual(expected, actual)

  def testEncodeToBytesUnicode(self):
    expected = (b'\xe1\xb9\xb2\xe1\xbe\x94\xe1\xb8\xaf\xc2\xa2'
                b'\xe2\x97\x8e\xe2\x85\xbe\xe2\x84\xaf')
    actual = console_attr.EncodeToBytes(_UNICODE)
    self.assertEqual(expected, actual)

  def testEncodeToBytesUtf8(self):
    expected = (b'\xe1\xb9\xb2\xe1\xbe\x94\xe1\xb8\xaf\xc2\xa2'
                b'\xe2\x97\x8e\xe2\x85\xbe\xe2\x84\xaf')
    actual = console_attr.EncodeToBytes(_UTF8)
    self.assertEqual(expected, actual)


class ConsoleAttrDecodeTests(ConsoleAttrTestBase):

  def testDecodeException(self):
    self.assertEqual('ascii', console_attr.Decode(Exception('ascii')))
    self.assertEqual('\xff', console_attr.Decode(Exception('\xff')))
    self.assertEqual('\u1000', console_attr.Decode(Exception('\u1000')))
    if six.PY2:
      self.assertEqual('\xff', console_attr.Decode(Exception(b'\xc3\xbf')))
    else:
      # On Py3, bytes are not treated as strings and the str() of Exception
      # contains the repr(). This should be fine because on Py3 Exceptions
      # should not contain bytes anyway, and if they do, there is no expectation
      # that it can be decoded.
      self.assertEqual(
          r"b'\xc3\xbf'", console_attr.Decode(Exception(b'\xc3\xbf')))

  def testDecodeAscii(self):
    expected = _ASCII
    actual = console_attr.Decode(_ASCII)
    self.assertEqual(expected, actual)

  def testDecodeUtf8Attr(self):
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetEncoding').return_value = 'utf8'
    expected = _UNICODE
    actual = console_attr.Decode(_UTF8)
    self.assertEqual(expected, actual)

  def testDecodeUtf8AttrKwarg(self):
    expected = _ISO_8859_1.decode('iso-8859-1')
    actual = console_attr.Decode(_ISO_8859_1, encoding='utf8')
    self.assertEqual(expected, actual)

  def testDecodeUtf8FileSyetem(self):
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetEncoding').return_value = 'ascii'
    self.StartObjectPatch(sys, 'getfilesystemencoding').return_value = 'utf8'
    expected = _UNICODE
    actual = console_attr.Decode(_UTF8)
    self.assertEqual(expected, actual)

  def testDecodeUtf8Default(self):
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetEncoding').return_value = 'ascii'
    self.StartObjectPatch(sys, 'getfilesystemencoding').return_value = 'ascii'
    self.StartObjectPatch(sys, 'getdefaultencoding').return_value = 'utf8'
    expected = _UNICODE
    actual = console_attr.Decode(_UTF8)
    self.assertEqual(expected, actual)

  def testDecodeUtf8None(self):
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetEncoding').return_value = 'ascii'
    self.StartObjectPatch(sys, 'getfilesystemencoding').return_value = 'ascii'
    self.StartObjectPatch(sys, 'getdefaultencoding').return_value = 'ascii'
    expected = _UNICODE
    actual = console_attr.Decode(_UTF8)
    self.assertEqual(expected, actual)

  def testDecodeIso8859_1None(self):
    self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetEncoding').return_value = 'ascii'
    self.StartObjectPatch(sys, 'getfilesystemencoding').return_value = 'ascii'
    self.StartObjectPatch(sys, 'getdefaultencoding').return_value = 'ascii'
    expected = _ISO_8859_1.decode('iso-8859-1')
    actual = console_attr.Decode(_ISO_8859_1)
    self.assertEqual(expected, actual)

  def testDecodeObjectAscii(self):
    obj = _Object()
    expected = 'abc=123'
    actual = console_attr.Decode(obj)
    self.assertEqual(expected, actual)

  def testDecodeObjectUnicode(self):
    obj = _Object(name='Ṁöë', value=".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW")
    expected = "Ṁöë=.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"
    actual = console_attr.Decode(obj)
    self.assertEqual(expected, actual)


if __name__ == '__main__':
  test_case.main()
