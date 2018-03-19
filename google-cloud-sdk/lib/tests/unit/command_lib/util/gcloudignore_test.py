# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for googlecloudsdk.command_lib.util.gcloudignore."""
import contextlib
import ntpath
import os
import shutil
import tempfile

from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock


IGNORE = gcloudignore.Match.IGNORE
NO_MATCH = gcloudignore.Match.NO_MATCH
INCLUDE = gcloudignore.Match.INCLUDE


@contextlib.contextmanager
def _TempDir():
  temp_path = tempfile.mkdtemp()
  try:
    yield temp_path
  finally:
    shutil.rmtree(temp_path)


class PatternTest(parameterized.TestCase, test_case.TestCase):

  def _RunTest(self, pattern, path, result, is_dir=False):
    pattern = gcloudignore.Pattern.FromString(pattern)
    self.assertEqual(pattern.Matches(path, is_dir), result)

  @parameterized.parameters(
      ('foo', IGNORE),
      ('foo' + os.path.sep, IGNORE),
      ('bar', NO_MATCH),
      (os.path.join('bar', 'foo'), IGNORE),
      (os.path.join('foo', 'bar'), NO_MATCH),
      ('foobar', NO_MATCH),
      ('barfoo', NO_MATCH)
  )
  def testPattern_Basic(self, path, result):
    self._RunTest('foo', path, result)

  @parameterized.parameters(
      ('foo', INCLUDE),
      ('foo' + os.path.sep, INCLUDE),
      ('bar', NO_MATCH),
      (os.path.join('bar', 'foo'), INCLUDE),
      (os.path.join('foo', 'bar'), NO_MATCH),
  )
  def testPattern_Negated(self, path, result):
    self._RunTest('!foo', path, result)

  @parameterized.parameters(
      ('!foo', IGNORE),
      ('foo', NO_MATCH),
  )
  def testPattern_BeginsWithBang(self, path, result):
    self._RunTest('\\!foo', path, result)

  @parameterized.parameters(
      ('\\#foo', '#foo', IGNORE),
      ('foo#', 'foo#', IGNORE),
      ('foo\\#', 'foo#', IGNORE),
      ('foo#bar', 'foo#bar', IGNORE),
      ('foo\\#bar', 'foo#bar', IGNORE),
  )
  def testPattern_Hash(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  def testPattern_BeginsWithHash(self):
    with self.assertRaises(gcloudignore.InvalidLineError):
      gcloudignore.Pattern.FromString('#foo')

  @parameterized.parameters(
      ('',),
      ('  ',),
  )
  def testPattern_BlankLineInvalid(self, pattern):
    with self.assertRaises(gcloudignore.InvalidLineError):
      gcloudignore.Pattern.FromString(pattern)

  def testPattern_TrailingBackslash(self):
    with self.assertRaises(gcloudignore.InvalidLineError):
      gcloudignore.Pattern.FromString('\\')

  @parameterized.parameters(
      ('**/', os.path.join('foo', 'bar'), False, NO_MATCH),
      ('**/', os.path.join('foo', 'bar'), True, IGNORE),
      ('**/bar', 'bar', False, IGNORE),
      ('**/bar', os.path.join('foo', 'bar'), False, IGNORE),
      ('**/bar/', 'bar', True, IGNORE),
      ('**/bar/', 'bar', False, NO_MATCH),
  )
  def testPattern_LeadingConsecutiveStars(self, pattern, path, is_dir, result):
    self._RunTest(pattern, path, result, is_dir=is_dir)

  @parameterized.parameters(
      ('/**', 'foo', IGNORE),
      ('/**', os.path.join('foo', 'bar'), IGNORE),
      ('foo/**', 'foo', IGNORE),
      ('foo/**', os.path.join('foo', 'bar'), IGNORE),
      ('foo/**', os.path.join('baz', 'foo', 'bar'), NO_MATCH),
      ('foo/**', os.path.join('baz', 'bar'), NO_MATCH),
  )
  def testPattern_TrailingConsecutiveStars(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('/**/', 'foo', True, IGNORE),
      ('/**/', 'foo', False, NO_MATCH),
      ('/**/', os.path.join('foo', 'bar'), True, IGNORE),
      ('/**/', os.path.join('foo', 'bar'), False, NO_MATCH),
      ('foo/**/', os.path.join('baz', 'foo', 'bar'), True, NO_MATCH),
      ('foo/**/', os.path.join('baz', 'foo', 'bar'), False, NO_MATCH),
      ('/**/bar', 'bar', False, IGNORE),
      ('/**/bar', os.path.join('foo', 'bar'), False, IGNORE),
      ('foo/**/bar', os.path.join('foo', 'baz', 'bar'), False, IGNORE),
      ('foo/**/bar', os.path.join('foo', 'bar'), False, IGNORE),
  )
  def testPattern_MiddleConsecutiveStars(self, pattern, path, is_dir, result):
    self._RunTest(pattern, path, result, is_dir=is_dir)

  @parameterized.parameters(
      ('foo[*]*bar', 'foo*baz-bar', IGNORE),
      ('foo[*]*bar', 'foobaz-bar', NO_MATCH),
      ('foo[*][*]bar', 'foo**bar', IGNORE),
      ('foo[*][*]bar', 'foo-bar', NO_MATCH),
      ('foo*[*]bar', 'foo-*bar', IGNORE),
      ('foo*[*]bar', 'foo-bar', NO_MATCH),
  )
  def testPattern_EscapedConsecutiveStars(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('***', 'a', IGNORE),
      ('foo**', 'foo-', IGNORE),
      ('foo**', '-foo-', NO_MATCH),
      ('**bar', '-bar', IGNORE),
      ('**bar', '-bar-', NO_MATCH),
      ('foo**bar', 'foobar', IGNORE),
      ('foo**bar', 'foo-bar', IGNORE),
      ('foo/**bar', os.path.join('foo', '-bar'), IGNORE),
      ('foo/**bar', os.path.join('foo', '-bar-'), NO_MATCH),
      ('foo/bar**', os.path.join('foo', 'bar-'), IGNORE),
      ('foo/bar**', os.path.join('foo', '-bar-'), NO_MATCH),
  )
  def testPattern_InvalidConsecutiveStars(self, pattern, path, result):
    """Tests cases that gitignore spec calls 'invalid'."""
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('foo ', 'foo', IGNORE),
      ('foo ', 'foo ', NO_MATCH),
      ('foo\\ ', 'foo ', IGNORE),
      ('foo\\ ', 'foo', NO_MATCH),
      ('foo\t', 'foo', NO_MATCH),
      ('foo\t', 'foo\t', IGNORE),
      ('foo\\\t', 'foo\t', IGNORE),
      ('foo\\\t', 'foo', NO_MATCH),
      (' foo', ' foo', IGNORE),
      (' foo', 'foo', NO_MATCH),
      ('\\ foo', ' foo', IGNORE),
      ('\\ foo', 'foo', NO_MATCH),
      ('\tfoo', 'foo', NO_MATCH),
      ('\tfoo', '\tfoo', IGNORE),
      ('\\\tfoo', 'foo', NO_MATCH),
      ('\\\tfoo', '\tfoo', IGNORE),
  )
  def testPattern_TrailingSpaces(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('foo*baz', 'foobarbaz', IGNORE),
      ('foo*baz', 'foobaz', IGNORE),
      ('foo*baz', 'foo/baz', NO_MATCH),
      ('foo/*baz', 'foo/baz', IGNORE),
      ('foo/*baz', 'foo/bar/baz', NO_MATCH),
      ('foo?baz', 'foo-baz', IGNORE),
      ('foo?baz', 'foo--baz', NO_MATCH),
      ('foo-[ab]', 'foo-a', IGNORE),
      ('foo-[ab]', 'foo-b', IGNORE),
      ('foo-[ab]', 'foo-c', NO_MATCH),
      ('foo-[A-C]', 'foo-A', IGNORE),
      ('foo-[A-C]', 'foo-C', IGNORE),
      ('foo-[A-C]', 'foo-D', NO_MATCH),
      ('foo-[!ab]', 'foo-a', NO_MATCH),
      ('foo-[!ab]', 'foo-c', IGNORE),
      ('foo[*]', 'foo*', IGNORE),
      ('foo[*]', 'foo-', NO_MATCH),
      ('foo[?]', 'foo?', IGNORE),
      ('foo[?]', 'foo-', NO_MATCH),
      ('foo[[]', 'foo[', IGNORE),
      ('foo[[]', 'foo-', NO_MATCH),
      ('foo[', 'foo[', IGNORE),
      ('foo]', 'foo]', IGNORE),
  )
  def testPattern_ShellGlob(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('foo/bar', os.path.join('foo', 'bar'), IGNORE),
      ('bar/baz', os.path.join('foo', 'bar', 'baz'), IGNORE),
      ('bar/baz', os.path.join('foo', 'baz'), NO_MATCH),
      ('foo/ba[rz]', os.path.join('foo', 'bar'), IGNORE),
      ('foo/ba[rz]', os.path.join('foo', 'baz'), IGNORE),
      ('foo/ba[rz]', os.path.join('foo', 'bad'), NO_MATCH),
  )
  def testPattern_Subdirectory(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('foo/', 'foo/', True, IGNORE),
      ('foo/', 'foo/', False, NO_MATCH),
      ('foo/bar/', os.path.join('foo', 'bar'), True, IGNORE),
      ('foo/bar/', os.path.join('foo', 'bar'), False, NO_MATCH),
  )
  def testPattern_MustMatchDir(self, pattern, path, is_dir, result):
    pattern = gcloudignore.Pattern.FromString(pattern)
    self.assertEqual(pattern.Matches(path, is_dir=is_dir), result)

  @parameterized.parameters(
      ('/foo/bar', os.path.join('foo', 'bar'), IGNORE),
      ('/bar/baz', os.path.join('foo', 'bar', 'baz'), NO_MATCH),
      ('/bar/baz', os.path.join('foo', 'baz'), NO_MATCH),
      ('*', '', IGNORE),
      ('/*', '', NO_MATCH),
      ('/*', 'foo', IGNORE),
  )
  def testPattern_LeadingSlash(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  @parameterized.parameters(
      ('/#!foo', '#!foo', IGNORE),
      ('/!#foo', '!#foo', IGNORE),
      ('/!#foo', os.path.join('bar', '!#foo'), NO_MATCH),
      ('\\#/!foo', os.path.join('#', '!foo'), IGNORE),
      ('\\#!/foo', os.path.join('#!', 'foo'), IGNORE),
      ('!/#foo', '#foo', INCLUDE),
      ('!/#foo', os.path.join('bar', '#foo'), NO_MATCH),
      ('!#/foo', os.path.join('#', 'foo'), INCLUDE)
  )
  def testPattern_CombinedLeadingCharacters(self, pattern, path, result):
    self._RunTest(pattern, path, result)

  def testPattern_Windows(self):
    self.StartObjectPatch(os, 'path', ntpath)
    self._RunTest('foo/bar', 'foo\\bar', IGNORE)

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
    self.assertEquals(gcloudignore._Unescape(escaped), unescaped)

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
    self.assertEquals(gcloudignore._HandleSpaces(original), stripped)


class FileChooserTest(parameterized.TestCase, test_case.Base):

  def _TestFromStringAndText(self, text, path, result, is_dir=False):
    file_chooser = gcloudignore.FileChooser.FromString(text)
    self.assertEqual(file_chooser.IsIncluded(path, is_dir=is_dir), result)

    with tempfile.NamedTemporaryFile(delete=False) as f:
      self.addCleanup(os.unlink, f.name)
      f.write(text)
    file_chooser = gcloudignore.FileChooser.FromFile(f.name)
    self.assertEqual(file_chooser.IsIncluded(path, is_dir=is_dir), result)

  @parameterized.parameters(
      ('', 'foo', True),
      ('', os.path.join('foo', 'bar'), True),
      ('foo', 'foo', False),
      ('foo/foo', 'foo', True),
      ('foo/foo', os.path.join('foo', 'foo'), False),
      ('foo', os.path.join('foo', 'bar'), False),
      ('bar', os.path.join('foo', 'bar'), False),
      ('foo\nbar', 'foo', False),
      ('foo\nbar', 'bar', False),
  )

  def testIsIncluded(self, text, path, result):
    self._TestFromStringAndText(text, path, result)

  @parameterized.parameters(
      ('foo\r\nbar', 'foo', False),
      ('foo\r\nbar', 'bar', False),
  )
  def testIsIncluded_WindowsNewlines(self, text, path, result):
    self._TestFromStringAndText(text, path, result)

  @parameterized.parameters(
      ('foo/', 'foo', True, False),
      ('foo/', 'foo', False, True),
  )
  def testIsIncluded_Directory(self, text, path, is_dir, result):
    self._TestFromStringAndText(text, path, result, is_dir=is_dir)

  @parameterized.parameters(
      ('foo\n!foo', 'foo', True),
      ('foo\n!foo\nfoo', 'foo', False),
  )
  def testIsIncluded_LastMatchWins(self, text, path, result):
    self._TestFromStringAndText(text, path, result)

  @parameterized.parameters(
      ('#foo', '#foo', True),
      ('\\#foo', '#foo', False),
      ('foo ', 'foo', False),
      ('foo\n\\ \nbar', ' ', False),
      ('foo\n\nbar\n \t\nbaz', 'foo', False),
      ('foo\n\nbar\n \t\nbaz', 'bar', False),
      ('foo\n\nbar\n \t\nbaz', 'baz', False),
      ('foo\n\nbar\n \t\nbaz', 'qux', True),
  )
  def testIsIncluded_BlankLinesCommentsWhitespace(self, text, path, result):
    self._TestFromStringAndText(text, path, result)

  @parameterized.parameters(
      ('foo/\n!foo/bar', os.path.join('foo', 'bar'), False),
      # This example only includes foo/bar and its contents
      ('/*\n!/foo\n/foo/*\n!foo/bar', 'foo', True),
      ('/*\n!/foo\n/foo/*\n!foo/bar', 'qux', False),
      ('/*\n!/foo\n/foo/*\n!foo/bar', os.path.join('foo', 'bar'), True),
      ('/*\n!/foo\n/foo/*\n!foo/bar', os.path.join('foo', 'bar', 'baz'), True),
      ('/*\n!/foo\n/foo/*\n!foo/bar', os.path.join('foo', 'baz'), False),
      # Because of the '*', the root directory is excluded and nothing can get
      # re-included.
      ('*\n!/foo\n/foo/*\n!foo/bar', os.path.join('foo', 'bar'), False),
      ('*\n!/foo\n/foo/*\n!foo/bar', os.path.join('foo', 'bar', 'baz'), False),
  )
  def testIsIncluded_ParentDirectoryExcluded(self, text, path, result):
    self._TestFromStringAndText(text, path, result)


class FileChooserRecursiveTest(parameterized.TestCase,
                               sdk_test_base.WithLogCapture):

  @parameterized.parameters(
      ('ignore1', 0, 'foo', True),
      ('ignore1', 0, 'bar', True),
      ('ignore1', 1, 'foo', False),
      ('ignore1', 1, 'bar', True),
      ('ignore1', 2, 'foo', True),
      ('ignore1', 2, 'bar', False),
      ('ignore1', 3, 'foo', True),
      ('ignore1', 3, 'bar', False),
      ('ignore2', 0, 'foo', False),
      ('ignore2', 0, 'bar', True),
      ('ignore2', 1, 'foo', True),
      ('ignore2', 1, 'bar', False),
      ('ignore2', 2, 'foo', True),
      ('ignore2', 2, 'bar', False),
  )
  def testFromFile_Recursive(self, ignore_file, recurse, path, result):
    with _TempDir() as temp_path:
      self.Touch(temp_path, 'ignore1', contents='#!include:ignore2')
      self.Touch(temp_path, 'ignore2', contents='foo\n#!include:ignore3')
      self.Touch(temp_path, 'ignore3', contents='bar\n!foo')

      ignore_file_path = os.path.join(temp_path, ignore_file)
      file_chooser = gcloudignore.FileChooser.FromFile(ignore_file_path,
                                                       recurse=recurse)
    self.assertEquals(file_chooser.IsIncluded(path), result)

  def testFromString_Recursive(self):
    with _TempDir() as temp_path:
      self.Touch(temp_path, 'gcloudignore', contents='foo')
      file_chooser = gcloudignore.FileChooser.FromString(
          '#!include:gcloudignore', recurse=1, dirname=temp_path)
    self.assertFalse(file_chooser.IsIncluded('foo'))
    self.assertTrue(file_chooser.IsIncluded('bar'))

  def testFromFile_BadFile(self):
    with _TempDir() as temp_path:
      with self.assertRaises(gcloudignore.BadFileError):
        gcloudignore.FileChooser.FromFile('not-exists')

      # And again, recursive:
      ignore_file = self.Touch(temp_path, 'ignore',
                               contents='#!include:not-exists')
      with self.assertRaises(gcloudignore.BadIncludedFileError):
        gcloudignore.FileChooser.FromFile(ignore_file)

  def testFromFile_DifferentDirectoryNotAllowed(self):
    with _TempDir() as temp_path:
      ignore_files = [
          self.Touch(os.path.join('subdir', temp_path), 'ignore',
                     contents='#!include:subsubdir/ignore', makedirs=True),
          self.Touch(os.path.join(temp_path, 'subdir', 'subsubdir'), 'ignore',
                     contents='#!include:../ignore', makedirs=True)
      ]
      for ignore_file in ignore_files:
        with self.assertRaises(gcloudignore.BadIncludedFileError):
          gcloudignore.FileChooser.FromFile(ignore_file)


class FileChooserGetIncludedFilesTest(test_case.Base):

  def testGetIncludedFiles(self):
    files = {
        'gcloudignore': 'foo\nbar/',
        'foo': '',
        'bar': '',
        os.path.join('baz', 'bar', 'qux'): '',
        os.path.join('quux', 'quuz'): ''
    }
    expected_files = set(['gcloudignore', 'bar', 'quux',
                          os.path.join('quux', 'quuz'), 'baz'])
    with _TempDir() as temp_path:
      for file_, contents in files.items():
        self.Touch(os.path.join(temp_path, os.path.dirname(file_)),
                   os.path.basename(file_), contents=contents, makedirs=True)
      file_chooser = gcloudignore.FileChooser.FromFile(
          os.path.join(temp_path, 'gcloudignore'))
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        expected_files)

  def testGetIncludedFiles_SkipDirs(self):
    files = {
        'gcloudignore': 'gcloudignore',
        os.path.join('baz', 'bar', 'qux'): '',
    }
    expected_files = set([os.path.join('baz', 'bar', 'qux')])
    with _TempDir() as temp_path:
      for file_, contents in files.items():
        self.Touch(os.path.join(temp_path, os.path.dirname(file_)),
                   os.path.basename(file_), contents=contents, makedirs=True)
      file_chooser = gcloudignore.FileChooser.FromFile(
          os.path.join(temp_path, 'gcloudignore'))
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path,
                                                          include_dirs=False)),
                        expected_files)

  def testGetIncludedFiles_SkipsUnincludedDirectories(self):
    old_join = os.path.join
    def _FakeJoin(*args):
      if 'should-not-be-checked' in args:
        self.fail('Should skip this file because its parent is not included.')
      return old_join(*args)
    with _TempDir() as temp_path:
      self.Touch(os.path.join(temp_path, 'foo'), 'should-not-be-checked',
                 makedirs=True)
      file_chooser = gcloudignore.FileChooser.FromString('foo/')
      with mock.patch.object(os.path, 'join', side_effect=_FakeJoin):
        self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                          set([]))

  def testGetIncludedFiles_DoesntSkipReincludedDirectories(self):
    files = {
        'gcloudignore': '/*\n!/foo\n/foo/*\n!foo/bar',
        'qux': '',
        os.path.join('foo', 'bar', 'baz'): '',
        os.path.join('foo', 'baz'): '',
    }
    expected_files = set([
        'foo', os.path.join('foo', 'bar'), os.path.join('foo', 'bar', 'baz')
    ])
    with _TempDir() as temp_path:
      for file_, contents in files.items():
        self.Touch(os.path.join(temp_path, os.path.dirname(file_)),
                   os.path.basename(file_), contents=contents, makedirs=True)
      file_chooser = gcloudignore.FileChooser.FromFile(
          os.path.join(temp_path, 'gcloudignore'))
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        expected_files)

  @test_case.Filters.DoNotRunOnWindows(
      'Symlinks don\'t work on Windows without binary extensions to Python.')
  def testGetIncludedFiles_SymlinksAreNotDirectories(self):
    with _TempDir() as temp_path:
      self.Touch(os.path.join(temp_path, 'foo'), 'bar', makedirs=True)
      os.symlink(os.path.join(temp_path, 'foo'), os.path.join(temp_path, 'baz'))
      file_chooser = gcloudignore.FileChooser.FromString('baz/')
      self.assertIn('baz', set(file_chooser.GetIncludedFiles(temp_path)))


class GetFileChooserForDirTests(sdk_test_base.WithLogCapture):

  def testGetFileChooserForDir_NoIgnoreFiles(self):
    with _TempDir() as temp_path:
      self.Touch(temp_path, 'foo')
      self.Touch(temp_path, 'bar')
      file_chooser = gcloudignore.GetFileChooserForDir(
          temp_path, default_ignore_file='foo')
      self.assertTrue(file_chooser)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['foo', 'bar']))

  def testGetFileChooserForDir_GcloudignoreFile(self):
    with _TempDir() as temp_path:
      self.Touch(temp_path, '.gcloudignore', contents='foo\n')
      self.Touch(temp_path, 'foo')
      self.Touch(temp_path, 'bar')
      file_chooser = gcloudignore.GetFileChooserForDir(temp_path)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['.gcloudignore', 'bar']))

  def testGetFileChooserForDir_Gitfiles(self):
    with _TempDir() as temp_path:
      self.Touch(os.path.join(temp_path, '.git'), 'git-metadata', makedirs=True)
      self.Touch(temp_path, 'foo')
      file_chooser = gcloudignore.GetFileChooserForDir(temp_path)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['foo']))
      self.assertTrue(os.path.exists(os.path.join(temp_path, '.gcloudignore')))

  def testGetFileChooserForDir_Gitignore(self):
    with _TempDir() as temp_path:
      self.Touch(os.path.join(temp_path, '.git'), 'git-metadata', makedirs=True)
      self.Touch(temp_path, 'foo')
      self.Touch(temp_path, 'bar')
      self.Touch(temp_path, '.gitignore', contents='foo')
      file_chooser = gcloudignore.GetFileChooserForDir(temp_path)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['bar']))
      self.assertTrue(os.path.exists(os.path.join(temp_path, '.gcloudignore')))

  def testGetFileChooserForDir_GitignoreDoNotWrite(self):
    with _TempDir() as temp_path:
      self.Touch(os.path.join(temp_path, '.git'), 'git-metadata', makedirs=True)
      self.Touch(temp_path, 'foo')
      self.Touch(temp_path, 'bar')
      self.Touch(temp_path, '.gitignore', contents='foo')
      file_chooser = gcloudignore.GetFileChooserForDir(temp_path,
                                                       write_on_disk=False)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['bar']))
      self.assertFalse(os.path.exists(os.path.join(temp_path, '.gcloudignore')))

  @test_case.Filters.DoNotRunOnWindows(
      'It\'s nontrivial to make an unwritable directory on Windows.')
  def testGetFileChooserForDir_GitignoreNotWritable(self):
    with _TempDir() as temp_path:
      self.Touch(os.path.join(temp_path, '.git'), 'git-metadata', makedirs=True)
      self.Touch(temp_path, 'foo')
      self.Touch(temp_path, 'bar')
      self.Touch(temp_path, '.gitignore', contents='foo')
      try:
        os.chmod(temp_path, 0555)
        file_chooser = gcloudignore.GetFileChooserForDir(temp_path)
      finally:
        os.chmod(temp_path, 0777)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['bar']))
      self.assertFalse(os.path.exists(os.path.join(temp_path, '.gcloudignore')))

  def testGetFileChooserForDir_GcloudignoreTrumpsGitignore(self):
    with _TempDir() as temp_path:
      self.Touch(temp_path, '.gcloudignore', contents='foo\n')
      self.Touch(temp_path, '.gitignore', contents='bar\n')
      self.Touch(temp_path, 'foo')
      self.Touch(temp_path, 'bar')
      file_chooser = gcloudignore.GetFileChooserForDir(temp_path)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['.gcloudignore', '.gitignore', 'bar']))

  def testGetFileChooserForDir_DisableGcloudignore(self):
    properties.VALUES.gcloudignore.enabled.Set(False)
    with _TempDir() as temp_path:
      self.Touch(temp_path, '.gcloudignore', contents='foo\n')
      self.Touch(temp_path, 'foo')
      self.Touch(temp_path, 'bar')
      file_chooser = gcloudignore.GetFileChooserForDir(temp_path)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['.gcloudignore', 'bar', 'foo']))

  def testGetFileChooserForDir_DontIncludeGitignore(self):
    with _TempDir() as temp_path:
      self.Touch(temp_path, 'foo')
      self.Touch(temp_path, 'bar')
      self.Touch(temp_path, '.gitignore', contents='bar\n')
      file_chooser = gcloudignore.GetFileChooserForDir(
          temp_path,
          default_ignore_file='\n'.join(['.gitignore', '.gcloudignore']),
          include_gitignore=False)
      self.assertEquals(set(file_chooser.GetIncludedFiles(temp_path)),
                        set(['foo', 'bar']))


if __name__ == '__main__':
  test_case.main()
