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

"""Support for multiple lightweight subtest in one unittest test method.

Ideal for unit tests on functions that transform multiple inputs, such as
lexers, parsers, and expression evaluators, where devising unittest test method
names for each test case would be tedious and get in the way of what is being
tested.

(1) consider tests for a simple calculator using one method per test case:

  class CalculatorEvalTest(test_case.Base):

    def testOnePlusOneEqualsTwo(self):
      actual = self.calculator.Eval('1+1')
      self.assertEqual(2, actual)

    def testOnePlusOneEqualsTwoWithSpaces(self):
      actual = self.calculator.Eval('1 + 1')
      self.assertEqual(2, actual)

    def testOnePlusOneEqualsTwoWithParentheses(self):
      actual = self.calculator.Eval('(1 + 1)')
      self.assertEqual(2, actual)

(2) versus using subtests:

  class CalculatorEvalTest(subtests.Base):

    def RunSubTest(self, expression):
      return self.calculator.Eval(expression)

    def testArithmetic(self):

      self.Run(2, '1+1')
      self.Run(2, '1 + 1')
      self.Run(2, '(1 + 1)')

(3) or through a function that sets up common args for a set of subtests:

  class CalculatorEvalTest(subtests.Base):

    def RunSubTest(self, expression, error_context):
      result = self.calculator.Eval(expression)
      # Add a follow-on test to verify the error character position.
      self.AddFollowOnTest(
        'error-context', error_context, self.calculator.GetErrorContext)
      return result

    def testSyntaxErrors(self):

      def T(expression):
        # depth=2 because self.Run() is being called inside a function.
        # This make the subtest runner report the line number of the T() call
        # on error instead of the line number of the self.Run() call.
        self.Run(
          None, expression, depth=2, exception=self.calculator.SyntaxError)

      T('+', error_context='character:1')
      T('1+', error_context='character:2')
      T(') 1 + 1 (', error_context='character:1')
      T('( 1 + 1', error_context='character:7')
      T('( 1 + 1 (', error_context='character:9')

Test failures are collected and reported when the test method returns. The
report includes the line numbers of failed subtests.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import abc
import inspect
import operator

from tests.lib import test_case
import six


def GetCallerSourceLine(n):
  """Returns the source line number n callers back.

  Args:
    n: int, The number of caller frames to back up.

  For example:
    If A() calls B() and B() calls GetCallerSourceLine(n) then
      n=0 => the source line where GetCallerSourceLine() was called from
      n=1 => the source line where B() was called from
      n=2 => the source line where A() was called from

  Returns:
    int, The source line number n callers back.
  """
  frame = inspect.currentframe()
  while n >= 0:
    n -= 1
    frame = frame.f_back
  return frame.f_lineno


class Base(test_case.Base):
  """Test case subtest controller."""

  def SetUp(self):
    self.test_count = 0
    self.failures = []
    self.follow_on_tests = []

  def TearDown(self):
    if self.failures:
      self.fail('{failures}/{total} subtests failed:\n  {messages}\n'.format(
          failures=len(self.failures), total=self.test_count,
          messages='\n  '.join(self.failures)))

  @abc.abstractmethod
  def RunSubTest(self, *args, **kwargs):
    """Runs the actual subtest."""
    return None

  def AddFollowOnTest(self, title, expected, func):
    """Adds a follow-on subtest. These are run and popped after each subtest.

    Args:
      title: The follow-on test string name for error reporting.
      expected: The expected return value of the subtest func.
      func: The follow-on test function, called as: actual = func().
    """
    self.follow_on_tests.append((title, expected, func))

  def Run(self, expected, *args, **kwargs):
    """Runs one subtest.

    Runs self.RunSubTest(*args, **kwargs).
    Failures are collected and reported as a group.

    Args:
      expected: The expected return value from self.RunSubTest().
      *args: Passed to self.RunSubTest.
      **kwargs: Passed to self.RunSubTest except for:
        depth=N -- The call stack depth of Run(). The default is depth=1 for
          when self.Run() is called from the test method (example (2) above).
          Use depth=2 if self.Run() is called indirectly through another
          function (example (3) above). This value makes sure the subtest
          report contains the correct line number for each subtest error.
        exception=exception -- The expected exception type or object raised by
          self.RunSubTest(). If it is an instantiated object then the object
          unicode() value (the exception error message string) is matched
          against the actual error message using the matches function.
        matches=matches -- bool func(expected, actual) that determines if
          the actual value matches the expected value. The default is
            matches=operator.eq, called as matches(expected, actual)
    """

    self.test_count += 1
    line = GetCallerSourceLine(kwargs.pop('depth', 1))
    expected_exception = kwargs.pop('exception', None)
    if expected_exception:
      expected_exception_type = type(expected_exception)
      if isinstance(expected_exception, type):
        # An exception class type.
        expected_exception_message = None
      else:
        # An instantiated exception.
        expected_exception_message = six.text_type(expected_exception)
    else:
      expected_exception_type = None
      expected_exception_message = None
    matches = kwargs.pop('matches', operator.eq)
    exception_type = None
    exception_message = None
    try:
      actual = self.RunSubTest(*args, **kwargs)
    except Exception as e:  # pylint: disable=broad-except
      exception_type = type(e)
      exception_message = six.text_type(e)

    argv = ["'" + six.text_type(a) + "'" for a in args]
    for name, value in sorted(six.iteritems(kwargs)):
      argv.append("{name}='{value}'".format(name=name, value=value))
    args = ', '.join(argv)

    if (expected_exception_type == exception_type or
        isinstance(exception_type, type(expected_exception_type))):
      if not exception_type and not matches(expected, actual):
        self.failures.append("[{args}] result ['{actual}'] does not match"
                             " ['{expected}'] at line {line}.".format(
                                 args=args, actual=actual,
                                 expected=expected, line=line))
      elif (expected_exception_message and
            not matches(expected_exception_message, exception_message)):
        self.failures.append("Exception message ['{actual}'] does not match "
                             "['{expected}'] at line {line}.".format(
                                 actual=exception_message,
                                 expected=expected_exception_message,
                                 line=line))
    elif exception_type:
      self.failures.append(
          '[{0}] should not raise {1} [{2}] at line {3}.'.format(
              args, exception_type.__name__,
              exception_message or exception_type, line))
    else:
      self.failures.append(
          '[{0}] should raise an exception at line {1}.'.format(args, line))

    while self.follow_on_tests:
      title, expected, func = self.follow_on_tests.pop()
      actual = func()
      if not matches(expected, actual):
        self.failures.append('[{0}] {1} mismatch at line {2}.'.format(
            actual, title, line))
