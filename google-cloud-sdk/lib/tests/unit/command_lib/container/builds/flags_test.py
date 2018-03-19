# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for container builds flags module."""

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.container.builds import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import completer_test_base
from tests.lib import sdk_test_base


class CompletionTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                     completer_test_base.CompleterBase):

  def SetUp(self):
    self.StartObjectPatch(times, 'Now', return_value=times.ParseDateTime(
        '2016-05-26T00:05:00.000000Z'))
    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)
    properties.VALUES.core.project.Set('my-project')
    self.cloudbuild_v1_messages = core_apis.GetMessagesModule(
        'cloudbuild', 'v1')
    self._statuses = self.cloudbuild_v1_messages.Build.StatusValueValuesEnum

  def testBuildsCompleter(self):
    self.mocked_cloudbuild_v1.projects_builds.List.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsListRequest(
            pageToken=None,
            projectId=u'my-project',
        ),
        response=self.cloudbuild_v1_messages.ListBuildsResponse(
            builds=[
                self.cloudbuild_v1_messages.Build(
                    id='123-456-789',
                    projectId='my-project',
                    createTime='2016-05-26T00:00:00.000000Z',
                    finishTime='2016-05-26T00:05:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    source=self.cloudbuild_v1_messages.Source(
                        repoSource=self.cloudbuild_v1_messages.RepoSource(
                            repoName='default',
                            branchName='master',
                        ),
                    ),
                    results=self.cloudbuild_v1_messages.Results(
                        images=[
                            self.cloudbuild_v1_messages.BuiltImage(
                                name='gcr.io/myproject/myimage-1',
                            ),
                            self.cloudbuild_v1_messages.BuiltImage(
                                name='gcr.io/myproject/myimage-2',
                            )
                        ]
                    ),
                    status=self._statuses.SUCCESS,
                ),
                self.cloudbuild_v1_messages.Build(
                    id='987-654-321',
                    projectId='my-project',
                    createTime='2016-05-26T00:00:00.000000Z',
                    finishTime='2016-05-26T00:05:00.000000Z',
                    startTime='2016-05-26T00:00:01.000000Z',
                    source=self.cloudbuild_v1_messages.Source(
                        repoSource=self.cloudbuild_v1_messages.RepoSource(
                            repoName='default',
                            branchName='master',
                        ),
                    ),
                    results=self.cloudbuild_v1_messages.Results(
                        images=[
                            self.cloudbuild_v1_messages.BuiltImage(
                                name='gcr.io/myproject/myimage-1',
                            ),
                            self.cloudbuild_v1_messages.BuiltImage(
                                name='gcr.io/myproject/myimage-2',
                            )
                        ]
                    ),
                    status=self._statuses.SUCCESS,
                ),
            ],
        )
    )

    self.RunCompleter(
        flags.BuildsCompleter,
        expected_command=[
            'container',
            'builds',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=['123-456-789', '987-654-321'],
        cli=self.cli,
    )


if __name__ == '__main__':
  completer_test_base.main()
