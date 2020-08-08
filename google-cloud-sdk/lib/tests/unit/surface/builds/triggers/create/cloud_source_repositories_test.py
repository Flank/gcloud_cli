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

import copy

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class CreateTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                 sdk_test_base.WithTempCWD, parameterized.TestCase):

  message = core_apis.GetMessagesModule('cloudbuild', 'v1')

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')

    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)

  @parameterized.parameters(
      {
          'command': [
              'alpha', 'builds', 'triggers', 'create',
              'cloud-source-repositories', '--name=my-trigger',
              '--description=foo', '--repo=projects/foo/repos/test',
              '--branch-pattern=.*', '--dockerfile=Dockerfile'
          ],
          'trigger':
              message.BuildTrigger(
                  name='my-trigger',
                  description='foo',
                  triggerTemplate=message.RepoSource(
                      repoName='test',
                      branchName='.*',
                  ),
                  build=message.Build(steps=[
                      message.BuildStep(
                          name='gcr.io/cloud-builders/docker',
                          dir='/',
                          args=[
                              'build', '-t',
                              'gcr.io/my-project/test:$COMMIT_SHA', '-f',
                              'Dockerfile', '.'
                          ],
                      )
                  ])),
      }, {
          'command': [
              'alpha',
              'builds',
              'triggers',
              'create',
              'cloud-source-repositories',
              '--name=my-trigger',
              '--description=foo',
              '--repo=projects/foo/repos/test',
              '--branch-pattern=.*',
              '--dockerfile=Dockerfile',
              '--dockerfile-image=gcr.io/other-project/other-test:123abc',
          ],
          'trigger':
              message.BuildTrigger(
                  name='my-trigger',
                  description='foo',
                  triggerTemplate=message.RepoSource(
                      repoName='test',
                      branchName='.*',
                  ),
                  build=message.Build(steps=[
                      message.BuildStep(
                          name='gcr.io/cloud-builders/docker',
                          dir='/',
                          args=[
                              'build', '-t',
                              'gcr.io/other-project/other-test:123abc', '-f',
                              'Dockerfile', '.'
                          ],
                      )
                  ])),
      }, {
          'command': [
              'alpha', 'builds', 'triggers', 'create',
              'cloud-source-repositories', '--repo=test', '--tag-pattern=.*',
              '--build-config=cloudbuild.yaml',
              '--substitutions=_FAVORITE_COLOR=blue', '--included-files=src/**',
              '--ignored-files=docs/**'
          ],
          'trigger':
              message.BuildTrigger(
                  triggerTemplate=message.RepoSource(
                      repoName='test',
                      tagName='.*',
                  ),
                  filename='cloudbuild.yaml',
                  substitutions=message.BuildTrigger
                  .SubstitutionsValue(additionalProperties=[
                      message.BuildTrigger.SubstitutionsValue
                      .AdditionalProperty(key='_FAVORITE_COLOR', value='blue')
                  ]),
                  includedFiles=['src/**'],
                  ignoredFiles=['docs/**'],
              ),
      })
  def test_create_cloud_source_repositories_trigger(self, command, trigger):
    want = copy.deepcopy(trigger)
    want.id = 'id'
    self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
        self.message.CloudbuildProjectsTriggersCreateRequest(
            projectId='my-project', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run(command)
    self.assertEqual(want, resp)

  @parameterized.parameters([
      message.BuildTrigger(
          triggerTemplate=message.RepoSource(
              repoName='test',
              branchName='.*',
          ),
          filename='cloudbuild.yaml',
          substitutions=encoding.PyValueToMessage(
              message.BuildTrigger.SubstitutionsValue,
              {'_FAVORITE_COLOR': 'blue'}),
      )
  ])
  def test_create_csr_trigger_configfile(self, trigger):
    path = self.Touch(
        '.', 'trigger.json', contents=encoding.MessageToJson(trigger))

    want = copy.deepcopy(trigger)
    want.id = 'id'

    self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
        self.message.CloudbuildProjectsTriggersCreateRequest(
            projectId='my-project', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run([
        'alpha', 'builds', 'triggers', 'create', 'cloud-source-repositories',
        '--trigger-config', path
    ])
    self.assertEqual(want, resp)


if __name__ == '__main__':
  test_case.main()
