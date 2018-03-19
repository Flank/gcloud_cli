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

"""Tests for the source capture module."""


import os

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.source import capture
from googlecloudsdk.api_lib.source import source
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files as file_utils
from tests.lib import sdk_test_base
from googlecloudsdk.third_party.appengine.tools import context_util as contexts
import mock
from mock import patch


class _FakeZipInfo(object):

  def __init__(self, name):
    self.filename = name


class _FakeZipFile(object):

  def __init__(self, files):
    self._files = dict(files)

  def infolist(self):
    for name in self._files:
      yield _FakeZipInfo(name)

  def read(self, path):
    return self._files[path]

  def close(self):
    pass


class _FakeWorkspaceInfo(object):

  def __init__(self, name):
    self.name = name


def _fake_file_list(names):
  return [(name, 'contents of ' + name) for name in names]


def _create_fake_files(root, file_list):
  for name, contents in file_list:
    path = os.path.join(root, name)
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
      os.makedirs(dirname)
    with open(path, 'w') as f:
      f.write(contents)


def _fake_write_file(path, contents):
  if path.endswith('.big'):
    raise source.FileTooBigException(path, len(contents), len(contents) - 1)


def _capture_context(capture_name):
  return {
      'context': {
          'cloudWorkspace': {
              'workspaceId': {
                  'name': capture_name,
                  'repoId': {
                      'projectRepoId': {
                          'projectId': 'test_project',
                          'repoName': 'google-source-captures'}}}}},
      'labels': {'category': 'capture'}}


class CaptureManagerTest(sdk_test_base.WithOutputCapture,
                         sdk_test_base.WithFakeAuth):
  """Tests CaptureManager class."""

  def SetUp(self):
    self.StartObjectPatch(properties.VALUES.core.project, 'Get',
                          return_value='test_project')
    self.StartObjectPatch(source.Project, 'GetRepo', return_value=True)
    self.messages = apis.GetMessagesModule('source', 'v1')
    self.client = api_mock.Client(apis.GetClientClass('source', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

  def _fake_create_ws(self, name, _=None):
    return source.Workspace('test_project', name, 'test_repo',
                            client=self.client)

  def _fake_get_capture(self, name):
    return capture.Capture('test_project', 'test_repo',
                           capture.CAPTURE_PREFIX + name)

  def testCreateNamedCapture(self):
    fake_capture = self._fake_get_capture('fake-capture-name')
    fake_ws = source.Workspace('test_project', fake_capture.workspace_name,
                               repo_name=capture.CAPTURE_REPO_NAME,
                               state=None)
    self.StartObjectPatch(source.Repo, 'GetWorkspace', return_value=fake_ws)
    find_mock = self.StartObjectPatch(capture.CaptureManager, '_FindCapture',
                                      return_value=fake_capture)
    populate_mock = self.StartObjectPatch(capture.CaptureManager,
                                          '_PopulateCapture')

    mgr = capture.CaptureManager()
    mgr.UploadCapture('fake-capture-name', '/any/dir', '')

    find_mock.assert_called_with('fake-capture-name')
    populate_mock.assert_called_with(fake_capture, fake_ws, '/any/dir', '')

  def testCreateFromJar(self):
    self.StartObjectPatch(contexts, 'CalculateExtendedSourceContexts',
                          return_value=[])
    self.StartObjectPatch(capture.CaptureManager, '_FindCapture',
                          side_effect=self._fake_get_capture)
    self.StartObjectPatch(source.Repo, 'GetWorkspace',
                          side_effect=self._fake_create_ws)
    write_file = self.StartObjectPatch(source.Workspace, 'WriteFile')
    flush_actions = self.StartObjectPatch(source.Workspace,
                                          'FlushPendingActions')
    mgr = capture.CaptureManager()
    fake_jar_files = [
        'a/b/file1.java',
        'a/b/file2.java',
        'file3.java',
        'not_a_java_file.class']
    fake_jar = _FakeZipFile(_fake_file_list(fake_jar_files))

    with patch('zipfile.ZipFile', return_value=fake_jar):
      result = mgr.UploadCapture('dummy_capture', 'dummy.jar', '')
    write_file.assert_has_calls(
        [mock.call(name, contents)
         for name, contents in _fake_file_list(fake_jar_files)
         if name.endswith('java')],
        any_order=True)
    flush_actions.assert_called_with()
    self.assertEquals(
        result['capture'],
        capture.Capture('test_project', 'test_repo', 'dummy_capture'))

  def testCreateFromDirectory(self):
    self.StartObjectPatch(contexts, 'CalculateExtendedSourceContexts',
                          return_value=[])
    self.StartObjectPatch(capture.CaptureManager, '_FindCapture',
                          side_effect=self._fake_get_capture)
    self.StartObjectPatch(source.Repo, 'GetWorkspace',
                          side_effect=self._fake_create_ws)
    write_file = self.StartObjectPatch(source.Workspace, 'WriteFile')
    flush_actions = self.StartObjectPatch(source.Workspace,
                                          'FlushPendingActions')

    # Normalize names because this test may run on Windows, which uses \
    fake_filenames = [os.path.normpath(name) for name in [
        'a/b/file1.java',
        'a/b/file2.py',
        'file3',
        'not_a_java_file.class']]

    with file_utils.TemporaryDirectory() as tmpdir:
      fake_files = _fake_file_list(fake_filenames)

      _create_fake_files(tmpdir, fake_files)

      mgr = capture.CaptureManager()
      mgr.UploadCapture('my-capture', tmpdir, '')

      write_file.assert_has_calls(
          [mock.call(name, contents) for name, contents in fake_files],
          any_order=True)
      flush_actions.assert_called_with()

  def testCreateResult(self):
    self.StartObjectPatch(contexts, 'CalculateExtendedSourceContexts',
                          return_value=[])
    self.StartObjectPatch(capture.CaptureManager, '_FindCapture',
                          side_effect=self._fake_get_capture)
    self.StartObjectPatch(source.Repo, 'GetWorkspace',
                          side_effect=self._fake_create_ws)
    self.StartObjectPatch(source.Workspace, 'FlushPendingActions')
    self.StartObjectPatch(source.Workspace, 'WriteFile',
                          side_effect=_fake_write_file)

    with file_utils.TemporaryDirectory() as tmpdir:
      fake_files = [
          ('file1', 'x' * 5),
          ('file2', 'y' * 10),
          ('skippedfile.big', 'z'*1000)]

      _create_fake_files(tmpdir, fake_files)

      mgr = capture.CaptureManager()
      result = mgr.UploadCapture('dummy_capture', tmpdir, '')
    self.assertEquals({
        'capture': self._fake_get_capture('dummy_capture'),
        'source_contexts': [_capture_context('dummy_capture')],
        'files_written': 2,
        'files_skipped': 1,
        'size_written': 15}, result)

  def testCreateFromGitDirectory(self):
    self.StartObjectPatch(contexts, 'CalculateExtendedSourceContexts',
                          return_value=[])
    self.StartObjectPatch(capture.CaptureManager, '_FindCapture',
                          side_effect=self._fake_get_capture)
    self.StartObjectPatch(source.Repo, 'GetWorkspace',
                          side_effect=self._fake_create_ws)
    write_file = self.StartObjectPatch(source.Workspace, 'WriteFile')
    flush_actions = self.StartObjectPatch(source.Workspace,
                                          'FlushPendingActions')

    # Normalize names because this test may run on Windows, which uses \
    fake_filenames = [os.path.normpath(name) for name in [
        'a/b/file1.java',
        'a/b/file2.py',
        'file3',
        'not_a_java_file.class']]

    # Create some files in a dummy '.git' directory, which should be ignored
    ignored_git_filenames = [os.path.normpath(name) for name in [
        '.git/file1',
        '.git/subdir/file2']]

    with file_utils.TemporaryDirectory() as tmpdir:
      fake_files = _fake_file_list(fake_filenames)

      _create_fake_files(tmpdir, fake_files)
      _create_fake_files(tmpdir, _fake_file_list(ignored_git_filenames))

      mgr = capture.CaptureManager()
      mgr.UploadCapture('my-capture', tmpdir, '')

      write_file.assert_has_calls(
          [mock.call(name, contents) for name, contents in fake_files],
          any_order=True)
      flush_actions.assert_called_with()

  def testCreateIgnoresGit(self):
    self.StartObjectPatch(contexts, 'CalculateExtendedSourceContexts',
                          return_value=[])
    self.StartObjectPatch(capture.CaptureManager, '_FindCapture',
                          side_effect=self._fake_get_capture)
    self.StartObjectPatch(source.Repo, 'GetWorkspace',
                          side_effect=self._fake_create_ws)
    write_file = self.StartObjectPatch(source.Workspace, 'WriteFile')
    flush_actions = self.StartObjectPatch(source.Workspace,
                                          'FlushPendingActions')

    # Normalize names because this test may run on Windows, which uses \
    fake_filenames = [os.path.normpath(name) for name in [
        'a/b/file1.java',
        'a/b/file2.py',
        'file3',
        'not_a_java_file.class']]

    with file_utils.TemporaryDirectory() as tmpdir:
      fake_files = _fake_file_list(fake_filenames)

      _create_fake_files(tmpdir, fake_files)

      # Create some directories that should be ignored because they look like
      # git control files.
      _create_fake_files(tmpdir, _fake_file_list(
          ['.git/dummy1', '.git/b/dummy2', 'a/.git/dummy3',
           '.git.foo~1/dummy4']))

      mgr = capture.CaptureManager()
      mgr.UploadCapture('my-capture', tmpdir, '')

      write_file.assert_has_calls(
          [mock.call(name, contents) for name, contents in fake_files],
          any_order=True)
      flush_actions.assert_called_with()

  def testCreateIgnoresBigFiles(self):
    self.StartObjectPatch(contexts, 'CalculateExtendedSourceContexts',
                          return_value=[])
    self.StartObjectPatch(capture.CaptureManager, '_FindCapture',
                          side_effect=self._fake_get_capture)
    self.StartObjectPatch(source.Repo, 'GetWorkspace',
                          side_effect=self._fake_create_ws)
    write_file = self.StartObjectPatch(
        source.Workspace, 'WriteFile', side_effect=_fake_write_file)
    flush_actions = self.StartObjectPatch(source.Workspace,
                                          'FlushPendingActions')

    # Normalize names because this test may run on Windows, which uses \
    fake_filenames = [os.path.normpath(name) for name in [
        'a/b/file1.java',
        'a/b/file2.big',
        'a/b/file3.py',
        'file4',
        'not_a_java_file.class']]

    with file_utils.TemporaryDirectory() as tmpdir:
      fake_files = _fake_file_list(fake_filenames)

      _create_fake_files(tmpdir, fake_files)

      mgr = capture.CaptureManager()
      mgr.UploadCapture('my-capture', tmpdir, '')

      write_file.assert_has_calls(
          [mock.call(name, contents) for name, contents in fake_files],
          any_order=True)
      flush_actions.assert_called_with()
      self.AssertErrContains(
          'Could not write file "' + os.path.join('a', 'b', 'file2.big') + '"')

  def testCreateFromJarAndDirectories(self):
    self.StartObjectPatch(contexts, 'CalculateExtendedSourceContexts',
                          return_value=[])
    self.StartObjectPatch(capture.CaptureManager, '_FindCapture',
                          side_effect=self._fake_get_capture)
    self.StartObjectPatch(source.Repo, 'GetWorkspace',
                          side_effect=self._fake_create_ws)
    write_file = self.StartObjectPatch(source.Workspace, 'WriteFile')
    flush_actions = self.StartObjectPatch(source.Workspace,
                                          'FlushPendingActions')
    fake_jar_files = [
        'a/b/file1.java',
        'a/b/file2.java',
        'file3.java',
        'not_a_java_file.class']
    fake_jar = _FakeZipFile(_fake_file_list(fake_jar_files))

    # Normalize names because this test may run on Windows, which uses \
    fake_filenames = [os.path.normpath(name) for name in [
        'dir1/a/b/file1.java',
        'dir1/a/b/file2.py',
        'dir1/file3',
        'dir1/not_a_java_file.class',
        'dir2/a/b/file1.java',
        'dir2/a/b/file2.py',
        'dir2/file3',
        'dir2/not_a_java_file.class']]

    with file_utils.TemporaryDirectory() as tmpdir:
      fake_files = _fake_file_list(fake_filenames)
      _create_fake_files(tmpdir, fake_files)

      with patch('zipfile.ZipFile', return_value=fake_jar):
        mgr = capture.CaptureManager()
        mgr.UploadCapture('dummy_ws', 'dummy.jar', '')
        mgr.UploadCapture('dummy_ws', os.path.join(tmpdir, 'dir1'), 'dir1')
        mgr.UploadCapture('dummy_ws', os.path.join(tmpdir, 'dir2'), 'dir2')

      java_calls = [
          mock.call(name, contents)
          for name, contents in _fake_file_list(fake_jar_files)
          if name.endswith('java')]
      file_calls = [mock.call(name, contents) for name, contents in fake_files]
      write_file.assert_has_calls(java_calls + file_calls, any_order=True)
      flush_actions.assert_called_with()

  def testListCapture(self):
    mgr = capture.CaptureManager()
    fake_workspaces = [
        _FakeWorkspaceInfo(name) for name in [
            capture.CAPTURE_PREFIX + 'cap1',
            'workspace1', 'workspace2', capture.CAPTURE_PREFIX + 'cap2',
            'workspace3', 'workspace4', capture.CAPTURE_PREFIX + 'cap3',
            'workspace5', 'workspace6', capture.CAPTURE_PREFIX + 'cap4',
            'workspace7', 'workspace8', capture.CAPTURE_PREFIX + 'cap5',
        ]]
    self.StartObjectPatch(source.Repo, 'ListWorkspaces',
                          return_value=fake_workspaces)
    i = 1
    for s in mgr.ListCaptures():
      expected = capture.Capture(
          'test_project', capture.CAPTURE_REPO_NAME, 'cap{0}'.format(i))
      self.assertEquals(s, expected)
      i += 1
    self.assertEquals(i, 6)

  def testFindCapture(self):
    mgr = capture.CaptureManager()
    fake_workspaces = [
        _FakeWorkspaceInfo(name) for name in [
            capture.CAPTURE_PREFIX + 'cap1',
            'workspace1', 'workspace2', capture.CAPTURE_PREFIX + 'cap2',
            'workspace3', 'workspace4', capture.CAPTURE_PREFIX + 'cap3',
            'workspace5', 'workspace6', capture.CAPTURE_PREFIX + 'cap4',
            'workspace7', 'workspace8', capture.CAPTURE_PREFIX + 'cap5',
        ]]
    self.StartObjectPatch(source.Repo, 'ListWorkspaces',
                          return_value=fake_workspaces)
    for i in range(1, 6):
      name = 'cap{0}'.format(i)
      cap = mgr._FindCapture(name)
      self.assertEquals(cap, capture.Capture(
          'test_project', capture.CAPTURE_REPO_NAME, name))

if __name__ == '__main__':
  sdk_test_base.main()
