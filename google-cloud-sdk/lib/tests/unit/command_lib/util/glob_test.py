# -*- coding: utf-8 -*- #
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

"""Tests for googlecloudsdk.command_lib.util.glob."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import ntpath
import os
import shutil
import tempfile

from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.command_lib.util import glob
from tests.lib import parameterized
from tests.lib import test_case


@contextlib.contextmanager
def _TempDir():
  temp_path = tempfile.mkdtemp()
  try:
    yield temp_path
  finally:
    shutil.rmtree(temp_path)


class PatternTest(parameterized.TestCase, test_case.TestCase):

  def _RunTest(self, pattern, path, result, is_dir=False):
    pattern = glob.Glob.FromString(pattern)
    self.assertEqual(pattern.Matches(path, is_dir), result)

  @parameterized.parameters(
      ('foo', True),
      ('foo' + os.path.sep, True),
      ('bar', False),
      (os.path.join('bar', 'foo'), True),
      (os.path.join('foo', 'bar'), False),
      ('foobar', False),
      ('barfoo', False)
  )
  def testPattern_Basic(self, path, result):
    self._RunTest('foo', path, result)

  @parameterized.parameters(
      ('\\#foo', '#foo', True),
      ('foo#', 'foo#', True),
      ('foo\\#', 'foo#', True),
      ('foo#bar', 'foo#bar', True),
      ('foo\\#bar', 'foo#bar', True),
  )
  def testPattern_Hash(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  def testPattern_BeginsWithHash(self):
    with self.assertRaises(glob.InvalidLineError):
      gcloudignore.Pattern.FromString('#foo')

  @parameterized.parameters(
      ('',),
      ('  ',),
  )
  def testPattern_BlankLineInvalid(self, pattern):
    with self.assertRaises(glob.InvalidLineError):
      gcloudignore.Pattern.FromString(pattern)

  def testPattern_TrailingBackslash(self):
    with self.assertRaises(glob.InvalidLineError):
      gcloudignore.Pattern.FromString('\\')

  @parameterized.parameters(
      ('**/', os.path.join('foo', 'bar'), False, False),
      ('**/', os.path.join('foo', 'bar'), True, True),
      ('**/bar', 'bar', False, True),
      ('**/bar', os.path.join('foo', 'bar'), False, True),
      ('**/bar/', 'bar', True, True),
      ('**/bar/', 'bar', False, False),
  )
  def testPattern_LeadingConsecutiveStars(self, pattern, path, is_dir, result):
    self._RunTest(pattern, path, result, is_dir=is_dir)

  @parameterized.parameters(
      ('/**', 'foo', True),
      ('/**', os.path.join('foo', 'bar'), True),
      ('foo/**', 'foo', True),
      ('foo/**', os.path.join('foo', 'bar'), True),
      ('foo/**', os.path.join('baz', 'foo', 'bar'), False),
      ('foo/**', os.path.join('baz', 'bar'), False),
  )
  def testPattern_TrailingConsecutiveStars(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('/**/', 'foo', True, True),
      ('/**/', 'foo', False, False),
      ('/**/', os.path.join('foo', 'bar'), True, True),
      ('/**/', os.path.join('foo', 'bar'), False, False),
      ('foo/**/', os.path.join('baz', 'foo', 'bar'), True, False),
      ('foo/**/', os.path.join('baz', 'foo', 'bar'), False, False),
      ('/**/bar', 'bar', False, True),
      ('/**/bar', os.path.join('foo', 'bar'), False, True),
      ('foo/**/bar', os.path.join('foo', 'baz', 'bar'), False, True),
      ('foo/**/bar', os.path.join('foo', 'bar'), False, True),
  )
  def testPattern_MiddleConsecutiveStars(self, pattern, path, is_dir, result):
    self._RunTest(pattern, path, result, is_dir=is_dir)

  @parameterized.parameters(
      ('foo[*]*bar', 'foo*baz-bar', True),
      ('foo[*]*bar', 'foobaz-bar', False),
      ('foo[*][*]bar', 'foo**bar', True),
      ('foo[*][*]bar', 'foo-bar', False),
      ('foo*[*]bar', 'foo-*bar', True),
      ('foo*[*]bar', 'foo-bar', False),
  )
  def testPattern_EscapedConsecutiveStars(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('***', 'a', True),
      ('foo**', 'foo-', True),
      ('foo**', '-foo-', False),
      ('**bar', '-bar', True),
      ('**bar', '-bar-', False),
      ('foo**bar', 'foobar', True),
      ('foo**bar', 'foo-bar', True),
      ('foo/**bar', os.path.join('foo', '-bar'), True),
      ('foo/**bar', os.path.join('foo', '-bar-'), False),
      ('foo/bar**', os.path.join('foo', 'bar-'), True),
      ('foo/bar**', os.path.join('foo', '-bar-'), False),
  )
  def testPattern_InvalidConsecutiveStars(self, pattern, path, result):
    """Tests cases that gitignore spec calls 'invalid'."""
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('foo ', 'foo', True),
      ('foo ', 'foo ', False),
      ('foo\\ ', 'foo ', True),
      ('foo\\ ', 'foo', False),
      ('foo\t', 'foo', False),
      ('foo\t', 'foo\t', True),
      ('foo\\\t', 'foo\t', True),
      ('foo\\\t', 'foo', False),
      (' foo', ' foo', True),
      (' foo', 'foo', False),
      ('\\ foo', ' foo', True),
      ('\\ foo', 'foo', False),
      ('\tfoo', 'foo', False),
      ('\tfoo', '\tfoo', True),
      ('\\\tfoo', 'foo', False),
      ('\\\tfoo', '\tfoo', True),
  )
  def testPattern_TrailingSpaces(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('foo*baz', 'foobarbaz', True),
      ('foo*baz', 'foobaz', True),
      ('foo*baz', 'foo/baz', False),
      ('foo/*baz', 'foo/baz', True),
      ('foo/*baz', 'foo/bar/baz', False),
      ('foo?baz', 'foo-baz', True),
      ('foo?baz', 'foo--baz', False),
      ('foo-[ab]', 'foo-a', True),
      ('foo-[ab]', 'foo-b', True),
      ('foo-[ab]', 'foo-c', False),
      ('foo-[A-C]', 'foo-A', True),
      ('foo-[A-C]', 'foo-C', True),
      ('foo-[A-C]', 'foo-D', False),
      ('foo-[!ab]', 'foo-a', False),
      ('foo-[!ab]', 'foo-c', True),
      ('foo[*]', 'foo*', True),
      ('foo[*]', 'foo-', False),
      ('foo[?]', 'foo?', True),
      ('foo[?]', 'foo-', False),
      ('foo[[]', 'foo[', True),
      ('foo[[]', 'foo-', False),
      ('foo[', 'foo[', True),
      ('foo]', 'foo]', True),
  )
  def testPattern_ShellGlob(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('foo/bar', os.path.join('foo', 'bar'), True),
      ('bar/baz', os.path.join('foo', 'bar', 'baz'), True),
      ('bar/baz', os.path.join('foo', 'baz'), False),
      ('foo/ba[rz]', os.path.join('foo', 'bar'), True),
      ('foo/ba[rz]', os.path.join('foo', 'baz'), True),
      ('foo/ba[rz]', os.path.join('foo', 'bad'), False),
  )
  def testPattern_Subdirectory(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('foo/', 'foo/', True, True),
      ('foo/', 'foo/', False, False),
      ('foo/bar/', os.path.join('foo', 'bar'), True, True),
      ('foo/bar/', os.path.join('foo', 'bar'), False, False),
  )
  def testPattern_MustMatchDir(self, pattern, path, is_dir, result):
    self._RunTest(pattern, path, result, is_dir=is_dir)

  @parameterized.parameters(
      ('/foo/bar', os.path.join('foo', 'bar'), True),
      ('/bar/baz', os.path.join('foo', 'bar', 'baz'), False),
      ('/bar/baz', os.path.join('foo', 'baz'), False),
      ('*', '', True),
      ('/*', '', False),
      ('/*', 'foo', True),
  )
  def testGlob_LeadingSlash(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  def testGlob_Windows(self):
    self.StartObjectPatch(os, 'path', ntpath)
    self._RunTest('foo/bar', 'foo\\bar', True)

  @parameterized.parameters(
      ('', ''),
      ('foo', 'foo'),
      ('\\#foo', '#foo'),
      ('\\!foo', '!foo'),
      ('\\\\foo', '\\foo'),
      ('foo\\#', 'foo#'),
      ('foo\\!', 'foo!'),
      ('foo\\\\', 'foo\\'),
      ('\\\\foo', '\\foo'),
      ('\\a', 'a'),
      ('\\ ', ' '),
      ('\\*', '*'),
      ('\\?', '?'),
      ('\\[', '['),
      ('\\]', ']'),
  )
  def testUnescape(self, escaped, unescaped):
    self.assertEqual(glob._Unescape(escaped), unescaped)

  @parameterized.parameters(
      ('', ''),
      ('  ', ''),
      ('\\  ', ' '),
      ('\\ \\ ', '  '),
      (' \\ ', '  '),
      ('\\\\ ', '\\\\'),
      ('\t', '\t'),
      ('\\\t', '\\\t'),
      ('f\\!oo  ', 'f\\!oo'),
      ('f\\!oo\\  ', 'f\\!oo '),
      ('f\\!oo\\ \\ ', 'f\\!oo  '),
      ('  f\\!oo', '  f\\!oo'),
      ('\\  f\\!oo', '  f\\!oo'),
      ('\\ \\ f\\!oo', '  f\\!oo'),
  )
  def testHandleSpaces(self, original, stripped):
    self.assertEqual(glob._HandleSpaces(original), stripped)


if __name__ == '__main__':
  test_case.main()
