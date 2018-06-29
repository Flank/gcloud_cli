# Copyright 2018 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals

import traceback

from googlecloudsdk.core import exceptions
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
    if six.PY2:
      # py2 retains sys.exc_info outside try-except
      return
    with self.assertRaises(ValueError):
      exceptions.ExceptionContext(exception_value)


if __name__ == '__main__':
  test_case.main()
