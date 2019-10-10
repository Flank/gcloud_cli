# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import platforms
from tests.lib import parameterized
from tests.lib import test_case


class PlatformsTest(test_case.TestCase):

  def testParseOperatingSystem(self):
    os = platforms.OperatingSystem.FromId('WINDOWS')
    self.assertEqual(os, platforms.OperatingSystem.WINDOWS)

  def testParseArchitecture(self):
    os = platforms.Architecture.FromId('x86')
    self.assertEqual(os, platforms.Architecture.x86)

  def testFailedParseOperatingSystem(self):
    with self.assertRaisesRegex(
        platforms.InvalidEnumValue,
        r'Could not parse \[asdf\] into a valid Operating System.  Valid '
        r'values are \[WINDOWS, MACOSX, LINUX, CYGWIN, MSYS\]'):
      platforms.OperatingSystem.FromId('asdf')

  def testFailedParseArchitecture(self):
    with self.assertRaisesRegex(
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


class PythonVersionTest(test_case.WithOutputCapture, parameterized.TestCase):

  @parameterized.parameters([
      ((2, 5), False,
       'ERROR: Python 2.5 is not compatible with the Google Cloud SDK. Please '
       'use Python version 2.7.x or 3.5 and up.'),
      ((2, 6), True,
       'WARNING:  Python 2.6.x is no longer officially supported by the Google '
       'Cloud SDK\nand may not function correctly.  Please use Python version '
       '2.7.x or 3.5 and up.'),
      ((2, 7), True, ''),
      ((3, 0), False,
       'ERROR: Python 3.0 is not compatible with the Google Cloud SDK. Please '
       'use Python version 2.7.x or 3.5 and up.'),
      ((3, 1), False,
       'ERROR: Python 3.1 is not compatible with the Google Cloud SDK. Please '
       'use Python version 2.7.x or 3.5 and up.'),
      ((3, 2), False,
       'ERROR: Python 3.2 is not compatible with the Google Cloud SDK. Please '
       'use Python version 2.7.x or 3.5 and up.'),
      ((3, 3), False,
       'ERROR: Python 3.3 is not compatible with the Google Cloud SDK. Please '
       'use Python version 2.7.x or 3.5 and up.'),
      ((3, 4), True,
       'WARNING:  Python 3.4.x is no longer officially supported by the Google '
       'Cloud SDK\nand may not function correctly.  Please use Python version '
       '2.7.x or 3.5 and up.'),
      ((3, 5), True, ''),
      ((3, 6), True, ''),
      ((3, 7), True, ''),
      ((4, 0), True, ''),
  ])
  def testIsCompatible(self, version, is_compatible, error_string):
    self.assertEqual(
        is_compatible,
        platforms.PythonVersion(version).IsCompatible())
    if error_string:
      error_string += """\


If you have a compatible Python interpreter installed, you can use it by setting
the CLOUDSDK_PYTHON environment variable to point to it.

"""
      self.AssertErrEquals(error_string)
    else:
      self.AssertErrEquals('')

  def testRaise(self):
    with self.assertRaisesRegex(
        platforms.Error,
        'ERROR: Python 3.0 is not compatible with the Google Cloud SDK.'
        ' Please use Python version 2.7.x or 3.5 and up.'):
      platforms.PythonVersion((3, 0)).IsCompatible(raise_exception=True)

  def testUnknownVersion(self):
    version = platforms.PythonVersion()
    version.version = None
    self.assertFalse(version.IsCompatible())
    self.AssertErrContains('ERROR: Your current version of Python is not ')


if __name__ == '__main__':
  test_case.main()
