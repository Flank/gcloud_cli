# -*- coding: utf-8 -*- #
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
"""Test for the git wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import os
import re
import subprocess
import textwrap

from googlecloudsdk.api_lib.source import git
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.source import base
import mock


class GitTest(base.SourceTest):

  def SetUp(self):
    self.git_version_mock = self.StartObjectPatch(subprocess, 'check_output')
    self.git_version_mock.return_value = 'git version 1.7.9'
    self.clone_command_mock = self.StartObjectPatch(subprocess, 'check_call')

  @test_case.Filters.DoNotRunOnWindows
  def testCloneMacOrLinuxGitSupportsHelperButNotEmptyHelper(self):
    properties.VALUES.core.account.Set('fake-git-account')
    self.git_version_mock.return_value = 'git version 2.0.1'

    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path')
    repo_path = os.path.abspath('repo-path')
    self.assertEqual(repo_path, path)
    self.assertEqual([
        mock.call([
            'git', 'clone',
            'https://source.developers.google.com/p/fake-project/r/fake-repo',
            repo_path, '--config', 'credential.helper=', '--config',
            'credential.helper='
            '!gcloud auth git-helper --account=fake-git-account '
            '--ignore-unknown $@'
        ])
    ], self.clone_command_mock.call_args_list)

  @test_case.Filters.RunOnlyOnWindows
  def testCloneRepoWindowsGitSupportsCredHelperButNotEmptyHelper(self):
    self.git_version_mock.return_value = 'git version 2.10.0'

    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path')
    repo_path = os.path.abspath('repo-path')
    self.assertEqual(repo_path, path)
    self.AssertErrContains('gcloud auth print-access-token')
    self.assertEqual([
        mock.call([
            'git', 'clone',
            'https://source.developers.google.com/p/fake-project/r/fake-repo',
            repo_path
        ])
    ], self.clone_command_mock.call_args_list)

  def testCloneRepoGitSupportsEmptyHelper(self):
    properties.VALUES.core.account.Set('fake-git-account')
    self.git_version_mock.return_value = 'git version 2.15.0'

    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path')
    repo_path = os.path.abspath('repo-path')
    self.assertEqual(repo_path, path)
    self.assertEqual([
        mock.call([
            'git', 'clone',
            'https://source.developers.google.com/p/fake-project/r/fake-repo',
            repo_path, '--config', 'credential.helper=', '--config',
            'credential.helper='
            '!gcloud auth git-helper --account=fake-git-account '
            '--ignore-unknown $@'
        ])
    ], self.clone_command_mock.call_args_list)

  def testCloneRepo_DryRun(self):
    properties.VALUES.core.account.Set('fake-git-account')
    self.git_version_mock.return_value = 'git version 2.15.0'

    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path', dry_run=True)
    repo_path = os.path.abspath('repo-path')
    self.assertEqual(repo_path, path)
    self.AssertOutputContains(
        'git clone '
        'https://source.developers.google.com/p/fake-project/r/fake-repo {0} '
        '--config credential.helper= '
        '--config credential.helper='
        '!gcloud auth git-helper --account=fake-git-account '
        '--ignore-unknown $@'.format(repo_path))

  def testCloneRepoOldGitVersion_NoCredentialHelper(self):
    self.git_version_mock.return_value = 'git version 1.7.9'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path', dry_run=True)
    repo_path = os.path.abspath('repo-path')
    self.assertEqual(repo_path, path)
    self.AssertOutputEquals(
        'git clone '
        'https://source.developers.google.com/p/fake-project/r/fake-repo {0}\n'
        .format(repo_path))

  def testCloneRepoOldGitVersion(self):
    self.git_version_mock.return_value = 'git version 1.7.9'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')

    expected_min = '2.0.1'
    if (platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS
       ):
      expected_min = '2.15.0'
    project_repo = git.Git('fake-project', 'fake-repo')
    repo_path = os.path.abspath('repo-path')
    project_repo.Clone(destination_path=repo_path, dry_run=True)
    self.AssertErrContains(
        textwrap.dedent("""\
    WARNING: You are using a Google-hosted repository with a
    git version {current} which is older than {min_version}. If you upgrade
    to {min_version} or later, gcloud can handle authentication to
    this repository. Otherwise, to authenticate, use your Google
    account and the password found by running the following command.
     $ gcloud auth print-access-token
               """.format(current='1.7.9', min_version=expected_min)))
    self.AssertOutputEquals(
        'git clone '
        'https://source.developers.google.com/p/fake-project/r/fake-repo {0}\n'
        .format(repo_path))

  def testCloneRepoDirExistsIsEmpty(self):
    properties.VALUES.core.account.Set('fake-git-account')
    self.git_version_mock.return_value = 'git version 2.15.0'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')

    project_repo = git.Git('fake-project', 'fake-repo')
    path = project_repo.Clone(destination_path='repo-path')
    path_exists_mock = self.StartObjectPatch(os.path, 'exists')
    path_exists_mock.return_value = True
    repo_path = os.path.abspath('repo-path')
    self.assertEqual(repo_path, path)
    self.assertEqual([
        mock.call([
            'git', 'clone',
            'https://source.developers.google.com/p/fake-project/r/fake-repo',
            repo_path, '--config', 'credential.helper=', '--config',
            'credential.helper='
            '!gcloud auth git-helper --account=fake-git-account '
            '--ignore-unknown $@'
        ])
    ], self.clone_command_mock.call_args_list)

  def testCloneRepoDirExistsIsNotEmpty(self):
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    self.StartObjectPatch(os, 'listdir')
    listdir_mock = self.StartObjectPatch(os, 'listdir')
    listdir_mock.return_value = ('test.txt')
    project_repo = git.Git('fake-project', 'fake-repo')
    repo_path = self.CreateTempDir('repo-path')
    with self.assertRaisesRegex(
        git.CannotInitRepositoryException,
        re.escape('Directory path specified exists and is not empty')):
      project_repo.Clone(destination_path=repo_path)

  def testCloneRemoteDoesntExist(self):
    project_repo = git.Git('fake-project', 'fake-repo')
    repo_path = self.CreateTempDir('repo-path')
    project_repo._uri = 'abcd'
    subprocess_mock = self.StartObjectPatch(subprocess, 'check_call')
    subprocess_mock.side_effect = subprocess.CalledProcessError(
        1, ('fatal: repository {0} does not exist'.format(project_repo._uri)))
    with self.assertRaisesRegex(
        git.CannotFetchRepositoryException,
        re.escape('fatal: repository abcd does not exist')):
      project_repo.Clone(destination_path=repo_path)

  def testCloneRepoDirExistsGitNotFound(self):
    self.git_version_mock.side_effect = OSError(errno.ENOENT, 'not found')
    project_repo = git.Git('fake-project', 'fake-repo')
    repo_path = self.CreateTempDir('repo-path')
    with self.assertRaisesRegex(
        git.NoGitException,
        re.escape('Cannot find git. Please install git and try again.')):
      project_repo.Clone(destination_path=repo_path)

  @sdk_test_base.Filters.RunOnlyInBundle
  def testCredentialHelperFindableFromInstall(self):
    with mock.patch.dict('os.environ', {'PATH': config.Paths().sdk_bin_path}):
      gcloud = git._GetGcloudScript()

    self.assertIsNotNone(gcloud)
    self.assertTrue(
        os.path.exists(os.path.join(config.Paths().sdk_bin_path, gcloud)) or
        gcloud == (config.Paths().sdk_bin_path + '/gcloud'))

  def testCredentialHelperGoodGcloudPathFullPathFalse(self):
    with mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath') as find_gcloud:
      find_gcloud.return_value = 'abC/1234/has-hyphen/with_underscore/gcloud'
      gcloud = git._GetGcloudScript()
      # ignore .cmd suffix
      self.assertEqual(gcloud[:6], 'gcloud')

  def testCredentialHelperGoodGcloudPathFullPathTrue(self):
    with mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath') as find_gcloud:
      find_gcloud.return_value = 'abC/1234/has-hyphen/with_underscore/gcloud'
      gcloud = git._GetGcloudScript(full_path=True)
      self.AssertErrNotContains('credential helper may not work correctly')
      self.assertEqual(gcloud, 'abC/1234/has-hyphen/with_underscore/gcloud')

  def testCredentialHelperGcloudWithSpaces(self):
    with mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath') as find_gcloud:
      find_gcloud.return_value = '/path/google cloud SDK/gcloud'
      gcloud = git._GetGcloudScript()
      # ignore .cmd suffix
      self.assertEqual(gcloud[:6], 'gcloud')

  def testCredentialHelperGcloudWithSpacesAndFullPath(self):
    with mock.patch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath') as find_gcloud:
      find_gcloud.return_value = '/path/google cloud SDK/gcloud'
      gcloud = git._GetGcloudScript(full_path=True)
      self.AssertErrContains('credential helper may not work correctly')
      self.assertEqual(gcloud, '/path/google cloud SDK/gcloud')

  def testCredentialHelperNotInPath(self):
    with mock.patch.dict('os.environ', {'PATH': 'bogus'}):
      self.assertRaises(git.GcloudIsNotInPath, git._GetGcloudScript)

  def testForcePushFilesToBranchWithCredHelper(self):
    self.git_version_mock.return_value = 'git version 2.15.0'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    properties.VALUES.core.account.Set('fake-git-account')
    subprocess_mock = self.StartObjectPatch(subprocess, 'check_call')
    cred_helper_command = ('!gcloud auth git-helper '
                           '--account=fake-git-account --ignore-unknown $@')
    temp_path = '/tmp/path'
    self.StartObjectPatch(
        file_utils.TemporaryDirectory, '__enter__', return_value=temp_path)
    self.StartObjectPatch(file_utils, 'RmTree')
    abspath_mock = self.StartObjectPatch(os.path, 'abspath')
    abspath_mock.side_effect = (
        lambda p: p if p.startswith('/') else '/'.join(['/dir', p]))

    repo_url = 'https://source.developers.google.com/p/fake-project/r/fake-repo'
    repo = git.Git('fake-project', 'fake-repo')

    expected_calls = [mock.call(['git', 'init', temp_path])]

    def add_expected_call(*args):
      git_dir = '--git-dir=' + os.path.join(temp_path, '.git')
      work_tree = '--work-tree=/dir'
      expected_calls.append(mock.call(['git', git_dir, work_tree] + list(args)))

    add_expected_call('checkout', '-b', 'branch1')
    add_expected_call('add', '/dir/file1', '/dir/dir2/file2')
    add_expected_call('commit', '-m', 'source capture uploaded from gcloud')
    add_expected_call('config', 'credential.helper', cred_helper_command)
    add_expected_call('remote', 'add', 'origin', repo_url)
    add_expected_call('push', '-f', 'origin', 'branch1')

    repo.ForcePushFilesToBranch(
        'branch1', '/dir', ['/dir/file1', '/dir/dir2/file2'])

    self.assertEqual(expected_calls, subprocess_mock.call_args_list)

    # Test that relative paths are converted to absolute.
    subprocess_mock.reset_mock()
    repo.ForcePushFilesToBranch('branch1', '/dir', ['file1', 'dir2/file2'])

    self.assertEqual(expected_calls, subprocess_mock.call_args_list)

  def testForcePushFilesToBranchNoCredHelper(self):
    self.git_version_mock.return_value = 'git version 1.7.9'
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    properties.VALUES.core.account.Set('fake-git-account')
    subprocess_mock = self.StartObjectPatch(subprocess, 'check_call')
    temp_path = '/tmp/path'
    self.StartObjectPatch(
        file_utils.TemporaryDirectory, '__enter__', return_value=temp_path)
    self.StartObjectPatch(file_utils, 'RmTree')
    abspath_mock = self.StartObjectPatch(os.path, 'abspath')
    abspath_mock.side_effect = (
        lambda p: p if p.startswith('/') else '/'.join(['/dir', p]))

    repo_url = 'https://source.developers.google.com/p/fake-project/r/fake-repo'
    repo = git.Git('fake-project', 'fake-repo')

    expected_calls = [mock.call(['git', 'init', temp_path])]

    def add_expected_call(*args):
      git_dir = '--git-dir=' + os.path.join(temp_path, '.git')
      work_tree = '--work-tree=/dir'
      expected_calls.append(mock.call(['git', git_dir, work_tree] + list(args)))

    add_expected_call('checkout', '-b', 'branch1')
    add_expected_call('add', '/dir/file1', '/dir/dir2/file2')
    add_expected_call('commit', '-m', 'source capture uploaded from gcloud')
    add_expected_call('remote', 'add', 'origin', repo_url)
    add_expected_call('push', '-f', 'origin', 'branch1')

    repo.ForcePushFilesToBranch(
        'branch1', '/dir', ['/dir/file1', '/dir/dir2/file2'])

    self.assertEqual(expected_calls, subprocess_mock.call_args_list)

  def testForcePushFilesToBranchGitSubdirectory(self):
    repo = git.Git('fake-project', 'fake-repo')
    with self.assertRaisesRegex(
        git.CannotPushToRepositoryException,
        (r"Can't upload the file tree.*abc")):
      repo.ForcePushFilesToBranch('branch1', '/dir', ['/dir/.git/abc'])

    with self.assertRaisesRegex(
        git.CannotPushToRepositoryException,
        (r"Can't upload the file tree.*gitignore")):
      repo.ForcePushFilesToBranch('branch1', '/dir', ['/dir/sub/.gitignore'])


class GitVersionTest(base.SourceTest):

  def SetUp(self):
    self.min_version = (2, 0, 1)
    self.min_windows_version = (2, 15, 0)
    self.subprocess_mock = self.StartObjectPatch(subprocess, 'check_output')

  def testMatchesMinVersionWhenGreater(self):
    self.subprocess_mock.return_value = 'git version 2.1.1'
    self.assertEqual(True, git.CheckGitVersion(self.min_version))

  def testMatchesMinVersionWhenEqual(self):
    self.subprocess_mock.return_value = 'git version 2.0.1'
    self.assertEqual(True, git.CheckGitVersion(self.min_version))

  def testNoCheckMinVersion(self):
    self.subprocess_mock.return_value = 'git version 0.0.0'
    self.assertEqual(True, git.CheckGitVersion())

  def testRaisesWhenMinVersionIsSmaller(self):
    self.subprocess_mock.return_value = 'git version 1.8.9'
    with self.assertRaisesRegex(
        git.GitVersionException,
        (r'Your git version .*\..* is older than the minimum version (\d+)\.')):
      git.CheckGitVersion(self.min_version)

  def testRaisesWhenNoVersion(self):
    self.subprocess_mock.return_value = ''
    with self.assertRaisesRegex(git.InvalidGitException,
                                ('The git version string is empty.')):
      git.CheckGitVersion(self.min_version)

  def testRaisesWhenBadOutput(self):
    self.subprocess_mock.return_value = 'sit versi'
    with self.assertRaisesRegex(
        git.InvalidGitException,
        ('The git version string must start with git version')):
      git.CheckGitVersion(self.min_version)

  def testRaisesWhenBadVersionNumber(self):
    self.subprocess_mock.return_value = 'git version x'
    with self.assertRaisesRegex(
        git.InvalidGitException,
        ('The git version string must contain a version number')):
      git.CheckGitVersion(self.min_version)

  def testRaisesWhenNotFound(self):
    self.subprocess_mock.side_effect = OSError(errno.ENOENT, 'not found')
    with self.assertRaisesRegex(
        git.NoGitException,
        ('Cannot find git. Please install git and try again.')):
      git.CheckGitVersion(self.min_version)


@mock.patch('subprocess.check_output')
class GitCredentialHelperCheckTest(base.SourceTest):

  def SetUp(self):
    self.StartObjectPatch(git, '_GetGcloudScript', return_value='gcloud')
    self.StartObjectPatch(git, 'CheckGitVersion', return_value=True)
    self.StartObjectPatch(
        properties.VALUES.core.account, 'Get', return_value='somevalue')
    self.StartObjectPatch(subprocess, 'check_call')

  def testEmptyCredentialHelper(self, subprocess_mock):
    subprocess_mock.return_value = 'credential.helper='
    project_repo = git.Git('fake-project', 'fake-repo')
    project_repo.Clone('dest', dry_run=True)
    self.AssertErrNotContains('cancel.')

  def testNoCredentialHelper(self, subprocess_mock):
    subprocess_mock.return_value = ''
    project_repo = git.Git('fake-project', 'fake-repo')
    project_repo.Clone('dest', dry_run=True)
    self.AssertErrNotContains('cancel')


if __name__ == '__main__':
  test_case.main()
