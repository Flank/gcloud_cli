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
"""Tests for sourcerepo API wrapper module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.source.repos import sourcerepo
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from six.moves import range  # pylint: disable=redefined-builtin


def _GetRelativeName(project, repo_name):
  res = resources.REGISTRY.Parse(
      repo_name,
      params={'projectsId': project},
      collection='sourcerepo.projects.repos')
  return res.RelativeName()


class _SourceRepoMockApiTest(sdk_test_base.WithFakeAuth):
  """Base class for all sourcerepo mock tests."""

  def Project(self):
    return 'fake-project'

  def SetUp(self):
    self.messages = apis.GetMessagesModule('sourcerepo', 'v1')
    properties.VALUES.core.project.Set(self.Project())
    self.mocked_client = api_mock.Client(
        apis.GetClientClass('sourcerepo', 'v1'))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.source_handler = sourcerepo.Source(self.mocked_client)

  def testListReposWhenEmpty(self):
    res = resources.REGISTRY.Parse(
        None,
        params={'projectsId': self.Project},
        collection='sourcerepo.projects')
    request = self.messages.SourcerepoProjectsReposListRequest(
        name=res.RelativeName())
    self.mocked_client.projects_repos.List.Expect(
        request=request, response=self.messages.ListReposResponse(repos=[]))
    self.assertEqual([], list(self.source_handler.ListRepos(res)))

  def testListReposReturnsBackendList(self):
    res = resources.REGISTRY.Parse(
        None,
        params={'projectsId': 'testproject'},
        collection='sourcerepo.projects')
    repo_list = [
        self.messages.Repo(
            name=_GetRelativeName('testproject', str(i)),
            size=24601,
            url='https://host/p/proj/r/{0}'.format(i))  # NOTYPO
        for i in range(0, 10)
    ]
    request = self.messages.SourcerepoProjectsReposListRequest(
        name='projects/testproject')
    self.mocked_client.projects_repos.List.Expect(
        request=request,
        response=self.messages.ListReposResponse(repos=repo_list))
    self.assertEqual(repo_list, list(self.source_handler.ListRepos(res)))

  def testGetRepo(self):
    res = resources.REGISTRY.Parse(
        'test_repo',
        params={'projectsId': 'testproject'},
        collection='sourcerepo.projects.repos')
    repo = self.messages.Repo(
        name=_GetRelativeName('testproject', 'test_repo'),
        size=24601,
        url='http://stuff/more/')
    request = self.messages.SourcerepoProjectsReposGetRequest(
        name=_GetRelativeName('testproject', 'test_repo'))
    self.mocked_client.projects_repos.Get.Expect(request=request, response=repo)
    self.assertEqual(repo, self.source_handler.GetRepo(res))

  def testCreateRepo(self):
    proj_res = resources.REGISTRY.Create(
        'sourcerepo.projects', projectsId=self.Project)
    res = resources.REGISTRY.Parse(
        'repo1',
        params={'projectsId': self.Project},
        collection='sourcerepo.projects.repos')
    request = self.messages.SourcerepoProjectsReposCreateRequest(
        parent=proj_res.RelativeName(),
        repo=self.messages.Repo(name=_GetRelativeName(self.Project, 'repo1')))
    response = self.messages.Repo(
        name=res.RelativeName(), size=0, url='http://')
    self.mocked_client.projects_repos.Create.Expect(
        request=request, response=response)
    self.assertEqual(response, self.source_handler.CreateRepo(res))

  def testGetIamPolicy(self):
    res = resources.REGISTRY.Parse(
        'test_repo',
        params={'projectsId': 'testproject'},
        collection='sourcerepo.projects.repos')
    request = self.messages.SourcerepoProjectsReposGetIamPolicyRequest(
        resource=res.RelativeName())
    response = self.messages.Policy()
    self.mocked_client.projects_repos.GetIamPolicy.Expect(
        request=request, response=response)
    self.assertEqual(response, self.source_handler.GetIamPolicy(res))

  def testSetIamPolicy(self):
    res = resources.REGISTRY.Parse(
        'test_repo',
        params={'projectsId': 'testproject'},
        collection='sourcerepo.projects.repos')
    policy = self.messages.Policy()
    set_req = self.messages.SetIamPolicyRequest(policy=policy)
    request = self.messages.SourcerepoProjectsReposSetIamPolicyRequest(
        resource=res.RelativeName(), setIamPolicyRequest=set_req)
    self.mocked_client.projects_repos.SetIamPolicy.Expect(
        request=request, response=policy)
    self.assertEqual(policy, self.source_handler.SetIamPolicy(res, policy))

  def testParseRepoFails(self):
    properties.VALUES.core.project.Set(None)
    with self.assertRaises(sourcerepo.RepoResourceError):
      sourcerepo.ParseRepo('reponame')


if __name__ == '__main__':
  sdk_test_base.main()
