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
"""Test base for compute routers unit tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class RouterTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for routers tests."""

  def SetUp(self):
    for api_version in core_apis.GetVersions('compute'):
      mock_client = mock.Client(
          core_apis.GetClientClass('compute', api_version),
          real_client=core_apis.GetClientInstance(
              'compute', api_version, no_http=True))
      setattr(self, 'compute_' + api_version, mock_client)
      setattr(self, api_version + '_messages',
              core_apis.GetMessagesModule('compute', api_version))

  def SelectApi(self, track, api_version):
    self.track = track
    self.messages = getattr(self, api_version + '_messages')
    self.mock_client = getattr(self, 'compute_' + api_version)
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def ExpectInsert(self, expected_message):
    """Expect a Routers 'Insert' request."""
    self.mock_client.routers.Insert.Expect(
        self.messages.ComputeRoutersInsertRequest(
            project=self.Project(),
            region='us-central1',
            router=expected_message),
        self.messages.Operation(
            name='operation-X',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING))

  def ExpectGet(self, expected_message):
    """Expect a Routers 'Get' request."""
    self.mock_client.routers.Get.Expect(
        self.messages.ComputeRoutersGetRequest(
            project=self.Project(), region='us-central1', router='my-router'),
        expected_message)

  def ExpectPatch(self, expected_message):
    """Expect a Routers 'Patch' request."""
    self.mock_client.routers.Patch.Expect(
        self.messages.ComputeRoutersPatchRequest(
            project=self.Project(),
            region='us-central1',
            router='my-router',
            routerResource=expected_message),
        self.messages.Operation(
            name='operation-X',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING))

  def ExpectOperationsGet(self):
    """Expect a Router Operations 'Get' request for polling."""
    self.mock_client.regionOperations.Get.Expect(
        self.messages.ComputeRegionOperationsGetRequest(
            project=self.Project(),
            region='us-central1',
            operation='operation-X'),
        self.messages.Operation(
            name='operation-X',
            status=self.messages.Operation.StatusValueValuesEnum.DONE))
