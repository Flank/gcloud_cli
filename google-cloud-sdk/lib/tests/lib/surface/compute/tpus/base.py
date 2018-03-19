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
"""Base class for all tpu_nodes tests."""

from apitools.base.py import encoding as apitools_encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class TpuUnitTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for all TPU unit tests."""
  API_VERSION = 'v1alpha1'

  def _SetTrack(self, track):
    self.track = track

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.messages = core_apis.GetMessagesModule('tpu', self.API_VERSION)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('tpu', self.API_VERSION),
        real_client=core_apis.GetClientInstance(
            'tpu', self.API_VERSION, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    properties.VALUES.core.user_output_enabled.Set(False)

  def GetReadyState(self):
    return self.messages.Node.StateValueValuesEnum.READY

  def GetTestTPU(self,
                 name,
                 cidr='10.142.0.0/29',
                 description=None,
                 health_description=None,
                 ip_address=None,
                 network='global/networks/default',
                 version=None,
                 port='2222',
                 accelerator_type='tpu-v2'
                ):
    return self.messages.Node(
        name=name,
        cidrBlock=cidr,
        description=description,
        healthDescription=health_description,
        ipAddress=ip_address,
        network=network,
        state=self.GetReadyState(),
        tensorflowVersion=version,
        port=port,
        acceleratorType=accelerator_type
    )

  def GetOperationResponse(
      self,
      op_name,
      error_json=None,
      is_done=True,
      response_value=None):

    operation = self.messages.Operation(name=op_name, done=is_done)
    if error_json:
      is_done = True
      operation.error = apitools_encoding.PyValueToMessage(
          self.messages.Status,
          error_json)

    if response_value:
      operation.response = response_value

    return operation

  def ExpectLongRunningOpResult(self,
                                op_name,
                                poll_count=3,
                                response_value=None,
                                error_json=None):
    for _ in xrange(poll_count):
      op_polling_response = self.GetOperationResponse(op_name, is_done=False)
      self.mock_client.projects_locations_operations.Get.Expect(
          self.messages.TpuProjectsLocationsOperationsGetRequest(
              name='projects/{0}/locations/{1}/operations/{2}'.format(
                  self.Project(),
                  self.zone,
                  op_name)),
          op_polling_response
      )

    op_done_response = self.GetOperationResponse(op_name,
                                                 is_done=True,
                                                 error_json=error_json)

    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/{2}'.format(
                self.Project(),
                self.zone,
                op_name)),
        op_done_response
    )
    return op_done_response
