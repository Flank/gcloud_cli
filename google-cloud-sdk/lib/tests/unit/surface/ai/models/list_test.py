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
"""Tests for google3.third_party.py.tests.unit.surface.ai.models.list."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ListModelsUnitTestBase(cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('aiplatform', 'v1beta1')

  def RunCommandBeta(self, *command):
    return self.Run(['beta', 'ai', 'models'] + list(command))


class ListModelsUnitTest(ListModelsUnitTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.region = 'us-central1'
    self.mock_client = mock.Client(
        apis.GetClientClass('aiplatform', 'v1beta1'),
        real_client=apis.GetClientInstance(
            'aiplatform', 'v1beta1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def _buildModel(self, name=None, display_name=None):
    return self.messages.GoogleCloudAiplatformV1beta1Model(
        name=name, displayName=display_name)

  def testListModelsBeta(self):
    request = self.messages.AiplatformProjectsLocationsModelsListRequest(
        pageSize=100,
        parent='projects/{}/locations/{}'.format('fake-project', 'us-central1'))
    expected_response = self.messages.GoogleCloudAiplatformV1beta1ListModelsResponse(
        models=[
            self._buildModel(
                name='projects/fake-project/locations/us-central1/models/1',
                display_name=u'display_name_1'),
            self._buildModel(
                name='projects/fake-project/locations/us-central1/models/2',
                display_name=u'display_name_2')
        ])
    self.mock_client.projects_locations_models.List.Expect(
        request, response=expected_response)
    self.RunCommandBeta('list', '--region={}'.format(self.region))
    self.AssertErrContains(
        'Using endpoint [https://us-central1-aiplatform.googleapis.com/')
    self.AssertOutputContains(
        'name: projects/fake-project/locations/us-central1/models/1')
    self.AssertOutputContains('displayName: display_name_1')
    self.AssertOutputContains(
        'name: projects/fake-project/locations/us-central1/models/2')
    self.AssertOutputContains('displayName: display_name_2')
