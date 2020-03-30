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
"""Test of the 'source clone' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as client_mock
from googlecloudsdk.api_lib.source import git
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as c_exc
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.source import base
import mock


class RepoCloneTestGA(base.SourceSdkTest, sdk_test_base.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('sourcerepo', 'v1')
    self.mock_client = client_mock.Client(
        core_apis.GetClientClass('sourcerepo', 'v1'),
        real_client=core_apis.GetClientInstance(
            'sourcerepo', 'v1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testClone(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/' + self.Project() + '/repos/default'),
        self.messages.Repo(name='default', url='https'))
    with mock.patch.object(git.Git, 'Clone', autospec=True) as clone_mock:
      clone_mock.return_value = 'default'
      self.Run(['source', 'repos', 'clone', 'default'])
      clone_mock.assert_called_once_with(
          mock.ANY, full_path=False, destination_path='default', dry_run=False)
      self.AssertErrContains('Project [{0}] repository [default] was'
                             ' cloned to [default].\n'.format(self.Project()))

  def testCloneDryRun(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/' + self.Project() + '/repos/default'),
        self.messages.Repo(name='default', url='https'))
    with mock.patch.object(git.Git, 'Clone', autospec=True) as clone_mock:
      clone_mock.return_value = 'default'
      self.Run(['source', 'repos', 'clone', 'default', '--dry-run'])
      clone_mock.assert_called_once_with(
          mock.ANY, full_path=False, destination_path='default', dry_run=True)
      self.AssertErrNotContains('was cloned')

  def testCloneWithDestination(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/' + self.Project() + '/repos/my-repo'),
        self.messages.Repo(name='my-repo', url='https'))
    with mock.patch.object(git.Git, 'Clone', autospec=True) as clone_mock:
      clone_mock.return_value = 'my-repo-path'
      self.Run(['source', 'repos', 'clone', 'my-repo', 'my-repo-path'])
      clone_mock.assert_called_once_with(
          mock.ANY,
          full_path=False,
          destination_path='my-repo-path',
          dry_run=False)
      self.AssertErrContains('Project [{0}] repository [my-repo] was cloned to '
                             '[my-repo-path].\n'.format(self.Project()))

  def testCloneFails(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/' + self.Project() + '/repos/my-repo'),
        self.messages.Repo(name='my-repo', url='https'))
    with mock.patch.object(git.Git, 'Clone', autospec=True) as clone_mock:
      clone_mock.return_value = None
      self.Run(['source', 'repos', 'clone', 'my-repo'])
      clone_mock.assert_called_once_with(
          mock.ANY, full_path=False, destination_path='my-repo', dry_run=False)
      self.assertEqual('', self.GetErr())

  def testGetRepoRaisesPermissionDenied(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/' + self.Project() + '/repos/my-repo'),
        exception=http_error.MakeHttpError(code=403))
    with self.assertRaises(exceptions.HttpException):
      self.RunSourceRepos(['clone', 'my-repo'])
      self.AssertErrContains('PERMISSION_DENIED')

  def testGetRepoRaisesNotFound(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/' + self.Project() + '/repos/my-repo'),
        exception=http_error.MakeHttpError(code=404))
    with self.assertRaises(exceptions.HttpException):
      self.RunSourceRepos(['clone', 'my-repo'])
      self.AssertErrContains('NOT_FOUND')


class RepoCloneTestBeta(RepoCloneTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class RepoCloneTestAlpha(RepoCloneTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class CloneTestGaOnly(base.SourceSdkTest, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('sourcerepo', 'v1')
    self.mock_client = client_mock.Client(
        core_apis.GetClientClass('sourcerepo', 'v1'),
        real_client=core_apis.GetClientInstance(
            'sourcerepo', 'v1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testFullPathRaisesException(self):
    err = """\
 --use-full-gcloud-path flag is available in one or more alternate release tracks. Try:

  gcloud alpha source repos clone --use-full-gcloud-path
  gcloud beta source repos clone --use-full-gcloud-path
"""
    with self.AssertRaisesArgumentErrorRegexp(
        err):
      self.RunSourceRepos(['clone', 'default', '--use-full-gcloud-path'])

  def testCloneMirror(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/' + self.Project() + '/repos/is-mirror'),
        self.messages.Repo(
            name='is-mirror',
            url='https',
            mirrorConfig=self.messages.MirrorConfig(url='someurl')))
    with mock.patch.object(git.Git, 'Clone', autospec=True) as clone_mock:
      clone_mock.return_value = 'is-mirror'
      self.Run(['source', 'repos', 'clone', 'is-mirror'])
      clone_mock.assert_called_once_with(
          mock.ANY,
          full_path=False,
          destination_path='is-mirror',
          dry_run=False)
      self.AssertErrContains(
          'WARNING: Repository "is-mirror" in project "fake-project" is a '
          'mirror. Pushing to this clone will have no effect.')


class CloneTestBetaOnly(base.SourceSdkTest, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.messages = core_apis.GetMessagesModule('sourcerepo', 'v1')
    self.mock_client = client_mock.Client(
        core_apis.GetClientClass('sourcerepo', 'v1'),
        real_client=core_apis.GetClientInstance(
            'sourcerepo', 'v1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testCloneWithMirrored(self):
    with mock.patch.object(git.Git, 'Clone', autospec=True) as clone_mock:
      self.mock_client.projects_repos.Get.Expect(
          self.messages.SourcerepoProjectsReposGetRequest(
              name='projects/' + self.Project() + '/repos/is-mirror'),
          self.messages.Repo(
              name='is-mirror',
              url='https',
              mirrorConfig=self.messages.MirrorConfig(url='someurl')))
      with self.AssertRaisesExceptionRegexp(
          c_exc.InvalidArgumentException,
          (r'Repository ".*" in project ".*" is a '
           'mirror. Clone the mirrored repository '
           'directly')):
        self.RunSourceRepos(['clone', 'is-mirror'])
        clone_mock.assert_not_called()

  def testCloneWithFullPath(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(
            name='projects/' + self.Project() + '/repos/default'),
        self.messages.Repo(name='default', url='https'))
    with mock.patch.object(git.Git, 'Clone', autospec=True) as clone_mock:
      clone_mock.return_value = 'default'
      self.RunSourceRepos(['clone', 'default', '--use-full-gcloud-path'])
      clone_mock.assert_called_once_with(
          mock.ANY, full_path=True, dry_run=False, destination_path='default')
      self.AssertErrContains('Project [{0}] repository [default] was cloned to '
                             '[default].\n'.format(self.Project()))


if __name__ == '__main__':
  test_case.main()
