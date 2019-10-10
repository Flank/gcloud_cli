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
"""Tests for error reporting util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ntpath
import os
import posixpath
import textwrap

from googlecloudsdk.command_lib import error_reporting_util
from tests.lib import test_case


class FormatTracebackPathTest(test_case.TestCase):

  _EXAMPLE_TRACEBACK_UNIX_USER_STACK = textwrap.dedent("""\
  Traceback (most recent call last):
    File "/path/to/cloudsdk/google-cloud-sdk/lib/test.py", line 3, in <module>
      main()
    File "/path/to/cloudsdk/google-cloud-sdk/lib/test.py", line 2, in main
      example.method()
    File "/path/to/cloudsdk/google-cloud-sdk/lib/example.py", line 70, in method
      a = b + foo.Bar()
    File "/path/to/cloudsdk/google-cloud-sdk/lib/googlecloudsdk/foo.py", line 700, in bar
      c.function()
    File "/path/to/cloudsdk/google-cloud-sdk/lib/third_party/bread/toast.py", line 1, in function
      raise Exception('really really long message')
  Exception: really really long message""")

  _EXAMPLE_TRACEBACK_UNIX_USER_STACK_TWO_LINE_MESSAGE = textwrap.dedent("""\
  Traceback (most recent call last):
    File "/path/to/cloudsdk/google-cloud-sdk/lib/test.py", line 3, in <module>
      main()
    File "/path/to/cloudsdk/google-cloud-sdk/lib/test.py", line 2, in main
      example.method()
    File "/path/to/cloudsdk/google-cloud-sdk/lib/example.py", line 70, in method
      a = b + foo.Bar()
    File "/path/to/cloudsdk/google-cloud-sdk/lib/googlecloudsdk/foo.py", line 700, in bar
      c.function()
    File "/path/to/cloudsdk/google-cloud-sdk/lib/third_party/bread/toast.py", line 1, in function
      raise Exception('really really long\\ntwo line message')
  Exception: really really long
  two line message""")

  _EXAMPLE_TRACEBACK_WINDOWS_USER_STACK = textwrap.dedent("""\
  Traceback (most recent call last):
    File "C:\\Program Files (x86)\\path\\cloudsdk\\google-cloud-sdk\\lib\\test.py", line 3, in <module>
      main()
    File "C:\\Program Files (x86)\\path\\cloudsdk\\google-cloud-sdk\\lib\\test.py", line 2, in main
      example.method()
    File "C:\\Program Files (x86)\\path\\loudsdk\\google-cloud-sdk\\lib\\example.py", line 70, in method
      a = b + foo.Bar()
    File "C:\\Program Files (x86)\\path\\cloudsdk\\google-cloud-sdk\\lib\\googlecloudsdk\\foo.py", line 700, in bar
      c.function()
    File "C:\\Program Files (x86)\\path\\cloudsdk\\google-cloud-sdk\\lib\\third_party\\bread\\toast.py", line 1, in function
      raise Exception('really really long message')
  Exception: really really long message""")

  _EXAMPLE_WRONG_TRACEBACK = textwrap.dedent("""\
  WrongTraceback (not most recent calll):
    File "this/is/not/correct", in <module>, line 2
      main()
  Exception: this is an incorrectly formatted traceback""")

  def testFormatTracebackRemoveInfo_UnixPathSept(self):
    self.StartObjectPatch(os.path, 'sep', posixpath.sep)
    self.StartObjectPatch(os.path, 'dirname', posixpath.dirname)
    self.StartObjectPatch(os.path, 'commonprefix', posixpath.commonprefix)
    expected_formatted_stacktrace = textwrap.dedent("""\
    Traceback (most recent call last):
      File "google-cloud-sdk/lib/test.py", line 3, in <module>
        main()
      File "google-cloud-sdk/lib/test.py", line 2, in main
        example.method()
      File "google-cloud-sdk/lib/example.py", line 70, in method
        a = b + foo.Bar()
      File "google-cloud-sdk/lib/googlecloudsdk/foo.py", line 700, in bar
        c.function()
      File "google-cloud-sdk/lib/third_party/bread/toast.py", line 1, in function
        raise Exception('really really long message')
    Exception
    """)
    self.assertEqual(
        expected_formatted_stacktrace,
        error_reporting_util.RemovePrivateInformationFromTraceback(
            self._EXAMPLE_TRACEBACK_UNIX_USER_STACK))

  def testRemovePrivateInfoTwoLineExceptionMessage(self):
    self.StartObjectPatch(os.path, 'sep', posixpath.sep)
    self.StartObjectPatch(os.path, 'dirname', posixpath.dirname)
    self.StartObjectPatch(os.path, 'commonprefix', posixpath.commonprefix)
    expected_formatted_stacktrace = textwrap.dedent("""\
    Traceback (most recent call last):
      File "google-cloud-sdk/lib/test.py", line 3, in <module>
        main()
      File "google-cloud-sdk/lib/test.py", line 2, in main
        example.method()
      File "google-cloud-sdk/lib/example.py", line 70, in method
        a = b + foo.Bar()
      File "google-cloud-sdk/lib/googlecloudsdk/foo.py", line 700, in bar
        c.function()
      File "google-cloud-sdk/lib/third_party/bread/toast.py", line 1, in function
        raise Exception('really really long\\ntwo line message')
    Exception
    """)
    self.assertEqual(
        expected_formatted_stacktrace,
        error_reporting_util.RemovePrivateInformationFromTraceback(
            self._EXAMPLE_TRACEBACK_UNIX_USER_STACK_TWO_LINE_MESSAGE))

  def testFormatTracebackRemoveInfo_WindowsPathSept(self):
    self.StartObjectPatch(os.path, 'sep', ntpath.sep)
    self.StartObjectPatch(os.path, 'dirname', ntpath.dirname)
    self.StartObjectPatch(os.path, 'commonprefix', ntpath.commonprefix)
    expected_formatted_stacktrace = textwrap.dedent("""\
    Traceback (most recent call last):
      File "google-cloud-sdk\\lib\\test.py", line 3, in <module>
        main()
      File "google-cloud-sdk\\lib\\test.py", line 2, in main
        example.method()
      File "google-cloud-sdk\\lib\\example.py", line 70, in method
        a = b + foo.Bar()
      File "google-cloud-sdk\\lib\\googlecloudsdk\\foo.py", line 700, in bar
        c.function()
      File "google-cloud-sdk\\lib\\third_party\\bread\\toast.py", line 1, in function
        raise Exception('really really long message')
    Exception
    """)
    self.assertEqual(
        expected_formatted_stacktrace,
        error_reporting_util.RemovePrivateInformationFromTraceback(
            self._EXAMPLE_TRACEBACK_WINDOWS_USER_STACK))

  def testFormatTracebackIncorrecTracebackFormat(self):
    self.StartObjectPatch(os.path, 'sep', posixpath.sep)
    self.StartObjectPatch(os.path, 'dirname', posixpath.dirname)
    self.StartObjectPatch(os.path, 'commonprefix', posixpath.commonprefix)
    self.assertEqual(
        None,
        error_reporting_util.RemovePrivateInformationFromTraceback(
            self._EXAMPLE_WRONG_TRACEBACK))
