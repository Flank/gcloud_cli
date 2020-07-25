# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.builds.triggers.create.cloud_source_repo."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class RunTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
              sdk_test_base.WithTempCWD):

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')

    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)

    self.msg = core_apis.GetMessagesModule('cloudbuild', 'v1')

  def test_run_branch(self):
    self.mocked_cloudbuild_v1.projects_triggers.Run.Expect(
        self.msg.CloudbuildProjectsTriggersRunRequest(
            projectId='my-project',
            triggerId='tacocat',
            repoSource=self.msg.RepoSource(branchName='main')),
        response=self.msg.Operation(),
    )
    properties.VALUES.core.user_output_enabled.Set(False)
    self.Run(
        ['alpha', 'builds', 'triggers', 'run', 'tacocat', '--branch=main'])

  def test_run_tag(self):
    self.mocked_cloudbuild_v1.projects_triggers.Run.Expect(
        self.msg.CloudbuildProjectsTriggersRunRequest(
            projectId='my-project',
            triggerId='tacocat',
            repoSource=self.msg.RepoSource(tagName='v1')),
        response=self.msg.Operation(),
    )
    properties.VALUES.core.user_output_enabled.Set(False)
    self.Run(['alpha', 'builds', 'triggers', 'run', 'tacocat', '--tag=v1'])

  def test_run_sha(self):
    self.mocked_cloudbuild_v1.projects_triggers.Run.Expect(
        self.msg.CloudbuildProjectsTriggersRunRequest(
            projectId='my-project',
            triggerId='tacocat',
            repoSource=self.msg.RepoSource(commitSha='abc')),
        response=self.msg.Operation(),
    )
    properties.VALUES.core.user_output_enabled.Set(False)
    self.Run(['alpha', 'builds', 'triggers', 'run', 'tacocat', '--sha=abc'])


if __name__ == '__main__':
  test_case.main()
