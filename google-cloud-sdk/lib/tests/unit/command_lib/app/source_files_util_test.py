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
"""Unit tests for source_files_util module."""

from __future__ import absolute_import
import re

from googlecloudsdk.api_lib.app import util
from googlecloudsdk.command_lib.app import source_files_util
from googlecloudsdk.command_lib.util import gcloudignore
from tests.lib import sdk_test_base

import mock


class SourceFileIteratorTest(sdk_test_base.SdkBase):
  """Tests for source_files_util.GetSourceFileIterator."""

  def testNodeStandardUsesGcloudignore(self):
    """No .gcloudignore on Node Standard should generate .gcloudignore."""
    with mock.patch.object(gcloudignore, 'GetFileChooserForDir') as mock_method:
      source_files_util.GetSourceFileIterator(self.temp_path, re.compile(r'.'),
                                              False, 'nodejs8',
                                              util.Environment.STANDARD)
      mock_method.assert_called_once_with(
          self.temp_path,
          default_ignore_file=source_files_util._NODE_GCLOUDIGNORE,
          include_gitignore=False,
          gcloud_ignore_creation_predicate=mock.ANY,
          write_on_disk=True)

  def testNodeFlexDoesNotUseGcloudignore(self):
    """No .gcloudignore on Node Flex should not generate .gcloudignore."""
    skip_files_regex = re.compile(r'.')
    with mock.patch.object(gcloudignore, 'GetFileChooserForDir') as gcloud_mock:
      with mock.patch.object(util, 'FileIterator') as util_mock:
        source_files_util.GetSourceFileIterator(
            self.temp_path, skip_files_regex, False, 'nodejs8',
            util.Environment.FLEX)
        util_mock.assert_called_once_with(self.temp_path, skip_files_regex)
        gcloud_mock.assert_not_called()

  def testPhp72StandardUsesGcloudignore(self):
    """No .gcloudignore on PHP72 Standard should generate .gcloudignore."""
    with mock.patch.object(gcloudignore, 'GetFileChooserForDir') as mock_method:
      source_files_util.GetSourceFileIterator(self.temp_path, re.compile(r'.'),
                                              False, 'php72',
                                              util.Environment.STANDARD)
      mock_method.assert_called_once_with(
          self.temp_path,
          default_ignore_file=source_files_util._PHP_GCLOUDIGNORE,
          include_gitignore=False,
          gcloud_ignore_creation_predicate=mock.ANY,
          write_on_disk=True)

  def testPhp55StandardDoesNotUseGcloudignore(self):
    """No .gcloudignore on PHP55 Standard should not generate .gcloudignore."""
    skip_files_regex = re.compile(r'.')
    with mock.patch.object(gcloudignore, 'GetFileChooserForDir') as gcloud_mock:
      with mock.patch.object(util, 'FileIterator') as util_mock:
        source_files_util.GetSourceFileIterator(
            self.temp_path, skip_files_regex, False, 'php55',
            util.Environment.STANDARD)
        util_mock.assert_called_once_with(self.temp_path, skip_files_regex)
        gcloud_mock.assert_not_called()

  def testSkipFilesAndGcloudignoreNewRuntimeRaisesError(self):
    """.gcloudignore and skip_files on Node Standard should error out."""
    self.Touch(self.temp_path, '.gcloudignore')
    with self.assertRaises(source_files_util.SkipFilesError):
      source_files_util.GetSourceFileIterator(
          self.temp_path, re.compile(r'.'), True, 'nodejs8',
          util.Environment.STANDARD)

  def testSkipFilesAndGcloudignoreOldRuntimeRaisesError(self):
    """.gcloudignore and skip_files on Python2.7 Standard should error out."""
    self.Touch(self.temp_path, '.gcloudignore')
    with self.assertRaises(source_files_util.SkipFilesError):
      source_files_util.GetSourceFileIterator(
          self.temp_path, re.compile(r'.'), True, 'python27',
          util.Environment.STANDARD)

  def testGcloudignoreAndNoSkipFilesDoesNotGenerateNewGcloudignore(self):
    """.gcloudignore and no skip_files python2.7 does not make .gcloudignore."""
    self.Touch(self.temp_path, '.gcloudignore')
    with mock.patch.object(gcloudignore,
                           'GetFileChooserForDir') as gcloud_mock:
      source_files_util.GetSourceFileIterator(
          self.temp_path, re.compile(r'.'), False, 'python27',
          util.Environment.STANDARD)
      gcloud_mock.assert_called_once_with(self.temp_path)
