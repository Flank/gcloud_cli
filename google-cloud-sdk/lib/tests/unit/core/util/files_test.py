# -*- coding: utf-8 -*- #
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

"""Unit tests for the file_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import re
import shutil
import stat
import sys
import threading
import time

from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms
from googlecloudsdk.core.util import retry
from tests.lib import test_case

import mock
import six
from six.moves import range  # pylint: disable=redefined-builtin


# Every system we care about handles 7-bit ASCII.
_TEST_ASCII = 'Unicode'
# ÜñîçòÐé for 8-bit Windows mbcs.
_TEST_LATIN = b'\xdc\xf1\xee\xe7\xf2\xd0\xe9'.decode('iso-8859-1')
# Windows mbcs can't handle all of these UNICODE runes.
_TEST_UNICODE = 'Ṳᾔḯ¢◎ⅾℯ'


def FilesystemSupportsNonAsciiPaths():
  """Returns True if the filesystem supports UNICODE encoded paths."""
  try:
    path = _TEST_UNICODE
    path.encode(sys.getfilesystemencoding())
    return True
  except (UnicodeError, TypeError):
    return False


class PrivateFilesTest(test_case.Base):

  @test_case.Filters.DoNotRunOnWindows
  def testMakePrivateFile(self):
    with file_utils.TemporaryDirectory() as t:
      private_path = os.path.join(t, 'f.txt')
      file_utils.WriteFileContents(private_path, 'hello', private=True)
      mode = os.stat(private_path).st_mode
      # mode & 0777 strips the higher level bits that we don't care about,
      # leaving only the three permissions octals.
      self.assertEqual(mode & 0o777, 0o600)

  def testMakePrivateFile_Binary(self):
    with file_utils.TemporaryDirectory() as t:
      private_path = os.path.join(t, 'f.txt')
      file_utils.WriteBinaryFileContents(private_path, b'\nhello\n',
                                         private=True)
      with io.open(private_path, 'rb') as f:
        self.assertEqual(b'\nhello\n', f.read())

  @test_case.Filters.RunOnlyOnWindows
  def testMakePrivateFile_Text(self):
    with file_utils.TemporaryDirectory() as t:
      private_path = os.path.join(t, 'f.txt')
      file_utils.WriteFileContents(private_path, '\nhello\n', private=True)
      with io.open(private_path, 'rb') as f:
        self.assertEqual(b'\r\nhello\r\n', f.read())


def _ChmodRecursive(root, mode):
  """Changes file/directory permissions recursively."""
  for dirpath, filenames, _ in os.walk(root):
    for path in [dirpath] + [os.path.join(dirpath, f) for f in filenames]:
      os.chmod(path, mode)


class CopyTreeTest(test_case.Base):
  """Test for our wrapper for shutil.copytree.

  It uses a well-known method under the hood, so we don't do extensive testing;
  we just check (1) that it continues to do what we expect in a normal
  situation, and (2) that it works in the situation that we added the wrapper to
  address (copying a read-only directory should result in a writable directory).
  """

  # Creates a, b, and c/d files in the test directory. Used for creating a
  # source directory as well as verifying that the copy was performed
  # successfully.
  _TEST_FILE_PATH_PARTS = [
      ('a',),
      ('b',),
      ('c', 'd')
  ]
  _TEST_FILE_PATH_PARTS_LATIN = [
      (_TEST_LATIN + '-a',),
      (_TEST_LATIN + '-b',),
      (_TEST_LATIN + '-c', _TEST_LATIN + '-d')
  ]
  _TEST_FILE_PATH_PARTS_UNICODE = [
      (_TEST_UNICODE + '-a',),
      (_TEST_UNICODE + '-b',),
      (_TEST_UNICODE + '-c', _TEST_UNICODE + '-d')
  ]

  def _AssertWritable(self, *path_parts):
    path = os.path.join(*path_parts)
    try:
      with open(path, 'w') as f:
        f.write('test data')
    except (IOError, OSError):
      self.fail('[{}] is not writable.'.format(path))

  def _SetUpSrcDst(self, file_path_parts, src='src', dst='dst'):
    temp_dir = file_utils.TemporaryDirectory()
    self.addCleanup(temp_dir.Close)

    self.temp_path = temp_dir.path
    src_dir = os.path.join(self.temp_path, src)
    dst_dir = os.path.join(self.temp_path, dst)

    for path_parts in file_path_parts:
      dirname = os.path.join(src_dir, *path_parts[:-1])
      filename = path_parts[-1]
      self.Touch(dirname, filename, makedirs=True)

    return src_dir, dst_dir

  def _AssertTestFilesExist(self, path, file_path_parts):
    for path_parts in file_path_parts:
      self.AssertFileExists(path, *path_parts)

  def _CopyTreeTest(self, file_path_parts, src='src', dst='dst'):
    src_dir, dst_dir = self._SetUpSrcDst(file_path_parts, src=src, dst=dst)
    file_utils.CopyTree(src_dir, dst_dir)
    self._AssertTestFilesExist(dst_dir, file_path_parts)

  def testCopyTree(self):
    """Tests basic copytree functionality.

    shutil.copytree would pass this as well.
    """
    self._CopyTreeTest(self._TEST_FILE_PATH_PARTS)

  @test_case.Filters.RunOnlyIf(FilesystemSupportsNonAsciiPaths(), 'LATIN')
  def testCopyTreeLatinPaths(self):
    self._CopyTreeTest(self._TEST_FILE_PATH_PARTS_LATIN)

  @test_case.Filters.RunOnlyIf(FilesystemSupportsNonAsciiPaths(), 'LATIN')
  def testCopyTreeLatinSrcLATINPaths(self):
    self._CopyTreeTest(self._TEST_FILE_PATH_PARTS_LATIN, src=_TEST_LATIN)

  @test_case.Filters.RunOnlyIf(FilesystemSupportsNonAsciiPaths(), 'LATIN')
  def testCopyTreeLatinDstLATINPaths(self):
    self._CopyTreeTest(self._TEST_FILE_PATH_PARTS_LATIN, dst=_TEST_LATIN)

  @test_case.Filters.DoNotRunOnWindows('mbcs is 8-bit!')
  @test_case.Filters.RunOnlyIf(FilesystemSupportsNonAsciiPaths(), 'UNICODE')
  def testCopyTreeUnicodePaths(self):
    self._CopyTreeTest(self._TEST_FILE_PATH_PARTS_UNICODE)

  @test_case.Filters.DoNotRunOnWindows('mbcs is 8-bit!')
  @test_case.Filters.RunOnlyIf(FilesystemSupportsNonAsciiPaths(), 'UNICODE')
  def testCopyTreeUnicodeSrcUnicodePaths(self):
    self._CopyTreeTest(self._TEST_FILE_PATH_PARTS_UNICODE, src=_TEST_UNICODE)

  @test_case.Filters.DoNotRunOnWindows('mbcs is 8-bit!')
  @test_case.Filters.RunOnlyIf(FilesystemSupportsNonAsciiPaths(), 'UNICODE')
  def testCopyTreeUnicodeDstUnicodePaths(self):
    self._CopyTreeTest(self._TEST_FILE_PATH_PARTS_UNICODE, dst=_TEST_UNICODE)

  def testCopyTree_ReadOnlySource(self):
    file_path_parts = self._TEST_FILE_PATH_PARTS
    src_dir, dst_dir = self._SetUpSrcDst(file_path_parts)
    try:
      _ChmodRecursive(src_dir, 0o555)  # 555 for read-only
      file_utils.CopyTree(src_dir, dst_dir)
      self._AssertTestFilesExist(dst_dir, file_path_parts)
      # Check that copied files *and* some new files in the directory can be
      # written to.
      for path_parts in file_path_parts + [('c', 'e'), ('f',)]:
        self._AssertWritable(os.path.join(dst_dir, *path_parts))
    finally:
      _ChmodRecursive(self.temp_path, 0o755)  # 755 for writable (by owner)


class TemporaryDirectoryTest(test_case.Base):

  def testCreateAndDestroy(self):
    t = file_utils.TemporaryDirectory()
    name = t.path
    self.assertTrue(os.path.isdir(name))
    t.Close()
    self.assertFalse(os.path.exists(name))

  def testUsingWithStatement(self):
    with file_utils.TemporaryDirectory() as t:
      self.assertTrue(os.path.isdir(t))
    self.assertFalse(os.path.exists(t))

  def testWithException(self):
    with self.assertRaises(Exception):
      with file_utils.TemporaryDirectory() as t:
        self.assertTrue(os.path.isdir(t))
        raise Exception('Test')
    self.assertFalse(os.path.exists(t))

  def testWithCleanupException(self):
    with self.assertRaisesRegex(ValueError, 'Close Error'):
      tmp_dir = file_utils.TemporaryDirectory()
      with tmp_dir as t:
        close_mock = self.StartObjectPatch(tmp_dir, 'Close')
        close_mock.side_effect = ValueError('Close Error')
    self.assertTrue(os.path.isdir(t))
    file_utils.RmTree(t)

  @test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/72871195')
  def testWithCleanupExceptionWhileAnotherException(self):
    with self.assertRaisesRegex(
        RuntimeError,
        re.escape('ValueError: Close Error\n'
                  'while another exception was active '
                  '<type \'exceptions.RuntimeError\'> [Another Error]')):
      tmp_dir = file_utils.TemporaryDirectory()
      with tmp_dir as t:
        close_mock = self.StartObjectPatch(tmp_dir, 'Close')
        close_mock.side_effect = ValueError('Close Error')
        raise RuntimeError('Another Error')
    self.assertTrue(os.path.isdir(t))
    file_utils.RmTree(t)
    self.assertFalse(os.path.isdir(t))


@test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/72871195')
class TemporaryDirectoryUnicodeTest(test_case.Base):

  def testWithCleanupExceptionWhileAnotherExceptionUnicode(self):
    try:
      tmp_dir = file_utils.TemporaryDirectory()
      with tmp_dir as t:
        close_mock = self.StartObjectPatch(tmp_dir, 'Close')
        close_mock.side_effect = ValueError('Close Ṳᾔḯ¢◎ⅾℯ Error')
        raise RuntimeError('Another Ṳᾔḯ¢◎ⅾℯ Error')
    except RuntimeError as e:
      self.assertRegexpMatches(
          six.text_type(e),
          re.escape('ValueError: Close '
                    '\\u1e72\\u1f94\\u1e2f\\xa2\\u25ce\\u217e\\u212f Error\n'
                    'while another exception was active '
                    "<type 'exceptions.RuntimeError'> [Another Ṳᾔḯ¢◎ⅾℯ Error]")
      )
    self.assertTrue(os.path.isdir(t))
    file_utils.RmTree(t)
    self.assertFalse(os.path.isdir(t))

  def testWithCleanupExceptionWhileAnotherExceptionUnicodeEncoded(self):
    try:
      tmp_dir = file_utils.TemporaryDirectory()
      with tmp_dir as t:
        close_mock = self.StartObjectPatch(tmp_dir, 'Close')
        close_mock.side_effect = ValueError(
            'Close Ṳᾔḯ¢◎ⅾℯ Error'.encode('utf8'))
        raise RuntimeError('Another Ṳᾔḯ¢◎ⅾℯ Error'.encode('utf8'))
    except RuntimeError as e:
      self.assertRegexpMatches(
          six.text_type(e),
          re.escape('ValueError: Close Ṳᾔḯ¢◎ⅾℯ Error\n'
                    'while another exception was active '
                    "<type 'exceptions.RuntimeError'> [Another Ṳᾔḯ¢◎ⅾℯ Error]")
      )
    self.assertTrue(os.path.isdir(t))
    file_utils.RmTree(t)
    self.assertFalse(os.path.isdir(t))


class MakeDirTest(test_case.Base):

  def SetUp(self):
    self.temp_dir = file_utils.TemporaryDirectory()
    self.temp_dir.__enter__()
    self.path = os.path.join(self.temp_dir.path, 'subdir')

  def TearDown(self):
    self.temp_dir.__exit__(None, None, None)

  def testMakeDir(self):
    self.assertFalse(os.path.exists(self.path))
    file_utils.MakeDir(self.path)
    self.assertTrue(os.path.exists(self.path))
    file_utils.MakeDir(self.path)
    self.assertTrue(os.path.exists(self.path))

  def testMakeDirFileExists(self):
    filepath = os.path.join(self.temp_dir.path, 'file')
    self.Touch(self.temp_dir.path, 'file')
    with self.assertRaisesRegex(
        file_utils.Error,
        re.escape(('Could not create directory [{0}]: A file exists at that '
                   'location.\n\n').format(filepath))):
      file_utils.MakeDir(filepath)

  @test_case.Filters.DoNotRunOnWindows(
      "It's non-trivial to create a directory that you can't write to, as long "
      "as you own it")
  def testMakeDirBadPermissions(self):
    os.chmod(self.temp_dir.path, stat.S_IREAD)
    try:
      with self.assertRaisesRegex(
          file_utils.Error,
          re.escape(('Could not create directory [{0}]: Permission denied.\n\n'
                     'Please verify that you have permissions to write to the '
                     'parent directory.').format(self.path))):
        file_utils.MakeDir(self.path)
    finally:
      os.chmod(self.temp_dir.path, stat.S_IREAD | stat.S_IWRITE)


class RmTreeTest(test_case.Base, test_case.WithOutputCapture):

  @test_case.Filters.RunOnlyOnWindows
  def testRmTreeWithWindowsError(self):
    wait_mock = self.StartObjectPatch(file_utils, '_WaitForRetry')
    rmdir_mock = self.StartObjectPatch(os, 'rmdir')
    rmdir_mock.side_effect = WindowsError(32, 'File access error')  # pylint: disable=undefined-variable
    temp_dir = file_utils.TemporaryDirectory()
    # The TemporaryDirectory is used without a "with" statement here because
    # it will call RmTree when it closes, raising the mocked error
    temp_dir.__enter__()
    with self.assertRaises(WindowsError):  # pylint: disable=undefined-variable
      self.RmTree(temp_dir.path)
    # Check that we retry after this error
    self.assertEqual(wait_mock.call_count, file_utils.NUM_RETRIES)
    self.assertTrue(os.path.isdir(temp_dir.path))

  @test_case.Filters.RunOnlyOnWindows
  def testRmTreeWithWindowsErrorNoRetry(self):
    wait_mock = self.StartObjectPatch(file_utils, '_WaitForRetry')
    rmdir_mock = self.StartObjectPatch(os, 'rmdir')
    rmdir_mock.side_effect = WindowsError(47, 'Random error')  # pylint: disable=undefined-variable
    temp_dir = file_utils.TemporaryDirectory()
    temp_dir.__enter__()
    with self.assertRaises(WindowsError):  # pylint: disable=undefined-variable
      self.RmTree(temp_dir.path)
    # Test that we don't retry the operation that raised an error
    # if its code isn't in file_utils.RETRY_ERROR_CODES
    self.assertEqual(wait_mock.call_count, 0)
    self.assertTrue(os.path.isdir(temp_dir.path))

  @test_case.Filters.RunOnlyOnWindows
  def testRmTreeWithBadPermissions(self):
    temp_dir = file_utils.TemporaryDirectory()
    temp_dir.__enter__()
    os.chmod(temp_dir.path, stat.S_IREAD)
    # Check we have successfully changed permissions here
    with self.assertRaises(WindowsError):  # pylint: disable=undefined-variable
      shutil.rmtree(temp_dir.path)
    self.RmTree(temp_dir.path)
    # Check that RmTree succeeds on read-only directory
    self.assertFalse(os.path.isdir(temp_dir.path))

  def testRmTreeWithOSError(self):
    wait_mock = self.StartObjectPatch(file_utils, '_WaitForRetry')
    rmdir_mock = self.StartObjectPatch(os, 'rmdir')
    rmdir_mock.side_effect = OSError
    temp_dir = file_utils.TemporaryDirectory()
    temp_dir.__enter__()
    with self.assertRaises(OSError):
      file_utils.RmTree(temp_dir.path)
    # Check that we don't retry after this error
    self.assertEqual(wait_mock.call_count, 0)
    self.assertTrue(os.path.isdir(temp_dir.path))


class WritePermissionsTest(test_case.Base):

  @test_case.Filters.DoNotRunOnWindows
  def testHasPermissions(self):
    with file_utils.TemporaryDirectory() as t:
      self.assertTrue(file_utils.HasWriteAccessInDir(t))
      try:
        os.chmod(t, 0o600)
        self.assertFalse(file_utils.HasWriteAccessInDir(t))
        os.chmod(t, 0o500)
        self.assertFalse(file_utils.HasWriteAccessInDir(t))
        os.chmod(t, 0o400)
        self.assertFalse(file_utils.HasWriteAccessInDir(t))
      finally:
        os.chmod(t, 0o755)
    with self.assertRaisesRegex(ValueError, 'is not a directory'):
      file_utils.HasWriteAccessInDir(self.RandomFileName())


class DirectoryFindTest(test_case.Base):

  def testFindDirectoryContaining(self):
    with file_utils.TemporaryDirectory() as t:
      starting_dir = os.path.join(t, 'foo', 'bar', 'baz')
      file_utils.MakeDir(starting_dir)

      to_find = 'to_find'
      file_utils.MakeDir(os.path.join(t, 'foo', to_find))
      self.Touch(os.path.join(t, 'foo', 'bar'), to_find)

      real_foo = os.path.realpath(os.path.join(t, 'foo'))
      self.assertEqual(
          real_foo,
          file_utils.FindDirectoryContaining(starting_dir, to_find))
      self.assertEqual(
          real_foo,
          file_utils.FindDirectoryContaining(os.path.join(t, 'foo'), to_find))
      self.assertEqual(
          None,
          file_utils.FindDirectoryContaining(starting_dir,
                                             self.RandomFileName()))


class IsDirAncestorOfTest(test_case.Base):
  """Tests for file_utils.IsDirAncestorOf.

  Sets up a temporary directory with the following contents (relative to the
  root of the temporary directory):

  * /
  * /file.txt
  * /dir/
  * /dir/file.txt
  * /dir/subdir/
  * /dir/subdir/file.txt

  Optionally (because symlinking requires special permissions on Windows), the
  following symbolic links are added:

  * /link.txt -> /dir/subdir/file.txt
  * /link -> /dir

  Which means that the following links are valid:

  * /link/file.txt -> /dir/file.txt
  * /link/subdir/file.txt -> /dir/subdir/file.txt

  The tests in this class check whether various sets of files and directories
  are reported as "in" other directories. They're very comprehensive, because
  there's a lot of edge cases around symlinks.

  The tests refer to the short, Unix-style paths of all of these files for
  concision, but they are expanded to the correct full paths on non-Unix
  systems.
  """

  def _GetFullPath(self, path):
    """Convert from short Unix-style path name to actual path on disk."""
    return os.path.join(self.temp_dir.path, *path.split('/'))

  def SetUp(self):
    self.temp_dir = file_utils.TemporaryDirectory()
    self.temp_dir.__enter__()
    self.files = [
        'file.txt',
        '/dir/file.txt',
        '/dir/subdir/file.txt'
    ]
    if FilesystemSupportsNonAsciiPaths():
      self.files.append('/Ṳᾔḯ-dir/Ṳᾔḯ-subdir/Ṳᾔḯ-file.txt')
    for file_ in self.files:
      path = self._GetFullPath(file_)
      file_utils.MakeDir(os.path.dirname(path))
      self.Touch(os.path.dirname(path), os.path.basename(path))

  def AssertPathInDirectory(self, path, directory):
    self.assertTrue(file_utils.IsDirAncestorOf(self._GetFullPath(directory),
                                               self._GetFullPath(path)),
                    '[{0}] should be "in" [{1}]'.format(
                        console_attr.SafeText(path),
                        console_attr.SafeText(directory)))

  def AssertPathNotInDirectory(self, path, directory):
    self.assertFalse(file_utils.IsDirAncestorOf(self._GetFullPath(directory),
                                                self._GetFullPath(path)),
                     '[{0}] should not be "in" [{1}]'.format(
                         console_attr.SafeText(path),
                         console_attr.SafeText(directory)))

  def TearDown(self):
    self.temp_dir.__exit__(None, None, None)

  def _MakeLinks(self):
    # We don't do this in SetUp because symlinking on Windows requires special
    # permission
    links = [
        ('/dir', '/link'),
        ('/dir/subdir/file.txt', '/link.txt')
    ]
    for src, dst in links:
      os.symlink(self._GetFullPath(src),
                 self._GetFullPath(dst))

  def testFileInDirectory_AllFilesInRoot(self):
    # All files should be in root directory.
    for file_ in self.files:
      self.AssertPathInDirectory(file_, '/')

  def testPathInDirectory_FilesInDirectories(self):
    self.AssertPathInDirectory('/file.txt', '/')
    self.AssertPathNotInDirectory('/file.txt', '/dir')
    self.AssertPathNotInDirectory('/file.txt', '/dir/subdir')

    self.AssertPathInDirectory('/dir/file.txt', '/')
    self.AssertPathInDirectory('/dir/file.txt', '/dir')
    self.AssertPathNotInDirectory('/dir/file.txt', '/dir/subdir')

    self.AssertPathInDirectory('/dir/subdir/file.txt', '/')
    self.AssertPathInDirectory('/dir/subdir/file.txt', '/dir')
    self.AssertPathInDirectory('/dir/subdir/file.txt', '/dir/subdir')

  @test_case.Filters.RunOnlyIf(FilesystemSupportsNonAsciiPaths(), 'UNICODE')
  def testPathInDirectory_FilesInDirectories_Unicode(self):
    self.AssertPathInDirectory('/Ṳᾔḯ-dir/Ṳᾔḯ-subdir/Ṳᾔḯ-file.txt', '/')
    self.AssertPathInDirectory('/Ṳᾔḯ-dir/Ṳᾔḯ-subdir/Ṳᾔḯ-file.txt',
                               '/Ṳᾔḯ-dir')
    self.AssertPathInDirectory('/Ṳᾔḯ-dir/Ṳᾔḯ-subdir/Ṳᾔḯ-file.txt',
                               '/Ṳᾔḯ-dir/Ṳᾔḯ-subdir')

  def testPathInDirectory_DirectoriesInDirectories(self):
    self.AssertPathInDirectory('/', '/')
    self.AssertPathNotInDirectory('/', '/dir')
    self.AssertPathNotInDirectory('/', '/dir/subdir')

    self.AssertPathInDirectory('/dir', '/')
    self.AssertPathInDirectory('/dir', '/dir')
    self.AssertPathNotInDirectory('/dir', '/dir/subdir')

    self.AssertPathInDirectory('/dir/subdir', '/')
    self.AssertPathInDirectory('/dir/subdir', '/dir')
    self.AssertPathInDirectory('/dir/subdir', '/dir/subdir')

  @test_case.Filters.RunOnlyIf(FilesystemSupportsNonAsciiPaths(), 'UNICODE')
  def testPathInDirectory_DirectoriesInDirectories_Unicode(self):
    self.AssertPathNotInDirectory('/', '/Ṳᾔḯ-dir')
    self.AssertPathNotInDirectory('/', '/Ṳᾔḯ-dir/Ṳᾔḯ-subdir')

    self.AssertPathInDirectory('/Ṳᾔḯ-dir', '/')
    self.AssertPathInDirectory('/Ṳᾔḯ-dir', '/Ṳᾔḯ-dir')
    self.AssertPathNotInDirectory('/Ṳᾔḯ-dir', '/Ṳᾔḯ-dir/Ṳᾔḯ-subdir')

    self.AssertPathInDirectory('/Ṳᾔḯ-dir/Ṳᾔḯ-subdir', '/')
    self.AssertPathInDirectory('/Ṳᾔḯ-dir/Ṳᾔḯ-subdir', '/Ṳᾔḯ-dir')
    self.AssertPathInDirectory('/Ṳᾔḯ-dir/Ṳᾔḯ-subdir', '/Ṳᾔḯ-dir/Ṳᾔḯ-subdir')

  @test_case.Filters.DoNotRunOnWindows
  def testPathInDirectory_LinkedFileInTargetParent(self):
    self._MakeLinks()

    self.AssertPathInDirectory('/link.txt', '/')
    self.AssertPathInDirectory('/link.txt', '/dir')
    self.AssertPathInDirectory('/link.txt', '/dir/subdir')

  @test_case.Filters.DoNotRunOnWindows
  def testPathInDirectory_LinkedDirectoryContentsInTargetParent(self):
    self._MakeLinks()

    self.AssertPathInDirectory('/link/file.txt', '/')
    self.AssertPathInDirectory('/link/file.txt', '/dir')
    self.AssertPathNotInDirectory('/link/file.txt', '/dir/subdir')

    self.AssertPathInDirectory('/link/subdir', '/')
    self.AssertPathInDirectory('/link/subdir', '/dir')
    self.AssertPathInDirectory('/link/subdir', '/dir/subdir')

    self.AssertPathInDirectory('/link/subdir/file.txt', '/')
    self.AssertPathInDirectory('/link/subdir/file.txt', '/dir')
    self.AssertPathInDirectory('/link/subdir/file.txt', '/dir/subdir')

  @test_case.Filters.DoNotRunOnWindows
  def testPathInDirectory_LinkedDirectoryContentsInLinkDirectory(self):
    self._MakeLinks()

    self.AssertPathInDirectory('/link', '/link')
    self.AssertPathInDirectory('/link/file.txt', '/link')
    self.AssertPathInDirectory('/link/subdir', '/link')
    self.AssertPathInDirectory('/link/subdir/file.txt', '/link')

    self.AssertPathInDirectory('/link/subdir', '/link/subdir')
    self.AssertPathInDirectory('/link/subdir/file.txt', '/link/subdir')

  @test_case.Filters.DoNotRunOnWindows
  def testPathInDirectory_TargetContentsInLinkDirectory(self):
    self._MakeLinks()

    self.AssertPathNotInDirectory('/file.txt', '/link')

    self.AssertPathInDirectory('/dir', '/link')
    self.AssertPathInDirectory('/dir/file.txt', '/link')
    self.AssertPathInDirectory('/dir/subdir', '/link')
    self.AssertPathInDirectory('/dir/subdir/file.txt', '/link')

    self.AssertPathInDirectory('/dir/subdir', '/link/subdir')
    self.AssertPathInDirectory('/dir/subdir/file.txt', '/link/subdir')

  def testPathInDirectory_GiveFileInsteadOfDirectory(self):
    self.assertRaises(ValueError, file_utils.IsDirAncestorOf,
                      self._GetFullPath('/file.txt'),
                      self._GetFullPath('/file.txt'))

  def testPathInDirectory_DifferentDrives(self):
    self.assertFalse(file_utils.IsDirAncestorOf(self._GetFullPath('/'),
                                                r'Z:\foo\bar'))
    self.assertFalse(file_utils.IsDirAncestorOf(self._GetFullPath('/'),
                                                r'\\baz\qux'))


def Touch(path, contents=''):
  with open(path, 'w') as fp:
    fp.write(contents)
  return path


class SearchOnPathTests(test_case.Base):
  """Tests of checking the path for old executables."""

  def testSearchOnPath(self):
    with file_utils.TemporaryDirectory() as t:
      dir1 = os.path.join(t, 'dir1')
      dir2 = os.path.join(t, 'dir2')
      os.mkdir(dir1)
      os.mkdir(dir2)
      filea1 = os.path.join(dir1, 'filea')
      Touch(filea1)
      filea2 = os.path.join(dir2, 'filea')
      Touch(filea2)
      fileb1 = os.path.join(dir1, 'fileb')
      Touch(fileb1)

      path_both = os.pathsep.join([dir1, dir2])

      self.assertEqual([filea1],
                       file_utils.SearchForExecutableOnPath('filea', dir1))
      self.assertEqual([], file_utils.SearchForExecutableOnPath('fileb', dir2))
      self.assertEqual(
          [filea1, filea2],
          file_utils.SearchForExecutableOnPath('filea', path_both))
      self.assertEqual(
          [fileb1],
          file_utils.SearchForExecutableOnPath('fileb', path_both))


class FindOnPathTests(test_case.Base):
  """Tests finding executables with optional extension on PATH."""

  def SetUp(self):
    tmp_dir = file_utils.TemporaryDirectory(change_to=True)
    self.addCleanup(tmp_dir.Close)

  def Populate(self, path, executable):
    path_str = os.path.join(*path)
    Touch(path_str)
    if executable:
      st = os.stat(path_str)
      # On Windows has no effect
      os.chmod(path_str, st.st_mode | stat.S_IEXEC)
    return path_str

  def testNoPath(self):
    self.assertIsNone(file_utils.FindExecutableOnPath(
        'ls', path='', pathext=('',)))

  def testEmptyDir(self):
    self.assertIsNone(file_utils.FindExecutableOnPath(
        'ls', path='.', pathext=('',)))

  def testSingleFile(self):
    file_path = self.Populate(['foo'], True)
    self.assertEqual(
        file_path,
        file_utils.FindExecutableOnPath(file_path, path='.', pathext=('',)))

  def testInMultiplePaths(self):
    os.mkdir('bin')
    os.mkdir('sbin')
    self.Populate(['bin', 'foo'], True)
    self.Populate(['bin', 'bar'], True)
    self.Populate(['sbin', 'foo'], True)
    self.assertEqual(
        os.path.join('sbin', 'foo'),
        file_utils.FindExecutableOnPath(
            'foo', path=os.pathsep.join(['sbin', 'bin']), pathext=('',)))
    self.assertEqual(
        os.path.join('bin', 'bar'),
        file_utils.FindExecutableOnPath(
            'bar', path=os.pathsep.join(['sbin', 'bin']), pathext=('',)))
    self.StartEnvPatch({'PATH': os.pathsep.join(['sbin', 'bin'])})
    self.assertEqual(
        os.path.join('sbin', 'foo'),
        file_utils.FindExecutableOnPath('foo', pathext=('',)))

  def testSinglePathExt(self):
    self.Populate(['foo.exe'], True)
    self.assertEqual(
        'foo.exe',
        file_utils.FindExecutableOnPath('foo', path='.', pathext=('.exe',)))
    self.assertIsNone(
        file_utils.FindExecutableOnPath('foo', path='.', pathext=('',)))

  def testMultiplePathExt(self):
    self.Populate(['foo'], True)
    self.Populate(['foo.exe'], True)
    self.Populate(['foo.bat'], True)
    self.Populate(['foo.exe.bat'], True)
    self.assertEqual(
        'foo',
        file_utils.FindExecutableOnPath(
            'foo', path='.', pathext=('', '.exe', '.bat')))
    self.assertEqual(
        'foo.bat',
        file_utils.FindExecutableOnPath(
            'foo', path='.', pathext=('.bat', '.exe', '')))

  def testWindowsDefaultExtensions(self):
    self.Populate(['foo'], True)
    self.Populate(['foo.exe'], True)
    self.Populate(['bar.sh'], True)
    self.Populate(['bar.cmd'], True)

    self.StartObjectPatch(
        platforms.OperatingSystem, 'Current',
        return_value=platforms.OperatingSystem.WINDOWS)
    self.assertEqual(
        'foo.exe',
        file_utils.FindExecutableOnPath('foo', path='.'))
    self.assertEqual(
        'bar.cmd',
        file_utils.FindExecutableOnPath('bar', path='.'))

  def testUnixDefaultExtensions(self):
    self.Populate(['foo'], True)
    self.Populate(['foo.exe'], True)
    self.Populate(['bar.sh'], True)
    self.Populate(['bar.cmd'], True)

    self.StartObjectPatch(
        platforms.OperatingSystem, 'Current',
        return_value=platforms.OperatingSystem.LINUX)
    self.assertEqual(
        'foo',
        file_utils.FindExecutableOnPath('foo', path='.'))
    self.assertEqual(
        'bar.sh',
        file_utils.FindExecutableOnPath('bar', path='.'))

  @test_case.Filters.DoNotRunOnWindows
  def testExecutableAttribute(self):
    # On Windows executable attribute is always True.
    self.Populate(['foo'], False)
    self.assertIsNone(
        file_utils.FindExecutableOnPath('foo', path='.', pathext=('',)))
    self.Populate(['foo'], True)
    self.assertEqual(
        'foo',
        file_utils.FindExecutableOnPath('foo', path='.', pathext=('',)))

  def testExtensionHasPriorityOverPath(self):
    os.mkdir('usr')
    os.mkdir('home')
    self.Populate(['usr', 'foo.ext1'], True)
    self.Populate(['home', 'foo.ext2'], True)
    self.assertEqual(
        os.path.join('usr', 'foo.ext1'),
        file_utils.FindExecutableOnPath(
            'foo',
            path=os.pathsep.join(['home', 'usr']),
            pathext=('.ext1', '.ext2')))

  def testQuotedPath(self):
    os.mkdir('program files')
    os.mkdir('home')
    self.Populate(['program files', 'foo.ext1'], True)
    self.Populate(['home', 'foo.ext2'], True)
    self.assertEqual(
        os.path.join('program files', 'foo.ext1'),
        file_utils.FindExecutableOnPath(
            'foo',
            path=os.pathsep.join(['"program files"', 'usr']),
            pathext=('.ext1', '.ext2')))

  def testNoExtensionInExecutableArg(self):
    with self.assertRaisesRegex(ValueError, r'must not have an extension'):
      file_utils.FindExecutableOnPath('foo.exe')

  def testAllowExtensionInExecutableArg(self):
    self.Populate(['foo.sh'], True)
    self.assertEqual(
        'foo.sh',
        file_utils.FindExecutableOnPath(
            'foo.sh', path='.', pathext=('',), allow_extensions=True))

  def testNoPathInExecutableArg(self):
    with self.assertRaisesRegex(ValueError, r'must not have a path'):
      file_utils.FindExecutableOnPath('bin/foo')

  def testNoStringAsPathextArg(self):
    with self.assertRaisesRegex(ValueError, r'got a string'):
      file_utils.FindExecutableOnPath('foo', pathext='x')


class ChecksumTest(test_case.Base, test_case.WithOutputCapture):

  def testAddFile(self):
    with file_utils.TemporaryDirectory() as t:
      contents = b'ascii\n'
      f = os.path.join(t, 'foo')
      with open(f, 'wb') as fp:
        fp.write(contents)
      digest1 = file_utils.Checksum().AddFileContents(f).HexDigest()
      digest2 = file_utils.Checksum().AddContents(contents).HexDigest()
      self.assertEqual(digest1, digest2)
      # Verify no unicode equality failure warnings.
      self.AssertOutputEquals('')
      self.AssertErrEquals('')

  def testAddFileUnicode(self):
    with file_utils.TemporaryDirectory() as t:
      contents = 'Ṳᾔḯ¢◎ⅾℯ\n'
      encoding = 'utf-8'
      f = os.path.join(t, 'foo')
      with open(f, 'wb') as fp:
        fp.write(contents.encode(encoding))
      digest1 = file_utils.Checksum().AddFileContents(f).HexDigest()
      digest2 = file_utils.Checksum().AddContents(
          contents.encode(encoding)).HexDigest()
      self.assertEqual(digest1, digest2)
      # Verify no unicode equality failure warnings.
      self.AssertOutputEquals('')
      self.AssertErrEquals('')

  def _MakeTree(self, root, extra_contents='', extra_file=False,
                alt_file_link=False, alt_dir_link=False, broken_link=False):
    os.mkdir(root)
    a = os.path.join(root, 'a')
    b = os.path.join(root, 'b')
    c = os.path.join(root, 'c')
    for item in [a, b, c]:
      os.mkdir(item)

    Touch(os.path.join(a, 'foo'), 'some stuff' + extra_contents)
    Touch(os.path.join(a, 'bar'), 'some other stuff')
    if extra_file:
      Touch(os.path.join(a, 'baz'), 'even more stuff')

    if alt_file_link:
      os.symlink('a/bar', os.path.join(root, 'filelink'))
    else:
      os.symlink('a/foo', os.path.join(root, 'filelink'))

    if alt_dir_link:
      os.symlink('b', os.path.join(root, 'linkdir'))
    else:
      os.symlink('a', os.path.join(root, 'linkdir'))

    if broken_link:
      os.symlink('DoesNotExist', os.path.join(root, 'broken'))

    return root

  @test_case.Filters.DoNotRunOnWindows
  @test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/72871195')
  def testDirectoryTrees(self):
    with file_utils.TemporaryDirectory() as t:
      roots = [
          self._MakeTree(os.path.join(t, 'root0')),
          self._MakeTree(os.path.join(t, 'root1')),
          self._MakeTree(os.path.join(t, 'root2'), extra_contents='asdf'),
          self._MakeTree(os.path.join(t, 'root3'), extra_file=True),
          self._MakeTree(os.path.join(t, 'root4'), alt_dir_link=True),
          self._MakeTree(os.path.join(t, 'root5'), alt_file_link=True),
          self._MakeTree(os.path.join(t, 'root6'), broken_link=True),
      ]

      digests = [file_utils.Checksum().AddDirectory(root).HexDigest()
                 for root in roots]

      self.assertEqual(digests[0], digests[1])
      for i in range(2, len(roots)):
        self.assertNotEqual(digests[0], digests[i],
                            'Failed for root: ' + str(i))

  @test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/72871195')
  def testSingleFile(self):
    """Test FromSingleFile and HashSingleFile methods."""
    with file_utils.TemporaryDirectory() as t:
      f = os.path.join(t, 'foo')
      with open(f, 'w') as fp:
        fp.write('some stuff')
      digest1 = file_utils.Checksum.HashSingleFile(f)
      checksum = file_utils.Checksum.FromSingleFile(f)
      digest2 = file_utils.Checksum().AddContents('some stuff').HexDigest()
      self.assertEqual(digest1, digest2)
      self.assertEqual(checksum.HexDigest(), digest2)


class RetryTest(test_case.Base):

  def SetUp(self):
    self.exc_info = (Exception, None, None)
    self.func = mock.MagicMock()
    self.func.side_effect = RuntimeError('fail')

    # Just don't want to actually introduce a sleep in the unit tests.
    self.StartObjectPatch(file_utils, '_WaitForRetry')
    self.retry_test_function = self.StartObjectPatch(
        file_utils, '_ShouldRetryOperation', return_value=True)

  def testRetry(self):
    result = file_utils._RetryOperation(
        self.exc_info, self.func, ('asdf', 'qwer'), self.retry_test_function)
    self.assertFalse(result)
    self.func.call_count = file_utils.NUM_RETRIES
    self.func.assert_called_with('asdf', 'qwer')
    self.retry_test_function.call_count = file_utils.NUM_RETRIES

  def testRetrySingleArg(self):
    with self.assertRaises(Exception):
      file_utils._HandleRemoveError(self.func, 'path', self.exc_info)
    self.func.call_count = file_utils.NUM_RETRIES
    self.func.assert_called_with('path')
    self.retry_test_function.call_count = file_utils.NUM_RETRIES


class FileLockTest(test_case.Base):

  def SetUp(self):
    self.locks = []

  def TearDown(self):
    for lock in self.locks:
      try:
        lock.Unlock()
      except file_utils.Error:
        pass

  def _NewFileLock(self, lockfile, timeout_secs=None):
    """Creates, registers, and return a lock that is unlocked at teardown."""
    lock = file_utils.FileLock(lockfile, timeout_secs)
    self.locks.append(lock)
    return lock

  class Locker(object):
    """Helper for attempting to acquire a lock in another thread."""

    def __init__(self, lock):
      """Constructs the locker.

      Args:
        lock: file_utils.FileLock, the lock this Locker will use. The lock
          should not be touched by other parties while the locking thread is
          running.
      """
      self.lock = lock
      self.started = False
      self.stopped = False
      # Locking succeeded if stopped=True and last_error=None.
      self.last_error = None

    def Run(self):
      """Locks the lock, blocking forever if necessary."""
      self.started = True
      try:
        self.lock.Lock()
        self.lock.Unlock()
      except file_utils.Error as e:
        self.last_error = e
      self.stopped = True

  def testLocking_NonBlocking(self):
    with file_utils.TemporaryDirectory() as temp_dir:
      lockfile = os.path.join(temp_dir, 'lockfile')
      lock1 = self._NewFileLock(lockfile, timeout_secs=0)
      lock2 = self._NewFileLock(lockfile, timeout_secs=0)

      with lock1:
        with self.assertRaises(file_utils.FileLockTimeoutError):
          lock2.Lock()

      lock2.Lock()  # Succeeds
      lock2.Unlock()

  def testLocking_BlockingNoTimeout(self):
    with file_utils.TemporaryDirectory() as temp_dir:
      lockfile = os.path.join(temp_dir, 'lockfile')
      lock1 = self._NewFileLock(lockfile)
      lock2 = self._NewFileLock(lockfile)
      lock2_locker = FileLockTest.Locker(lock2)
      r = retry.Retryer(max_wait_ms=5000)

      # With lock1 locked...
      with lock1:
        t = threading.Thread(target=lock2_locker.Run)
        t.start()
        # Wait for the thread to begin running.
        r.RetryOnResult(lambda: lock2_locker.started, should_retry_if=False,
                        sleep_ms=100)
        # The thread has started. It should not be able to acquire the lock,
        # but it should not stop trying.
        time.sleep(0.1)
        self.assertFalse(lock2_locker.stopped)

      # lock1 is released. The thread should now be able to acquire it.
      r.RetryOnResult(lambda: lock2_locker.stopped, should_retry_if=False,
                      sleep_ms=100)
      self.assertIsNone(lock2_locker.last_error)

  def testLocking_BlockingWithTimeout(self):
    with file_utils.TemporaryDirectory() as temp_dir:
      lockfile = os.path.join(temp_dir, 'lockfile')
      lock1 = self._NewFileLock(lockfile)
      lock2 = self._NewFileLock(lockfile, timeout_secs=0.5)
      lock2_locker = FileLockTest.Locker(lock2)
      r = retry.Retryer(max_wait_ms=5000)

      # With lock1 locked...
      with lock1:
        t = threading.Thread(target=lock2_locker.Run)
        t.start()
        # Wait for the thread to begin running.
        r.RetryOnResult(lambda: lock2_locker.started, should_retry_if=False,
                        sleep_ms=100)
        # The thread has started. It should not be able to acquire the lock,
        # and should stop trying after the timeout.
        r.RetryOnResult(lambda: lock2_locker.stopped, should_retry_if=False,
                        sleep_ms=100)
        # The thread should have encountered a timeout error.
        self.assertIsInstance(lock2_locker.last_error,
                              file_utils.FileLockTimeoutError)

  def testReentrancy(self):
    with file_utils.TemporaryDirectory() as temp_dir:
      lockfile = os.path.join(temp_dir, 'lockfile')
      lock = self._NewFileLock(lockfile, timeout_secs=0.5)
      # This test passes as long as no exceptions are thrown.
      lock.Lock()
      try:
        lock.Lock()
        lock.Unlock()
      finally:
        lock.Unlock()

  def testRelocking(self):
    with file_utils.TemporaryDirectory() as temp_dir:
      lockfile = os.path.join(temp_dir, 'lockfile')
      lock = self._NewFileLock(lockfile, timeout_secs=0.5)
      # This test passes as long as no exceptions are thrown.
      lock.Lock()
      lock.Unlock()
      lock.Lock()
      lock.Unlock()

  def testNoParentDirectory(self):
    lockfile = os.path.join('no', 'such', 'directory', 'lockfile')
    with self.assertRaises(file_utils.FileLockLockingError):
      with self._NewFileLock(lockfile):
        pass

  def testExceptionInContext(self):
    with file_utils.TemporaryDirectory() as temp_dir:
      with self.assertRaises(ValueError) as ctx:
        lockfile = os.path.join(temp_dir, 'lockfile')
        with self._NewFileLock(lockfile):
          raise ValueError('foo')

      self.assertEqual(six.text_type(ctx.exception), 'foo')


class FileInBinaryModeTest(test_case.Base):

  def SetUp(self):
    self.dir = file_utils.TemporaryDirectory()

  @test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/72871195')
  def testReading(self):
    contents = b'foo\nbar\r\nbaz\r\r'
    filename = self.Touch(self.dir.path, contents=contents)

    # NB: opening in text mode; on Windows, this would cause EOL marker
    # alterations...
    with open(filename, 'r') as f:
      # ...but _FileInBinaryMode should prevent them.
      with file_utils._FileInBinaryMode(f):
        self.assertEqual(f.read(), contents)

  @test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/72871195')
  def testWriting(self):
    contents = b'foo\nbar\r\nbaz\r\r'
    filename = os.path.join(self.dir.path, self.RandomFileName())

    # NB: opening in text mode; on Windows, this would cause EOL marker
    # alterations...
    with open(filename, 'w') as f:
      # ...but _FileInBinaryMode should prevent them.
      with file_utils._FileInBinaryMode(f):
        f.write(contents)
        # Flush to force content to be written out with the correct mode.
        f.flush()

    with open(filename, 'rb') as f:
      self.assertEqual(f.read(), contents)

  @test_case.Filters.RunOnlyOnWindows('Testing platform-specific syscalls')
  @test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/72871195')
  def testCleanupOnWindows(self):
    filename = self.Touch(self.dir.path, contents='foo\nbar\r\nbaz\r\r')

    # pylint: disable=g-import-not-at-top
    import msvcrt
    with open(filename, 'r') as f:
      # The _setmode syscall returns the previous mode. Use this to verify that
      # f is in text mode.
      self.assertEqual(msvcrt.setmode(f.fileno(), os.O_TEXT), os.O_TEXT)
      with file_utils._FileInBinaryMode(f):
        self.assertEqual(msvcrt.setmode(f.fileno(), os.O_BINARY), os.O_BINARY)
      # verify the mode is reverted outside of _FileInBinaryMode.
      self.assertEqual(msvcrt.setmode(f.fileno(), os.O_TEXT), os.O_TEXT)

  def testStringIO(self):
    contents = 'foo\nbar\r\nbaz\r\r'
    s = io.StringIO(contents)
    with file_utils._FileInBinaryMode(s):
      self.assertEqual(s.read(), contents)


class ReadFileContentsTest(test_case.Base):

  def SetUp(self):
    self.dir = file_utils.TemporaryDirectory()

  def testSuccessfulRead(self):
    filename = self.Touch(self.dir.path, contents='abc123')
    contents = file_utils.ReadFileContents(filename)
    self.assertEqual(contents, 'abc123')

  def testBinaryMode(self):
    # self.Touch writes with mode 'w+b'.
    filename = self.Touch(self.dir.path, contents=b'foo\nbar\r\nbaz\r\r')

    contents = file_utils.ReadBinaryFileContents(filename)
    # If read in text mode, this fails on Windows due to EOL marker
    # manipulation. See the 'On Windows...' note in the docs for more info:
    # https://docs.python.org/2/tutorial/inputoutput.html#reading-and-writing-files
    self.assertEqual(contents, b'foo\nbar\r\nbaz\r\r')

  def testFileNotFound(self):
    filename = 'nonexistent'
    with self.assertRaises(file_utils.Error):
      file_utils.ReadFileContents(filename)


class GetFileOrStdinContentsTest(test_case.WithInput):

  def SetUp(self):
    self.dir = file_utils.TemporaryDirectory()

  def testGetStdinBytes(self):
    console_attr.GetConsoleAttr(encoding='utf-8', reset=True)
    self.WriteInput('ÜñîçòÐé')
    self.assertEqual(
        file_utils.ReadStdinBytes(),
        b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n')


class WriteFileContentsTest(test_case.Base):

  def SetUp(self):
    self.dir = file_utils.TemporaryDirectory()

  def testNewFile(self):
    path = os.path.join(self.dir.path, self.RandomFileName())
    contents = 'abc123'
    file_utils.WriteFileContents(path, contents, overwrite=False)
    self.AssertFileEquals(contents, path)

  def testFileCannotBeCreated(self):
    path = os.path.join(self.dir.path, 'nonexistent-dir', self.RandomFileName())
    contents = 'abc123'
    with self.assertRaises(file_utils.Error):
      file_utils.WriteFileContents(path, contents, overwrite=False)

  def testOverwrite(self):
    path = self.Touch(self.dir.path, contents='abc123')
    contents = 'def456'
    file_utils.WriteFileContents(path, contents, overwrite=True)
    self.AssertFileEquals(contents, path)

  def testCannotOverwriteByDefault(self):
    contents = 'abc123'
    path = self.Touch(self.dir.path, contents=contents)
    with self.assertRaises(file_utils.Error):
      file_utils.WriteFileContents(path, 'def456', overwrite=False)
    self.AssertFileEquals(contents, path)

  def testBinary(self):
    path = os.path.join(self.dir.path, self.RandomFileName())
    contents = b'foo\nbar\r\nbaz\r\r'
    file_utils.WriteBinaryFileContents(path, contents)
    # If written in text mode, this fails on Windows due to EOL marker
    # manipulation. See the 'On Windows...' note in the docs for more info:
    # https://docs.python.org/2/tutorial/inputoutput.html#reading-and-writing-files
    with io.open(path, 'rb') as f:
      actual_contents = f.read()
    self.assertEqual(contents, actual_contents)


class WriteFileOrStdoutContentsTest(test_case.Base,
                                    test_case.WithOutputCapture):

  def SetUp(self):
    self.dir = file_utils.TemporaryDirectory()

  def testFileWrite(self):
    contents = 'abc123'
    path = os.path.join(self.dir.path, self.RandomFileName())
    file_utils.WriteFileContents(path, contents)
    self.AssertFileEquals(contents, path)

  def testFileWriteBinary(self):
    contents = b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n'
    path = os.path.join(self.dir.path, self.RandomFileName())
    file_utils.WriteBinaryFileContents(path, contents)
    self.assertEqual(file_utils.ReadBinaryFileContents(path), contents)

  def testFileWritePrivate(self):
    contents = 'abc123'
    path = os.path.join(self.dir.path, self.RandomFileName())
    file_utils.WriteFileContents(path, contents, private=True)
    self.AssertFileEquals(contents, path)

    mode = os.stat(path).st_mode
    if platforms.OperatingSystem.IsWindows():
      self.assertEqual(mode & 0o777, 0o666)
    else:
      # mode & 0777 strips the higher level bits that we don't care about,
      # leaving only the three permissions octals.
      self.assertEqual(mode & 0o777, 0o600)

  def testFileWriteBinaryPrivate(self):
    contents = b'abc123'
    path = os.path.join(self.dir.path, self.RandomFileName())
    file_utils.WriteBinaryFileContents(path, contents, private=True)
    self.AssertBinaryFileEquals(contents, path)

    mode = os.stat(path).st_mode
    if platforms.OperatingSystem.IsWindows():
      self.assertEqual(mode & 0o777, 0o666)
    else:
      # mode & 0777 strips the higher level bits that we don't care about,
      # leaving only the three permissions octals.
      self.assertEqual(mode & 0o777, 0o600)


class GetTreeSizeBytesTest(test_case.Base):

  def SetUp(self):
    self.dir = file_utils.TemporaryDirectory()

  def testOneFileSize(self):
    contents = 'abc123'
    self.Touch(self.dir.path, contents=contents)
    self.assertEqual(len(contents),
                     file_utils.GetTreeSizeBytes(self.dir.path, None))

  def testTwoFilesSize(self):
    contents1 = 'abc123'
    contents2 = 'def4'
    self.Touch(self.dir.path, contents=contents1)
    self.Touch(self.dir.path, contents=contents2)
    self.assertEqual(len(contents1) + len(contents2),
                     file_utils.GetTreeSizeBytes(self.dir.path, None))

  def testSizeWithNestedDir(self):
    subdir = os.path.join(self.dir.path, 'subdir')
    file_utils.MakeDir(subdir)
    contents1 = 'abc123'
    contents2 = 'def4'
    self.Touch(self.dir.path, contents=contents1)
    self.Touch(subdir, contents=contents2)
    self.assertEqual(len(contents1) + len(contents2),
                     file_utils.GetTreeSizeBytes(self.dir.path, None))

  def testSizeWithFilter(self):

    def RegexPredicate(f):
      return not re.match(r'.*subdir.*', f)

    subdir = os.path.join(self.dir.path, 'subdir')
    file_utils.MakeDir(subdir)
    contents1 = 'abc123'
    contents2 = 'def4'
    self.Touch(self.dir.path, contents=contents1)
    self.Touch(subdir, contents=contents2)

    self.assertEqual(
        len(contents1),
        file_utils.GetTreeSizeBytes(self.dir.path, RegexPredicate))


class WriteFileAtomicallyTest(test_case.Base, test_case.WithOutputCapture):

  def SetUp(self):
    self.dir = file_utils.TemporaryDirectory()

  def GetTestFilePath(self):
    return os.path.join(self.dir.path, self.RandomFileName())

  def testWriteSucceeds(self):
    path = self.GetTestFilePath()
    contents = 'Test Content'
    file_utils.WriteFileAtomically(path, contents)
    self.AssertFileEquals(contents, path)

  def testWriteEmptyFileSucceeds(self):
    path = self.GetTestFilePath()
    file_utils.WriteFileAtomically(path, '')
    self.AssertFileEquals('', path)

  def testWriteMissingContentsError(self):
    with self.assertRaisesRegex(ValueError,
                                r'Empty file_name \[/fake/path\] '
                                r'or contents \[None\].'):
      file_utils.WriteFileAtomically('/fake/path', None)

  def testWriteBadFilenameError(self):
    with self.assertRaisesRegex(ValueError,
                                r'Empty file_name \[None\] '
                                r'or contents \[\].'):
      file_utils.WriteFileAtomically(None, '')

  def testWriteBadContentsError(self):
    with self.assertRaisesRegex(TypeError, r'Invalid contents \[\{\}\].'):
      file_utils.WriteFileAtomically('/fake/path', {})

  def testDirDoesNotExistSucceeds(self):
    path = self.GetTestFilePath()
    dirname = os.path.dirname(path)
    os.rmdir(dirname)

    test_contents = 'Test Content'

    file_utils.WriteFileAtomically(path, test_contents)
    self.AssertFileEquals(test_contents, path)


class HomeDirTest(test_case.Base):

  def testGetHomeDirascii(self):
    self.StartObjectPatch(os.path, 'expanduser',
                          return_value='abc.xyz'.encode('ascii'))
    self.assertEqual('abc.xyz', file_utils.GetHomeDir())

  def testGetHomeDirutf8(self):
    self.StartObjectPatch(os.path, 'expanduser',
                          return_value='Ṳᾔḯ¢◎ⅾℯ'.encode('utf8'))
    self.assertEqual('Ṳᾔḯ¢◎ⅾℯ', file_utils.GetHomeDir())

  def testGetHomeDirunicode(self):
    self.StartObjectPatch(os.path, 'expanduser', return_value='Ṳᾔḯ¢◎ⅾℯ')
    self.assertEqual('Ṳᾔḯ¢◎ⅾℯ', file_utils.GetHomeDir())

  def testExpandHomeDirascii(self):
    self.StartObjectPatch(os.path, 'expanduser',
                          return_value='abc.xyz'.encode('ascii'))
    self.assertEqual('abc.xyz', file_utils.ExpandHomeDir('~user'))

  def testExpandHomeDirutf8(self):
    self.StartObjectPatch(os.path, 'expanduser',
                          return_value='Ṳᾔḯ¢◎ⅾℯ'.encode('utf8'))
    self.assertEqual('Ṳᾔḯ¢◎ⅾℯ', file_utils.ExpandHomeDir('~user'))

  def testExpandHomeDirunicode(self):
    self.StartObjectPatch(os.path, 'expanduser', return_value='Ṳᾔḯ¢◎ⅾℯ')
    self.assertEqual('Ṳᾔḯ¢◎ⅾℯ', file_utils.ExpandHomeDir('~user'))


class GetCWDTest(test_case.Base):

  def testGetCWDascii(self):
    self.StartObjectPatch(os, 'getcwd', return_value='abc.xyz'.encode('ascii'))
    self.assertEqual('abc.xyz', file_utils.GetCWD())

  def testGetCWDutf8(self):
    self.StartObjectPatch(os, 'getcwd', return_value='Ṳᾔḯ¢◎ⅾℯ'.encode('utf8'))
    self.assertEqual('Ṳᾔḯ¢◎ⅾℯ', file_utils.GetCWD())

  def testGetCWDunicode(self):
    self.StartObjectPatch(os, 'getcwd', return_value='Ṳᾔḯ¢◎ⅾℯ')
    self.assertEqual('Ṳᾔḯ¢◎ⅾℯ', file_utils.GetCWD())


if __name__ == '__main__':
  test_case.main()
