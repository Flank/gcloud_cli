# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Unit tests for path expansion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import expansion
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error


class LocalExpansionTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    self.expander = expansion.LocalPathExpander()
    self._Touch('dir1/sub1/a.txt')
    self._Touch('dir1/sub1/aab.txt')
    self._Touch('dir1/sub2/aaaa.txt')
    self._Touch('dir1/sub2/c.txt')
    self._Touch('dir2/sub1/aaaaaa.txt')
    self._Touch('dir2/sub1/d.txt')
    self._Touch('dir2/sub2/aaaaaaaa.txt')
    self._Touch('dir2/sub2/e.txt')
    self._Touch('dir3/deeper/sub1/a.txt')
    self._Touch('dir3/deeper/sub2/b.txt')

  def _Touch(self, path):
    parts = path.rsplit('/', 1)
    dir_path, filename = parts[0], parts[1]
    self.Touch(os.path.join(self.root_path, dir_path), filename, makedirs=True)

  @parameterized.named_parameters([
      ('DirNoExpansion', 'dir1', [], ['dir1/']),
      ('SubDirNoExpansion', 'dir1/sub1', [], ['dir1/sub1/']),
      ('FileNoExpansion', 'dir1/sub1/a.txt', ['dir1/sub1/a.txt'], []),
      ('NonExistingNoExpansion', 'dir1/sub1/asdf', [], []),
      ('EndOnlyWildcard', 'dir1/sub1/*',
       ['dir1/sub1/a.txt', 'dir1/sub1/aab.txt'], []),
      ('EndMultipleWildcard', 'dir1/sub1/*b*',
       ['dir1/sub1/aab.txt'], []),
      ('EndRecursive', 'dir1/sub1/**',
       ['dir1/sub1/a.txt', 'dir1/sub1/aab.txt'], []),
      ('EndRecursiveHigher', 'dir1/**',
       ['dir1/sub1/a.txt', 'dir1/sub1/aab.txt',
        'dir1/sub2/aaaa.txt', 'dir1/sub2/c.txt'], []),
      ('MiddleRecursive', '**/sub1', [],
       ['dir1/sub1/', 'dir2/sub1/', 'dir3/deeper/sub1/']),
      ('MiddleNotRecursive', '*/sub1', [],
       ['dir1/sub1/', 'dir2/sub1/']),
      ('MiddleEndRecursive', '**/sub1/**',
       ['dir1/sub1/a.txt', 'dir1/sub1/aab.txt',
        'dir2/sub1/aaaaaa.txt', 'dir2/sub1/d.txt',
        'dir3/deeper/sub1/a.txt'], []),
      ('MiddleNotRecursiveEndRecursive', '*/sub1/**',
       ['dir1/sub1/a.txt', 'dir1/sub1/aab.txt',
        'dir2/sub1/aaaaaa.txt', 'dir2/sub1/d.txt'], []),
      ('SingleChar', 'dir1/sub?/?.txt',
       ['dir1/sub1/a.txt', 'dir1/sub2/c.txt'], []),
      ('CharRange', '**/[a-b].txt',
       ['dir1/sub1/a.txt', 'dir3/deeper/sub1/a.txt',
        'dir3/deeper/sub2/b.txt'], []),
      ('Root', '**/[a-b].txt',
       ['dir1/sub1/a.txt', 'dir3/deeper/sub1/a.txt',
        'dir3/deeper/sub2/b.txt'], []),
      ('WrongDoubleStar', 'd**/[a-b].txt', [], []),
      ('StarDoubleStar', 'd*/**/[a-b].txt',
       ['dir1/sub1/a.txt', 'dir3/deeper/sub1/a.txt',
        'dir3/deeper/sub2/b.txt'], []),
      ('DoubleSlash', 'dir1//sub*/a.txt', ['dir1/sub1/a.txt'], []),
      ('Dot', 'dir1/./sub*/a.txt', ['dir1/sub1/a.txt'], []),
      ('DotDot', 'dir1/../dir2/**/?.txt',
       ['dir2/sub1/d.txt', 'dir2/sub2/e.txt'], []),
  ])
  def testGlob(self, pattern, expected_files, expected_dirs):
    processed_pattern = pattern.replace('/', os.sep)
    (actual_files, actual_dirs) = self.expander.ExpandPath(
        os.path.join(self.root_path, processed_pattern))
    processed_expected_files = {
        os.path.join(self.root_path, p.replace('/', os.sep))
        for p in expected_files}
    processed_expected_dirs = {
        os.path.join(self.root_path, p.replace('/', os.sep))
        for p in expected_dirs}
    self.assertEqual(actual_files, processed_expected_files)
    self.assertEqual(actual_dirs, processed_expected_dirs)


class GcsExpansionTest(sdk_test_base.WithFakeAuth, parameterized.TestCase):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)
    self.client = mock.Client(client_class=apis.GetClientClass('storage', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

    self.messages = apis.GetMessagesModule('storage', 'v1')
    self.expander = expansion.GCSPathExpander()

    self.buckets_response = self.messages.Buckets(items=[
        self.messages.Bucket(name='bucket1'),
        self.messages.Bucket(name='bucket2'),
    ])
    self.bucket1_resp = self.messages.Objects(items=[
        self.messages.Object(name='dir1/sub1/a.txt'),
        self.messages.Object(name='dir1/sub1/aab.txt'),
        self.messages.Object(name='dir1/sub2/aaaa.txt'),
        self.messages.Object(name='dir1/sub2/c.txt'),
        self.messages.Object(name='dir2/sub1/aaaaaa.txt'),
        self.messages.Object(name='dir2/sub1/d.txt'),
        self.messages.Object(name='dir2/sub2/aaaaaaaa.txt'),
        self.messages.Object(name='dir2/sub2/e.txt'),
        self.messages.Object(name='dir3/deeper/sub1/a.txt'),
        self.messages.Object(name='dir3/deeper/sub2/b.txt'),
    ])

  def testListDirRoot(self):
    self.client.buckets.List.Expect(
        self.messages.StorageBucketsListRequest(project=self.project),
        self.buckets_response)
    actual = sorted(self.expander.ListDir('gs://'))
    self.assertEqual(sorted({'bucket1', 'bucket2'}), actual)

  @parameterized.named_parameters([
      ('Bucket', 'gs://bucket1', {'dir1', 'dir2', 'dir3'}),
      ('SubDir', 'gs://bucket1/dir2', {'sub1', 'sub2'}),
      ('SubDirWithFiles', 'gs://bucket1/dir2/sub1', {'aaaaaa.txt', 'd.txt'}),
  ])
  def testListDir(self, path, expected):
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket1'),
        self.bucket1_resp)
    self.assertEqual(sorted(self.expander.ListDir(path)), sorted(expected))

  @parameterized.named_parameters([
      ('Bucket', 'gs://bucket1', True, True),
      ('SubDir', 'gs://bucket1/dir2', True, True),
      ('SubDirNotExist', 'gs://bucket1/dir6', False, False),
      ('SubDirWithFiles', 'gs://bucket1/dir2/sub1', True, True),
      ('SubDirWithFilesNotExist', 'gs://bucket1/dir2/sub6', False, False),
      ('File', 'gs://bucket1/dir2/sub1/d.txt', True, False),
      ('FileNotExist', 'gs://bucket1/dir2/sub1/x.txt', False, False),
  ])
  def testExists(self, path, exists, is_dir):
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket1'),
        self.bucket1_resp)
    self.assertEqual(self.expander.Exists(path), exists)
    self.assertEqual(self.expander.IsDir(path), is_dir)

  def testBucketNotExist(self):
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket3'),
        exception=http_error.MakeHttpError(code=404))
    self.assertEqual(self.expander.Exists('gs://bucket3'), False)
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket3'),
        exception=http_error.MakeHttpError(code=404))
    self.assertEqual(self.expander.IsDir('gs://bucket3'), False)

  @parameterized.named_parameters([
      ('DirNoExpansion', 'gs://bucket1/dir1', [], ['gs://bucket1/dir1/']),
      ('SubDirNoExpansion', 'gs://bucket1/dir1/sub1', [],
       ['gs://bucket1/dir1/sub1/']),
      ('FileNoExpansion', 'gs://bucket1/dir1/sub1/a.txt',
       ['gs://bucket1/dir1/sub1/a.txt'], []),
      ('NonExistingNoExpansion', 'gs://bucket1/dir1/sub1/asdf', [], []),
      ('EndOnlyWildcard', 'gs://bucket1/dir1/sub1/*',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir1/sub1/aab.txt'], []),
      ('EndMultipleWildcard', 'gs://bucket1/dir1/sub1/*b*',
       ['gs://bucket1/dir1/sub1/aab.txt'], []),
      ('EndRecursive', 'gs://bucket1/dir1/sub1/**',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir1/sub1/aab.txt'], []),
      ('EndRecursiveHigher', 'gs://bucket1/dir1/**',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir1/sub1/aab.txt',
        'gs://bucket1/dir1/sub2/aaaa.txt', 'gs://bucket1/dir1/sub2/c.txt'], []),
      ('EndRecursiveAfterBucket', 'gs://bucket1/**',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir1/sub1/aab.txt',
        'gs://bucket1/dir1/sub2/aaaa.txt', 'gs://bucket1/dir1/sub2/c.txt',
        'gs://bucket1/dir2/sub1/aaaaaa.txt', 'gs://bucket1/dir2/sub1/d.txt',
        'gs://bucket1/dir2/sub2/aaaaaaaa.txt', 'gs://bucket1/dir2/sub2/e.txt',
        'gs://bucket1/dir3/deeper/sub1/a.txt',
        'gs://bucket1/dir3/deeper/sub2/b.txt'], []),
      ('MiddleRecursive', 'gs://bucket1/**/sub1', [],
       ['gs://bucket1/dir1/sub1/', 'gs://bucket1/dir2/sub1/',
        'gs://bucket1/dir3/deeper/sub1/']),
      ('MiddleNotRecursive', 'gs://bucket1/*/sub1', [],
       ['gs://bucket1/dir1/sub1/', 'gs://bucket1/dir2/sub1/']),
      ('MiddleEndRecursive', 'gs://bucket1/**/sub1/**',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir1/sub1/aab.txt',
        'gs://bucket1/dir2/sub1/aaaaaa.txt', 'gs://bucket1/dir2/sub1/d.txt',
        'gs://bucket1/dir3/deeper/sub1/a.txt'], []),
      ('MiddleNotRecursiveEndRecursive', 'gs://bucket1/*/sub1/**',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir1/sub1/aab.txt',
        'gs://bucket1/dir2/sub1/aaaaaa.txt', 'gs://bucket1/dir2/sub1/d.txt'],
       []),
      ('SingleChar', 'gs://bucket1/dir1/sub?/?.txt',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir1/sub2/c.txt'], []),
      ('CharRange', 'gs://bucket1/**/[a-b].txt',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir3/deeper/sub1/a.txt',
        'gs://bucket1/dir3/deeper/sub2/b.txt'], []),
      ('DoubleSlash', 'gs://bucket1/dir1//sub*/a.txt',
       ['gs://bucket1/dir1/sub1/a.txt'], []),
      # '.' and '..' are valid identifiers in GCS so this should be an exact
      # match only.
      ('Dot', 'gs://bucket1/dir1/./sub*/a.txt', [], []),
      ('DotDot', 'gs://bucket1/dir1/../sub*/a.txt', [], []),
  ])
  def testGlob(self, pattern, expected_files, expected_dirs):
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket1'),
        self.bucket1_resp)
    (actual_files, actual_dirs) = self.expander.ExpandPath(pattern)
    self.assertEqual(actual_files, set(expected_files))
    self.assertEqual(actual_dirs, set(expected_dirs))

  @parameterized.named_parameters([
      ('Root', 'gs://**/[a-b].txt',
       ['gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir3/deeper/sub1/a.txt',
        'gs://bucket1/dir3/deeper/sub2/b.txt', 'gs://bucket2/dir1/sub1/a.txt',
        'gs://bucket2/dir3/deeper/sub1/a.txt',
        'gs://bucket2/dir3/deeper/sub2/b.txt'], []),
  ])
  def testGlobBuckets(self, pattern, expected_files, expected_dirs):
    self.client.buckets.List.Expect(
        self.messages.StorageBucketsListRequest(project=self.project),
        self.buckets_response)
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket1'),
        self.bucket1_resp)
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket2'),
        self.bucket1_resp)
    (actual_files, actual_dirs) = self.expander.ExpandPath(pattern)
    self.assertEqual(actual_files, set(expected_files))
    self.assertEqual(actual_dirs, set(expected_dirs))

  def testObjectDetails(self):
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket1'),
        self.bucket1_resp)
    # Just load the object details.
    self.expander.ExpandPath('gs://bucket1/**')
    details = self.expander.GetSortedObjectDetails(
        {'gs://bucket1/dir1/sub2/aaaa.txt', 'gs://bucket1/dir1/sub1/a.txt',
         'gs://bucket1/dir1/sub1', 'gs://bucket1/dir1/sub1/aab.txt',
         'gs://bucket1/dir1/sub2'})
    self.assertEqual(
        ['gs://bucket1/dir1/sub1/', 'gs://bucket1/dir1/sub2/',
         'gs://bucket1/dir1/sub1/a.txt', 'gs://bucket1/dir1/sub1/aab.txt',
         'gs://bucket1/dir1/sub2/aaaa.txt'],
        [d['path'] for d in details])


if __name__ == '__main__':
  test_case.main()
