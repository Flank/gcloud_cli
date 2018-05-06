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

"""Tests for the console_attr_os module."""

from __future__ import absolute_import
from __future__ import unicode_literals
import copy
import io
import os
import struct
import subprocess
import sys
import types

from googlecloudsdk.core.console import console_attr_os
from googlecloudsdk.core.util import encoding
from tests.lib import test_case

from six.moves import range  # pylint: disable=redefined-builtin
import six.moves.builtins


class ImportMocker(object):

  def __init__(self):
    self.sys_modules = sys.modules
    sys.modules = copy.copy(sys.modules)
    self.builtin_import = six.moves.builtins.__import__
    six.moves.builtins.__import__ = self.Import
    self.imports = {}

  # pylint: disable=invalid-name
  def Done(self):
    six.moves.builtins.__import__ = self.builtin_import
    sys.modules = self.sys_modules

  # pylint: disable=invalid-name,redefined-builtin
  def Import(self, name, globals=None, locals=None, fromlist=None, level=0):
    if name not in self.imports:
      return self.builtin_import(
          name, globals=globals, locals=locals, fromlist=fromlist, level=level)
    module_class = self.imports[name]
    if module_class:
      return module_class()
    raise ImportError

  # pylint: disable=invalid-name
  def SetImport(self, name, module):
    self.imports[name] = module
    if name in sys.modules:
      sys.modules[name] = None


@test_case.Filters.DoNotRunOnWindows
class ConsoleAttrOsGetTermsizePosixTests(test_case.Base):

  class MockFcntlModule(object):

    # pylint: disable=invalid-name
    def ioctl(self, fd, unused_op, unused_value):
      if fd < 3:
        raise IOError
      return struct.pack(b'hh', 25, 81)

  class MockTermiosModule(object):

    TIOCGWINSZ = 0

  def SetUp(self):
    self.imports = ImportMocker()
    self.imports.SetImport('ctypes', None)
    self.imports.SetImport('fcntl', self.MockFcntlModule)
    self.imports.SetImport('termios', self.MockTermiosModule)
    self.StartEnvPatch({})
    encoding.SetEncodedValue(os.environ, 'COLUMNS', None)
    self.check_output = self.StartObjectPatch(subprocess, 'check_output')
    self.check_output.side_effect = OSError
    self.has_os_ctermid = hasattr(os, 'ctermid')
    if not self.has_os_ctermid:
      setattr(os, 'ctermid', None)
    self.ctermid = self.StartObjectPatch(os, 'ctermid')
    self.ctermid.return_value = os.devnull

  def TearDown(self):
    if not self.has_os_ctermid:
      delattr(os, 'ctermid')
    self.imports.Done()

  def testGetTermsizePosix(self):
    columns, lines = console_attr_os.GetTermSize()
    self.assertEqual((81, 25), (columns, lines))


class ConsoleAttrOsGetTermsizeWindowsTests(test_case.Base):

  class MockCtypesModuleNoScreenBuffer(object):

    class MockWinDllModule(object):

      class Kernel32(object):

        # pylint: disable=invalid-name
        def GetConsoleScreenBufferInfo(self, unused_handle, unused_csbi):
          return None

        # pylint: disable=invalid-name
        def GetStdHandle(self, index):
          return index

      def __init__(self):
        self.kernel32 = self.Kernel32()

    class StringBuffer(object):

      def __init__(self):
        self.raw = struct.pack(b'hhhhHhhhhhh', 1, 2, 3, 4, 5, 1, 1, 82, 26, 6,
                               7)

    def __init__(self):
      self.windll = self.MockWinDllModule()

    # pylint: disable=invalid-name
    def create_string_buffer(self, unused_size):
      return self.StringBuffer()

  class MockCtypesModuleScreenBuffer(object):

    class MockWinDllModule(object):

      class Kernel32(object):

        # pylint: disable=invalid-name
        def GetConsoleScreenBufferInfo(self, unused_handle, csbi):
          return csbi

        # pylint: disable=invalid-name
        def GetStdHandle(self, index):
          return index

      def __init__(self):
        self.kernel32 = self.Kernel32()

    class StringBuffer(object):

      def __init__(self):
        self.raw = struct.pack(b'hhhhHhhhhhh', 1, 2, 3, 4, 5, 1, 1, 82, 26, 6,
                               7)

    def __init__(self):
      self.windll = self.MockWinDllModule()

    # pylint: disable=invalid-name
    def create_string_buffer(self, unused_size):
      return self.StringBuffer()

  def SetUp(self):
    self.imports = ImportMocker()
    self.imports.SetImport('fcntl', None)
    self.imports.SetImport('termios', None)
    self.StartEnvPatch({})
    encoding.SetEncodedValue(os.environ, 'COLUMNS', None)
    self.check_output = self.StartObjectPatch(subprocess, 'check_output')
    self.check_output.side_effect = OSError

  def TearDown(self):
    self.imports.Done()

  def testGetTermsizeWindowsScreenBuffer(self):
    self.imports.SetImport('ctypes', self.MockCtypesModuleScreenBuffer)
    columns, lines = console_attr_os.GetTermSize()
    self.assertEqual((82, 26), (columns, lines))

  def testGetTermsizeWindowsNoScreenBuffer(self):
    self.imports.SetImport('ctypes', self.MockCtypesModuleNoScreenBuffer)
    columns, lines = console_attr_os.GetTermSize()
    self.assertEqual((80, 24), (columns, lines))


class ConsoleAttrOsGetTermsizeEnvironmentTests(test_case.Base):

  def SetUp(self):
    self.imports = ImportMocker()
    self.imports.SetImport('ctypes', None)
    self.imports.SetImport('fcntl', None)
    self.imports.SetImport('termios', None)
    self.StartEnvPatch(os.environ)
    encoding.SetEncodedValue(os.environ, 'COLUMNS', '83')
    encoding.SetEncodedValue(os.environ, 'LINES', '27')
    self.check_output = self.StartObjectPatch(subprocess, 'check_output')
    self.check_output.side_effect = OSError

  def TearDown(self):
    self.imports.Done()

  def testGetTermsizeEnvironment(self):
    columns, lines = console_attr_os.GetTermSize()
    self.assertEqual((83, 27), (columns, lines))


class ConsoleAttrOsGetTermsizeTputTests(test_case.Base):

  def MockCheckOutput(self, args, stderr=None):
    if args[1] == 'cols':
      return '84\n'
    if args[1] == 'lines':
      return '28\n'
    return 'ERROR\n'

  def SetUp(self):
    self.imports = ImportMocker()
    self.imports.SetImport('ctypes', None)
    self.imports.SetImport('fcntl', None)
    self.imports.SetImport('termios', None)
    self.StartEnvPatch(os.environ)
    encoding.SetEncodedValue(os.environ, 'COLUMNS', None)
    self.check_output = self.StartObjectPatch(subprocess, 'check_output')
    self.check_output.side_effect = self.MockCheckOutput

  def TearDown(self):
    self.imports.Done()

  def testGetTermsizeTput(self):
    columns, lines = console_attr_os.GetTermSize()
    self.assertEqual((84, 28), (columns, lines))


class ConsoleAttrOsGetTermsizeFallBackTests(test_case.Base):

  def SetUp(self):
    self.imports = ImportMocker()
    self.imports.SetImport('ctypes', None)
    self.imports.SetImport('fcntl', None)
    self.imports.SetImport('termios', None)
    self.StartEnvPatch(os.environ)
    encoding.SetEncodedValue(os.environ, 'COLUMNS', None)
    self.check_output = self.StartObjectPatch(subprocess, 'check_output')
    self.check_output.side_effect = OSError

  def TearDown(self):
    self.imports.Done()

  def testGetTermsizeFallBack(self):
    columns, lines = console_attr_os.GetTermSize()
    self.assertEqual((80, 24), (columns, lines))


class ConsoleAttrOsGetRawKeyFunctionPosixTests(test_case.Base):

  class MockTtyModule(object):

    # pylint: disable=invalid-name
    def setraw(self, unused_fd):
      return 0

  class MockTtyModuleIOError(object):

    # pylint: disable=invalid-name
    def setraw(self, unused_fd):
      raise IOError

  class MockTermiosModule(object):

    TCSADRAIN = 0

    # pylint: disable=invalid-name
    def tcgetattr(self, unused_fd):
      return 0

    # pylint: disable=invalid-name
    def tcsetattr(self, unused_fd, unused_op, unused_previous):
      return 0

  def MockFileNo(self):
    return 0

  def SetUp(self):
    self.imports = ImportMocker()
    self.imports.SetImport('msvcrt', None)
    self.imports.SetImport('termios', self.MockTermiosModule)
    self.stdin = sys.stdin
    sys.stdin = io.StringIO('A\x1bA\x1bB\x1bD\x1bC\x1b5~\x1b6~\x1bH\x1bF'
                            '\x1bM\x1bS\x1bT\x1b\x1b\x04\x1a/?\n')
    sys.stdin.fileno = self.MockFileNo

  def TearDown(self):
    sys.stdin = self.stdin
    self.imports.Done()

  def testGetRawKeyFunctionPosix(self):
    expected = [
        'A',
        '<UP-ARROW>',
        '<DOWN-ARROW>',
        '<LEFT-ARROW>',
        '<RIGHT-ARROW>',
        '<PAGE-UP>',
        '<PAGE-DOWN>',
        '<HOME>',
        '<END>',
        '<DOWN-ARROW>',
        '<PAGE-UP>',
        '<PAGE-DOWN>',
        '\x1b',
        None,
        None,
        '/',
    ]

    self.imports.SetImport('tty', self.MockTtyModule)
    getrawkey = console_attr_os.GetRawKeyFunction()
    actual = []
    for _ in range(len(expected)):
      actual.append(getrawkey())
    self.assertEqual(expected, actual)

  def testGetRawKeyFunctionPosixIOError(self):
    self.imports.SetImport('tty', self.MockTtyModuleIOError)
    getrawkey = console_attr_os.GetRawKeyFunction()
    c = getrawkey()
    self.assertEqual(None, c)


class ConsoleAttrOsGetRawKeyFunctionWindowsCodeTests(test_case.Base):

  class MockMsvcrtModule(object):

    def __init__(self):
      self.rawin = io.StringIO(
          'A\xe0H\xe0P\xe0K\xe0M\xe0I\xe0Q\xe0G\xe0O\x1b\x04\x1a/?\n')

    # pylint: disable=invalid-name
    def getch(self):
      return self.rawin.read(1)

  def SetUp(self):
    self.imports = ImportMocker()
    self.imports.SetImport('msvcrt', self.MockMsvcrtModule)
    self.imports.SetImport('termios', None)
    self.imports.SetImport('tty', None)

  def TearDown(self):
    self.imports.Done()

  def testGetRawKeyFunctionWindows(self):
    expected = [
        'A',
        '<UP-ARROW>',
        '<DOWN-ARROW>',
        '<LEFT-ARROW>',
        '<RIGHT-ARROW>',
        '<PAGE-UP>',
        '<PAGE-DOWN>',
        '<HOME>',
        '<END>',
        '\x1b',
        None,
        None,
        '/',
    ]

    getrawkey = console_attr_os.GetRawKeyFunction()
    actual = []
    for _ in range(len(expected)):
      actual.append(getrawkey())
    self.assertEqual(expected, actual)


class ConsoleAttrOsGetRawKeyFunctionFallBackTests(test_case.Base):

  def SetUp(self):
    self.imports = ImportMocker()
    self.imports.SetImport('msvcrt', None)
    self.imports.SetImport('termios', None)
    self.imports.SetImport('tty', None)
    self.stdin = sys.stdin
    sys.stdin = io.StringIO('??\n')

  def TearDown(self):
    sys.stdin = self.stdin
    self.imports.Done()

  def testGetRawKeyFunctionFallBack(self):
    getrawkey = console_attr_os.GetRawKeyFunction()
    c = getrawkey()
    self.assertEqual(None, c)


class ConsoleAttrOsGetTermSizeNativeTests(test_case.Base):

  def SetUp(self):
    self.StartEnvPatch(os.environ)

  def Run(self, get_term_size, required=False, value=None):
    try:
      xy = get_term_size()
    except:  # pylint: disable=bare-except
      xy = None
    if value:
      self.assertEqual(value, xy)
    elif xy:
      self.assertTrue(xy[0] > 0)
      self.assertTrue(xy[1] > 0)
    elif required:
      self.fail('Terminal (x,y) size expected, None returned.')

  def testGetTermSizeNative(self):
    encoding.SetEncodedValue(os.environ, 'COLUMNS', None)
    self.Run(console_attr_os.GetTermSize, required=True)

  def testGetTermSizePosixNative(self):
    self.Run(console_attr_os._GetTermSizePosix)

  def testGetTermSizeWindowsNative(self):
    self.Run(console_attr_os._GetTermSizeWindows)

  def testGetTermSizeEnvNative(self):
    encoding.SetEncodedValue(os.environ, 'LINES', '33')
    encoding.SetEncodedValue(os.environ, 'COLUMNS', '88')
    self.Run(console_attr_os._GetTermSizeEnvironment, value=(88, 33))

  def testGetTermSizeTputNative(self):
    self.Run(console_attr_os._GetTermSizeTput)


class ConsoleAttrOsGetRawKeyFunctionNativeTests(test_case.Base):

  def Run(self, get_raw_key_function, required=False):
    try:
      fun = get_raw_key_function()
    except:  # pylint: disable=bare-except
      fun = None
    if fun or required:
      self.assertTrue(type(fun) is types.FunctionType)

  def testGetGetRawKeyFunctionNative(self):
    self.Run(console_attr_os.GetRawKeyFunction, required=True)

  def testGetGetRawKeyFunctionPosixNative(self):
    self.Run(console_attr_os._GetRawKeyFunctionPosix)

  def testGetGetRawKeyFunctionWindowsNative(self):
    self.Run(console_attr_os._GetRawKeyFunctionWindows)


if __name__ == '__main__':
  test_case.main()
