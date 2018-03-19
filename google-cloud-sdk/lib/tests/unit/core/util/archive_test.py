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
"""Unit tests for the archive module."""

import os
import re
import zipfile

from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files
from tests.lib import test_case


class ArchiveTest(test_case.TestCase):

  def _MakeZip(self, src_dir):
    with files.TemporaryDirectory() as dst_dir:
      zip_file = os.path.join(dst_dir, 'arch.zip')
      archive.MakeZipFromDir(zip_file, src_dir)
      zf = zipfile.ZipFile(zip_file)
      try:
        self.assertIsNone(zf.testzip())
        name_list = [(name, zf.read(name)) for name in zf.namelist()]
      finally:
        zf.close()
    return name_list

  def testZipDirEmpty(self):
    with files.TemporaryDirectory() as src_dir:
      name_list = self._MakeZip(src_dir)
    self.assertEquals([], name_list)

  def testZipDirSingleEmptyDir(self):
    with files.TemporaryDirectory() as src_dir:
      os.makedirs(os.path.join(src_dir, 'empty_dir'))
      name_list = self._MakeZip(src_dir)
    self.assertEquals([('empty_dir/', '')], name_list)

  def testZipDirSingleFile(self):
    with files.TemporaryDirectory() as src_dir:
      with open(os.path.join(src_dir, 'sample.txt'), 'a'):
        pass
      name_list = self._MakeZip(src_dir)
    self.assertEquals([('sample.txt', '')], name_list)

  def testZipDirFull(self):
    with files.TemporaryDirectory() as src_dir:
      os.makedirs(os.path.join(src_dir, 'empty_dir'))
      with open(os.path.join(src_dir, 'sample.txt'), 'a'):
        pass
      full_dir = os.path.join(src_dir, 'full_dir')
      os.makedirs(full_dir)
      with open(os.path.join(full_dir, 'sample1.txt'), 'a'):
        pass
      with open(os.path.join(full_dir, 'sample2.txt'), 'a') as f:
        f.write('Hello')
      name_list = self._MakeZip(src_dir)
    self.assertEquals([('empty_dir/', ''), ('full_dir/', ''),
                       ('full_dir/sample1.txt', ''),
                       ('full_dir/sample2.txt', 'Hello'),
                       ('sample.txt', '')], sorted(name_list))

  def testZipDirFullWithFilter(self):

    def RegexPredicate(f):
      return not re.match(
          r'empty_dir|full_dir{}.*'.format(re.escape(os.sep)), f)

    with files.TemporaryDirectory() as src_dir:
      os.makedirs(os.path.join(src_dir, 'empty_dir'))
      with open(os.path.join(src_dir, 'sample.txt'), 'a'):
        pass
      full_dir = os.path.join(src_dir, 'full_dir')
      os.makedirs(full_dir)
      with open(os.path.join(full_dir, 'sample1.txt'), 'a'):
        pass
      with open(os.path.join(full_dir, 'sample2.txt'), 'a') as f:
        f.write('Hello')
      full_directory = os.path.join(src_dir, 'full_directory')
      os.makedirs(full_directory)
      with open(os.path.join(full_directory, 'sample1.txt'), 'a'):
        pass
      with open(os.path.join(full_directory, 'sample2.txt'), 'a') as f:
        f.write('Hello')
      with files.TemporaryDirectory() as dst_dir:
        zip_file = os.path.join(dst_dir, 'arch.zip')
        archive.MakeZipFromDir(zip_file, src_dir, RegexPredicate)
        zf = zipfile.ZipFile(zip_file)
        try:
          self.assertIsNone(zf.testzip())
          name_list = [(name, zf.read(name)) for name in zf.namelist()]
        finally:
          zf.close()
    self.assertEquals([('full_dir/', ''),
                       ('full_directory/', ''),
                       ('full_directory/sample1.txt', ''),
                       ('full_directory/sample2.txt', 'Hello'),
                       ('sample.txt', '')], sorted(name_list))


if __name__ == '__main__':
  test_case.main()
