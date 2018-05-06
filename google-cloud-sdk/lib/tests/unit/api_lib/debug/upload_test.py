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
"""Tests for the upload wrapper module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from datetime import datetime

import os
import uuid

from apitools.base.py.testing import mock as client_mock
from googlecloudsdk.api_lib.debug import upload
from googlecloudsdk.api_lib.source import git
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files as file_utils
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error

import six


class UploadManagerTest(sdk_test_base.WithOutputCapture,
                        sdk_test_base.WithFakeAuth):
  """Tests UploadManager class."""

  def SetUp(self):
    self.tmpdir = file_utils.TemporaryDirectory().path
    self.StartObjectPatch(
        properties.VALUES.core.project, 'Get', return_value='test_project')
    self.push_mock = self.StartObjectPatch(git.Git, 'ForcePushFilesToBranch')

    self.messages = core_apis.GetMessagesModule('sourcerepo', 'v1')
    self.mock_client = client_mock.Client(
        core_apis.GetClientClass('sourcerepo', 'v1'),
        real_client=core_apis.GetClientInstance(
            'sourcerepo', 'v1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def SetGetRepoSuccess(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/test_project/repos/google-source-captures'),
        self.messages.Repo(name='google-source-captures', url='https'))

  def SetGetRepoNotFound(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/test_project/repos/google-source-captures'),
        exception=http_error.MakeHttpError(code=404))

  def CreateFiles(self, paths):
    full_paths = []
    for path in paths:
      full_path = os.path.join(self.tmpdir, os.path.normpath(path))
      file_utils.MakeDir(os.path.dirname(full_path))
      with open(full_path, 'w') as f:
        f.write('contents of ' + path)
      full_paths.append(full_path)
    return full_paths

  def testUploadWithNoRepo(self):
    self.SetGetRepoNotFound()
    with self.assertRaises(upload.RepoNotFoundError) as e:
      upload.UploadManager().Upload('branch1', self.tmpdir)
    self.assertIn('gcloud source repos create', six.text_type(e.exception))

  def testUpload(self):
    self.SetGetRepoSuccess()
    full_paths = self.CreateFiles(['dir/file2', 'file1'])

    result = upload.UploadManager().Upload('branch1', self.tmpdir)

    self.push_mock.assert_called_with('branch1', self.tmpdir, full_paths)

    self.assertEqual('branch1', result['branch'])
    self.assertEqual(2, result['files_written'])
    self.assertEqual(0, result['files_skipped'])
    self.assertEqual(
        sum([len(file_utils.GetFileContents(path)) for path in full_paths]),
        result['size_written'])

    cloud_repo = result['source_contexts'][0]['context']['cloudRepo']
    self.assertEqual({
        'projectId': 'test_project',
        'repoName': 'google-source-captures'
    }, cloud_repo['repoId']['projectRepoId'])
    self.assertEqual({
        'kind': 'MOVABLE',
        'name': 'branch1',
    }, cloud_repo['aliasContext'])

  def testUploadWithGeneratedName(self):
    self.SetGetRepoSuccess()
    self.StartObjectPatch(upload, '_GetNow', return_value=datetime(1970, 1, 1))
    self.StartObjectPatch(
        upload,
        '_GetUuid',
        return_value=uuid.UUID('12345678123456781234567812345678'))
    full_paths = self.CreateFiles(['dir/file2', 'file1'])

    upload.UploadManager().Upload(None, self.tmpdir)

    self.push_mock.assert_called_with(
        '1970/01/01-00.00.00.12345678123456781234567812345678', self.tmpdir,
        full_paths)

  def testUploadWithGitFiles(self):
    self.SetGetRepoSuccess()
    full_paths = self.CreateFiles(['file1', '.git/file2'])

    upload.UploadManager().Upload('branch1', self.tmpdir)

    self.push_mock.assert_called_with('branch1', self.tmpdir, full_paths[:1])

  def testUploadWithGitIgnore(self):
    self.SetGetRepoSuccess()
    full_paths = self.CreateFiles(
        ['.gitignore', 'file1', 'ignoredfile', 'ignoreddir/file'])
    with open(full_paths[0], 'w') as f:
      f.write('ignored*\n')

    upload.UploadManager().Upload('branch1', self.tmpdir)

    self.push_mock.assert_called_with('branch1', self.tmpdir, [full_paths[1]])

  def testUploadWithGcloudIgnore(self):
    self.SetGetRepoSuccess()
    full_paths = self.CreateFiles(
        ['.gcloudignore', 'file1', 'ignoredfile', 'ignoreddir/file'])
    with open(full_paths[0], 'w') as f:
      f.write('ignored*\n')

    upload.UploadManager().Upload('branch1', self.tmpdir)

    self.push_mock.assert_called_with('branch1', self.tmpdir,
                                      [full_paths[0], full_paths[1]])

  def testUploadWithTooLargeFiles(self):
    self.SetGetRepoSuccess()
    original_size_threshold = upload.UploadManager.SIZE_THRESHOLD

    try:
      self.assertEqual(256 * 2**10, original_size_threshold)
      full_paths = self.CreateFiles(['file1', 'filethatistoolarge'])
      upload.UploadManager.SIZE_THRESHOLD = len(
          file_utils.GetFileContents(full_paths[1])) - 1

      result = upload.UploadManager().Upload('branch1', self.tmpdir)

      self.push_mock.assert_called_with('branch1', self.tmpdir, full_paths[:1])
      self.assertEqual(1, result['files_skipped'])
    finally:
      upload.UploadManager.SIZE_THRESHOLD = original_size_threshold
