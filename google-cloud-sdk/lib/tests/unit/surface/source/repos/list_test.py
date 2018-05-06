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
"""Test of the 'source list' command."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.source import base

SAMPLE_OUTPUT = """\
REPO_NAME           PROJECT_ID URL
size_zero  myproject      https://
test-repo           myproject     https://
"""

SAMPLE_OUTPUT_SLASHES = """\
REPO_NAME           PROJECT_ID URL
size_zero  myproject      https://
this/repo/name/has/slashes           myproject     https://
"""

SAMPLE_OUTPUT_PAGE_SIZE_ONE = """\
REPO_NAME           PROJECT_ID URL
size_zero  myproject      https://
REPO_NAME           PROJECT_ID URL
test-repo           myproject     https://
"""

SAMPLE_OUTPUT_LIMIT_ONE = """\
REPO_NAME           PROJECT_ID URL
size_zero  myproject      https://
"""

MIRROR_OUTPUT = """\
REPO_NAME           PROJECT_ID  URL
has-mirror           myproject   https://mirror
"""


class ListTest(base.SourceSdkTest):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('sourcerepo', 'v1')
    self.mock_client = mock.Client(
        core_apis.GetClientClass('sourcerepo', 'v1'),
        real_client=core_apis.GetClientInstance(
            'sourcerepo', 'v1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.list_name = 'projects/' + self.Project()

  def testListWhenEmpty(self):
    self.mock_client.projects_repos.List.Expect(
        self.messages.SourcerepoProjectsReposListRequest(name=self.list_name),
        self.messages.ListReposResponse(repos=[]))
    result = self.RunSourceRepos(['list', '--format=disable'])
    result = list(result)  # Consume iterator and get a real list
    self.assertEqual([], result)

  def testListReturnsBackendList(self):
    repo_list = [
        self.messages.Repo(
            name='projects/myproject/repos/myrepo', size=0, url='http://')
    ]
    self.mock_client.projects_repos.List.Expect(
        self.messages.SourcerepoProjectsReposListRequest(name=self.list_name),
        self.messages.ListReposResponse(repos=repo_list))

    result = self.RunSourceRepos(['list', '--format=disable'])
    result = list(result)  # Consume iterator and get a real list
    self.assertEqual(repo_list, result)

  def testDisplay(self):
    repo_list = [
        # Note that size is None here, but needs to be printed as a zero
        self.messages.Repo(
            name='projects/myproject/repos/size_zero', url='https://'),
        self.messages.Repo(
            name='projects/myproject/repos/test-repo', size=2, url='https://')
    ]
    self.mock_client.projects_repos.List.Expect(
        self.messages.SourcerepoProjectsReposListRequest(name=self.list_name),
        self.messages.ListReposResponse(repos=repo_list))

    self.RunSourceRepos(['list'])
    self.AssertOutputEquals(SAMPLE_OUTPUT, normalize_space=True)
    self.AssertErrEquals('')

  def testDisplayWithSlashes(self):
    repo_list = [
        # Note that size is None here, but needs to be printed as a zero
        self.messages.Repo(
            name='projects/myproject/repos/size_zero', url='https://'),
        self.messages.Repo(
            name='projects/myproject/repos/this/repo/name/has/slashes',
            size=2,
            url='https://')
    ]
    self.mock_client.projects_repos.List.Expect(
        self.messages.SourcerepoProjectsReposListRequest(name=self.list_name),
        self.messages.ListReposResponse(repos=repo_list))

    self.RunSourceRepos(['list'])
    self.AssertOutputEquals(SAMPLE_OUTPUT_SLASHES, normalize_space=True)
    self.AssertErrEquals('')

  def testDisplayRepoWithMirror(self):
    repo_list = [
        self.messages.Repo(
            name='projects/myproject/repos/has-mirror',
            size=2,
            url='https://csr',
            mirrorConfig=self.messages.MirrorConfig(url='https://mirror'))
    ]
    self.mock_client.projects_repos.List.Expect(
        self.messages.SourcerepoProjectsReposListRequest(name=self.list_name),
        self.messages.ListReposResponse(repos=repo_list))
    self.RunSourceRepos(['list'])
    self.AssertOutputEquals(MIRROR_OUTPUT, normalize_space=True)
    self.AssertErrEquals('')

  def testDisplayPageSize(self):
    repo1 = self.messages.Repo(
        name='projects/myproject/repos/size_zero', url='https://')
    repo2 = self.messages.Repo(
        name='projects/myproject/repos/test-repo', size=2, url='https://')
    self.mock_client.projects_repos.List.Expect(
        self.messages.SourcerepoProjectsReposListRequest(
            name=self.list_name, pageSize=1),
        self.messages.ListReposResponse(
            nextPageToken='keepgoing', repos=[repo1]))
    self.mock_client.projects_repos.List.Expect(
        self.messages.SourcerepoProjectsReposListRequest(
            name=self.list_name, pageToken='keepgoing', pageSize=1),
        self.messages.ListReposResponse(repos=[repo2]))
    self.RunSourceRepos(['list', '--page-size=1'])
    self.AssertOutputEquals(SAMPLE_OUTPUT_PAGE_SIZE_ONE, normalize_space=True)
    self.AssertErrEquals('')

  def testDisplayLimit(self):
    repo_list = [
        self.messages.Repo(
            name='projects/myproject/repos/size_zero', url='https://'),
        self.messages.Repo(
            name='projects/myproject/repos/test-repo', size=2, url='https://')
    ]
    self.mock_client.projects_repos.List.Expect(
        self.messages.SourcerepoProjectsReposListRequest(name=self.list_name),
        self.messages.ListReposResponse(repos=repo_list))
    self.RunSourceRepos(['list', '--limit=1'])
    self.AssertOutputEquals(SAMPLE_OUTPUT_LIMIT_ONE, normalize_space=True)
    self.AssertErrEquals('')


if __name__ == '__main__':
  test_case.main()
