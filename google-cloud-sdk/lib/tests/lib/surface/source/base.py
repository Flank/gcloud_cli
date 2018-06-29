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
"""Base classes for repos tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


_API_NAME = 'sourcerepo'
_API_VERSION = 'v1'


class SourceTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for Cloud Source unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.client = mock.Client(
        client_class=apis.GetClientClass(_API_NAME, _API_VERSION))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule(_API_NAME, _API_VERSION)

  def _GetProjectRef(self, project_name=None):
    return resources.REGISTRY.Parse(
        None,
        params={'projectsId': project_name or self.Project},
        collection='sourcerepo.projects')

  def _GetRepoRef(self, repo_name='my-repo'):
    return resources.REGISTRY.Parse(
        repo_name,
        params={'projectsId': self.Project()},
        collection='sourcerepo.projects.repos')

  def _CreatePubsubConfig(self,
                          name,
                          message_format='json',
                          service_account=None):
    format_enums = self.messages.PubsubConfig.MessageFormatValueValuesEnum
    if message_format == 'json':
      msgs_format = format_enums.JSON
    else:
      msgs_format = format_enums.PROTOBUF

    return self.messages.PubsubConfig(
        topic=name,
        messageFormat=msgs_format,
        serviceAccountEmail=service_account)

  def _ExpectGetRepo(self, repo_ref, repo):
    req = self.messages.SourcerepoProjectsReposGetRequest(
        name=repo_ref.RelativeName())
    self.client.projects_repos.Get.Expect(request=req, response=repo)

  def _ExpectPatchRepo(self, repo, update_mask='pubsubConfigs'):
    req = self.messages.SourcerepoProjectsReposPatchRequest(
        name=repo.name,
        updateRepoRequest=self.messages.UpdateRepoRequest(
            repo=repo, updateMask=update_mask))
    self.client.projects_repos.Patch.Expect(request=req, response=repo)

  def _ExpectGetProjectConfig(self, project_ref, project_config):
    req = self.messages.SourcerepoProjectsGetConfigRequest(
        name=project_ref.RelativeName())
    self.client.projects.GetConfig.Expect(request=req, response=project_config)

  def _ExpectUpdateProjectConfig(self, project_config, update_mask):
    if update_mask not in ('enablePrivateKeyCheck', 'pubsubConfigs'):
      raise ValueError('Wrong update_mask.')
    req = self.messages.SourcerepoProjectsUpdateConfigRequest(
        name=project_config.name,
        updateProjectConfigRequest=self.messages.UpdateProjectConfigRequest(
            projectConfig=project_config, updateMask=update_mask))
    self.client.projects.UpdateConfig.Expect(
        request=req, response=project_config)


class SourceTest(cli_test_base.CliTestBase):

  def RunSource(self, command):
    return self.Run(['alpha', 'source'] + command)

  def RunSourceRepos(self, command):
    """Run gcloud source repos [command].

    It uses the inherited CliTestBase.Run method, which uses self.track to
    determine which track to run on.

    Args:
      command: list giving the command to run, without the source repos or track

    Returns:
      The result of executing the command.
    """
    return self.Run(['source', 'repos'] + command)


class SourceSdkTest(sdk_test_base.WithFakeAuth, SourceTest):
  pass


class SourceIntegrationTest(e2e_base.WithServiceAuth, SourceTest):
  """Base class for all source integration tests."""
