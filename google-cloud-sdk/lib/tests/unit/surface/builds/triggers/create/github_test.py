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
"""Tests for google3.third_party.py.tests.unit.surface.builds.triggers.create.github."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class CreateTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                 sdk_test_base.WithTempCWD):

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')

    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)

    self.msg = core_apis.GetMessagesModule('cloudbuild', 'v1')

  def test_create_github_trigger_dockerfile(self):
    trigger = self.msg.BuildTrigger(
        description='foo',
        github=self.msg.GitHubEventsConfig(
            owner='gcb',
            name='test',
            push=self.msg.PushFilter(branch='.*'),
        ),
        build=self.msg.Build(steps=[
            self.msg.BuildStep(
                name='gcr.io/cloud-builders/docker',
                dir='/',
                args=[
                    'build', '-t',
                    'gcr.io/my-project/github.com/gcb/test:$COMMIT_SHA', '-f',
                    'Dockerfile', '.'
                ],
            )
        ]))
    want = copy.deepcopy(trigger)
    want.id = 'id'
    self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
        self.msg.CloudbuildProjectsTriggersCreateRequest(
            projectId='my-project', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run([
        'alpha', 'builds', 'triggers', 'create', 'github', '--description=foo',
        '--repo-owner=gcb', '--repo-name=test', '--branch-pattern=.*',
        '--dockerfile=Dockerfile'
    ])
    self.assertEqual(want, resp)

  def test_create_github_trigger_pr_configfile(self):
    trigger = self.msg.BuildTrigger(
        github=self.msg.GitHubEventsConfig(
            owner='gcb',
            name='test',
            pullRequest=self.msg.PullRequestFilter(
                branch='.*',
                commentControl=self.msg.PullRequestFilter
                .CommentControlValueValuesEnum.COMMENTS_ENABLED,
            ),
        ),
        filename='cloudbuild.yaml',
        substitutions=encoding.PyValueToMessage(
            self.msg.BuildTrigger.SubstitutionsValue,
            {'_FAVORITE_COLOR': 'blue'}),
    )
    path = self.Touch(
        '.', 'trigger.json', contents=encoding.MessageToJson(trigger))

    want = copy.deepcopy(trigger)
    want.id = 'id'

    self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
        self.msg.CloudbuildProjectsTriggersCreateRequest(
            projectId='my-project', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run([
        'alpha', 'builds', 'triggers', 'create', 'github', '--trigger-config',
        path
    ])
    self.assertEqual(want, resp)

  def test_create_github_trigger_subs(self):
    trigger = self.msg.BuildTrigger(
        github=self.msg.GitHubEventsConfig(
            owner='gcb',
            name='test',
            push=self.msg.PushFilter(tag='.*',),
        ),
        filename='cloudbuild.yaml',
        substitutions=self.msg.BuildTrigger.SubstitutionsValue(
            additionalProperties=[
                self.msg.BuildTrigger.SubstitutionsValue.AdditionalProperty(
                    key='_FAVORITE_COLOR', value='blue')
            ]),
        includedFiles=['src/**'],
        ignoredFiles=['docs/**'],
    )

    want = copy.deepcopy(trigger)
    want.id = 'id'

    self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
        self.msg.CloudbuildProjectsTriggersCreateRequest(
            projectId='my-project', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run([
        'alpha', 'builds', 'triggers', 'create', 'github', '--repo-owner=gcb',
        '--repo-name=test', '--tag-pattern=.*',
        '--build-config=cloudbuild.yaml',
        '--substitutions=_FAVORITE_COLOR=blue', '--included-files=src/**',
        '--ignored-files=docs/**'
    ])
    self.assertEqual(want, resp)


if __name__ == '__main__':
  test_case.main()
