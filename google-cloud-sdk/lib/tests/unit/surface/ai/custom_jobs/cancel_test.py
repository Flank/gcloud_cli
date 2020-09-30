# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.ai.custom_jobs.cancel."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class CancelCustomJobUnitTestAlpha(cli_test_base.CliTestBase,
                                   sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('aiplatform', 'v1beta1')
    self.version = 'alpha'
    self.region = 'us-central1'
    self.mock_client = mock.Client(
        apis.GetClientClass('aiplatform', 'v1beta1'),
        real_client=apis.GetClientInstance(
            'aiplatform', 'v1beta1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def RunCommand(self, *command):
    return self.Run([self.version, 'ai', 'custom-jobs'] + list(command))

  def testCancelCustomJobAlpha(self):
    request = self.messages.AiplatformProjectsLocationsCustomJobsCancelRequest(
        name='projects/{}/locations/{}/customJobs/{}'.format(
            'fake-project', 'us-central1', '1'))
    self.mock_client.projects_locations_customJobs.Cancel.Expect(
        request, response=self.messages.GoogleProtobufEmpty())
    self.RunCommand('cancel', '1', '--region={}'.format(self.region))
    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertErrContains('Request to cancel custom job [1] has been sent')
    self.AssertErrContains('gcloud alpha ai custom-jobs describe 1')


class CancelCustomJobUnitTestBeta(CancelCustomJobUnitTestAlpha):

  def SetUp(self):
    self.version = 'beta'
