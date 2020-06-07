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
"""Unit tests for the archive module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re
import zipfile

from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files
from tests.lib import test_case


class ArchiveTest(test_case.TestCase):

  def _MakeZip(self, src_dir, update_date=False):
    with files.TemporaryDirectory() as dst_dir:
      zip_file = os.path.join(dst_dir, 'arch.zip')
      archive.MakeZipFromDir(zip_file, src_dir, update_date=update_date)
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
    self.assertEqual([], name_list)

  def testZipDirSingleEmptyDir(self):
    with files.TemporaryDirectory() as src_dir:
      os.makedirs(os.path.join(src_dir, 'empty_dir'))
      name_list = self._MakeZip(src_dir)
    self.assertEqual([('empty_dir/', b'')], name_list)

  def testZipDirSingleFile(self):
    with files.TemporaryDirectory() as src_dir:
      with open(os.path.join(src_dir, 'sample.txt'), 'a'):
        pass
      name_list = self._MakeZip(src_dir)
    self.assertEqual([('sample.txt', b'')], name_list)

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
    self.assertEqual([('empty_dir/', b''), ('full_dir/', b''),
                      ('full_dir/sample1.txt', b''),
                      ('full_dir/sample2.txt', b'Hello'),
                      ('sample.txt', b'')], sorted(name_list))

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
    self.assertEqual([('full_dir/', b''),
                      ('full_directory/', b''),
                      ('full_directory/sample1.txt', b''),
                      ('full_directory/sample2.txt', b'Hello'),
                      ('sample.txt', b'')], sorted(name_list))

  def testZipOlder1980(self):
    with files.TemporaryDirectory() as src_dir:
      os.makedirs(os.path.join(src_dir, 'empty_dir'))
      os.utime(os.path.join(src_dir, 'empty_dir'),
               (289955080, 289955080))  #  1979-03-10
      with open(os.path.join(src_dir, 'sample.txt'), 'a'):
        pass
      os.utime(os.path.join(src_dir, 'sample.txt'), (289955080, 289955080))
      full_dir = os.path.join(src_dir, 'full_dir')
      os.makedirs(full_dir)
      with open(os.path.join(full_dir, 'sample1.txt'), 'a'):
        pass
      with open(os.path.join(full_dir, 'sample2.txt'), 'a') as f:
        f.write('Hello')
      name_list = self._MakeZip(src_dir, update_date=True)
      self.assertEqual(os.path.getmtime(os.path.join(src_dir, 'sample.txt')),
                       289955080)
      self.assertEqual(os.path.getmtime(os.path.join(src_dir, 'empty_dir')),
                       289955080)
    self.assertEqual([('empty_dir/', b''), ('full_dir/', b''),
                      ('full_dir/sample1.txt', b''),
                      ('full_dir/sample2.txt', b'Hello'),
                      ('sample.txt', b'')], sorted(name_list))


if __name__ == '__main__':
  test_case.main()
