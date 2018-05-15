# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Test assertions for the subtests module. We must dig deeper."""

from __future__ import absolute_import
from __future__ import unicode_literals

import re

from unittest import case

from tests.lib import subtests
from tests.lib import test_case


class SubTestsExampleBase(subtests.Base):
  """Example subtests.Base tested by SubTestsTest.

  Even though this is an abstract base class, the test runner crashes with abc
  decorations.

  NOTE: In order to keep the test failure line numbers in sync, each example
  self.Run(...) or T(...) call must be on a single line.
  """

  TEST_COUNT = 9
  TEST_FAIL_COUNT = 5

  EXCEPTION_MESSAGE = '[exception] means raise an exception'
  UNKNOWN_MESSAGE = 'definitely not the exception message'

  def __init__(self, *args, **kwargs):
    super(SubTestsExampleBase, self).__init__(*args, **kwargs)
    self.direct_line_offset = 0
    self.indirect_line_offset = 0

  def runTest(self):
    """Foil the test runner."""
    pass

  def runExample(self):
    self.SetUp()
    self.exampleDirectSubTest()
    self.TearDown()

    self.SetUp()
    self.exampleIndirectSubTest()
    self.TearDown()

  def SetDirectLineOffset(self):
    self.direct_line_offset = subtests.GetCallerSourceLine(1)

  def SetIndirectLineOffset(self):
    self.indirect_line_offset = subtests.GetCallerSourceLine(1)

  def GetFailureCountsAndLines(self):
    """Returns the subtest example failure counts and source lines.

    All subtest example classes have the same subtest failure sequences and
    relative line numbers. The direct_line_offset and indirect_line_offseT
    example class attributes are the line offsets to the first direct and
    indirect example class subtests.

    Returns:
      The subtest example failure counts and source lines.
      Used to generate the expected subtest output strings.
    """

    def _Lines(offset):
      return [offset + 2, offset + 4, offset + 5, offset + 6, offset + 9]

    counts = [self.TEST_FAIL_COUNT, self.TEST_COUNT]
    return (counts +
            _Lines(self.direct_line_offset) +
            counts +
            _Lines(self.indirect_line_offset))

  def RunSubTest(self, value):
    """@abc.abstractmethod Runs a subtest on value."""
    pass

  def exampleDirectSubTest(self):
    """@abc.abstractmethod Runs all of the direct self.Run(...) subtests."""
    pass

  def exampleIndirectSubTest(self):
    """@abc.abstractmethod Runs all of the direct T(...) subtests."""
    pass


class SubTestsExampleRunner(test_case.Base):
  """Tests subtests.Base on SubTestsExampleBase."""

  def Fail(self, actual):
    self.actual.append(actual)

  def SetUp(self):
    self._fail = self.fail
    self.StartObjectPatch(case.TestCase, 'fail', side_effect=self.Fail)
    self.actual = []


class SubTestsExample(SubTestsExampleBase):
  """Example subtests.Base tested by SubTestsTest."""

  def RunSubTest(self, value):
    if value == 'exception':
      raise ValueError(self.EXCEPTION_MESSAGE)
    elif value == 'follow-on-pass':
      self.AddFollowOnTest('extra', 'FollowOnPass', lambda: 'FollowOnPass')
    elif value == 'follow-on-fail':
      self.AddFollowOnTest('extra', 'FollowOnFail', lambda: 'FOLLOW_ON_FAIL')
    return value.upper()

  def exampleDirectSubTest(self):
    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetDirectLineOffset()
    self.Run('VALUE', 'value')  # pass
    self.Run('error', 'value')  # fail
    self.Run('FOLLOW-ON-PASS', 'follow-on-pass')  # follow-on test pass
    self.Run('FOLLOW-ON-FAIL', 'follow-on-fail')  # follow-on test fail
    self.Run(None, 'exception')  # fail: unexpected exception
    self.Run('VALUE', 'value', exception=ValueError)  # fail: no exception
    self.Run(None, 'exception', exception=ValueError)  # pass: got exception
    self.Run(None, 'exception', exception=ValueError(self.EXCEPTION_MESSAGE))
    self.Run(None, 'exception', exception=ValueError(self.UNKNOWN_MESSAGE))

  def exampleIndirectSubTest(self):

    def T(expected, value, exception=None):
      self.Run(expected, value, depth=2, exception=exception)

    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetIndirectLineOffset()
    T('VALUE', 'value')
    T('error', 'value')
    T('FOLLOW-ON-PASS', 'follow-on-pass')
    T('FOLLOW-ON-FAIL', 'follow-on-fail')
    T(None, 'exception')
    T('VALUE', 'value', exception=ValueError)
    T(None, 'exception', exception=ValueError)
    T(None, 'exception', exception=ValueError(self.EXCEPTION_MESSAGE))
    T(None, 'exception', exception=ValueError(self.UNKNOWN_MESSAGE))


class SubTestsTest(SubTestsExampleRunner):
  """Tests subtests.Base on SubTestsExample."""

  def testSubTestsExample(self):
    example = SubTestsExample()
    example.runExample()
    expected = """\
{}/{} subtests failed:
  ['value'] result ['VALUE'] does not match ['error'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  ['exception'] should not raise ValueError [[exception] means raise an exception] at line {}.
  ['value'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely not the exception message'] at line {}.

{}/{} subtests failed:
  ['value'] result ['VALUE'] does not match ['error'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  ['exception'] should not raise ValueError [[exception] means raise an exception] at line {}.
  ['value'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely not the exception message'] at line {}.
""".format(*example.GetFailureCountsAndLines())
    actual = '\n'.join(self.actual)
    if expected != actual:
      self._fail("""\
stderr does not equal the expected value:
<<<EXPECTED>>>
{expected}
<<<ACTUAL>>>
{actual}
<<<END>>>
""".format(expected=expected, actual=actual))


class SubTestsExampleWithMultipleArgs(SubTestsExampleBase):
  """Example subtests.Base tested by SubTestsWithMultipleArgsTest."""

  def RunSubTest(self, arg1, arg2):
    value = arg1 + arg2
    if value == 'exception':
      raise ValueError('[{0}] means raise an exception'.format(value))
    elif value == 'follow-on-pass':
      self.AddFollowOnTest('extra', 'FollowOnPass', lambda: 'FollowOnPass')
    elif value == 'follow-on-fail':
      self.AddFollowOnTest('extra', 'FollowOnFail', lambda: 'FOLLOW_ON_FAIL')
    return value.upper()

  def exampleDirectSubTest(self):
    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetDirectLineOffset()
    self.Run('VALUE', 'v', 'alue')
    self.Run('error', 'v', 'alue')
    self.Run('FOLLOW-ON-PASS', 'f', 'ollow-on-pass')
    self.Run('FOLLOW-ON-FAIL', 'f', 'ollow-on-fail')
    self.Run(None, 'e', 'xception')
    self.Run('VALUE', 'v', 'alue', exception=ValueError)
    self.Run(None, 'e', 'xception', exception=ValueError)
    self.Run(None, 'e', 'xception', exception=ValueError(self.EXCEPTION_MESSAGE))
    self.Run(None, 'e', 'xception', exception=ValueError(self.UNKNOWN_MESSAGE))

  def exampleIndirectSubTest(self):

    def T(expected, arg1, arg2, exception=None):
      self.Run(expected, arg1, arg2, depth=2, exception=exception)

    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetIndirectLineOffset()
    T('VALUE', 'v', 'alue')
    T('error', 'v', 'alue')
    T('FOLLOW-ON-PASS', 'f', 'ollow-on-pass')
    T('FOLLOW-ON-FAIL', 'f', 'ollow-on-fail')
    T(None, 'e', 'xception')
    T('VALUE', 'v', 'alue', exception=ValueError)
    T(None, 'e', 'xception', exception=ValueError)
    T(None, 'e', 'xception', exception=ValueError(self.EXCEPTION_MESSAGE))
    T(None, 'e', 'xception', exception=ValueError(self.UNKNOWN_MESSAGE))


class SubTestsWithMultipleArgsTest(SubTestsExampleRunner):
  """Tests subtests.Base on SubTestsExampleWithMultipleArgs."""

  def testSubTestsExample(self):
    example = SubTestsExampleWithMultipleArgs()
    example.runExample()
    expected = """\
{}/{} subtests failed:
  ['v', 'alue'] result ['VALUE'] does not match ['error'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  ['e', 'xception'] should not raise ValueError [[exception] means raise an exception] at line {}.
  ['v', 'alue'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely not the exception message'] at line {}.

{}/{} subtests failed:
  ['v', 'alue'] result ['VALUE'] does not match ['error'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  ['e', 'xception'] should not raise ValueError [[exception] means raise an exception] at line {}.
  ['v', 'alue'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely not the exception message'] at line {}.
""".format(*example.GetFailureCountsAndLines())
    actual = '\n'.join(self.actual)
    if expected != actual:
      self._fail("""\
stderr does not equal the expected value:
<<<EXPECTED>>>
{expected}
<<<ACTUAL>>>
{actual}
<<<END>>>
""".format(expected=expected, actual=actual))


class SubTestsExampleWithMultipleKwargs(SubTestsExampleBase):
  """Example subtests.Base tested by SubTestsWithMultipleArgsTest."""

  def RunSubTest(self, arg1='', arg2=''):
    value = arg1 + arg2
    if value == 'exception':
      raise ValueError('[{0}] means raise an exception'.format(value))
    elif value == 'follow-on-pass':
      self.AddFollowOnTest('extra', 'FollowOnPass', lambda: 'FollowOnPass')
    elif value == 'follow-on-fail':
      self.AddFollowOnTest('extra', 'FollowOnFail', lambda: 'FOLLOW_ON_FAIL')
    return value.upper()

  def exampleDirectSubTest(self):
    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetDirectLineOffset()
    self.Run('VALUE', arg1='v', arg2='alue')
    self.Run('error', arg1='v', arg2='alue')
    self.Run('FOLLOW-ON-PASS', arg1='f', arg2='ollow-on-pass')
    self.Run('FOLLOW-ON-FAIL', arg1='f', arg2='ollow-on-fail')
    self.Run(None, arg1='e', arg2='xception')
    self.Run('VALUE', arg1='v', arg2='alue', exception=ValueError)
    self.Run(None, arg1='e', arg2='xception', exception=ValueError)
    self.Run(None, arg1='e', arg2='xception', exception=ValueError(self.EXCEPTION_MESSAGE))
    self.Run(None, arg1='e', arg2='xception', exception=ValueError(self.UNKNOWN_MESSAGE))

  def exampleIndirectSubTest(self):

    def T(expected, arg1='', arg2='', exception=None):
      self.Run(expected, arg1=arg1, arg2=arg2, depth=2, exception=exception)

    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetIndirectLineOffset()
    T('VALUE', arg2='value')
    T('error', arg1='value')
    T('FOLLOW-ON-PASS', arg1='f', arg2='ollow-on-pass')
    T('FOLLOW-ON-FAIL', arg1='f', arg2='ollow-on-fail')
    T(None, arg1='e', arg2='xception')
    T('VALUE', arg1='v', arg2='alue', exception=ValueError)
    T(None, arg1='e', arg2='xception', exception=ValueError)
    T(None, arg1='e', arg2='xception', exception=ValueError(self.EXCEPTION_MESSAGE))
    T(None, arg1='e', arg2='xception', exception=ValueError(self.UNKNOWN_MESSAGE))


class SubTestsWithMultipleKwargsTest(SubTestsExampleRunner):
  """Tests subtests.Base on SubTestsExampleWithMultipleKwargs."""

  def testSubTestsExample(self):
    example = SubTestsExampleWithMultipleKwargs()
    example.runExample()
    expected = """\
{}/{} subtests failed:
  [arg1='v', arg2='alue'] result ['VALUE'] does not match ['error'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  [arg1='e', arg2='xception'] should not raise ValueError [[exception] means raise an exception] at line {}.
  [arg1='v', arg2='alue'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely not the exception message'] at line {}.

{}/{} subtests failed:
  [arg1='value', arg2=''] result ['VALUE'] does not match ['error'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  [arg1='e', arg2='xception'] should not raise ValueError [[exception] means raise an exception] at line {}.
  [arg1='v', arg2='alue'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely not the exception message'] at line {}.
""".format(*example.GetFailureCountsAndLines())
    actual = '\n'.join(self.actual)
    if expected != actual:
      self._fail("""\
stderr does not equal the expected value:
<<<EXPECTED>>>
{expected}
<<<ACTUAL>>>
{actual}
<<<END>>>
""".format(expected=expected, actual=actual))


class SubTestsExampleWithMultipleArgsKwargs(SubTestsExampleBase):
  """Example subtests.Base tested by SubTestsWithMultipleArgsKwargsTest."""

  def RunSubTest(self, arg1, arg2, arg3='', arg4=''):
    value = arg1 + arg2 + arg3 + arg4
    if value == 'exception':
      raise ValueError('[{0}] means raise an exception'.format(value))
    elif value == 'follow-on-pass':
      self.AddFollowOnTest('extra', 'FollowOnPass', lambda: 'FollowOnPass')
    elif value == 'follow-on-fail':
      self.AddFollowOnTest('extra', 'FollowOnFail', lambda: 'FOLLOW_ON_FAIL')
    return value.upper()

  def exampleDirectSubTest(self):
    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetDirectLineOffset()
    self.Run('VALUE', 'v', 'a', arg3='l', arg4='ue')
    self.Run('error', 'v', 'a', arg3='l', arg4='ue')
    self.Run('FOLLOW-ON-PASS', 'f', 'o', arg3='l', arg4='low-on-pass')
    self.Run('FOLLOW-ON-FAIL', 'f', 'o', arg3='l', arg4='low-on-fail')
    self.Run(None, 'e', 'x', arg3='c', arg4='eption')
    self.Run('VALUE', 'v', 'a', arg3='l', arg4='ue', exception=ValueError)
    self.Run(None, 'e', 'x', arg3='c', arg4='eption', exception=ValueError)
    self.Run(None, 'e', 'x', arg3='c', arg4='eption', exception=ValueError(self.EXCEPTION_MESSAGE))
    self.Run(None, 'e', 'x', arg3='c', arg4='eption', exception=ValueError(self.UNKNOWN_MESSAGE))

  def exampleIndirectSubTest(self):

    def T(expected, arg1, arg2, arg3='', arg4='', exception=None):
      self.Run(expected, arg1, arg2, arg3=arg3, arg4=arg4, depth=2,
               exception=exception)

    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetIndirectLineOffset()
    T('VALUE', 'v', 'a', arg4='lue')
    T('error', 'v', 'a', arg3='lue')
    T('FOLLOW-ON-PASS', 'f', 'o', arg3='l', arg4='low-on-pass')
    T('FOLLOW-ON-FAIL', 'f', 'o', arg3='l', arg4='low-on-fail')
    T(None, 'e', 'x', arg3='c', arg4='eption')
    T('VALUE', 'v', 'a', arg3='l', arg4='ue', exception=ValueError)
    T(None, 'e', 'x', arg3='c', arg4='eption', exception=ValueError)
    T(None, 'e', 'x', arg3='c', arg4='eption', exception=ValueError(self.EXCEPTION_MESSAGE))
    T(None, 'e', 'x', arg3='c', arg4='eption', exception=ValueError(self.UNKNOWN_MESSAGE))


class SubTestsWithMultipleArgsKwargsTest(SubTestsExampleRunner):
  """Tests subtests.Base on SubTestsExampleWithMultipleArgsKwargs."""

  def testSubTestsExample(self):
    example = SubTestsExampleWithMultipleArgsKwargs()
    example.runExample()
    expected = """\
{}/{} subtests failed:
  ['v', 'a', arg3='l', arg4='ue'] result ['VALUE'] does not match ['error'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  ['e', 'x', arg3='c', arg4='eption'] should not raise ValueError [[exception] means raise an exception] at line {}.
  ['v', 'a', arg3='l', arg4='ue'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely not the exception message'] at line {}.

{}/{} subtests failed:
  ['v', 'a', arg3='lue', arg4=''] result ['VALUE'] does not match ['error'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  ['e', 'x', arg3='c', arg4='eption'] should not raise ValueError [[exception] means raise an exception] at line {}.
  ['v', 'a', arg3='l', arg4='ue'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely not the exception message'] at line {}.
""".format(*example.GetFailureCountsAndLines())
    actual = '\n'.join(self.actual)
    if expected != actual:
      self._fail("""\
stderr does not equal the expected value:
<<<EXPECTED>>>
{expected}
<<<ACTUAL>>>
{actual}
<<<END>>>
""".format(expected=expected, actual=actual))


class SubTestsMatchesExample(SubTestsExampleBase):
  """Example subtests.Base tested by SubTestsWithMatchesTest."""

  def RunSubTest(self, value):
    if value == 'exception':
      raise ValueError('[{0}] means raise an exception'.format(value))
    elif value == 'follow-on-pass':
      self.AddFollowOnTest('extra', 'FollowOnPass', lambda: 'FollowOnPass')
    elif value == 'follow-on-fail':
      self.AddFollowOnTest('extra', 'FollowOnFail', lambda: 'FOLLOW_ON_FAIL')
    return value.upper()

  def exampleDirectSubTest(self):
    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetDirectLineOffset()
    self.Run('V.*E', 'value', matches=re.match)
    self.Run('e.*r', 'value', matches=re.match)
    self.Run('F.*-O.*-P.*', 'follow-on-pass', matches=re.match)
    self.Run('F.*-O.*-F.*', 'follow-on-fail', matches=re.match)
    self.Run(None, 'exception', matches=re.match)
    self.Run('V.*E', 'value', exception=ValueError, matches=re.match)
    self.Run(None, 'exception', exception=ValueError, matches=re.match)
    self.Run(None, 'exception', exception=ValueError(re.escape(self.EXCEPTION_MESSAGE)), matches=re.match)
    self.Run(None, 'exception', exception=ValueError(re.escape(self.UNKNOWN_MESSAGE)), matches=re.match)

  def exampleIndirectSubTest(self):

    def T(expected, value, exception=None):
      self.Run(expected, value, depth=2, exception=exception, matches=re.match)

    # pylint: disable=line-too-long, preserve subtest line offsets
    self.SetIndirectLineOffset()
    T('V.*E', 'value')
    T('e.*r', 'value')
    T('F.*-O.*-P.*', 'follow-on-pass')
    T('F.*-O.*-F.*', 'follow-on-fail')
    T(None, 'exception')
    T('V.*E', 'value', exception=ValueError)
    T(None, 'exception', exception=ValueError)
    T(None, 'exception', exception=ValueError(re.escape(self.EXCEPTION_MESSAGE)))
    T(None, 'exception', exception=ValueError(re.escape(self.UNKNOWN_MESSAGE)))


class SubTestsWithMatchesTest(SubTestsExampleRunner):
  """Tests subtests.Base on SubTestsExample with matches=func."""

  def Fail(self, actual):
    self.actual.append(actual)

  def SetUp(self):
    self._fail = self.fail
    self.StartObjectPatch(case.TestCase, 'fail', side_effect=self.Fail)
    self.actual = []

  def testSubTestsMatchesExample(self):
    example = SubTestsMatchesExample()
    example.runExample()
    expected = """\
{}/{} subtests failed:
  ['value'] result ['VALUE'] does not match ['e.*r'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  ['exception'] should not raise ValueError [[exception] means raise an exception] at line {}.
  ['value'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely\\\\ not\\\\ the\\\\ exception\\\\ message'] at line {}.

{}/{} subtests failed:
  ['value'] result ['VALUE'] does not match ['e.*r'] at line {}.
  [FOLLOW_ON_FAIL] extra mismatch at line {}.
  ['exception'] should not raise ValueError [[exception] means raise an exception] at line {}.
  ['value'] should raise an exception at line {}.
  Exception message ['[exception] means raise an exception'] does not match ['definitely\\\\ not\\\\ the\\\\ exception\\\\ message'] at line {}.
""".format(*example.GetFailureCountsAndLines())
    actual = '\n'.join(self.actual)
    if expected != actual:
      self._fail("""\
stderr does not equal the expected value:
<<<EXPECTED>>>
{expected}
<<<ACTUAL>>>
{actual}
<<<END>>>
""".format(expected=expected, actual=actual))


if __name__ == '__main__':
  test_case.main()
