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
"""Base class for gcloud artifacts tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib import artifacts
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

API_NAME = 'artifactregistry'


class ARTestBase(sdk_test_base.WithLogCapture, sdk_test_base.WithFakeAuth,
                 cli_test_base.CliTestBase):
  """A base class for artifacts tests that need to use a mocked AR client."""

  def SetUp(self):
    self.api_version = artifacts.API_VERSION_FOR_TRACK[self.track]
    self.client = mock.Client(
        core_apis.GetClientClass(API_NAME, self.api_version),
        real_client=core_apis.GetClientInstance(API_NAME, self.api_version))
    self.client.Mock()
    self.messages = core_apis.GetMessagesModule(API_NAME, self.api_version)
    self.addCleanup(self.client.Unmock)

  def SetListLocationsExpect(self, location):
    self.client.projects_locations.List.Expect(
        self.messages.ArtifactregistryProjectsLocationsListRequest(
            name='projects/fake-project'),
        self.messages.ListLocationsResponse(locations=[
            self.messages.Location(
                name='projects/fake-project/locations/' + location,
                locationId=location)
        ]))

  def SetGetRepositoryExpect(self, location, repo, repo_format):
    repo_name = 'projects/fake-project/locations/{}/repositories/{}'.format(
        location, repo)
    self.client.projects_locations_repositories.Get.Expect(
        self.messages.ArtifactregistryProjectsLocationsRepositoriesGetRequest(
            name=repo_name),
        self.messages.Repository(name=repo_name, format=repo_format))
