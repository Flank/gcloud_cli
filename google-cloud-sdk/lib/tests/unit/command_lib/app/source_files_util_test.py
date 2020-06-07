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
"""Unit tests for source_files_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re

from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.command_lib.app import source_files_util
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib import test_case

import mock


class GcloudIgnoreRegistryTest(parameterized.TestCase, test_case.TestCase):
  """Sanity check on the ignore file registry."""

  def SetUp(self):
    self.reg = source_files_util._GetGcloudignoreRegistry()

  @parameterized.parameters(
      (env.STANDARD, 'nodejs8', r'node_modules'),
      (env.STANDARD, 'php72', r'vendor'),
      (env.STANDARD, 'go111', r'dylib'),
      (env.STANDARD, 'python37', r'__pycache__'),
      (env.STANDARD, 'java11', r'target'),
  )
  def testRegistryMatches(self, environment, runtime, ignore_regex):
    self.assertRegexpMatches(self.reg.Get(runtime, environment), ignore_regex)

  @parameterized.parameters(
      (env.STANDARD, 'python27'),
      (env.STANDARD, 'go19'),
      (env.FLEX, 'nodejs8'),
      (env.STANDARD, 'java8'),
  )
  def testRegistryNotMatches(self, environment, runtime):
    self.assertFalse(self.reg.Get(runtime, environment))


class GetSourceFilesTest(test_case.TestCase):
  """Tests for source_files_util.GetSourceFiles."""

  def SetUp(self):

    self.source_dir = 'upload-dir'
    self.upload_dir = 'source-dir'
    self.skip_files = re.compile(r'default-skip-expr')

    self.entry = False  # set to string to return from registry
    self.reg = mock.Mock()
    self.reg.Get = lambda unused_runtime, unused_env: self.entry

    self.StartObjectPatch(
        source_files_util, '_GetGcloudignoreRegistry',
        return_value=self.reg)

    self.file_chooser_mock = self.StartObjectPatch(
        gcloudignore, 'GetFileChooserForDir')
    self.file_iterator_mock = self.StartObjectPatch(
        util, 'FileIterator')

  def testNotInRegistry(self):
    """No registry entry, no explicit skip files."""
    source_files_util.GetSourceFiles(
        self.upload_dir, self.skip_files, False, 'fake-runtime', 'fake-env',
        self.source_dir)
    self.file_chooser_mock.assert_not_called()
    self.file_iterator_mock.assert_called_once_with(
        self.upload_dir, self.skip_files)

  def testInRegistry(self):
    """Has registry entry for .gcloudignore, no explicit skip files."""
    self.entry = 'gcloudignore-contents'
    source_files_util.GetSourceFiles(
        self.upload_dir, self.skip_files, False, 'fake-runtime', 'fake-env',
        self.source_dir)
    self.file_chooser_mock.assert_called_once_with(
        self.source_dir,
        default_ignore_file='gcloudignore-contents',
        include_gitignore=False,
        gcloud_ignore_creation_predicate=mock.ANY,
        write_on_disk=True)
    self.file_iterator_mock.assert_not_called()

  def testNotInRegistry_GcloudignoreExists(self):
    """A gcloudignore is allowed opt-in if not in registry."""
    exists = self.StartObjectPatch(os.path, 'exists', return_value=True)
    source_files_util.GetSourceFiles(
        self.upload_dir, self.skip_files, False, 'fake-runtime', 'fake-env',
        self.source_dir)
    exists.assert_called_once_with(
        os.path.join(self.source_dir, '.gcloudignore'))
    self.file_chooser_mock.assert_called_once_with(self.source_dir)
    self.file_iterator_mock.assert_not_called()

  def testInRegistry_ExplicitSkipFiles(self):
    """Skip files not allowed when there's a registry entry."""
    self.entry = 'gcloudignore-contents'
    with self.assertRaisesRegexp(
        source_files_util.SkipFilesError,
        r'cannot be used with the \[fake-runtime\] runtime'):
      source_files_util.GetSourceFiles(
          self.upload_dir, self.skip_files, True, 'fake-runtime', 'fake-env',
          self.source_dir)
    self.file_chooser_mock.assert_not_called()
    self.file_iterator_mock.assert_not_called()

  def testNotInRegistry_IgnoreFileExists(self):
    """Skip files specified in ignore-file."""
    exists = self.StartObjectPatch(os.path, 'exists', return_value=True)
    ignore_file = '.gcloudignore-testing-config1'
    source_files_util.GetSourceFiles(
        self.upload_dir, self.skip_files, False, 'fake-runtime', 'fake-env',
        self.source_dir, ignore_file)
    exists.assert_called_once_with(
        os.path.join(self.source_dir, ignore_file))
    self.file_chooser_mock.assert_called_once_with(self.source_dir,
                                                   ignore_file=ignore_file)
    self.file_iterator_mock.assert_not_called()

  def testNotInRegistry_ExplicitSkipFiles_IgnorefileExists(self):
    """Skip files never allowed in conjunction with gcloudignore."""
    exists = self.StartObjectPatch(os.path, 'exists', return_value=True)
    ignore_file = '.gcloudignore-testing-config1'
    with self.assertRaisesRegexp(
        source_files_util.SkipFilesError,
        r'Cannot have both an ignore file {0} and skip_files'
        .format(ignore_file)):
      source_files_util.GetSourceFiles(
          self.upload_dir, self.skip_files, True, 'fake-runtime', 'fake-env',
          self.source_dir, ignore_file)
    exists.assert_called_once_with(
        os.path.join(self.source_dir, ignore_file))
    self.file_chooser_mock.assert_not_called()
    self.file_iterator_mock.assert_not_called()

  def testIgnorefileNotExist(self):
    """Raise error if user specified ignore-file does not exist."""
    exists = self.StartObjectPatch(os.path, 'exists', return_value=False)
    ignore_file = '.gcloudignore-testing-config1'
    with self.assertRaisesRegexp(
        exceptions.FileNotFoundError,
        'File {0} referenced by --ignore-file does not exist.'
        .format(ignore_file)):
      source_files_util.GetSourceFiles(
          self.upload_dir, self.skip_files, True, 'fake-runtime', 'fake-env',
          self.source_dir, ignore_file)
    exists.assert_called_once_with(
        os.path.join(self.source_dir, ignore_file))
    self.file_chooser_mock.assert_not_called()
    self.file_iterator_mock.assert_not_called()

  def testNotInRegistry_ExplicitSkipFiles_GcloudignoreExists(self):
    """Skip files never allowed in conjunction with gcloudignore."""
    exists = self.StartObjectPatch(os.path, 'exists', return_value=True)
    with self.assertRaisesRegexp(
        source_files_util.SkipFilesError,
        r'Cannot have both a \.gcloudignore file and skip_files'):
      source_files_util.GetSourceFiles(
          self.upload_dir, self.skip_files, True, 'fake-runtime', 'fake-env',
          self.source_dir)
    exists.assert_called_once_with(
        os.path.join(self.source_dir, '.gcloudignore'))
    self.file_chooser_mock.assert_not_called()
    self.file_iterator_mock.assert_not_called()


class SourceFilesIntegrationTest(test_case.Base, parameterized.TestCase):
  """Tests GetSourceFiles using an actual file system.

  Verifies the returned paths w.r.t both
  implicit and explicit skip_files and .gcloudignore directives,
  and that .gcloudignore is written to disk when it's supposed to.

  We use __pycache__ because it is pulled from the default
  .gcloudignore contents from the python3* runtime.

  We use a *.pyc file with skip_files, simply to differentiate
  between the resulting file set compared to the .gcloudignore
  default.
  """

  def _WriteFiles(self, path):
    self.Touch(path, 'main.py')
    self.Touch(path, 'main.pyc')
    self.Touch(os.path.join(path, '__pycache__'), 'cached-file',
               makedirs=True)

  def SetUp(self):
    self.upload_dir = files.TemporaryDirectory()
    self.source_dir = files.TemporaryDirectory()
    self._WriteFiles(self.upload_dir.path)
    self._WriteFiles(self.source_dir.path)

    # May or may not be written depending on test
    self.gcloudignore_path = os.path.join(
        self.source_dir.path, '.gcloudignore')
    self.ignore_file_path = os.path.join(
        self.source_dir.path, '.gcloudignore-testing-config1')

    self.skip_files = re.compile(r'.*\.pyc')

  def testInRegistry(self):
    """In gcloudignore registry, writes .gcloudignore to disk."""
    it = source_files_util.GetSourceFiles(
        self.upload_dir.path,
        self.skip_files, False, 'python37', env.STANDARD,
        self.source_dir.path)
    self.assertListEqual(sorted(it), ['main.py', 'main.pyc'])
    self.AssertFileContains('__pycache__', self.gcloudignore_path)

  @parameterized.parameters(
      ('python27',),  # Not in .gcloudignore registry
      ('python37',),  # In registry
  )
  def testExistingGcloudignore(self, runtime):
    """Existing .gcloudignore overrides default .gcloudignore.

    This is an imaginary scenario where the user wants to upload
    pre-compiled *.pyc files only, and hence ignores *.py files.

    This behavior is independent of whether there is a
    .gcloudignore registry entry or not for the runtime.

    Args:
      runtime: str, runtime id.
    """
    self.Touch(self.source_dir.path, '.gcloudignore', '*.py')
    it = source_files_util.GetSourceFiles(
        self.upload_dir.path,
        self.skip_files, False, runtime, env.STANDARD,
        self.source_dir.path)
    self.assertListEqual(
        sorted(it), [os.path.join('__pycache__', 'cached-file'), 'main.pyc'])
    self.AssertFileEquals('*.py', self.gcloudignore_path)

  def testImplicitSkipFiles(self):
    """Not in gcloudignore registry, uses implicit skip_files."""
    it = source_files_util.GetSourceFiles(
        self.upload_dir.path,
        self.skip_files, False, 'python27', env.STANDARD,
        self.source_dir.path)
    self.assertListEqual(
        sorted(it), [os.path.join('__pycache__', 'cached-file'), 'main.py'])
    self.AssertFileNotExists(self.gcloudignore_path)

  def testExistingIgnorefile(self):
    """Existing ignore-file overrides .gcloudignore.

    This is an imaginary scenario where the user wants to upload
    pre-compiled *.pyc files only, and hence ignores *.py files.

    This behavior is independent of whether there is a
    registry entry or not for the runtime.
    """
    ignore_file = '.gcloudignore-testing-config1'
    self.Touch(self.source_dir.path, ignore_file, '*.py')
    it = source_files_util.GetSourceFiles(
        self.upload_dir.path,
        self.skip_files, False, 'python27', env.STANDARD,
        self.source_dir.path, ignore_file)
    self.assertListEqual(
        sorted(it), [os.path.join('__pycache__', 'cached-file'), 'main.pyc'])
    self.AssertFileEquals('*.py', self.ignore_file_path)
