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

import datetime
import json

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib import artifacts
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.core.credentials import credentials_test_base
from oauth2client import client
from google.auth import crypt as google_auth_crypt

API_NAME = 'artifactregistry'


class ARTestBase(sdk_test_base.WithLogCapture, cli_test_base.CliTestBase,
                 credentials_test_base.CredentialsTestBase):
  """A base class for artifacts tests that need to use a mocked AR client."""

  def SetUp(self):
    self.fake_project = 'fake-project'
    self.fake_account = 'fake-account'
    properties.VALUES.core.account.Set(self.fake_account)
    properties.VALUES.core.project.Set(self.fake_project)

    # Set up user credentials
    self.fake_cred = client.OAuth2Credentials(
        'access-token',
        'client_id',
        'client_secret',
        'fake-token',
        datetime.datetime(2021, 1, 8, 0, 0, 0),
        'token_uri',
        'user_agent',
        scopes=config.CLOUDSDK_SCOPES)
    self.StartPatch('oauth2client.crypt.Signer', autospec=True)
    self.StartObjectPatch(google_auth_crypt.RSASigner,
                          'from_service_account_info')
    store.Store(self.fake_cred)
    store.Load()

    self.api_version = artifacts.API_VERSION_FOR_TRACK[self.track]
    self.client = mock.Client(
        core_apis.GetClientClass(API_NAME, self.api_version),
        real_client=core_apis.GetClientInstance(API_NAME, self.api_version))
    self.client.Mock()
    self.messages = core_apis.GetMessagesModule(API_NAME, self.api_version)
    self.addCleanup(self.client.Unmock)

  def SetUpCreds(self):
    """Set up service account credentials."""
    sa_creds = self.MakeServiceAccountCredentials()
    sa_creds.token_expiry = (
        datetime.datetime.utcnow() + datetime.timedelta(hours=2))

    store.Store(sa_creds, self.fake_account)
    store.Load(self.fake_account)
    creds_type = creds.CredentialType.FromCredentials(sa_creds)
    paths = config.Paths()
    with open(paths.LegacyCredentialsAdcPath(self.fake_account)) as f:
      adc_file = json.load(f)
    # Compare file contents to make sure credentials are set up correctly.
    self.assertEqual(
        json.loads("""\
        {
          "client_email": "bar@developer.gserviceaccount.com",
          "client_id": "bar.apps.googleusercontent.com",
          "private_key": "-----BEGIN PRIVATE KEY-----\\nasdf\\n-----END PRIVATE KEY-----\\n",
          "private_key_id": "key-id",
          "type": "service_account"
        }"""), adc_file)
    self.assertEqual(creds.CredentialType.SERVICE_ACCOUNT, creds_type)

  def WriteKeyFile(self, key_file):
    """Write JSON key credentials to the given file.

    Args:
      key_file: str, temporary path to JSON key file.

    Returns:
      None
    """
    json_data = """{"a":"b"}"""
    files.WriteFileContents(key_file, json_data, private=True)

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
