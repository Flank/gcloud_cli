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
"""Tests for google3.third_party.py.tests.unit.surface.builds.triggers.import."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class ImportTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                 sdk_test_base.WithTempCWD):

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')

    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)

    self.msg = core_apis.GetMessagesModule('cloudbuild', 'v1')
    self.base_trigger = self.msg.BuildTrigger(
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

  def test_import_no_identifiers(self):
    trigger = copy.deepcopy(self.base_trigger)
    path = self.Touch('.', 'trigger.yaml',
                      yaml.dump(encoding.MessageToDict(trigger)))
    want = copy.deepcopy(trigger)
    want.id = 'id'
    self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
        self.msg.CloudbuildProjectsTriggersCreateRequest(
            projectId='my-project', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run(['alpha', 'builds', 'triggers', 'import', '--source', path])
    self.assertEqual([want], resp)

  def test_import_id_specified(self):
    trigger = copy.deepcopy(self.base_trigger)
    trigger.id = 'id'
    path = self.Touch('.', 'trigger.yaml',
                      yaml.dump(encoding.MessageToDict(trigger)))
    want = copy.deepcopy(trigger)
    self.mocked_cloudbuild_v1.projects_triggers.Patch.Expect(
        self.msg.CloudbuildProjectsTriggersPatchRequest(
            projectId='my-project', triggerId='id', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run(['alpha', 'builds', 'triggers', 'import', '--source', path])
    self.assertEqual([want], resp)

  def test_import_id_not_found(self):
    trigger = copy.deepcopy(self.base_trigger)
    trigger.id = 'id'
    path = self.Touch('.', 'trigger.yaml',
                      yaml.dump(encoding.MessageToDict(trigger)))
    self.mocked_cloudbuild_v1.projects_triggers.Patch.Expect(
        self.msg.CloudbuildProjectsTriggersPatchRequest(
            projectId='my-project', triggerId='id', buildTrigger=trigger),
        exception=apitools_exceptions.HttpNotFoundError('', '', ''))
    properties.VALUES.core.user_output_enabled.Set(False)
    with self.assertRaises(exceptions.HttpException):
      self.Run(['alpha', 'builds', 'triggers', 'import', '--source', path])

  def test_import_name_specified(self):
    trigger = copy.deepcopy(self.base_trigger)
    trigger.name = 'name'
    path = self.Touch('.', 'trigger.yaml',
                      yaml.dump(encoding.MessageToDict(trigger)))
    want = copy.deepcopy(trigger)
    want.id = 'id'
    self.mocked_cloudbuild_v1.projects_triggers.Patch.Expect(
        self.msg.CloudbuildProjectsTriggersPatchRequest(
            projectId='my-project', triggerId='name', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run(['alpha', 'builds', 'triggers', 'import', '--source', path])
    self.assertEqual([want], resp)

  def test_import_name_not_found(self):
    trigger = copy.deepcopy(self.base_trigger)
    trigger.name = 'name'
    path = self.Touch('.', 'trigger.yaml',
                      yaml.dump(encoding.MessageToDict(trigger)))
    want = copy.deepcopy(trigger)
    want.id = 'id'
    self.mocked_cloudbuild_v1.projects_triggers.Patch.Expect(
        self.msg.CloudbuildProjectsTriggersPatchRequest(
            projectId='my-project', triggerId='name', buildTrigger=trigger),
        exception=apitools_exceptions.HttpNotFoundError('', '', ''))
    self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
        self.msg.CloudbuildProjectsTriggersCreateRequest(
            projectId='my-project', buildTrigger=trigger),
        response=want)
    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run(['alpha', 'builds', 'triggers', 'import', '--source', path])
    self.assertEqual([want], resp)

  def test_import_multidoc(self):
    trigger1 = copy.deepcopy(self.base_trigger)
    trigger1.name = 'name1'
    trigger2 = copy.deepcopy(self.base_trigger)
    trigger2.name = 'name2'
    triggers = [trigger1, trigger2]

    encoded = [encoding.MessageToDict(trigger) for trigger in triggers]
    path = self.Touch('.', 'trigger.yaml', yaml.dump_all(encoded))

    wants = []
    for trigger in triggers:
      want = copy.deepcopy(trigger)
      want.id = 'id'
      wants.append(want)
      self.mocked_cloudbuild_v1.projects_triggers.Patch.Expect(
          self.msg.CloudbuildProjectsTriggersPatchRequest(
              projectId='my-project',
              triggerId=trigger.name,
              buildTrigger=trigger),
          exception=apitools_exceptions.HttpNotFoundError('', '', ''))
      self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
          self.msg.CloudbuildProjectsTriggersCreateRequest(
              projectId='my-project', buildTrigger=trigger),
          response=want)

    properties.VALUES.core.user_output_enabled.Set(False)
    resp = self.Run(['alpha', 'builds', 'triggers', 'import', '--source', path])
    self.assertEqual(wants, resp)


if __name__ == '__main__':
  test_case.main()
