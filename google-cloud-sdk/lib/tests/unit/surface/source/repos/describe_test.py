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
"""Test of the 'source repos describe' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.source import base


YAML_OUTPUT = """\
mirrorConfig:
  url: https://mirror
name: projects/myproject/repos/has-mirror
size: '2'
url: https://csr
"""


class DescribeTest(base.SourceSdkTest):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('sourcerepo', 'v1')
    self.mock_client = mock.Client(
        core_apis.GetClientClass('sourcerepo', 'v1'),
        real_client=core_apis.GetClientInstance(
            'sourcerepo', 'v1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.repo_name = 'projects/' + self.Project() + '/repos/has-mirror'

  def testDescribeSuccess(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(name=self.repo_name),
        self.messages.Repo(
            name='projects/myproject/repos/has-mirror',
            size=2,
            url='https://csr',
            mirrorConfig=self.messages.MirrorConfig(url='https://mirror')))

    self.RunSourceRepos(['describe', 'has-mirror'])
    self.AssertOutputEquals(YAML_OUTPUT)
    self.AssertErrEquals('')

  def testDescribeNotFoundFailure(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(name=self.repo_name),
        exception=http_error.MakeHttpError(code=404))
    with self.assertRaises(exceptions.HttpException):
      self.RunSourceRepos(['describe', 'has-mirror'])
      self.AssertErrContains('NOT_FOUND')

  def testDescribePermissionDeniedFailure(self):
    self.mock_client.projects_repos.Get.Expect(
        self.messages.SourcerepoProjectsReposGetRequest(name=self.repo_name),
        exception=http_error.MakeHttpError(code=403))
    with self.assertRaises(exceptions.HttpException):
      self.RunSourceRepos(['describe', 'has-mirror'])
      self.AssertErrContains('PERMISSION_DENIED')


if __name__ == '__main__':
  test_case.main()
