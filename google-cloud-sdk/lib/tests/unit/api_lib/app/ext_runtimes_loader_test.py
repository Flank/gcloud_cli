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

# Note: this file is part of the sdk-ext-runtime package.  It gets copied into
# individual GAE runtime modules so that they can be easily deployed.

"""Test suite for external runtime loaders."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shutil
import socket
import stat
import threading
from wsgiref import simple_server

from dulwich import objects
from dulwich import repo
from dulwich import server
from dulwich import web

from googlecloudsdk.api_lib.app.ext_runtimes import loader
from tests.lib import sdk_test_base
from tests.lib import test_case
import six


class WSGIServerLoggerIPv6(web.WSGIServerLogger):
  """Wrapper around WSGIServerLogger for compatibility with IPV6."""
  address_family = socket.AF_INET6


class TCPGitServerIPv6(server.TCPGitServer):
  """Wrapper around TCPGitServer for compatibility with IPV6."""
  address_family = socket.AF_INET6


@sdk_test_base.Filters.DoNotRunOnWindows
@test_case.Filters.DoNotRunOnPy3('Deprecated command; no py3 support')
class LoaderTests(sdk_test_base.SdkBase):

  def SetUp(self):
    self.repo_path = os.path.join(self.temp_path, 'repo')
    self.repo_clone = os.path.join(self.temp_path, 'repo_clone')
    self.server = None

  def TearDown(self):
    if self.server:
      self.server.shutdown()
      self.server_thread.join()

    # Delete repo_clone, which may have been set to read-only in the test.
    def ChmodAndDelete(delete_func, path, exception):
      # We have to change the permissions on the parent directory in the
      # course of this.
      parent = os.path.dirname(path)
      file_stat = os.stat(parent)[0]
      os.chmod(parent, file_stat | stat.S_IWRITE)

      file_stat = os.stat(path)[0]
      os.chmod(path, file_stat | stat.S_IWRITE)

      delete_func(path)
    if os.path.exists(self.repo_clone):
      shutil.rmtree(self.repo_clone, onerror=ChmodAndDelete)

  def _WSGIServerClass(self):
    if socket.has_ipv6:
      return WSGIServerLoggerIPv6
    return web.WSGIServerLogger

  def _GitServerClass(self):
    if socket.has_ipv6:
      return TCPGitServerIPv6
    return server.TCPGitServer

  def _CommitFile(self, contents, commit_message, branch=None):
    blob = objects.Blob.from_string(contents)
    tree = objects.Tree()
    tree.add(b'myfile', 0o100644, blob.id)
    self.repo.object_store.add_object(blob)
    self.repo.object_store.add_object(tree)
    commit_id = self.repo.do_commit(tree=tree.id, message=commit_message,
                                    ref=branch,
                                    committer='User Larry <user@example.com>')
    self.repo[b'HEAD'] = commit_id
    return commit_id

  def _MakeRepo(self, set_latest=True, start_server=True, branch=None):
    """Make a git repository to test against.

    Args:
      set_latest: (bool) Create 'refs/tags/latest' pointing at the first
        commit.
      start_server: (bool) Start an HTTP server.
      branch: (str or None) branch to check in on.
    """
    self.repo = repo.Repo.init(self.repo_path, mkdir=True)

    commit_id = self._CommitFile(b'first contents', b'first commit', branch)
    if set_latest:
      self.repo[b'refs/tags/latest'] = commit_id

    # This second commit will just show up under refs/heads/main, we add it
    # to verify that we're pulling from "latest" tag, and not from "main".
    self._CommitFile(b'second contents', b'second commit')

    if start_server:
      backend = server.DictBackend({'/': self.repo})
      self.server = (
          simple_server.make_server('localhost', 0,
                                    web.make_wsgi_chain(backend),
                                    handler_class=web.WSGIRequestHandlerLogger,
                                    server_class=self._WSGIServerClass()))
      self.server_thread = threading.Thread(target=self.server.serve_forever)
      self.server_thread.start()

  def _GetRepoUrl(self):
    return 'http://localhost:{port}/'.format(port=self.server.server_port)

  def testBasicFlow(self):
    self._MakeRepo()
    loader.InstallRuntimeDef(self._GetRepoUrl(), self.repo_clone)
    self.AssertFileExistsWithContents(b'first contents', self.repo_clone,
                                      'myfile')

    # Verify that updating an existing repo works.  (We do a commit and then
    # update the latest tag to verify that both tags and objects get fetched).
    self._CommitFile(b'third contents', b'third commit')
    self.repo[b'refs/tags/latest'] = self.repo[b'refs/heads/main']
    loader.InstallRuntimeDef(self._GetRepoUrl(), self.repo_clone)
    self.AssertFileExistsWithContents(b'third contents', self.repo_clone,
                                      'myfile')

  def testTraditionalClients(self):
    self._MakeRepo(start_server=False)
    self.server = (
        self._GitServerClass()(server.FileSystemBackend(self.repo_path),
                               'localhost', 0))
    self.server_thread = threading.Thread(target=self.server.serve_forever)
    self.server_thread.start()

    loader.InstallRuntimeDef(
        'git://localhost:{port}'.format(port=self.server.server_address[1]),
        self.repo_clone)

    self.AssertFileExistsWithContents(b'first contents', self.repo_clone,
                                      'myfile')

  def testLocalRepo(self):
    self._MakeRepo(start_server=False)
    loader.InstallRuntimeDef(self.repo_path, self.repo_clone)

    self.AssertFileExistsWithContents(b'first contents', self.repo_clone,
                                      'myfile')

  def testNoLatestTag(self):
    self._MakeRepo(set_latest=False)
    loader.InstallRuntimeDef(self._GetRepoUrl(), self.repo_clone)

    # Since there's no "latest" tag, we should get the head of "main" which
    # will be the second commit.
    self.AssertFileExistsWithContents(b'second contents', self.repo_clone,
                                      'myfile')

  # Windows interprets "bogus:protocol" as a path and generates a WindowsError.
  @sdk_test_base.Filters.DoNotRunOnWindows
  def testInvalidURL(self):
    with self.assertRaises(loader.RepositoryCommunicationError):
      loader.InstallRuntimeDef('bogus:protocol', self.repo_clone)

  def testMissingTargetBaseDirectory(self):
    self._MakeRepo()
    with self.assertRaises(loader.InvalidTargetDirectoryError):
      loader.InstallRuntimeDef(self._GetRepoUrl(),
                               os.path.join(self.temp_path, 'bogus', 'clone'))

  def testNonGitTargetDirectory(self):
    self._MakeRepo()
    os.mkdir(self.repo_clone)
    with self.assertRaises(loader.InvalidTargetDirectoryError):
      loader.InstallRuntimeDef(self._GetRepoUrl(),
                               os.path.join(self.temp_path, 'bogus', 'clone'))

  def testReadonlyTargetDirectory(self):

    # Install a new repo, then change the original repo.
    self._MakeRepo()
    loader.InstallRuntimeDef(self._GetRepoUrl(), self.repo_clone)
    self._CommitFile(b'third contents', b'third commit')
    self.repo[b'refs/tags/latest'] = self.repo[b'refs/heads/main']

    # Make the files in the target dir readonly.
    for dirpath, dirnames, filenames in os.walk(six.text_type(self.repo_clone)):
      for name in filenames:
        full_name = os.path.join(dirpath, name)
        os.chmod(full_name, stat.S_IREAD)

    with self.assertRaises(loader.InvalidTargetDirectoryError):
      loader.InstallRuntimeDef(self._GetRepoUrl(), self.repo_clone)

    # Make all the directories read-only.
    for dirpath, dirnames, filenames in os.walk(six.text_type(self.repo_clone)):
      for name in dirnames:
        full_name = os.path.join(dirpath, name)
        file_stat = os.stat(full_name)[0]
        os.chmod(full_name, file_stat & ~stat.S_IWRITE)

    with self.assertRaises(loader.InvalidTargetDirectoryError):
      loader.InstallRuntimeDef(self._GetRepoUrl(), self.repo_clone)

  # The following two tests should also happen for fetching from an
  # empty or divergent repository after cloning from a good repository.
  # Unfortunately, dulwich doesn't generate an error in those cases :-/

  def testCreateFromEmptyRepo(self):
    self.repo = repo.Repo.init(self.repo_path, mkdir=True)
    with self.assertRaises(loader.InvalidRepositoryError):
      loader.InstallRuntimeDef(self.repo_path, self.repo_clone)

  def testCreateFromNoMainBranch(self):
    self._MakeRepo(set_latest=False, start_server=False,
                   branch='refs/heads/foo')
    loader.InstallRuntimeDef(self.repo_path, self.repo_clone)

if __name__ == '__main__':
  test_case.main()
