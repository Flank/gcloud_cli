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

"""Tests for the exceptions module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import sys
import traceback

from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import test_case

import six


class ExceptionContextTest(test_case.TestCase):

  def testExceptionContext(self):
    exception_context = None
    try:
      int('bogus number')
    except ValueError as e:
      exception_context = exceptions.ExceptionContext(e)
    self.assertIsNotNone(exception_context)
    with self.assertRaises(ValueError):
      exception_context.Reraise()

  def testExceptionContextTraceback(self):
    exception_context = None
    try:
      int('bogus number')
    except ValueError as e:
      exception_context = exceptions.ExceptionContext(e)
    self.assertIsNotNone(exception_context)

    try:
      exception_context.Reraise()
    except ValueError as e:
      context = exceptions.ExceptionContext(e)
      traceback_lines = traceback.format_tb(context._traceback)
      self.assertTrue(any("int('bogus number')" in x for x in traceback_lines))
    else:
      self.fail('ValueError exception not raised')

  def testExceptionContextOutsideExceptClause(self):
    exception_value = None
    try:
      int('bogus number')
    except ValueError as e:
      exception_value = e
    self.assertIsNotNone(exception_value)
    # Python 2 retains sys.exc_info until exiting the frame where it was caught,
    # so clear it manually here.
    if six.PY2:
      sys.exc_clear()
    with self.assertRaises(exceptions.InternalError):
      exceptions.ExceptionContext(exception_value)


class RaiseWithContextTest(test_case.WithOutputCapture,
                           parameterized.TestCase):

  def _RaiseWithContext(self, msg1, msg2):
    try:
      raise ValueError(msg1)
    except ValueError as e1:
      tb1 = sys.exc_info()[2]
      try:
        raise RuntimeError(msg2)
      except RuntimeError as e2:
        tb2 = sys.exc_info()[2]
        exceptions.RaiseWithContext(type(e1), e1, tb1, type(e2), e2, tb2)

  @parameterized.parameters(
      ('First error', 'Second error', 'Second error'),
      ('C:\\Users\\first', 'C:\\Users\\second', re.escape('C:\\Users\\second')),
      ('First Ṳᾔḯ¢◎ⅾℯ error', 'Second Ṳᾔḯ¢◎ⅾℯ error', 'Second Ṳᾔḯ¢◎ⅾℯ error'),
  )
  def testRaiseWithContext(self, msg1, msg2, expected_msg_regex):
    msg1 = six.ensure_str(msg1)
    msg2 = six.ensure_str(msg2)
    try:
      self._RaiseWithContext(msg1, msg2)
    except RuntimeError as e:
      self.assertRegexpMatches(six.text_type(e), expected_msg_regex)  # pylint: disable=g-assert-in-except
    else:
      self.fail('RuntimeError not raised')

  @test_case.Filters.RunOnlyOnPy2(
      'Only a potential problem in Python 2. This will already be tested '
      'implicitly for Python 3 in the test above, so no need to run it again '
      'here.')
  def testRaiseWithContextUnicodeUnencoded(self):
    # Python 2's traceback module does a terrible job formatting exceptions
    # raised with unicode error messages, and ends up losing information because
    # it encodes the message using backslashreplace as a fallback:
    #
    # https://github.com/python/cpython/blob/35f9bccd8198330579ecb4b4c503062f8b5da130/Lib/traceback.py#L219
    #
    # There's no way to reverse this unambiguously so we have to settle for
    # unicode escape sequences appearing in the error message if the exception
    # messages aren't encoded when they're raised initially (which is what we
    # did in the test above by calling six.ensure_str). Here we're mostly just
    # checking that we don't crash in Python 2 with a Unicode-related error.
    msg1 = 'Ṳᾔḯ¢◎ⅾℯ C:\\Users\\first'
    msg2 = 'Ṳᾔḯ¢◎ⅾℯ C:\\Users\\second'
    try:
      self._RaiseWithContext(msg1, msg2)
    except RuntimeError as e:
      self.assertRegexpMatches(
          six.text_type(e),
          re.escape('\\u1e72\\u1f94\\u1e2f\\xa2\\u25ce\\u217e\\u212f '
                    'C:\\Users\\second'))
    except UnicodeError as e:
      self.fail(e)
    else:
      self.fail('RuntimeError not raised')

  def testRaiseWithContextStderr(self):
    try:
      self._RaiseWithContext('first', 'second')
    except RuntimeError:
      traceback.print_exc()
    self.AssertErrMatches(
        'ValueError: first.+'
        'During handling of the above exception, another exception occurred:.+'
        'RuntimeError: second')
    # Ensure we don't duplicate this info in Python 3.
    self.AssertErrNotMatches('.*During handling.*During handling.*')


if __name__ == '__main__':
  test_case.main()
