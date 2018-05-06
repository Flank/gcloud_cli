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

"""Base classes for all 'gcloud firebase test network-profiles' unit tests."""

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib.surface.firebase.test import unit_base

TESTING_V1_MSGS = core_apis.GetMessagesModule('testing', 'v1')

NETWORK_CATALOG_GET = TESTING_V1_MSGS.TestingTestEnvironmentCatalogGetRequest(
    environmentType=(TESTING_V1_MSGS.TestingTestEnvironmentCatalogGetRequest.
                     EnvironmentTypeValueValuesEnum.NETWORK_CONFIGURATION),
    projectId=unit_base.TestUnitTestBase.PROJECT_ID)


class NetworkUnitTestBase(unit_base.TestUnitTestBase):
  """Base class for all 'gcloud firebase test network-profiles' unit tests."""


class NetworkMockClientTest(unit_base.TestMockClientTest):
  """Base class for all 'gcloud test' tests using mocked ApiTools clients.

  Attributes:
    testing_client: mocked ApiTools client for the Testing API.
    tr_client: mocked ApiTools client for the ToolResults API.
    context: the gcloud command context (a str:value dict) which holds common
      initialization values, such as the client and messages objects generated
      from the Testing API definition by ApiTools.
  """

  def SetUp(self):
    self.CreateMockedClients()

  def ExpectNetworkCatalogGet(self, mock_catalog):
    """Expect a testEnvironmentCatalog.Get call with a mock_catalog response."""
    self.testing_client.testEnvironmentCatalog.Get.Expect(
        request=NETWORK_CATALOG_GET,
        response=self.testing_msgs.TestEnvironmentCatalog(
            networkConfigurationCatalog=mock_catalog))

  def ExpectNetworkCatalogGetError(self, error):
    """Expect a testEnvironmentCatalog.Get call with a mocked error response."""
    self.testing_client.testEnvironmentCatalog.Get.Expect(
        request=NETWORK_CATALOG_GET, exception=error)
