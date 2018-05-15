# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Base class for Google Serverless Engine unit tests."""

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base


class ServerlessBase(cli_test_base.CliTestBase):
  """Base class for Google Serverless Engine unit tests."""

  def SetUp(self):

    # Mock ServerlessApiClient
    self.mock_serverless_client = apitools_mock.Client(
        core_apis.GetClientClass('serverless', 'v1alpha1'),
        real_client=core_apis.GetClientInstance(
            'serverless', 'v1alpha1', no_http=True))
    self.mock_serverless_client.Mock()
    self.addCleanup(self.mock_serverless_client.Unmock)
    self.serverless_messages = core_apis.GetMessagesModule(
        'serverless', 'v1alpha1')

  def ExpectRevisionsList(self, service):
    """List call for two revisions against the Serverless API."""

    request = (
        self.
        serverless_messages.ServerlessProjectsLocationsRevisionsListRequest(
            parent='projects/{}/locations/{}'.format(
                self.Project(), properties.VALUES.serverless.region.Get())))
    revisions_responses = self.serverless_messages.RevisionList(
        items=[
            self.serverless_messages.Revision(
                metadata=self.serverless_messages.ObjectMeta(
                    name='r1'
                )
            ),
            self.serverless_messages.Revision(
                metadata=self.serverless_messages.ObjectMeta(
                    name='r2'
                )
            ),
        ]
    )

    self.mock_serverless_client.projects_locations_revisions.List.Expect(
        request, response=revisions_responses)


