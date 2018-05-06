# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Unit tests for the platforms module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import os
import sys

from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import pkg_resources
from tests.lib import test_case


def Touch(path, contents=''):
  with open(path, 'w') as fp:
    fp.write(contents)
  return path


def MakeZip(src_dir, dst_dir, name):
  zip_pkg = os.path.join(dst_dir, name + '.zip')
  archive.MakeZipFromDir(zip_pkg, src_dir)
  return zip_pkg


class PkgResourcesTest(test_case.TestCase):

  def testIsImportable(self):
    with files.TemporaryDirectory() as t:
      Touch(os.path.join(t, 'foo.py'), '"""Foo module."""')
      self.assertFalse(pkg_resources.IsImportable('foo', t))

      Touch(os.path.join(t, '__init__.py'), '"""Package marker."""')
      self.assertTrue(pkg_resources.IsImportable('foo', t))

  def testIsImportableFromZip(self):
    with files.TemporaryDirectory() as t:
      Touch(os.path.join(t, 'foo.py'), 'class Foo(): VALUE=5')
      Touch(os.path.join(t, '__init__.py'), '"""Package marker."""')
      os.makedirs(os.path.join(t, 'pkg'))
      Touch(os.path.join(t, 'pkg', '__init__.py'), '"""Package marker."""')
      Touch(os.path.join(t, 'pkg', 'bar.py'), 'class Bar(): VALUE=7')

      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertTrue(pkg_resources.IsImportable('foo', zip_pkg))
        self.assertTrue(pkg_resources.IsImportable('pkg.bar', zip_pkg))
        self.assertTrue(
            pkg_resources.IsImportable('bar', os.path.join(zip_pkg, 'pkg')))
        self.assertFalse(pkg_resources.IsImportable('pkg.baz', zip_pkg))

  def testListPackage(self):
    with files.TemporaryDirectory() as t:
      self.assertEqual(([], []), pkg_resources.ListPackage(t))
      Touch(os.path.join(t, 'foo.py'), '"""Foo module."""')
      self.assertEqual(([], ['foo']), pkg_resources.ListPackage(t))
      Touch(os.path.join(t, '__init__.py'), '"""Package marker."""')
      self.assertEqual(([], ['foo']), pkg_resources.ListPackage(t))
      os.makedirs(os.path.join(t, 'pkg'))
      self.assertEqual(([], ['foo']), pkg_resources.ListPackage(t))
      Touch(os.path.join(t, 'pkg', '__init__.py'), '"""Package marker."""')
      self.assertEqual((['pkg'], ['foo']), pkg_resources.ListPackage(t))
      Touch(os.path.join(t, 'bar.py'), '"""Bar module."""')
      self.assertEqual((['pkg'], ['bar', 'foo']), pkg_resources.ListPackage(t))

      # Check support for additional extensions.
      self.assertEqual((['pkg'], ['bar', 'foo']),
                       pkg_resources.ListPackage(
                           t, extra_extensions=['.yaml', '.junk']))
      Touch(os.path.join(t, 'baz.yaml'), '')
      Touch(os.path.join(t, 'baz.junk'), '')
      self.assertEqual((['pkg'], ['bar', 'baz.yaml', 'foo']),
                       pkg_resources.ListPackage(
                           t, extra_extensions=['.yaml']))
      self.assertEqual((['pkg'], ['bar', 'baz.junk', 'baz.yaml', 'foo']),
                       pkg_resources.ListPackage(
                           t, extra_extensions=['.yaml', '.junk']))

  def testListPackageResources(self):
    with files.TemporaryDirectory() as t:
      self.assertEqual([], sorted(pkg_resources.ListPackageResources(t)))
      Touch(os.path.join(t, 'foo.py'), '"""Foo module."""')
      self.assertEqual(['foo.py'],
                       sorted(pkg_resources.ListPackageResources(t)))
      Touch(os.path.join(t, '__init__.py'), '"""Package marker."""')
      self.assertEqual(['__init__.py', 'foo.py'],
                       sorted(pkg_resources.ListPackageResources(t)))
      os.makedirs(os.path.join(t, 'pkg'))
      self.assertEqual(['__init__.py', 'foo.py', 'pkg' + os.sep],
                       sorted(pkg_resources.ListPackageResources(t)))
      Touch(os.path.join(t, 'pkg', '__init__.py'), '"""Package marker."""')
      self.assertEqual(['__init__.py', 'foo.py', 'pkg' + os.sep],
                       sorted(pkg_resources.ListPackageResources(t)))
      Touch(os.path.join(t, 'bar'), 'BAR')
      self.assertEqual(['__init__.py', 'bar', 'foo.py', 'pkg' + os.sep],
                       sorted(pkg_resources.ListPackageResources(t)))
      self.assertEqual(
          b'BAR', pkg_resources.GetResourceFromFile(os.path.join(t, 'bar')))

      with self.assertRaises(IOError):
        pkg_resources.GetResourceFromFile(os.path.join(t, 'non_existant_file'))

  def testListPackageInZip(self):
    with files.TemporaryDirectory() as t:
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(([], []), pkg_resources.ListPackage(zip_pkg))
      Touch(os.path.join(t, 'foo.py'), '"""Foo module."""')
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(([], ['foo']), pkg_resources.ListPackage(zip_pkg))
      Touch(os.path.join(t, '__init__.py'), '"""Package marker."""')
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(([], ['foo']), pkg_resources.ListPackage(zip_pkg))
      os.makedirs(os.path.join(t, 'pkg'))
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(([], ['foo']), pkg_resources.ListPackage(zip_pkg))
      Touch(os.path.join(t, 'pkg', '__init__.py'), '"""Package marker."""')
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual((['pkg'], ['foo']),
                         pkg_resources.ListPackage(zip_pkg))
      Touch(os.path.join(t, 'bar.py'), '"""Bar module."""')
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual((['pkg'], ['bar', 'foo']),
                         pkg_resources.ListPackage(zip_pkg))

  def testListPackageResourcesInZip(self):
    with files.TemporaryDirectory() as t:
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual([],
                         sorted(pkg_resources.ListPackageResources(zip_pkg)))
      Touch(os.path.join(t, 'foo.py'), '"""Foo module."""')
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(['foo.py'],
                         sorted(pkg_resources.ListPackageResources(zip_pkg)))
      Touch(os.path.join(t, '__init__.py'), '"""Package marker."""')
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(['__init__.py', 'foo.py'],
                         sorted(pkg_resources.ListPackageResources(zip_pkg)))
      os.makedirs(os.path.join(t, 'pkg'))
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(['__init__.py', 'foo.py', 'pkg' + os.sep],
                         sorted(pkg_resources.ListPackageResources(zip_pkg)))
      Touch(os.path.join(t, 'pkg', '__init__.py'), '"""Package marker."""')
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(['__init__.py', 'foo.py', 'pkg' + os.sep],
                         sorted(pkg_resources.ListPackageResources(zip_pkg)))
      Touch(os.path.join(t, 'bar'), 'BAR')
      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        self.assertEqual(['__init__.py', 'bar', 'foo.py', 'pkg' + os.sep],
                         sorted(pkg_resources.ListPackageResources(zip_pkg)))
        self.assertEqual(
            b'BAR', pkg_resources.GetResourceFromFile(os.path.join(t, 'bar')))
        with self.assertRaises(IOError):
          pkg_resources.GetResourceFromFile(
              os.path.join(zip_pkg, 'non_existant_file'))

  def testGetResourceFromFile(self):
    this_file, _ = os.path.splitext(__file__)
    this_file_contents = pkg_resources.GetResourceFromFile(this_file + '.py')
    self.assertIn(b'This is the string I am looking for', this_file_contents)

  def testGetModuleFromPath(self):
    with files.TemporaryDirectory() as t:
      Touch(os.path.join(t, 'foo.py'), 'class Foo(): VALUE=5')
      Touch(os.path.join(t, '__init__.py'), '"""Package marker."""')
      os.makedirs(os.path.join(t, 'pkg'))
      Touch(os.path.join(t, 'pkg', '__init__.py'), '"""Package marker."""')
      Touch(os.path.join(t, 'pkg', 'bar.py'), 'class Bar(): VALUE=7')
      foo_mod = pkg_resources.GetModuleFromPath('my.foo.mod',
                                                os.path.join(t, 'foo'))
      self.assertIn('my.foo.mod', sys.modules)
      del sys.modules['my.foo.mod']
      self.assertEqual(5, foo_mod.Foo.VALUE)
      self.assertEqual('my.foo.mod', foo_mod.__name__)

      bar_mod = pkg_resources.GetModuleFromPath('my.bar.mod',
                                                os.path.join(t, 'pkg', 'bar'))
      self.assertIn('my.bar.mod', sys.modules)
      del sys.modules['my.bar.mod']
      self.assertEqual(7, bar_mod.Bar.VALUE)
      self.assertEqual('my.bar.mod', bar_mod.__name__)
      self.assertEqual('my.bar.mod', bar_mod.Bar.__module__)

      with self.assertRaises(ImportError):
        pkg_resources.GetModuleFromPath('my.baz.mod',
                                        os.path.join(t, 'pkg', 'baz'))

  def testGetModuleFromZipPath(self):
    with files.TemporaryDirectory() as t:
      Touch(os.path.join(t, 'foo.py'), 'class Foo(): VALUE=5')
      Touch(os.path.join(t, '__init__.py'), '"""Package marker."""')
      os.makedirs(os.path.join(t, 'pkg'))
      Touch(os.path.join(t, 'pkg', '__init__.py'), '"""Package marker."""')
      Touch(os.path.join(t, 'pkg', 'bar.py'), 'class Bar(): VALUE=7')

      with files.TemporaryDirectory() as zip_tmp_dir:
        zip_pkg = MakeZip(t, zip_tmp_dir, 'pkg')
        foo_mod = pkg_resources.GetModuleFromPath('my.foo.mod',
                                                  os.path.join(zip_pkg, 'foo'))
        self.assertIn('my.foo.mod', sys.modules)
        del sys.modules['my.foo.mod']
        self.assertEqual(5, foo_mod.Foo.VALUE)
        self.assertEqual('my.foo.mod', foo_mod.__name__)

        bar_mod = pkg_resources.GetModuleFromPath(
            'my.bar.mod', os.path.join(zip_pkg, 'pkg', 'bar'))
        self.assertIn('my.bar.mod', sys.modules)
        del sys.modules['my.bar.mod']
        self.assertEqual(7, bar_mod.Bar.VALUE)
        self.assertEqual('my.bar.mod', bar_mod.__name__)
        self.assertEqual('my.bar.mod', bar_mod.Bar.__module__)

        with self.assertRaises(ImportError):
          pkg_resources.GetModuleFromPath('my.baz.mod',
                                          os.path.join(zip_pkg, 'pkg', 'baz'))


if __name__ == '__main__':
  test_case.main()
