# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
import re

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.storage import copying
from googlecloudsdk.command_lib.storage import paths
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import six


class CopyingTest(sdk_test_base.WithFakeAuth, parameterized.TestCase):

  def SetUp(self):
    self.project = 'fake-project'
    properties.VALUES.core.project.Set(self.project)
    self.client = mock.Client(
        client_class=apis.GetClientClass('storage', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

    self.messages = apis.GetMessagesModule('storage', 'v1')

    self.buckets_response = self.messages.Buckets(items=[
        self.messages.Bucket(name='bucket1'),
        self.messages.Bucket(name='bucket2'),
    ])
    self.bucket1_resp = self.messages.Objects(items=[
        self.messages.Object(name='file'),
        self.messages.Object(name='file2'),
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

    self._Touch('some/file')
    self._Touch('some/file2')
    self._Touch('another/file')
    self._Touch('another/file2')
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

  def _Abs(self, path):
    if path.startswith('gs://'):
      return paths.Path(path)
    return paths.Path(os.path.join(self.root_path, path.replace('/', os.sep)))

  def testMultiSourceNoDirDest(self):
    with self.assertRaisesRegex(
        copying.Error,
        r'When copying multiple sources, destination must be a directory '
        r'\(a path ending with a slash\).'):
      copier = copying.CopyTaskGenerator()
      copier.GetCopyTasks(
          [self._Abs('some/file'), self._Abs('another/file')],
          paths.Path('gs://bucket1/o'))

  def testWildcardDestination(self):
    dest = self._Abs('foo/*')
    with self.assertRaisesRegex(
        copying.WildcardError,
        r'Destination \[{dest}\] cannot contain wildcards.'.format(
            dest=re.escape(dest.path))):
      copier = copying.CopyTaskGenerator()
      copier.GetCopyTasks([], dest)

  def testNoLocalCopy(self):
    with self.assertRaisesRegex(
        copying.LocationMismatchError,
        r'When destination is a local path, all sources must be remote paths.'):
      copier = copying.CopyTaskGenerator()
      copier.GetCopyTasks(
          [self._Abs('some/file'), self._Abs('gs://bucket1/file')],
          self._Abs('foo'))

  def testMissingRecursive(self):
    with self.assertRaisesRegex(
        copying.RecursionError,
        r'Source path matches directories but --recursive was not specified.'):
      copier = copying.CopyTaskGenerator()
      copier.GetCopyTasks([self._Abs('some')], self._Abs('gs://bucket1/'))

  @parameterized.named_parameters([
      ('FileToDir', 'some/file', 'gs://bucket1', True),
      ('DirToFile', 'some/', 'gs://bucket1/file', True),
      ('DirToDir', 'some/', 'gs://bucket1', True),
      # File overwrite is ok.
      ('FileToFile', 'some/file', 'gs://bucket1/file', False)
  ])
  def testCopyDestExists(self, source, dest, error):
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket1'),
        self.bucket1_resp)
    source = self._Abs(source)
    dest = self._Abs(dest)
    copier = copying.CopyTaskGenerator()
    if error:
      with self.assertRaisesRegex(
          copying.DestinationDirectoryExistsError,
          r'Cannot copy \[{source}\] to \[{dest}\]: '
          r'The destination already exists.'.format(
              source=re.escape(source.path), dest=re.escape(dest.path))):
        copier.GetCopyTasks([source], dest, recursive=True)
    else:
      tasks = copier.GetCopyTasks([source], dest, recursive=True)
      self.assertEqual(1, len(tasks))

  @parameterized.named_parameters([
      ('FileToDir', 'some/file', 'gs://bucket1/file/',
       'gs://bucket1/file/file'),
      ('DirToFile', 'some/', 'gs://bucket1/file/', 'gs://bucket1/file/some/'),
  ])
  def testCopyUnderFile(self, source, dest, target):
    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket1'),
        self.bucket1_resp)
    source = self._Abs(source)
    dest = self._Abs(dest)
    with self.assertRaisesRegex(
        copying.DestinationDirectoryExistsError,
        r'Cannot copy \[{source}\] to \[{target}\]: '
        r'\[{dest}\] exists and is a file.'.format(
            source=re.escape(source.path), target=re.escape(target),
            dest=re.escape(dest.path))):
      copier = copying.CopyTaskGenerator()
      copier.GetCopyTasks([source], dest, recursive=True)

  @parameterized.named_parameters([
      ('Upload', 'some/file', 'gs://bucket1/o',
       ['Upload: {root}{s}some{s}file --> gs://bucket1/o']),
      ('Download', 'gs://bucket1/file', 'some/file',
       ['Download: gs://bucket1/file --> {root}{s}some{s}file']),
      ('Copy', 'gs://bucket1/file', 'gs://bucket1/o2',
       ['Copy: gs://bucket1/file --> gs://bucket1/o2']),
  ])
  def testSingleSource(self, source, dest, expected):
    copier = copying.CopyTaskGenerator()
    if source.startswith('gs://') or dest.startswith('gs://'):
      self.client.objects.List.Expect(
          self.messages.StorageObjectsListRequest(bucket='bucket1'),
          self.bucket1_resp)

    tasks = copier.GetCopyTasks([self._Abs(source)], self._Abs(dest))
    expected = [e.format(root=self.root_path, s=os.sep) for e in expected]
    self.assertEqual(expected, [six.text_type(t) for t in tasks])

  @parameterized.named_parameters([
      ('UploadOne', ['some/file'], 'gs://bucket1/',
       ['Upload: {root}{s}some{s}file --> gs://bucket1/file']),
      ('DownloadOne', ['gs://bucket1/file'], 'some/',
       ['Download: gs://bucket1/file --> {root}{s}some{s}file']),
      ('CopyOne', ['gs://bucket1/file'], 'gs://bucket2/',
       ['Copy: gs://bucket1/file --> gs://bucket2/file']),
      ('UploadMulti', ['some/file', 'some/file2'], 'gs://bucket1/',
       ['Upload: {root}{s}some{s}file --> gs://bucket1/file',
        'Upload: {root}{s}some{s}file2 --> gs://bucket1/file2']),
      ('DownloadMulti', ['gs://bucket1/file', 'gs://bucket1/file2'], 'some/',
       ['Download: gs://bucket1/file --> {root}{s}some{s}file',
        'Download: gs://bucket1/file2 --> {root}{s}some{s}file2']),
      ('CopyMulti', ['gs://bucket1/file', 'gs://bucket1/file2'],
       'gs://bucket2/',
       ['Copy: gs://bucket1/file --> gs://bucket2/file',
        'Copy: gs://bucket1/file2 --> gs://bucket2/file2']),
      ('MixedRemoteDest',
       ['gs://bucket1/file', 'gs://bucket1/file2', 'some/file',
        'another/file2'], 'gs://bucket2/',
       ['Upload: {root}{s}another{s}file2 --> gs://bucket2/file2',
        'Upload: {root}{s}some{s}file --> gs://bucket2/file',
        'Copy: gs://bucket1/file --> gs://bucket2/file',
        'Copy: gs://bucket1/file2 --> gs://bucket2/file2']),
  ])
  def testDirDest(self, sources, dest, expected):
    bucket1 = [s for s in sources if 'bucket1' in s]
    if bucket1 or 'bucket1' in dest:
      self.client.objects.List.Expect(
          self.messages.StorageObjectsListRequest(bucket='bucket1'),
          self.bucket1_resp)
    bucket2 = [s for s in sources if 'bucket2' in s]
    if bucket2 or 'bucket2' in dest:
      self.client.objects.List.Expect(
          self.messages.StorageObjectsListRequest(bucket='bucket2'),
          self.messages.Objects(items=[]))

    copier = copying.CopyTaskGenerator()
    sources = [self._Abs(p) for p in sources]
    dest = self._Abs(dest)
    tasks = copier.GetCopyTasks(sources, dest)

    expected = [e.format(root=self.root_path, s=os.sep) for e in expected]
    self.assertCountEqual(expected, [six.text_type(t) for t in tasks])

  @parameterized.named_parameters([
      # Local source files have . and .. resolved so it's ok.
      ('DotSourceUpload', 'some/./file', 'gs://bucket1/file',
       ['Upload: {root}{s}some{s}file --> gs://bucket1/file']),
      ('DotDotSourceUpload', 'some/../some/file', 'gs://bucket1/file',
       ['Upload: {root}{s}some{s}file --> gs://bucket1/file']),
      # Local dest files have . and .. resolved so it's ok.
      ('DotDestDownload', 'gs://bucket1/file', 'some/./file',
       ['Download: gs://bucket1/file --> {root}{s}some{s}file']),
      ('DotDotDestDownload', 'gs://bucket1/file', 'some/../some/file',
       ['Download: gs://bucket1/file --> {root}{s}some{s}file']),
      # The source and dest are a single files, so there is no risk of the dirs
      # getting messed up.
      ('DotSourceDownloadToFile', 'gs://bucket1/./file', 'some/file',
       ['Download: gs://bucket1/./file --> {root}{s}some{s}file']),
      ('DotDotSourceDownloadToFile', 'gs://bucket1/../file', 'some/file',
       ['Download: gs://bucket1/../file --> {root}{s}some{s}file']),
      # The dest is a dir, but the source is not recursive, so there is no risk
      # of the dirs getting messed up.
      ('DotSourceDownloadToDir', 'gs://bucket1/./file', 'some/dir/',
       ['Download: gs://bucket1/./file --> {root}{s}some{s}dir{s}file']),
      ('DotDotSourceDownloadToDir', 'gs://bucket1/../file', 'some/dir/',
       ['Download: gs://bucket1/../file --> {root}{s}some{s}dir{s}file']),
  ])
  def testInterestingPaths(self, source, dest, expected):
    copier = copying.CopyTaskGenerator()
    if source.startswith('gs://') or dest.startswith('gs://'):
      bucket1_resp = self.messages.Objects(items=[
          self.messages.Object(name='file'),
          self.messages.Object(name='./file'),
          self.messages.Object(name='../file'),
      ])
      self.client.objects.List.Expect(
          self.messages.StorageObjectsListRequest(bucket='bucket1'),
          bucket1_resp)

    tasks = copier.GetCopyTasks([self._Abs(source)], self._Abs(dest))
    expected = [e.format(root=self.root_path, s=os.sep) for e in expected]
    self.assertEqual(expected, [six.text_type(t) for t in tasks])

  @parameterized.named_parameters([
      ('DotDestUpload', 'some/file', 'gs://bucket1/./file'),
      ('DotDotDestUpload', 'some/file', 'gs://bucket1/some/../file'),
  ])
  def testInterestingPathsError(self, source, dest):
    copier = copying.CopyTaskGenerator()
    if source.startswith('gs://') or dest.startswith('gs://'):
      bucket1_resp = self.messages.Objects(items=[
          self.messages.Object(name='file'),
          self.messages.Object(name='./file'),
          self.messages.Object(name='../file'),
      ])
      self.client.objects.List.Expect(
          self.messages.StorageObjectsListRequest(bucket='bucket1'),
          bucket1_resp)

    source = self._Abs(source)
    dest = self._Abs(dest)

    with self.assertRaisesRegex(
        copying.InvalidDestinationError,
        r'Cannot copy \[{source}\] to \[{dest}\] because of "." or ".." in the '
        r'path.'.format(source=re.escape(source.path),
                        dest=re.escape(dest.path))):
      copier.GetCopyTasks([source], dest)

  @parameterized.named_parameters([
      ('Dot', '.'),
      ('DotDot', '..'),
  ])
  def testInterestingPathsRecursiveError(self, bad_path):
    source = self._Abs('gs://bucket1/')
    dest = self._Abs('some/dir/')

    self.client.objects.List.Expect(
        self.messages.StorageObjectsListRequest(bucket='bucket1'),
        self.messages.Objects(
            items=[self.messages.Object(name=bad_path + '/file')]))

    copier = copying.CopyTaskGenerator()
    bad_source = source.Join(bad_path).Join('file')
    bad_dest = dest.Join('bucket1').Join(bad_path).Join('file')

    with self.assertRaisesRegex(
        copying.InvalidDestinationError,
        r'Cannot copy \[{source}\] to \[{dest}\] because of "." or ".." in the '
        r'path.'.format(source=re.escape(bad_source.path),
                        dest=re.escape(bad_dest.path))):
      copier.GetCopyTasks([source], dest, recursive=True)

if __name__ == '__main__':
  test_case.main()
