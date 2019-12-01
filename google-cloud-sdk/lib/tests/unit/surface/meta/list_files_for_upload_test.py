# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for gcloud meta list-files-for-upload."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import itertools
import os

from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import parameterized_line_no
from tests.lib import test_case
from six.moves import map


T = parameterized_line_no.LineNo


class ListFilesForUploadSanityTest(cli_test_base.CliTestBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def testListFilesForUpload_EmptyDirectory(self):
    results = self.Run('meta list-files-for-upload ' + self.temp_path)

    self.assertEqual(results, [])

  def testListFilesForUpload(self):
    self.Touch(self.temp_path, '.gcloudignore', contents='foo')
    self.Touch(self.temp_path, 'foo')
    self.Touch(os.path.join(self.temp_path, 'bar'), 'baz', makedirs=True)

    results = self.Run('meta list-files-for-upload ' + self.temp_path)

    self.assertEqual(results,
                     ['.gcloudignore', os.path.join('bar', 'baz')])


def _CombineFormats(fmts, vals):
  """Returns every combination of the given format string and values.

  For instance:

      >>> _CombineFormats(['{}', '{}-bar'], 'ab')
      ['a', 'a-bar', 'b', 'b-bar'

  Args:
    fmts: list of str, the format strings to use for each value
    vals: list of str, values to format in

  Returns:
    list of str, the formatted strings
  """

  return [fmt.format(val) for val in vals for fmt in fmts]


def _AddCrunchBangPrefixes(x):
  """Returns the given string with combinations of ! and # at the beginning."""
  prefixes = ['', '{}', r'\c', r'\\c']
  for bang in _CombineFormats(prefixes, '!'):
    for crunch in _CombineFormats(prefixes, '#'):
      yield bang + crunch + x
      yield crunch + bang + x


_CONSECUTIVE_STAR_FMTS = ['{0}**{0}', '{0}*{0}', '{0}-*{0}', '{0}*-0{0}',
                          '{0}--{0}',
                          os.path.join('dir', '{}'), os.path.join('dir', '-{}'),
                          os.path.join('dir', '-{}-')]
_SHELL_GLOB_FMTS = ['{0}{0}', '{0}4{0}', '{0}44{0}', '{0}[{0}', '{0}]{0}',
                    '{0}!{0}', '{0}?{0}', '{0}*{0}']


def _MakeShellGlobCases(c):
  """Returns the input with shell glob-related characters in the middle."""
  base = _CombineFormats(_SHELL_GLOB_FMTS, c)
  return base + [os.path.join('dir', name) for name in base]


@test_case.Filters.RunOnlyIfExecutablePresent('git')
class ListFilesForUploadTest(cli_test_base.CliTestBase, parameterized.TestCase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _GitInit(self):
    def _SwallowOutput(_):
      pass
    execution_utils.Exec(['git', 'init'], no_exit=True, out_func=_SwallowOutput)

  def _GitAddDryRun(self):
    output = io.StringIO()
    execution_utils.Exec(['git', 'add', '--dry-run', '.'], no_exit=True,
                         out_func=output.write)
    text = output.getvalue()
    if not text:
      return []
    text = text[len('add \''):-len('\'\n')]
    return text.split('\'\nadd \'')

  def _TouchFiles(self, paths):
    for path in paths:
      if (platforms.OperatingSystem.IsWindows() and
          ('\\' in path or '*' in path or '\t' in path or '?' in path)):
        continue  # Windows paths can't have many characters
      dir_ = self.temp_path
      if os.path.dirname(path):
        dir_ = os.path.join(dir_, os.path.dirname(path))
      self.Touch(dir_, os.path.basename(path), makedirs=True)

  def _RunListFilesForUpload(self, path):
    return self.Run('meta list-files-for-upload ' + path)

  def _RunTest(self, paths, gitignore=None):
    self._TouchFiles(paths)
    if gitignore is not None:
      self.Touch(self.temp_path, '.gitignore', contents=gitignore)
    with files.ChDir(self.temp_path):
      self._GitInit()
      git_uploaded_files = self._GitAddDryRun()
    uploaded_files = self._RunListFilesForUpload(self.temp_path)
    self.assertEqual(set(uploaded_files), set(git_uploaded_files))

  @parameterized.named_parameters(
      T('NoGitFiles', ['a', 'b'], None),
      T('NoMatches', ['a', 'b'], '.gitignore'),
      T('Basic1', ['a', 'b'], '.gitignore\na'),
      T('Basic2', ['a', 'ab'], '.gitignore\na'),
      T('BlankLine', ['a', 'b', 'c'], '.gitignore\na\n\nb'),
      T('SubdirMatch', [os.path.join('a', 'b')], '.gitignore\nb'),
      T('SubdirNoMatch', [os.path.join('a', 'b')], '.gitignore\nc'),
      T('Negated', ['a'], '.gitignore\na\n!a'),
      T('NegatedByWildcard', ['foo'], '.gitignore\nfoo\n!f*'),
      T('EscapedBang', _CombineFormats(['!{}', '{}', '{}!', '!{}!'], 'abcde'),
        '.gitignore\n\\!a\nb!\nc\\!\nd\n\\!e!\n\\!d\\!'),
      T('EscapedCrunch', _CombineFormats(['#{}', '{}', '{}#', '#{}#'], 'abcd'),
        '.gitignore\n\\#a\nb#\nc\\#\n\\#d#'),
      T('CombinedBangAndCrunch',
        itertools.chain.from_iterable(
            list(map(_AddCrunchBangPrefixes, 'abcd'))),
        '.gitignore\n!#a\n!\\#b\n\\!#c\n\\!\\#d'),
      T('Comment', ['foo', '#foo'], '.gitignore\n#foo'),
      T('LeadingConsecutiveStars',
        ['baz', os.path.join('foo', 'baz'), os.path.join('foo', 'bar', 'baz')],
        '.gitignore\n**/baz'),
      T('EscapedConsecutiveStars',
        _CombineFormats(_CONSECUTIVE_STAR_FMTS, 'abc'),
        '.gitignore\na[*]*a\nb[*][*]b\nc*[*]c'),
      T('MustMatchDir',
        [os.path.join('a', 'b'), 'b', os.path.join('c', 'd'), 'd'],
        '.gitignore\na/\nc/d/'),
      T('LeadingSlash',
        [os.path.join('a', 'b'), os.path.join('a', 'c'), 'b', 'c'],
        '.gitignore\n/a/b\n/a/c\n/b\n/c'),
      T('NeedlesslyEscapedCharacters',
        ['a', 'b', 'c d'],
        '.gitignore\n\\a\nb\nc\\ d'),
      T('InvalidConsecutiveStars',
        _CombineFormats(_CONSECUTIVE_STAR_FMTS, 'abcdefgh'),
        '.gitignore\na**\n**b\nc**d\ne/**f\ng/h**'),
      T('TrailingBackslash',
        _CombineFormats(['{}', '{}\\', r'{}\\'], 'ab'),
        '.gitignore\na\\\nb\\\\'),
      T('ShellGlob', _MakeShellGlobCases('abcdefghijklmno'),
        '.gitignore\n'
        'a*a\ndir/*b\nc?c\nd[4]d\ne[!4]e\nf]f\ng[[]g\nh[]]h\n'
        'i[*]i\nj[?]j\nk[-]k\nl[!]l\nm!m\nn[0-9]n\no[!0-9]o'),
      T('TrailingConsecutiveStars',
        ['baz', os.path.join('foo', 'baz'), os.path.join('foo', 'bar', 'baz'),
         os.path.join('bar', 'baz'), os.path.join('qux', 'bar', 'baz')],
        '.gitignore\nbar/**'),
      T('MiddleConsecutiveStars',
        [os.path.join('top-level', 'foo', 'baz', 'qux'),
         os.path.join('foo', 'bar', 'baz', 'qux')],
        '.gitignore\nfoo/**/qux'),
      T('BackslashBackslashSlash',
        [os.path.join('foo', 'bar'),
         os.path.join('foo\\', 'bar')],
        '.gitignore\nfoo\\\\/bar'),
      T('BackslashSlash',
        [os.path.join('foo', 'bar'),
         os.path.join('foo\\', 'bar')],
        '.gitignore\nfoo\\/bar'),
      T('TrailingBackslashBackslash',
        ['foo',
         'foo\\'],
        '.gitignore\nfoo\\\\'),
  )
  def testSameResultsAsGit(self, line, paths, gitignore):
    self._RunTest(paths, gitignore=gitignore)

  # The version of Git used in our .deb and .rpm packaging tests don't conform
  # to https://git-scm.com/docs/gitignore.
  #
  # In particular, with a file called '\t\t' and a line '\t\t ' in .gitignore,
  # they *do* upload the file. They should not, because trailing *spaces* should
  # be stripped, but other trailing whitespaces should not.
  @test_case.Filters.DoNotRunInDebPackage('DEB git doesn\'t follow spec.')
  @test_case.Filters.DoNotRunInRpmPackage('RPM git doesn\'t follow spec.')
  @parameterized.named_parameters(
      T('TrailingSpaces',
        _CombineFormats(
            ['{}', '{} ', '{}\t', r'{}\t', ' {}', '\t{}'], 'abcdef'),
        '.gitignore\na \nb\\ \nc\t\nc\\\t\\ e\nf'),
      T('AllTabs', ['\t', '\t\t'], '.gitignore\n\t\n\t\t '),
  )
  def testDifferentGitVersions(self, line, paths, gitignore):
    self._RunTest(paths, gitignore=gitignore)


if __name__ == '__main__':
  test_case.main()
