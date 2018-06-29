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
from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib.surface.source import base

from six.moves import range  # pylint: disable=redefined-builtin


def _GetRelativeName(project, repo_name):
  res = resources.REGISTRY.Parse(
      repo_name,
      params={'projectsId': project},
      collection='sourcerepo.projects.repos')
  return res.RelativeName()


class SourceRepoMockApiTest(base.SourceTestBase):
  """Base class for all repo api tests."""

  def Project(self):
    return 'fake-project'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())
    self.source_handler = sourcerepo.Source()
    self.repo_ref = resources.REGISTRY.Parse(
        'test_repo',
        params={'projectsId': 'testproject'},
        collection='sourcerepo.projects.repos')

  def testListReposWhenEmpty(self):
    res = resources.REGISTRY.Parse(
        None,
        params={'projectsId': self.Project},
        collection='sourcerepo.projects')
    request = self.messages.SourcerepoProjectsReposListRequest(
        name=res.RelativeName())
    self.client.projects_repos.List.Expect(
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
    self.client.projects_repos.List.Expect(
        request=request,
        response=self.messages.ListReposResponse(repos=repo_list))
    self.assertEqual(repo_list, list(self.source_handler.ListRepos(res)))

  def testGetRepo(self):
    repo = self.messages.Repo(
        name=_GetRelativeName('testproject', 'test_repo'),
        size=24601,
        url='http://stuff/more/')
    request = self.messages.SourcerepoProjectsReposGetRequest(
        name=_GetRelativeName('testproject', 'test_repo'))
    self.client.projects_repos.Get.Expect(request=request, response=repo)
    self.assertEqual(repo, self.source_handler.GetRepo(self.repo_ref))

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
    self.client.projects_repos.Create.Expect(request=request, response=response)
    self.assertEqual(response, self.source_handler.CreateRepo(res))

  def testGetIamPolicy(self):
    request = self.messages.SourcerepoProjectsReposGetIamPolicyRequest(
        resource=self.repo_ref.RelativeName())
    response = self.messages.Policy()
    self.client.projects_repos.GetIamPolicy.Expect(
        request=request, response=response)
    self.assertEqual(response, self.source_handler.GetIamPolicy(self.repo_ref))

  def testSetIamPolicy(self):
    policy = self.messages.Policy()
    set_req = self.messages.SetIamPolicyRequest(policy=policy)
    request = self.messages.SourcerepoProjectsReposSetIamPolicyRequest(
        resource=self.repo_ref.RelativeName(), setIamPolicyRequest=set_req)
    self.client.projects_repos.SetIamPolicy.Expect(
        request=request, response=policy)
    self.assertEqual(policy,
                     self.source_handler.SetIamPolicy(self.repo_ref, policy))

  def testPatch_topic(self):
    topic_name = 'projects/my-project/topics/aa'
    repo = self.messages.Repo(
        name=self.repo_ref.RelativeName(),
        pubsubConfigs=self.messages.Repo.PubsubConfigsValue(
            additionalProperties=[
                self.messages.Repo.PubsubConfigsValue.AdditionalProperty(
                    key=topic_name, value=self._CreatePubsubConfig(topic_name))
            ]))
    self._ExpectPatchRepo(repo)
    self.assertEqual(repo, self.source_handler.PatchRepo(repo))


if __name__ == '__main__':
  sdk_test_base.main()
