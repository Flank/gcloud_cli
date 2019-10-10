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

"""Test assertions for the test_case test assertions. We must dig deeper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from googlecloudsdk.core.util import files as file_utils
from tests.lib import test_case

import mock


class AssertStreamCompareTest(test_case.WithOutputCapture):
  """Tests _AssertStreamCompare variants."""

  def testAssertOutputMatches(self):
    sys.stdout.write("""\
usage: gcloud compute routes create  NAME --destination-range DESTINATION_RANGE [optional flags]
ERROR: (gcloud.compute.routes.create) one of the arguments --next-hop-instance --next-hop-address --next-hop-gateway is required
None
""")

    pattern = r'^usage:'
    self.AssertOutputMatches(pattern)
    self.AssertOutputMatches(pattern, success=True)

    pattern = r'^ERROR:'
    self.AssertOutputMatches(pattern)

    pattern = r'required$'
    self.AssertOutputMatches(pattern)

    pattern = r'\(gcloud.compute.routes.create\).*--next-hop-instance.*required'
    self.AssertOutputMatches(pattern)

    pattern = r'ThIs DoEs NoT mAtCh.'
    self.AssertOutputNotMatches(pattern)
    self.AssertOutputMatches(pattern, success=False)

  def testAssertOutputMatchesSuperfluousNormalized(self):
    sys.stdout.write("""\
usage: gcloud compute routes create  NAME --destination-range DESTINATION_RANGE [optional flags]
ERROR: (gcloud.compute.routes.create) one of the arguments --next-hop-instance --next-hop-address --next-hop-gateway is required
None
""")

    pattern = r'^usage:'
    self.AssertOutputMatches(pattern, normalize_space=True)
    self.AssertOutputMatches(pattern, normalize_space=True, success=True)

    pattern = r'^ERROR:'
    self.AssertOutputMatches(pattern, normalize_space=True)

    pattern = r'required$'
    self.AssertOutputMatches(pattern, normalize_space=True)

    pattern = r'\(gcloud.compute.routes.create\).*--next-hop-instance.*required'
    self.AssertOutputMatches(pattern, normalize_space=True)

    pattern = r'Not under Bozo\'s bigtop.'
    self.AssertOutputNotMatches(pattern, normalize_space=True)
    self.AssertOutputMatches(pattern, normalize_space=True, success=False)

  def testAssertOutputMatchesNeedsNormalized(self):
    sys.stdout.write("""\
\t \t \v usage: \t \v gcloud \t \v compute \t \v routes \t \v create \t \v  \t \v NAME \t \v --destination-range \t \v DESTINATION_RANGE \t \v [optional \t \v flags] \t \v
ERROR: \t \v (gcloud.compute.routes.create) \t \v one \t \v of \t \v the \t \v arguments \t \v --next-hop-instance \t \v --next-hop-address \t \v --next-hop-gateway \t \v is \t \v required  \t \v
None \t \v
""")

    pattern = r'^usage:'
    self.AssertOutputMatches(pattern, normalize_space=True)
    self.AssertOutputMatches(pattern, normalize_space=True, success=True)

    pattern = r'^ERROR:'
    self.AssertOutputMatches(pattern, normalize_space=True)

    pattern = r'required$'
    self.AssertOutputMatches(pattern, normalize_space=True)

    pattern = r'\(gcloud.compute.routes.create\).*--next-hop-instance.*required'
    self.AssertOutputMatches(pattern)

    pattern = r'ThIs DoEs NoT mAtCh.'
    self.AssertOutputNotMatches(pattern, normalize_space=True)
    self.AssertOutputMatches(pattern, normalize_space=True, success=False)

  def testAssertOutputMatchesStringFailure(self):
    sys.stdout.write('Nothing happens.\n')

    pattern = r'xyzzy'
    try:
      self.AssertOutputMatches(pattern)
    except self.failureException as e:
      sys.stderr.write(str(e))
    self.AssertErrContains('stdout does not match the expected pattern '
                           '[xyzzy]: [Nothing happens.\n]')

  def testAssertOutputMatchesLinesFailure(self):
    sys.stdout.write('xyzzy\nNothing happens.\n')

    pattern = 'hocus\npocus\n'
    try:
      self.AssertOutputMatches(pattern)
    except self.failureException as e:
      sys.stderr.write(str(e) + '\n')
    self.AssertErrContains("""\
stdout does not match the expected pattern:
<<<EXPECTED>>>
hocus
pocus
<<<ACTUAL>>>
xyzzy
Nothing happens.
<<<END>>>
""")

  def testAssertOutputMatchesLinesNormalizedFailure(self):
    sys.stdout.write("""\
\t \t \v usage: \t \v gcloud \t \v compute \t \v routes \t \v create \t \v  \t \v NAME \t \v --destination-range \t \v DESTINATION_RANGE \t \v [optional \t \v flags] \t \v
ERROR: \t \v (gcloud.compute.routes.create) \t \v one \t \v of \t \v the \t \v arguments \t \v --next-hop-instance \t \v --next-hop-address \t \v --next-hop-gateway \t \v is \t \v required  \t \v
None \t \v
""")

    pattern = 'hocus\npocus\n'
    try:
      self.AssertOutputMatches(pattern, normalize_space=True)
    except self.failureException as e:
      sys.stderr.write(str(e) + '\n')
    self.AssertErrContains("""\
stdout does not match the expected pattern:
<<<EXPECTED>>>
hocus
pocus
<<<ACTUAL>>>
usage: gcloud compute routes create NAME --destination-range DESTINATION_RANGE [optional flags]
ERROR: (gcloud.compute.routes.create) one of the arguments --next-hop-instance --next-hop-address --next-hop-gateway is required
None
<<<END>>>
""")

  def testAssertOutputMatchesLinesOutputNoNewline(self):
    sys.stdout.write('hocus\npocus')

    pattern = 'hocus\npocus\n'
    try:
      self.AssertOutputMatches(pattern)
    except self.failureException as e:
      sys.stderr.write(str(e) + '\n')
    self.AssertErrContains("""\
stdout does not match the expected pattern:
<<<EXPECTED>>>
hocus
pocus

<<<ACTUAL>>>
hocus
pocus
<<<END>>>
""")

  def testAssertOutputMatchesLinesPatternNoNewline(self):
    sys.stdout.write('pocus\nhocus\n')

    pattern = 'hocus\npocus'
    try:
      self.AssertOutputMatches(pattern)
    except self.failureException as e:
      sys.stderr.write(str(e) + '\n')
    self.AssertErrContains("""\
stdout does not match the expected pattern:
<<<EXPECTED>>>
hocus
pocus
<<<ACTUAL>>>
pocus
hocus

<<<END>>>
""")

  def testAssertOutputEqualsFilter(self):
    sys.stdout.write("""\
edit /tmp/tmp3ArSRR/dir/base-1.suffix
add /tmp/tmp3ArSRR/dir/base-2.suffix
""")

    expected = """\
edit //mock/tmp/dir/base-1.suffix
add //mock/tmp/dir/base-2.suffix
"""
    self.AssertOutputEquals(
        expected,
        actual_filter=lambda s: s.replace('/tmp/tmp3ArSRR', '//mock/tmp'))

  def testAssertOutputEqualsNormalizeWithNewlines(self):
    sys.stdout.write(' one \n two \n three \n four \n')
    expected = 'one\ntwo\nthree\nfour\n'
    self.AssertOutputEquals(expected, normalize_space=True)

  def testAssertOutputBytesEquals_EqualAscii(self):
    self.SetEncoding('utf8')
    sys.stdout.write('expected output')
    self.AssertOutputBytesEquals(b'expected output')

  def testAssertOutputBytesEquals_NotEqualAscii(self):
    self.SetEncoding('utf8')
    sys.stdout.write('expected output')
    with self.assertRaisesRegexp(
        AssertionError,
        r"stdout does not equal the expected value \[(b')?actual output'?\]: "
        r"\[(b')?expected output'?\]"):
      self.AssertOutputBytesEquals(b'actual output')

  def testAssertOutputBytesEquals_EqualUnicode(self):
    self.SetEncoding('utf8')
    unicode_string = 'Ṳᾔḯ¢◎ⅾℯ'
    sys.stdout.write(unicode_string)
    self.AssertOutputBytesEquals(unicode_string.encode('utf8'))

  def testAssertOutputBytesEquals_NotEqualUnicode(self):
    self.SetEncoding('utf8')
    unicode_string = 'Ṳᾔḯ¢◎ⅾℯ'
    sys.stdout.write('unicode')
    with self.assertRaisesRegexp(
        AssertionError,
        r'stdout does not equal the expected value.*'):
      self.AssertOutputBytesEquals(unicode_string.encode('utf8'))

  def testAssertOutputContainsUTF8WithAsciiEncodingMismatch(self):
    # Assertion failure messages should be immune to ascii encoding errors.
    sys.stdout.buffer.write('Ṳᾔḯ¢◎ⅾℯ'.encode('utf8'))
    expected = r'stdout does not equal the expected value.*\\u1e72'
    with self.assertRaisesRegex(AssertionError, expected):
      self.AssertOutputEquals('unicode')

  @test_case.Filters.RunOnlyOnPy2(
      'Encoding mismatches are not allowed to occur on Py3')
  def testAssertOutputContainsUTF8WithUTF8EncodingMismatch(self):
    # Assertion failure messages should be immune to ascii encoding errors.
    self.SetEncoding('utf8')
    sys.stdout.write('Ṳᾔḯ¢◎ⅾℯ'.encode('utf8'))
    # No Regexp here because pytest has a str() that trips ascii codec error.
    with self.assertRaises(AssertionError):
      self.AssertOutputEquals('unicode')

  @test_case.Filters.RunOnlyOnPy2(
      'Encoding mismatches are not allowed to occur on Py3')
  def testAssertOutputContainsUTF8WithUTF8EncodingMatch(self):
    # Assertion failure messages should be immune to ascii encoding errors.
    self.SetEncoding('utf8')
    sys.stdout.write('Ṳᾔḯ¢◎ⅾℯ'.encode('utf8'))
    self.AssertOutputEquals('Ṳᾔḯ¢◎ⅾℯ')


class AssertIsGoldenTest(test_case.WithOutputCapture):
  """Tests Assert*IsGolden variants."""

  def CreateTestDirectory(self, directory):
    test_dir = os.path.join(directory, 'test')
    file_utils.MakeDir(test_dir)
    with open(os.path.join(test_dir, 'empty.file'), 'w') as f:
      pass
    with open(os.path.join(test_dir, 'something.file'), 'w') as f:
      f.write('something\n')
    return test_dir

  def testAssertFileIsGolden(self):
    with file_utils.TemporaryDirectory() as directory:
      actual_file = os.path.join(directory, 'actual.txt')
      with open(actual_file, 'w') as f:
        f.write("""\
This is the
golden file
content.
""")
      self.AssertFileIsGolden(actual_file, __file__, 'golden-file.txt')

  def testAssertOutputIsGolden(self):
    sys.stdout.write("""\
This is the
golden file
content.
""")
    self.AssertOutputIsGolden(__file__, 'golden-file.txt')

  def testAssertOutputIsntGolden(self):
    sys.stdout.write("""\
This is the
golden file
content.
""")
    try:
      self.AssertOutputIsGolden(__file__, 'isnt', 'golden-file.txt')
    except self.failureException as e:
      sys.stderr.write(str(e) + '\n')
    self.AssertErrContains("""\
tests/unit/tests_lib/testdata/isnt/golden-file.txt does not contain the expected value
(see update-regressions.sh --help):
<<<EXPECTED>>>
No
it
isn't!
<<<ACTUAL>>>
This is the
golden file
content.
<<<END>>>
""")

  def testAssertDirectoryIsGolden(self):
    with file_utils.TemporaryDirectory() as directory:
      test_dir = self.CreateTestDirectory(directory)
      self.AssertDirectoryIsGolden(test_dir, __file__, 'is-golden.dir')

  def testAssertDirectoryIsntGolden(self):
    with file_utils.TemporaryDirectory() as directory:
      test_dir = self.CreateTestDirectory(directory)
      try:
        self.AssertDirectoryIsGolden(test_dir, __file__, 'isnt-golden.dir')
      except self.failureException as e:
        sys.stderr.write(str(e) + '\n')
      self.AssertErrContains("""\
tests/unit/tests_lib/testdata/isnt-golden.dir does not contain the expected value
(see update-regressions.sh --help):
<<<EXPECTED>>>
<<<DIRECTORY isnt>>>
12345 empty.file
00000 something.file
<<</DIRECTORY>>>
<<<ACTUAL>>>
<<<DIRECTORY test>>>
00000 empty.file
00010 something.file
<<</DIRECTORY>>>
<<<END>>>
""")

  def testGetTestdataRelativeAndPath(self):
    absolute = self.GetTestdataPath(__file__, 'is-golden.dir')
    package = self.GetTestdataPackagePath(absolute)
    self.assertTrue(absolute.endswith(package))
    expected = os.path.join(
        'tests', 'unit', 'tests_lib', 'testdata', 'is-golden.dir')
    self.assertEqual(expected, package)


class StripLongestCommonSpaceSuffixTest(test_case.Base):
  """Tests _StripLongestCommonSpaceSuffix."""

  def testStripLongestCommonSpaceSuffixEmpty(self):
    str_a = ''
    str_b = ''
    expected_a = ''
    expected_b = ''
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)

  def testStripLongestCommonSpaceSuffixOne(self):
    str_a = 'a'
    str_b = 'z'
    expected_a = 'a'
    expected_b = 'z'
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)

  def testStripLongestCommonSpaceSuffixAGtB(self):
    str_a = 'abc'
    str_b = 'z'
    expected_a = 'abc'
    expected_b = 'z'
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)

  def testStripLongestCommonSpaceSuffixALtB(self):
    str_a = 'a'
    str_b = 'xyz'
    expected_a = 'a'
    expected_b = 'xyz'
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)

  def testStripLongestCommonSpaceSuffixOneLine(self):
    str_a = '\n'
    str_b = '\n'
    expected_a = ''
    expected_b = ''
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)

  def testStripLongestCommonSpaceSuffixUnequalLines(self):
    str_a = '\n\n\n'
    str_b = '\n'
    expected_a = '\n\n'
    expected_b = ''
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)

  def testStripLongestCommonSpaceSuffixDiffSpace(self):
    str_a = 'a \t '
    str_b = 'xyz\t \t'
    expected_a = 'a \t '
    expected_b = 'xyz\t \t'
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)

  def testStripLongestCommonSpaceSuffixDiffAndSameSpace(self):
    str_a = 'a\t \t '
    str_b = 'xyz  \t '
    expected_a = 'a\t'
    expected_b = 'xyz '
    actual_a, actual_b = test_case._StripLongestCommonSpaceSuffix(str_a, str_b)
    self.assertEqual(expected_a, actual_a)
    self.assertEqual(expected_b, actual_b)


class TestSkipDecorator(test_case.Base):

  def SetUp(self):
    self.why = 'Just Because'
    self.bug = 'b/1234'
    self.bad_bug = 'later'
    self.expected_regex = r'.*Just Because.*b/1234.*'
    # Disable running skipped tests.
    self.StartEnvPatch({'CLOUDSDK_RUN_SKIPPED_TESTS': ''})

  @staticmethod
  def DummyCannedSkip(func):
    return test_case.Filters._CannedSkip(test_case.unittest.skipIf, True, func,
                                         'Dummy Skip')

  def testSimpleSkip(self):
    @test_case.Filters.skip(self.why, self.bug)
    def foo():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest,
                                self.expected_regex):
      foo()

  @mock.patch.object(test_case, 'pytest')
  def testSilence(self, pytest_mock):
    decorator_mock = mock.Mock()
    pytest_mock.mark.silence.return_value = decorator_mock

    def foo():
      return 42

    test_case.Filters._Silence(reason=self.why)(foo)
    decorator_mock.assert_called_with(foo)

  @test_case.Filters.RunOnlyIf(test_case.pytest, 'Requires pytest.')
  def testSilenceMark(self):
    @test_case.Filters._Silence(reason=self.why)
    def foo():
      return 42

    self.assertTrue(hasattr(foo, 'silence'))

  @mock.patch.object(test_case, 'pytest', mock.MagicMock())
  @mock.patch.object(test_case.Filters, '_Silence')
  def testRunSkippedTests(self, silence_mock):
    self.StartEnvPatch({'CLOUDSDK_RUN_SKIPPED_TESTS': 'True'})
    test_case.Filters.skip(self.why, self.bug)
    silence_mock.assert_called_once()

  @mock.patch.object(test_case, 'pytest', mock.MagicMock())
  @mock.patch.object(test_case.Filters, '_Silence')
  def testSkipAlways(self, silence_mock):
    self.StartEnvPatch({'CLOUDSDK_RUN_SKIPPED_TESTS': 'True'})
    @test_case.Filters.skipAlways(self.why, self.bug)
    def foo():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest,
                                self.expected_regex):
      foo()

    silence_mock.assert_not_called()

  @test_case.Filters.DoNotRunOnPy2('Python3 only functionality')
  @mock.patch.object(test_case, 'pytest', mock.MagicMock())
  @mock.patch.object(test_case.Filters, '_Silence')
  def testSkipOnPy3Always(self, silence_mock):
    self.StartEnvPatch({'CLOUDSDK_RUN_SKIPPED_TESTS': 'True'})
    @test_case.Filters.SkipOnPy3Always(self.why, self.bug)
    def foo():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest,
                                self.expected_regex):
      foo()

    silence_mock.assert_not_called()

  def testSkipIfTrue(self):
    @test_case.Filters.skipIf(True, self.why, self.bug)
    def foo():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest,
                                self.expected_regex):
      foo()

  def testSkipIfFalse(self):
    @test_case.Filters.skipIf(False, self.why, self.bug)
    def foo():
      return 42

    self.assertEqual(42, foo())

  def testSkipUnlessTrue(self):
    @test_case.Filters.skipUnless(True, self.why, self.bug)
    def foo():
      return 42

    self.assertEqual(42, foo())

  def testSkipUnlessFalse(self):
    @test_case.Filters.skipUnless(False, self.why, self.bug)
    def foo():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest,
                                self.expected_regex):
      foo()

  def testSkipNoExplanation(self):
    # These really ought to raise a more descriptive error, but I don't know how
    # to make them do that in a reasonable way
    with self.assertRaises(TypeError):
      @test_case.Filters.skip
      def unused_foo():
        return 42

  def testSkipBlankExplanation(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skip()
      def unused_foo():
        return 42

  def testSkipNoBugNumber(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skip(self.why)
      def unused_foo():
        return 42

  def testSkipInvalidBugNumber(self):
    with self.assertRaises(test_case.InvalidFilterError):
      @test_case.Filters.skip(self.why, self.bad_bug)
      def unused_foo():
        return 42

  def testSkipIfTrueNoExplanation(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skipIf(True)
      def unused_foo():
        return 42

  def testSkipIfFalseNoExplanation(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skipIf(False)
      def unused_foo():
        return 42

  def testSkipIfTrueNoBugNumber(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skipIf(True, self.why)
      def unused_foo():
        return 42

  def testSkipIfFalseNoBugNumber(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skipIf(False, self.why)
      def unused_foo():
        return 42

  def testSkipIfTrueInvalidBugNumber(self):
    with self.assertRaises(test_case.InvalidFilterError):
      @test_case.Filters.skipIf(True, self.why, self.bad_bug)
      def unused_foo():
        return 42

  def testSkipIfFalseInvalidBugNumber(self):
    with self.assertRaises(test_case.InvalidFilterError):
      @test_case.Filters.skipIf(False, self.why, self.bad_bug)
      def unused_foo():
        return 42

  def testSkipUnlessTrueNoExplanation(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skipUnless(True)
      def unused_foo():
        return 42

  def testSkipUnlessFalseNoExplanation(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skipUnless(False)
      def unused_foo():
        return 42

  def testSkipUnlessTrueNoBugNumber(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skipUnless(True, self.why)
      def unused_foo():
        return 42

  def testSkipUnlessFalseNoBugNumber(self):
    with self.assertRaises(TypeError):
      @test_case.Filters.skipIf(False, self.why)
      def unused_foo():
        return 42

  def testSkipUnlessTrueInvalidBugNumber(self):
    with self.assertRaises(test_case.InvalidFilterError):
      @test_case.Filters.skipUnless(True, self.why, self.bad_bug)
      def unused_foo():
        return 42

  def testSkipUnlessFalseInvalidBugNumber(self):
    with self.assertRaises(test_case.InvalidFilterError):
      @test_case.Filters.skipIf(False, self.why, self.bad_bug)
      def unused_foo():
        return 42

  def testCannedSkipDefault(self):
    @TestSkipDecorator.DummyCannedSkip
    def foo():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest, '.*Dummy Skip.*'):
      foo()

  def testCannedSkipNonDefault(self):
    @TestSkipDecorator.DummyCannedSkip('Explaining')
    def foo():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest, '.*Explaining.*'):
      foo()

  def testRunOnlyWithEnvEmpty(self):
    env = self.StartPatch('os.environ')
    env.get.return_value = None

    @test_case.Filters.RunOnlyWithEnv('FOO')
    def bar():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest, '.*FOO.*'):
      bar()

  def testRunOnlyWithEnvFalse(self):
    env = self.StartPatch('os.environ')
    env.get.return_value = False

    @test_case.Filters.RunOnlyWithEnv('FOO')
    def bar():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest, '.*FOO.*'):
      bar()

  def testRunOnlyWithEnvFalseString(self):
    # Specifically for Jenkins (underlying Kokoro) boolean compatibility
    env = self.StartPatch('os.environ')
    env.get.return_value = 'false'

    @test_case.Filters.RunOnlyWithEnv('FOO')
    def bar():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest, '.*FOO.*'):
      bar()

  def testRunOnlyWithEnvTrue(self):
    env = self.StartPatch('os.environ')
    env.get.side_effect = lambda x, _: x == 'FOO'

    @test_case.Filters.RunOnlyWithEnv('FOO')
    def bar():
      return 42

    self.assertEqual(42, bar())

  def testRunOnlyIfLongrunning(self):
    env = self.StartPatch('os.environ')
    env.get.side_effect = (
        lambda x, _: 'true' if x == 'ENABLE_LONGRUNNING_TESTS' else 'false')

    @test_case.Filters.RunOnlyIfLongrunning
    def bar():
      return 42

    self.assertEqual(42, bar())

  def testRunOnlyIfLongrunningFalse(self):
    env = self.StartPatch('os.environ')
    env.get.return_value = 'false'

    @test_case.Filters.RunOnlyIfLongrunning
    def bar():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest,
                                '.*marked as longrunning.*'):
      bar()

  def testRunOnlyIfLongrunningFalseReason(self):
    env = self.StartPatch('os.environ')
    env.get.return_value = 'false'

    @test_case.Filters.RunOnlyIfLongrunning('reason')
    def bar():
      return 42

    with self.assertRaisesRegex(test_case.unittest.SkipTest,
                                '.*reason.*'):
      bar()


class SkipFunctionTest(test_case.Base):

  def testSkipContextManager(self):
    with self.assertRaises(test_case.unittest.SkipTest):
      with self.SkipTestIfRaises(Exception):
        raise Exception('FOO')


class OSSkipsTest(test_case.Base):

  @test_case.Filters.DoNotRunOnWindows
  @test_case.Filters.DoNotRunOnMac
  @test_case.Filters.DoNotRunOnLinux
  def testSkipAllOS(self):
    raise Exception('This test should not run on any OS.')

  def testCountOSs(self):
    """Exactly one of these should run."""
    count = {'os': 0}

    try:
      @test_case.Filters.RunOnlyOnWindows
      def count_windows():
        count['os'] += 1
      count_windows()
    except test_case.unittest.SkipTest:
      pass

    try:
      @test_case.Filters.RunOnlyOnMac
      def count_mac():
        count['os'] += 1
      count_mac()
    except test_case.unittest.SkipTest:
      pass

    try:
      @test_case.Filters.RunOnlyOnLinux
      def count_linux():
        count['os'] += 1
      count_linux()
    except test_case.unittest.SkipTest:
      pass

    self.assertEqual(1, count['os'])


if __name__ == '__main__':
  test_case.main()
