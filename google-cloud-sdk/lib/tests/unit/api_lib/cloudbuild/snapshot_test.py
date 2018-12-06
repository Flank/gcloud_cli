# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for googlecloudsdk.api_lib.cloudbuild.snapshot."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from io import BytesIO
import os
import os.path
import stat
import tarfile

from googlecloudsdk.api_lib.cloudbuild import snapshot
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class FakeStorageClient(object):

  def CopyFileToGCS(self, local_path, target_obj_ref):
    del self, target_obj_ref  # Unused in CopyFileToGCS
    with open(local_path, 'rb') as f:
      return f.read()


class SnapshotTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                   sdk_test_base.WithLogCapture):

  def _writeFile(self, file_name, data):
    files.MakeDir(os.path.dirname(file_name))
    with open(file_name, 'w') as fp:
      fp.write(data)

  def testMakeTarball(self):
    """Test basic tarball with single file."""
    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')
    with files.ChDir(proj):
      with files.TemporaryDirectory() as tmp:
        archive_path = os.path.join(tmp, 'file.tgz')
        tf = snapshot.Snapshot(proj)._MakeTarball(archive_path)
        self.assertEqual(len(tf.getmembers()), 1)
        self.assertEqual(tf.getmember('Dockerfile').size, 5)
        tf.close()

  def testMakeTarball_EmptyDir(self):
    """Test tarball with file and empty dir."""
    proj = self.CreateTempDir('project')  # Directory to snapshot.
    os.mkdir(os.path.join(proj, 'emptydir'))
    os.chmod(os.path.join(proj, 'emptydir'), 0o777)
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')
    with files.ChDir(proj):
      with files.TemporaryDirectory() as tmp:
        archive_path = os.path.join(tmp, 'file.tgz')
        tf = snapshot.Snapshot(proj)._MakeTarball(archive_path)
        self.assertEqual(len(tf.getmembers()), 2)
        self.assertEqual(tf.getmember('Dockerfile').size, 5)
        self.assertTrue(tf.getmember('emptydir').isdir())
        mask = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        self.assertEqual(tf.getmember('emptydir').mode & mask, 0o777)
        tf.close()

  def testMakeTarball_NestedDir(self):
    """Test tarball with file in nested dir."""
    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'path', 'to', 'Dockerfile'), 'empty')
    with files.ChDir(proj):
      with files.TemporaryDirectory() as tmp:
        archive_path = os.path.join(tmp, 'file.tgz')
        tf = snapshot.Snapshot(proj)._MakeTarball(archive_path)
        self.assertEqual(len(tf.getmembers()), 3)
        self.assertEqual(tf.getmember('path/to/Dockerfile').size, 5)
        self.assertTrue(tf.getmember('path').isdir())
        self.assertTrue(tf.getmember('path/to').isdir())
        tf.close()

  def testMakeTarball_gcloudignore(self):
    """Test that gcloudignore is respected."""
    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')
    self._writeFile(os.path.join(proj, 'file_to_ignore'), 'empty')
    self._writeFile(os.path.join(proj, '.gcloudignore'), '.*\nfile_to_ignore')
    with files.ChDir(proj):
      with files.TemporaryDirectory() as tmp:
        archive_path = os.path.join(tmp, 'file.tgz')
        tf = snapshot.Snapshot(proj)._MakeTarball(archive_path)
        self.assertEqual(len(tf.getmembers()), 1)
        self.assertEqual(tf.getmember('Dockerfile').size, 5)
        tf.close()

  def testMakeTarball_gcloudignoreDisabled(self):
    """Test that gcloudignore is not respected when disabled."""
    properties.VALUES.gcloudignore.enabled.Set(False)
    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')
    self._writeFile(os.path.join(proj, 'file_to_ignore'), 'empty')
    self._writeFile(os.path.join(proj, '.gcloudignore'),
                    '.gcloudignore\nfile_to_ignore')
    with files.ChDir(proj):
      with files.TemporaryDirectory() as tmp:
        archive_path = os.path.join(tmp, 'file.tgz')
        tf = snapshot.Snapshot(proj)._MakeTarball(archive_path)
        self.assertEqual(len(tf.getmembers()), 3)
        self.assertEqual(tf.getmember('Dockerfile').size, 5)
        tf.close()

  def testMakeTarball_gitignore(self):
    """Test that gitignore is respected."""
    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')
    self._writeFile(os.path.join(proj, 'file_to_ignore'), 'empty')
    self._writeFile(os.path.join(proj, '.gitignore'), 'file_to_ignore')
    with files.ChDir(proj):
      with files.TemporaryDirectory() as tmp:
        archive_path = os.path.join(tmp, 'file.tgz')
        tf = snapshot.Snapshot(proj)._MakeTarball(archive_path)
        self.assertEqual(len(tf.getmembers()), 1)
        self.assertEqual(tf.getmember('Dockerfile').size, 5)
        tf.close()
    self.assertFalse(os.path.exists(os.path.join(proj, '.gcloudignore')))

  def testMakeTarball_gcloudignore_directory(self):
    """Test that directories in gcloudignore are respected."""
    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')
    self._writeFile(os.path.join(proj, 'subdir', 'somefile'), 'garbage')
    self._writeFile(os.path.join(proj, 'subdir', 'nested', 'nestedfile'),
                    'garbage')
    self._writeFile(os.path.join(proj, '.gcloudignore'),
                    '.gcloudignore\nsubdir')
    with files.ChDir(proj):
      with files.TemporaryDirectory() as tmp:
        archive_path = os.path.join(tmp, 'file.tgz')
        tf = snapshot.Snapshot(proj)._MakeTarball(archive_path)
        self.assertEqual(len(tf.getmembers()), 1)
        self.assertEqual(tf.getmember('Dockerfile').size, 5)
        tf.close()

  @test_case.Filters.SkipOnWindows('tarfile read frequently fails',
                                   'b/72631464')
  def testCopyTarballToGcs(self):
    object_ = resources.REGISTRY.Create(collection='storage.objects',
                                        bucket='bucket', object='object')
    fake_storage_client = FakeStorageClient()

    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')
    self._writeFile(os.path.join(proj, 'file_to_ignore'), 'empty')
    self._writeFile(os.path.join(proj, '.gitignore'), 'file_to_ignore')

    tf_data = snapshot.Snapshot(proj).CopyTarballToGCS(fake_storage_client,
                                                       object_)
    tf = tarfile.open(fileobj=BytesIO(tf_data), mode='r:*')
    self.assertEqual(len(tf.getmembers()), 1)
    self.assertEqual(tf.getmember('Dockerfile').size, 5)
    tf.close()

    self.assertFalse(os.path.exists(os.path.join(proj, '.gcloudignore')))
    self.AssertErrContains('Some files were not included')
    self.AssertErrContains('Check the gcloud log')
    self.AssertLogContains('Using default gcloudignore file')
    self.AssertLogContains('#!include:.gitignore')

  @test_case.Filters.SkipOnWindows('tarfile read frequently fails',
                                   'b/72631464')
  def testCopyTarballToGcs_gcloudignore(self):
    object_ = resources.REGISTRY.Create(collection='storage.objects',
                                        bucket='bucket', object='object')
    fake_storage_client = FakeStorageClient()

    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')
    self._writeFile(os.path.join(proj, 'file_to_ignore'), 'empty')
    self._writeFile(os.path.join(proj, '.gcloudignore'),
                    '.gcloudignore\nfile_to_ignore')

    tf_data = snapshot.Snapshot(proj).CopyTarballToGCS(fake_storage_client,
                                                       object_)
    tf = tarfile.open(fileobj=BytesIO(tf_data), mode='r:*')
    self.assertEqual(len(tf.getmembers()), 1)
    self.assertEqual(tf.getmember('Dockerfile').size, 5)
    tf.close()

    # This message doesn't display with an explicit gcloudignore file
    self.AssertErrNotContains('Some files were not included')
    self.AssertErrNotContains('Check the gcloud log')
    self.AssertLogContains('Using .gcloudignore file')

  @test_case.Filters.SkipOnWindows('tarfile read frequently fails',
                                   'b/72631464')
  def testCopyTarballToGcs_NoIgnoredFiles(self):
    object_ = resources.REGISTRY.Create(collection='storage.objects',
                                        bucket='bucket', object='object')
    fake_storage_client = FakeStorageClient()

    proj = self.CreateTempDir('project')  # Directory to snapshot.
    self._writeFile(os.path.join(proj, 'Dockerfile'), 'empty')

    tf_data = snapshot.Snapshot(proj).CopyTarballToGCS(fake_storage_client,
                                                       object_)
    tf = tarfile.open(fileobj=BytesIO(tf_data), mode='r:*')
    self.assertEqual(len(tf.getmembers()), 1)
    self.assertEqual(tf.getmember('Dockerfile').size, 5)
    tf.close()

    self.assertFalse(os.path.exists(os.path.join(proj, '.gcloudignore')))
    self.AssertErrNotContains('Some files were not included')
    self.AssertErrNotContains('Check the gcloud log')

if __name__ == '__main__':
  test_case.main()
