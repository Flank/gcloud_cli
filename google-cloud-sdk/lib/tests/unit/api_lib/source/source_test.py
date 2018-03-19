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

"""Tests for source API wrapper module."""

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.source import source
from googlecloudsdk.api_lib.util import apis
from tests.lib import sdk_test_base


class _SourceMockApiTest(sdk_test_base.WithFakeAuth):
  """Base class for all source mock tests."""

  def SetUp(self):
    self.messages = apis.GetMessagesModule('source', 'v1')
    self.mocked_client = api_mock.Client(apis.GetClientClass('source', 'v1'))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)


class ProjectTest(_SourceMockApiTest):
  """Tests Project class.

  The methods in Project mostly just pass on their arguments to JSON calls,
  so these tests just do minimal verification that there are no invalid
  arguments.
  """

  def SetUp(self):
    self.service = self.mocked_client.projects_repos

  def testGetRepo(self):
    project = source.Project('test project', client=self.mocked_client)
    repo = self.messages.Repo(projectId='test project', name='test_repo',
                              vcs=self.messages.Repo.VcsValueValuesEnum.GIT)
    request = self.messages.SourceProjectsReposGetRequest(
        projectId='test project', repoName='test_repo')
    self.service.Get.Expect(request=request, response=repo)
    self.assertEquals(repo, project.GetRepo(repo.name))

  def testListRepo(self):
    project = source.Project('test project', client=self.mocked_client)
    request = self.messages.SourceProjectsReposListRequest(
        projectId='test project')
    repos = [self.messages.Repo(name='repo-{}'.format(i)) for i in range(3)]
    response = self.messages.ListReposResponse(repos=repos)
    self.service.List.Expect(request, response)
    self.assertEquals(project.ListRepos(), repos)

  def tesCreateRepo(self):
    project = source.Project('test project', client=self.mocked_client)
    repo = self.messages.Repo(
        projectId='test project',
        name='my-repo',
        vcs=self.messages.Repo.VcsValueValuesEnum.GIT)
    self.service.Create.Expect(repo, repo)
    self.assertEquals(project.CreateRepo('my-repo'), repo)

  def tesDeleteRepo(self):
    project = source.Project('test project', client=self.mocked_client)
    request = self.messages.SourceProjectsReposDeleteRequest(
        projectId='test project', repoName='my-repo')
    self.service.Delete.Expect(request, self.messages.Empty())
    project.DeleteRepo('my-repo')


class RepoTest(_SourceMockApiTest):
  """Tests Repo Class."""

  def SetUp(self):
    self.project_id = 'test-project'
    self.repo_name = 'my-repo'
    self.service = self.mocked_client.projects_repos_workspaces

  def testListWorkspaces(self):
    repo = source.Repo(self.project_id, name=self.repo_name,
                       client=self.mocked_client)
    request = self.messages.SourceProjectsReposWorkspacesListRequest(
        projectId=self.project_id, repoName=self.repo_name,
        view=self.messages.SourceProjectsReposWorkspacesListRequest.
        ViewValueValuesEnum.MINIMAL)
    workspaces = [
        self.messages.Workspace(
            id=self.messages.CloudWorkspaceId(name='my-ws-{}'.format(i)))
        for i in range(3)]
    response = self.messages.ListWorkspacesResponse(workspaces=workspaces)
    self.service.List.Expect(request, response)
    self.assertEquals(list(repo.ListWorkspaces()),
                      [source.Workspace(self.project_id, workspace.id.name,
                                        self.repo_name, state=workspace)
                       for workspace in workspaces])

  def testGetWorkspace(self):
    repo = source.Repo(self.project_id, name=self.repo_name,
                       client=self.mocked_client)
    request = self.messages.SourceProjectsReposWorkspacesGetRequest(
        projectId=self.project_id, repoName=self.repo_name,
        name='my-ws')
    workspace = self.messages.Workspace(
        id=self.messages.CloudWorkspaceId(name='my-ws'))
    self.service.Get.Expect(request, workspace)
    self.assertEquals(repo.GetWorkspace('my-ws'),
                      source.Workspace(self.project_id, 'my-ws',
                                       self.repo_name, state=workspace))

  def testCreateWorkspace(self):
    repo = source.Repo(self.project_id, name=self.repo_name,
                       client=self.mocked_client)
    workspace_name = 'my-ws'
    alias_name = 'alias'
    workspace = self.messages.Workspace(
        id=self.messages.CloudWorkspaceId(name=workspace_name),
        alias=alias_name)
    request = self.messages.SourceProjectsReposWorkspacesCreateRequest(
        projectId=self.project_id, repoName=self.repo_name,
        createWorkspaceRequest=self.messages.CreateWorkspaceRequest(
            workspace=workspace))
    self.service.Create.Expect(request, workspace)
    self.assertEquals(repo.CreateWorkspace(workspace_name, alias_name),
                      source.Workspace(self.project_id, workspace_name,
                                       self.repo_name, state=workspace))

  def testDeleteWorkspace(self):
    repo = source.Repo(self.project_id, name=self.repo_name,
                       client=self.mocked_client)
    request = self.messages.SourceProjectsReposWorkspacesDeleteRequest(
        projectId=self.project_id, repoName=self.repo_name, name='my-ws')
    self.service.Delete.Expect(request, self.messages.Empty())
    repo.DeleteWorkspace('my-ws')


class WorkspaceTest(_SourceMockApiTest):
  """Tests Repo Class."""

  def SetUp(self):
    self.project_id = 'test-project'
    self.workspace_name = 'my-ws'
    self.repo_name = 'my-repo'
    self.service = self.mocked_client.projects_repos_workspaces

  def testWriteFile_Buffered(self):
    workspace = source.Workspace(self.project_id, self.workspace_name,
                                 self.repo_name)
    contents = 'Less than threshold'
    workspace.WriteFile('path', contents)

  def testWriteFile_ActionsFlushed(self):
    workspace = source.Workspace(self.project_id, self.workspace_name,
                                 self.repo_name)
    file_size = workspace.SIZE_THRESHOLD / 2
    files = [('path1', '0' * file_size), ('path2', '1' * file_size)]
    actions = [
        self.messages.Action(writeAction=self.messages.WriteAction(
            path=path, contents=contents,
            mode=self.messages.WriteAction.ModeValueValuesEnum.NORMAL))
        for path, contents in files]
    request = self.messages.SourceProjectsReposWorkspacesModifyWorkspaceRequest(
        projectId=self.project_id, repoName=self.repo_name,
        name=self.workspace_name,
        modifyWorkspaceRequest=self.messages.ModifyWorkspaceRequest(
            actions=actions))
    new_workspace = self.messages.Workspace(
        id=self.messages.CloudWorkspaceId(name=self.workspace_name),
        changedFiles=[self.messages.ChangedFileInfo(path=path)
                      for path, _ in files])
    self.service.ModifyWorkspace.Expect(request, new_workspace)
    for path, contents in files:
      workspace.WriteFile(path, contents)

if __name__ == '__main__':
  sdk_test_base.main()
