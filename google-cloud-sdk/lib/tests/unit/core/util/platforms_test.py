# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Unit tests for the platforms module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.util import platforms
from tests.lib import test_case


class PlatformsTest(test_case.TestCase):

  def testParseOperatingSystem(self):
    os = platforms.OperatingSystem.FromId('WINDOWS')
    self.assertEquals(os, platforms.OperatingSystem.WINDOWS)

  def testParseArchitecture(self):
    os = platforms.Architecture.FromId('x86')
    self.assertEquals(os, platforms.Architecture.x86)

  def testFailedParseOperatingSystem(self):
    with self.assertRaisesRegexp(
        platforms.InvalidEnumValue,
        r'Could not parse \[asdf\] into a valid Operating System.  Valid '
        r'values are \[WINDOWS, MACOSX, LINUX, CYGWIN, MSYS\]'):
      platforms.OperatingSystem.FromId('asdf')

  def testFailedParseArchitecture(self):
    with self.assertRaisesRegexp(
        platforms.InvalidEnumValue,
        r'Could not parse \[asdf\] into a valid Architecture.  Valid values '
        r'are \[x86, x86_64, PPC, arm\]'):
      platforms.Architecture.FromId('asdf')

  def testCurrent(self):
    current = platforms.Platform.Current()
    self.assertIsNotNone(current.operating_system)
    self.assertIsNotNone(current.architecture)

  def testIsWindows(self):
    current = platforms.OperatingSystem.Current()
    is_windows = current is platforms.OperatingSystem.WINDOWS
    self.assertEqual(is_windows, platforms.OperatingSystem.IsWindows())


class PythonVersionTest(test_case.WithOutputCapture):

  def testIsCompatible(self):
    self.assertTrue(
        platforms.PythonVersion((2, 6)).IsCompatible(print_errors=True))
    self.AssertErrContains('WARNING:  Python 2.6.x is no longer')
    self.ClearErr()
    self.assertTrue(
        platforms.PythonVersion((2, 7)).IsCompatible(print_errors=True))
    self.AssertErrEquals('')
    self.ClearErr()
    self.assertFalse(
        platforms.PythonVersion((3, 0)).IsCompatible(print_errors=True))
    self.AssertErrContains('Please use a Python 2.7.x version.')
    self.ClearErr()
    self.assertFalse(
        platforms.PythonVersion((4, 0)).IsCompatible(print_errors=True))
    self.AssertErrContains('Please use a Python 2.7.x version.')
    self.ClearErr()
    self.assertFalse(
        platforms.PythonVersion((2, 5)).IsCompatible(print_errors=True))
    self.AssertErrContains('Python 2.5 is not compatible')
    self.AssertErrContains('Please upgrade to Python 2.7.x')
    self.AssertErrNotContains('WARNING')
    self.ClearErr()
    ver = platforms.PythonVersion()
    ver.version = None
    self.assertFalse(ver.IsCompatible(print_errors=True))
    self.AssertErrContains('Please upgrade to Python 2.7.x')
    self.ClearErr()

    self.assertFalse(
        platforms.PythonVersion((3, 0)).IsCompatible(print_errors=False))
    self.AssertErrEquals('')
    self.ClearErr()
    self.assertTrue(
        platforms.PythonVersion((2, 6)).IsCompatible(print_errors=False))
    self.AssertErrEquals('')

  def testIsSupported(self):
    self.assertFalse(platforms.PythonVersion((2, 6)).IsSupported())
    self.assertTrue(platforms.PythonVersion((2, 7)).IsSupported())
    self.assertFalse(platforms.PythonVersion((3, 0)).IsSupported())
    self.assertFalse(platforms.PythonVersion((4, 0)).IsSupported())


if __name__ == '__main__':
  test_case.main()
