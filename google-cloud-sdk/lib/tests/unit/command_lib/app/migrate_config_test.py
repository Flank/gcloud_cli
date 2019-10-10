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

"""Tests for googlecloudsdk.command_lib.app.migrate_config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy
import os
import re

from googlecloudsdk.command_lib.app import migrate_config
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base


_FILE_MAP_BEFORE = {
    'f1.txt': 'f1 original contents',
    'mydir': {
        'sub': {
            'f2.txt': 'f2 original contents',
        }
    }
}

_FILE_MAP_AFTER = {
    'f1.txt': 'f1 new contents',
    'f1.txt.bak': 'f1 original contents',
    'mydir': {
        'f3.txt': 'f3 new contents',
        'sub': {
            'f2.txt.bak': 'f2 original contents',
        }
    }
}

_MIGRATION_MAP = collections.OrderedDict([
    ('f1.txt', 'f1 new contents'),  # overwrite
    (os.path.join('mydir', 'sub', 'f2.txt'), None),  # delete
    (os.path.join('mydir', 'f3.txt'), 'f3 new contents'),  # new file
])


def _ReadFileMap(src):
  """Returns the recursive file map for the directory.

  Args:
    src: str, path to directory.

  Returns:
    {str: ...}, recursive map structure from path to other file map if
    directory or to a string representing the file contents.
  """
  ret = {}
  for name in os.listdir(src):
    path = os.path.join(src, name)
    if os.path.isfile(path):
      ret[name] = files.ReadFileContents(path)
    else:
      ret[name] = _ReadFileMap(path)
  return ret


def _WriteFileMap(dst, file_map):
  """Writes a recursive file map to a directory.

  Args:
    dst: str, path to an existing, empty directory.
    file_map: {str: ...}, a recursive file map, see _ReadFileMap.
  """
  for name, contents_or_file_map in file_map.items():
    path = os.path.join(dst, name)
    if isinstance(contents_or_file_map, dict):
      files.MakeDir(path)
      _WriteFileMap(path, contents_or_file_map)
    else:
      files.WriteFileContents(path, contents_or_file_map)


class FileMapTest(sdk_test_base.WithTempCWD):
  """Testing of file map helper methods."""

  def testWriteFileMap(self):
    """Ensure that exactly all files are written, no more, no less."""
    self.assertEqual(os.listdir('.'), [])
    _WriteFileMap('.', _FILE_MAP_BEFORE)
    self.assertEqual(set(os.listdir('.')), {'f1.txt', 'mydir'})
    self.AssertFileExistsWithContents('f1 original contents', 'f1.txt')
    self.AssertDirectoryExists('mydir')
    self.assertEqual(set(os.listdir('mydir')), {'sub'})
    self.AssertDirectoryExists('mydir', 'sub')
    self.assertEqual(set(os.listdir(os.path.join('mydir', 'sub'))), {'f2.txt'})
    self.AssertFileExistsWithContents('f2 original contents',
                                      'mydir', 'sub', 'f2.txt')

  def testReadFileMap(self):
    """Ensure that exactly all files are read, no more, no less."""
    self.assertEqual(os.listdir('.'), [])
    files.MakeDir('mydir')
    files.MakeDir(os.path.join('mydir', 'sub'))
    files.WriteFileContents('f1.txt', 'f1 original contents')
    files.WriteFileContents(os.path.join('mydir', 'sub', 'f2.txt'),
                            'f2 original contents')
    file_map = _ReadFileMap('.')
    self.assertEqual(file_map, _FILE_MAP_BEFORE)


class MigrationResultTest(sdk_test_base.WithTempCWD):
  """Tests for migrate_config.MigrationResult."""

  def SetUp(self):
    self.result = migrate_config.MigrationResult(_MIGRATION_MAP)

  def testApplySuccess(self):
    """Compound check that write, overwrite & delete for success case."""
    _WriteFileMap('.', _FILE_MAP_BEFORE)
    self.result.Apply()
    self.assertEqual(_ReadFileMap('.'), _FILE_MAP_AFTER)

  def testApplyExistingBak(self):
    """Cancelling due to existing .bak file."""
    before = copy.deepcopy(_FILE_MAP_BEFORE)
    before['mydir']['sub']['f2.txt.bak'] = 'i am an old backup'
    _WriteFileMap('.', before)

    # f1 comes before in the OrderedDict, hence it is backed up before
    # the error with f2 is encountered. This is ok.
    after = copy.deepcopy(before)
    after['f1.txt.bak'] = 'f1 original contents'
    msg = 'Backup file path [{}] already exists'.format(
        os.path.join('mydir', 'sub', 'f2.txt.bak'))
    with self.assertRaisesRegex(
        migrate_config.MigrationError,
        re.escape(msg)):
      self.result.Apply()
    self.assertEqual(_ReadFileMap('.'), after)
