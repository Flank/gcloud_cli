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
"""Base class for Cloud Tasks tests."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib import tasks as cloudtasks_api
from googlecloudsdk.api_lib.tasks import locations
from googlecloudsdk.api_lib.tasks import queues
from googlecloudsdk.api_lib.tasks import tasks
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class CloudTasksTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for Cloud Tasks unit tests."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

    self.apitools_mock_client = mock.Client(
        client_class=apis.GetClientClass(cloudtasks_api.API_NAME,
                                         cloudtasks_api.API_VERSION))
    self.apitools_mock_client.Mock()
    self.addCleanup(self.apitools_mock_client.Unmock)

    api_adapter = cloudtasks_api.ApiAdapter()
    self.queues_client = queues.Queues(api_adapter)
    self.tasks_client = tasks.Tasks(api_adapter)
    self.locations_client = locations.Locations(api_adapter)
    self.messages = api_adapter.messages

    self.queues_service = self.apitools_mock_client.projects_locations_queues
    self.tasks_service = (
        self.apitools_mock_client.projects_locations_queues_tasks)
    self.locations_service = self.apitools_mock_client.projects_locations
