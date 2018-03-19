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
"""Test for the git wrapper."""

import errno
import itertools
import os
import re
import subprocess
import textwrap

from googlecloudsdk.api_lib.source import git
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.source import base
import mock


def _make_fake_paths_class():
  real_path = config.Paths()

  class _FakePaths(object):

    @property
    def sdk_bin_path(self):
      return None

    @property
    def named_config_activator_path(self):
      assert False
      return real_path.named_config_activator_path

  return _FakePaths


def _make_file(target_file, contents):
  dirname = os.path.dirname(target_file)
  if not os.path.exists(dirname):
    os.makedirs(dirname)
  with open(target_file, 'w') as f:
    f.write(contents)


def _make_git_handler(target_dir, ignore_files):
  # Create all the files before the handler
  for filename, _, contents in ignore_files:
    filename = os.path.join(target_dir, filename)
    _make_file(filename, contents)

  handler = git.GitIgnoreHandler()
  for filename, process_file, _ in ignore_files:
    filename = os.path.join(target_dir, filename)
    dirname = os.path.dirname(filename)
    if process_file:
      handler.ProcessGitIgnore(dirname)
  return handler


class GitIgnoreTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self._fake_home = self.CreateTempDir()
    self.StartObjectPatch(
        os.path,
        'expanduser',
        side_effect=lambda n: n.replace('~', self._fake_home))

  def testSimpleIgnore(self):
    # "**/" should be equivalent to no prefix. Verify they both behave the
    # same.
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, '**/exclude_recursively\n'
         'always_ignore_me\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'exclude_recursively')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'a/exclude_recursively')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'b/exclude_recursively')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'b/c/exclude_recursively')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'b/c/d/exclude_recursively')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'b/exclude_recursively')))
    self.assertFalse(
        handler.ShouldIgnoreFile(os.path.join(self.temp_path, 'not_excluded')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'always_ignore_me')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'subdir/always_ignore_me')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'a/b/c/d/e/foooo/always_ignore_me')))

  def testIgnoreCharacterRange(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, 'ignore_only_if_numbered_[0-9]\n'),
    ])
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_only_if_numbered_x')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_only_if_numbered_fooo')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_only_if_numbered_1fooo')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_only_if_numbered_1')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_only_if_numbered_5')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_only_if_numbered_9')))

  def testIgnoreNotCharacterRange(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, 'ignore_if_nonnumber_[^0-9]*\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_if_nonnumber_x')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_if_nonnumber_xfooo')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_if_nonnumber_9')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_if_nonnumber_9foo')))

  def testIgnoreUnderSubdir(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, 'a/**/exclude_under_a\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'a/exclude_under_a')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'a/b/exclude_under_a')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'a/b/c/exclude_under_a')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'a/b/c/d/exclude_under_a')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'this_is_not_in_a/a/b/exclude_under_a')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'exclude_under_a')))

  def testIgnoreDir(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, 'ignore_dir/**\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(os.path.join(self.temp_path, 'ignore_dir/')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_dir/file1')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_dir/file2')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_dir/x/file3')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'ignore_dir/dir1/dir2/dir3/t/u/file1')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'regular_dir/included_file')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'regular_dir/ignore_dir/not_really_ignored')))

  def testIgnoreWithSubOverride(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, '**/exclude_recursively\n'
         'ignore_prefix*\n'),
        ('override/.gitignore', True, '!ignore_prefix_but_not_in_override\n'
         'ignore_only_in_override\n'),
        ('subdir/override/.gitignore', True,
         'ignore_in_sub_override_not_override\n'
         '!ignore_prefix_but_not_sub_override\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_prefix_but_not_in_override')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_prefix_but_not_sub_override')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'override/ignore_prefix_but_not_sub_override')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'subdir/override/ignore_in_sub_override_not_override')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_only_in_override')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'override/ignore_prefix_but_not_in_override')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'subdir/override/ignore_prefix_but_not_sub_override')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'override/ignore_prefix_but_not_in_override')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'override/ignore_in_sub_override_not_override')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'subdir/override/ignore_prefix_but_not_sub_override')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'ignore_dir/a/b/c/never_ignore_me_even_if_ignoring_my_parents'))
    )

  def testIgnoreWithOverride(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, 'kinda_ignore/**\n'
         '!kinda_ignore/do_not_ignore[0-9]\n'
         '\n'
         '!kinda_ignore/include_me/**\n'
         '# Comment in the middle\n'
         '!kinda_ignore/not_me?\n'
         '!kinda_ignore/keep_wild*s\n'
         '!**/never_ignore_me_even_if_ignoring_my_parents\n'
         '!kinda_ignore/pretend_not_to_ignore/**\n'
         'kinda_ignore/pretend_not_to_ignore/ignore_anyway*\n'
         'ignore_trailing_space_in_pattern_not_file          \n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/ignore_me1')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/ignore_me2')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/ignore_me3456')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/ignore_me1')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/ignore_me2')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'kinda_ignore/do_not_ignore_but_really_do1')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/not_me_ok_really_me')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'kinda_ignore/keep_wild_things_but_not_me')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'kinda_ignore/pretend_not_to_ignore/ignore_anyway1')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'kinda_ignore/pretend_not_to_ignore/ignore_anyway_for_fun')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/do_not_ignore1')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/do_not_ignore2')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/do_not_ignore3')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/not_me1')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/not_mea')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/not_meb')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/not_me_')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/keep_wild_elephants')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/keep_wild_tardises')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/keep_wild_parties')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/include_me/file1')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/include_me/file2')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/include_me/file3')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'kinda_ignore/include_me/file4')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'kinda_ignore/pretend_not_to_ignore/really_do_not_ignore')))

  def testIgnoreWildcardDirectoryName(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, '**/ignore_*_everywhere/**\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'regular_dir/ignore_/ignore_dir_everywhere/really_ignored')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'regular_dir/ignore_foobar_everywhere/file100')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'regular_dir/ignore_foobar_everywhere/a/file100')))

  def testIgnoreComments(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, '\n'
         '\n'
         '# Comment line\n'
         '\n'
         '# not_excluded\n'
         '\n'
         'simple_ignore1\n'
         '# Comment in the middle\n'
         'simple_ignore2\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'simple_ignore1')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'simple_ignore2')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, '# Comment line')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, '# not_excluded')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, '# Comment in the middle')))
    self.assertFalse(
        handler.ShouldIgnoreFile(os.path.join(self.temp_path, 'not_ignored')))

  def testIgnoreOneDirectoryWildcard(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, '*/ignore_one_level_deep\n'
         'foo/*/ignore_one_level_under_foo\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'a/ignore_one_level_deep')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'b/ignore_one_level_deep')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'longdirname/ignore_one_level_deep')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'foo/a/ignore_one_level_under_foo')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'foo/b/ignore_one_level_under_foo')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'foo/longdirname/ignore_one_level_under_foo')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'level1/a/ignore_one_level_deep')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'lev1/lev2/b/ignore_one_level_deep')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'lev1/longdirname/ignore_one_level_deep')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'foo/a/lev2/ignore_one_level_under_foo')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'b/foo/ignore_one_level_under_foo')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'lev1/longdirname/ignore_one_level_under_foo')))

  def testIgnoreInOnePlace(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True, 'b/ignore_in_b_only\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'b/ignore_in_b_only')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_in_b_only')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'not_b/ignore_in_b_only')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'b/not_b/ignore_in_b_only')))

  def testIgnoreLeadingSlash(self):
    handler = _make_git_handler(self.temp_path,
                                [('.gitignore', True, '/log/*')])
    self.assertTrue(
        handler.ShouldIgnoreFile(os.path.join(self.temp_path, 'log/test.log')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'tmp/log/test.log')))

  def testIgnoreWhiteSpace(self):
    handler = _make_git_handler(self.temp_path, [
        ('.gitignore', True,
         'ignore_trailing_space_in_pattern_not_file          \n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'ignore_trailing_space_in_pattern_not_file')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'ignore_trailing_space_in_pattern_not_file          ')))

  def testExcludeFile(self):
    handler = _make_git_handler(self.temp_path, [
        ('.git/info/exclude', False, 'ignore_because_of_exclude_file\n'
         'ignore_because_of_exclude_file_except_in_override\n'),
        ('.gitignore', True,
         '# Dummy file to ensure processing this directory\n'),
        ('override/.gitignore', True, '!ignore_prefix_but_not_in_override\n'
         '!ignore_because_of_exclude_file_except_in_override\n'
         '!ignore_because_of_config_except_in_override\n'
         'ignore_only_in_override\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_because_of_exclude_file')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'ignore_because_of_exclude_file_except_in_override')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'a/b/c/ignore_because_of_exclude_file')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path,
                         'override/ignore_because_of_exclude_file')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'override/ignore_because_of_exclude_file_except_in_override')))

  def testConfigFile(self):
    _make_file(
        os.path.join(self._fake_home, '.config/git/ignore'),
        'ignore_because_of_config\n'
        'ignore_because_of_config_except_in_override\n')
    handler = _make_git_handler(self.temp_path, [
        ('override/.gitignore', True,
         '!ignore_because_of_config_except_in_override\n'),
    ])
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'override/ignore_because_of_config')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'override/ignore_because_of_config_except_in_override')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'ignore_because_of_config')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'a/b/c/ignore_because_of_config')))
    self.assertTrue(
        handler.ShouldIgnoreFile(
            os.path.join(self.temp_path, 'override/ignore_because_of_config')))
    self.assertFalse(
        handler.ShouldIgnoreFile(
            os.path.join(
                self.temp_path,
                'override/ignore_because_of_config_except_in_override')))

  def testGetFiles(self):
    # Normalize names because this test may run on Windows, which uses \
    handler = _make_git_handler(
        self.temp_path,
        [('.gitignore', True, 'ignore_file\n'
          'ignore_dir\n'
          'ignore_everywhere_*\n'
          'b/ignore_in_b\n'),
         ('has_ignore_override/.gitignore', True, '!ignore_everywhere_but*\n'
          'ignore_only_in_override\n')])
    included_files = [
        os.path.normpath(os.path.join(self.temp_path, f))
        for f in [
            'a/b/file1.java',
            'a/b/long_directory_name/file2.py',
            'a/b/c/long_file_name.py',
            'subdir/file2.py',
            'file3',
            'not_a_java_file.class',
            'ignore_only_in_override',
            'b/not_ignored',
            'has_ignore_override/ignore_everywhere_but_override',
        ]
    ]
    ignored_files = [
        os.path.normpath(os.path.join(self.temp_path, f))
        for f in [
            'a/b/ignore_file',
            'a/b/ignore_everywhere_but_override',
            'ignore_everywhere_but_override',
            'b/ignore_file',
            'b/ignore_in_b',
            'has_ignore_override/ignore_everywhere_but_override',
        ]
    ]
    for f in itertools.chain(included_files, ignored_files):
      _make_file(f, 'contents of ' + f)

    included_files.extend([
        os.path.normpath(os.path.join(self.temp_path, f))
        for f in ['.gitignore', 'has_ignore_override/.gitignore']
    ])
    included_files.sort()

    filtered_files = list(handler.GetFiles(self.temp_path))
    filtered_files.sort()
    self.assertEqual(filtered_files, included_files)


class GitTest(base.SourceTest):

  def SetUp(self):
    self.git_version_mock = self.StartObjectPatch(subprocess, 'check_output')
    self.git_version_mock.return_value = 'git version 1.7.9'
    self.clone_command_mock = self.StartObjectPatch(subprocess, 'check_call')

  @test_case.Filters.DoNotRunOnWindows
  def testCloneMacOrLinuxGitSupportsHelperButNotEmptyHelper(self):
    properties.VALUES.core.account.Set('fake-git-account')
    self.git_version_mock.return_value = 'git version 2.0.1'

    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path')
    repo_path = os.path.abspath('repo-path')
    self.assertEquals(repo_path, path)
    self.assertEquals([
        mock.call([
            'git', 'clone',
            'https://source.developers.google.com/p/fake-project/r/fake-repo',
            repo_path, '--config', 'credential.helper=', '--config',
            'credential.helper='
            '!gcloud auth git-helper --account=fake-git-account '
            '--ignore-unknown $@'
        ])
    ], self.clone_command_mock.call_args_list)

  @test_case.Filters.RunOnlyOnWindows
  def testCloneRepoWindowsGitSupportsCredHelperButNotEmptyHelper(self):
    self.git_version_mock.return_value = 'git version 2.10.0'

    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path')
    repo_path = os.path.abspath('repo-path')
    self.assertEquals(repo_path, path)
    self.AssertErrContains('gcloud auth print-access-token')
    self.assertEquals([
        mock.call([
            'git', 'clone',
            'https://source.developers.google.com/p/fake-project/r/fake-repo',
            repo_path
        ])
    ], self.clone_command_mock.call_args_list)

  def testCloneRepoGitSupportsEmptyHelper(self):
    properties.VALUES.core.account.Set('fake-git-account')
    self.git_version_mock.return_value = 'git version 2.15.0'

    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path')
    repo_path = os.path.abspath('repo-path')
    self.assertEquals(repo_path, path)
    self.assertEquals([
        mock.call([
            'git', 'clone',
            'https://source.developers.google.com/p/fake-project/r/fake-repo',
            repo_path, '--config', 'credential.helper=', '--config',
            'credential.helper='
            '!gcloud auth git-helper --account=fake-git-account '
            '--ignore-unknown $@'
        ])
    ], self.clone_command_mock.call_args_list)

  def testCloneRepo_DryRun(self):
    properties.VALUES.core.account.Set('fake-git-account')
    self.git_version_mock.return_value = 'git version 2.15.0'

    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path', dry_run=True)
    repo_path = os.path.abspath('repo-path')
    self.assertEquals(repo_path, path)
    self.AssertOutputContains(
        'git clone '
        'https://source.developers.google.com/p/fake-project/r/fake-repo {0} '
        '--config credential.helper= '
        '--config credential.helper='
        '!gcloud auth git-helper --account=fake-git-account '
        '--ignore-unknown $@'.format(repo_path))

  def testCloneRepoOldGitVersion_NoCredentialHelper(self):
    self.git_version_mock.return_value = 'git version 1.7.9'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path', dry_run=True)
    repo_path = os.path.abspath('repo-path')
    self.assertEquals(repo_path, path)
    self.AssertOutputEquals(
        'git clone '
        'https://source.developers.google.com/p/fake-project/r/fake-repo {0}\n'
        .format(repo_path))

  def testCloneRepoOldGitVersion(self):
    self.git_version_mock.return_value = 'git version 1.7.9'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')

    expected_min = '2.0.1'
    if (platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS
       ):
      expected_min = '2.15.0'
    project_repo = git.Git('fake-project', 'fake-repo')
    repo_path = os.path.abspath('repo-path')
    project_repo.Clone(destination_path=repo_path, dry_run=True)
    self.AssertErrContains(
        textwrap.dedent("""\
    WARNING: You are using a Google-hosted repository with a
    git version {current} which is older than {min_version}. If you upgrade
    to {min_version} or later, gcloud can handle authentication to
    this repository. Otherwise, to authenticate, use your Google
    account and the password found by running the following command.
     $ gcloud auth print-access-token
               """.format(current='1.7.9', min_version=expected_min)))
    self.AssertOutputEquals(
        'git clone '
        'https://source.developers.google.com/p/fake-project/r/fake-repo {0}\n'
        .format(repo_path))

  def testCloneRepoDirExistsIsEmpty(self):
    properties.VALUES.core.account.Set('fake-git-account')
    self.git_version_mock.return_value = 'git version 2.15.0'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')

    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path')
    path_exists_mock = self.StartObjectPatch(os.path, 'exists')
    path_exists_mock.return_value = True
    repo_path = os.path.abspath('repo-path')
    self.assertEquals(repo_path, path)
    self.assertEquals([
        mock.call([
            'git', 'clone',
            'https://source.developers.google.com/p/fake-project/r/fake-repo',
            repo_path, '--config', 'credential.helper=', '--config',
            'credential.helper='
            '!gcloud auth git-helper --account=fake-git-account '
            '--ignore-unknown $@'
        ])
    ], self.clone_command_mock.call_args_list)

  def testCloneRepoDirExistsIsNotEmpty(self):
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    self.StartObjectPatch(os, 'listdir')
    listdir_mock = self.StartObjectPatch(os, 'listdir')
    listdir_mock.return_value = ('test.txt')
    project_repo = git.Git('fake-project', 'fake-repo')
    repo_path = self.CreateTempDir('repo-path')
    with self.assertRaisesRegexp(
        git.CannotInitRepositoryException,
        re.escape('Directory path specified exists and is not empty')):
      project_repo.Clone(destination_path=repo_path)

  def testCloneRemoteDoesntExist(self):
    project_repo = git.Git('fake-project', 'fake-repo')
    repo_path = self.CreateTempDir('repo-path')
    project_repo._uri = 'abcd'
    subprocess_mock = self.StartObjectPatch(subprocess, 'check_call')
    subprocess_mock.side_effect = subprocess.CalledProcessError(
        1, ('fatal: repository {0} does not exist'.format(project_repo._uri)))
    with self.assertRaisesRegexp(
        git.CannotFetchRepositoryException,
        re.escape('fatal: repository abcd does not exist')):
      project_repo.Clone(destination_path=repo_path)

  def testCloneRepoDirExistsGitNotFound(self):
    self.git_version_mock.side_effect = OSError(errno.ENOENT, 'not found')
    project_repo = git.Git('fake-project', 'fake-repo')
    repo_path = self.CreateTempDir('repo-path')
    with self.assertRaisesRegexp(
        git.NoGitException,
        re.escape('Cannot find git. Please install git and try again.')):
      project_repo.Clone(destination_path=repo_path)

  @sdk_test_base.Filters.RunOnlyInBundle
  def testCredentialHelperFindableFromInstall(self):
    with mock.patch.dict('os.environ', {'PATH': config.Paths().sdk_bin_path}):
      gcloud = git._GetGcloudScript()

    self.assertIsNotNone(gcloud)
    self.assertTrue(
        os.path.exists(os.path.join(config.Paths().sdk_bin_path, gcloud)) or
        gcloud == (config.Paths().sdk_bin_path + '/gcloud'))

  def testCredentialHelperGoodGcloudPathFullPathFalse(self):
    with mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath') as find_gcloud:
      find_gcloud.return_value = 'abC/1234/has-hyphen/with_underscore/gcloud'
      gcloud = git._GetGcloudScript()
      # ignore .cmd suffix
      self.assertEqual(gcloud[:6], 'gcloud')

  def testCredentialHelperGoodGcloudPathFullPathTrue(self):
    with mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath') as find_gcloud:
      find_gcloud.return_value = 'abC/1234/has-hyphen/with_underscore/gcloud'
      gcloud = git._GetGcloudScript(full_path=True)
      self.AssertErrNotContains('credential helper may not work correctly')
      self.assertEqual(gcloud, 'abC/1234/has-hyphen/with_underscore/gcloud')

  def testCredentialHelperGcloudWithSpaces(self):
    with mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath') as find_gcloud:
      find_gcloud.return_value = '/path/google cloud SDK/gcloud'
      gcloud = git._GetGcloudScript()
      # ignore .cmd suffix
      self.assertEquals(gcloud[:6], 'gcloud')

  def testCredentialHelperGcloudWithSpacesAndFullPath(self):
    with mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath') as find_gcloud:
      find_gcloud.return_value = '/path/google cloud SDK/gcloud'
      gcloud = git._GetGcloudScript(full_path=True)
      self.AssertErrContains('credential helper may not work correctly')
      self.assertEquals(gcloud, '/path/google cloud SDK/gcloud')

  def testCredentialHelperNotInPath(self):
    with mock.patch.dict('os.environ', {'PATH': 'bogus'}):
      self.assertRaises(git.GcloudIsNotInPath, git._GetGcloudScript)

  def testForcePushFilesToBranchWithCredHelper(self):
    self.git_version_mock.return_value = 'git version 2.15.0'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    properties.VALUES.core.account.Set('fake-git-account')
    subprocess_mock = self.StartObjectPatch(subprocess, 'check_call')
    cred_helper_command = ('!gcloud auth git-helper '
                           '--account=fake-git-account --ignore-unknown $@')
    temp_path = '/tmp/path'
    self.StartObjectPatch(
        file_utils.TemporaryDirectory, '__enter__', return_value=temp_path)
    self.StartObjectPatch(file_utils, 'RmTree')

    repo_url = 'https://source.developers.google.com/p/fake-project/r/fake-repo'
    repo = git.Git('fake-project', 'fake-repo')

    expected_calls = [mock.call(['git', 'init', temp_path])]

    def add_expected_call(*args):
      git_dir = '--git-dir=' + os.path.join(temp_path, '.git')
      work_tree = '--work-tree=/dir'
      expected_calls.append(mock.call(['git', git_dir, work_tree] + list(args)))

    add_expected_call('checkout', '-b', 'branch1')
    add_expected_call('add', '/dir/file1', '/dir/dir2/file2')
    add_expected_call('commit', '-m', 'source capture uploaded from gcloud')
    add_expected_call('config', 'credential.helper', cred_helper_command)
    add_expected_call('remote', 'add', 'origin', repo_url)
    add_expected_call('push', '-f', 'origin', 'branch1')

    repo.ForcePushFilesToBranch(
        'branch1', '/dir', ['/dir/file1', '/dir/dir2/file2'])

    self.assertEqual(expected_calls, subprocess_mock.call_args_list)

  def testForcePushFilesToBranchNoCredHelper(self):
    self.git_version_mock.return_value = 'git version 1.7.9'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    properties.VALUES.core.account.Set('fake-git-account')
    subprocess_mock = self.StartObjectPatch(subprocess, 'check_call')
    temp_path = '/tmp/path'
    self.StartObjectPatch(
        file_utils.TemporaryDirectory, '__enter__', return_value=temp_path)
    self.StartObjectPatch(file_utils, 'RmTree')

    repo_url = 'https://source.developers.google.com/p/fake-project/r/fake-repo'
    repo = git.Git('fake-project', 'fake-repo')

    expected_calls = [mock.call(['git', 'init', temp_path])]

    def add_expected_call(*args):
      git_dir = '--git-dir=' + os.path.join(temp_path, '.git')
      work_tree = '--work-tree=/dir'
      expected_calls.append(mock.call(['git', git_dir, work_tree] + list(args)))

    add_expected_call('checkout', '-b', 'branch1')
    add_expected_call('add', '/dir/file1', '/dir/dir2/file2')
    add_expected_call('commit', '-m', 'source capture uploaded from gcloud')
    add_expected_call('remote', 'add', 'origin', repo_url)
    add_expected_call('push', '-f', 'origin', 'branch1')

    repo.ForcePushFilesToBranch(
        'branch1', '/dir', ['/dir/file1', '/dir/dir2/file2'])

    self.assertEqual(expected_calls, subprocess_mock.call_args_list)


class GitVersionTest(base.SourceTest):

  def SetUp(self):
    self.min_version = (2, 0, 1)
    self.min_windows_version = (2, 15, 0)
    self.subprocess_mock = self.StartObjectPatch(subprocess, 'check_output')

  def testMatchesMinVersionWhenGreater(self):
    self.subprocess_mock.return_value = 'git version 2.1.1'
    self.assertEqual(True, git.CheckGitVersion(self.min_version))

  def testMatchesMinVersionWhenEqual(self):
    self.subprocess_mock.return_value = 'git version 2.0.1'
    self.assertEqual(True, git.CheckGitVersion(self.min_version))

  def testNoCheckMinVersion(self):
    self.subprocess_mock.return_value = 'git version 0.0.0'
    self.assertEqual(True, git.CheckGitVersion())

  def testRaisesWhenMinVersionIsSmaller(self):
    self.subprocess_mock.return_value = 'git version 1.8.9'
    with self.assertRaisesRegexp(
        git.GitVersionException,
        (r'Your git version .*\..* is older than the minimum version (\d+)\.')):
      git.CheckGitVersion(self.min_version)

  def testRaisesWhenNoVersion(self):
    self.subprocess_mock.return_value = ''
    with self.assertRaisesRegexp(git.InvalidGitException,
                                 ('The git version string is empty.')):
      git.CheckGitVersion(self.min_version)

  def testRaisesWhenBadOutput(self):
    self.subprocess_mock.return_value = 'sit versi'
    with self.assertRaisesRegexp(
        git.InvalidGitException,
        ('The git version string must start with git version')):
      git.CheckGitVersion(self.min_version)

  def testRaisesWhenBadVersionNumber(self):
    self.subprocess_mock.return_value = 'git version x'
    with self.assertRaisesRegexp(
        git.InvalidGitException,
        ('The git version string must contain a version number')):
      git.CheckGitVersion(self.min_version)

  def testRaisesWhenNotFound(self):
    self.subprocess_mock.side_effect = OSError(errno.ENOENT, 'not found')
    with self.assertRaisesRegexp(
        git.NoGitException,
        ('Cannot find git. Please install git and try again.')):
      git.CheckGitVersion(self.min_version)


@mock.patch('subprocess.check_output')
class GitCredentialHelperCheckTest(base.SourceTest):

  def SetUp(self):
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    self.StartObjectPatch(git, 'CheckGitVersion', return_value=True)
    self.StartObjectPatch(
        properties.VALUES.core.account, 'Get', return_value='somevalue')
    self.StartObjectPatch(subprocess, 'check_call')

  def testEmptyCredentialHelper(self, subprocess_mock):
    subprocess_mock.return_value = 'credential.helper='
    project_repo = git.Git('fake-project', 'fake-repo')
    project_repo.Clone('dest', dry_run=True)
    self.AssertErrNotContains('cancel.')

  def testNoCredentialHelper(self, subprocess_mock):
    subprocess_mock.return_value = ''
    project_repo = git.Git('fake-project', 'fake-repo')
    project_repo.Clone('dest', dry_run=True)
    self.AssertErrNotContains('cancel')


if __name__ == '__main__':
  test_case.main()
