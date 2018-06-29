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

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import encoding as apitools_encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from six.moves import range


class TpuUnitTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for all TPU unit tests."""
  API_VERSION = 'v1'

  def _SetTrack(self, track):
    self.track = track

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.messages = core_apis.GetMessagesModule('tpu', self.API_VERSION)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('tpu', self.API_VERSION),
        real_client=core_apis.GetClientInstance(
            'tpu', TpuUnitTestBase.API_VERSION, no_http=True))
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
                 network='data-test',
                 version=None,
                 port='2222',
                 accelerator_type='v2-8',
                 preemptible=False
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
        acceleratorType=accelerator_type,
        networkEndpoints=self._GetNetworkEndpoints(cidr, port, 2),
        schedulingConfig=self.messages.SchedulingConfig(preemptible=preemptible)
    )

  def _GetNetworkEndpoints(self, base_range, port, count):
    base_ip, _ = base_range.split('/')
    octets = [int(x) for x in base_ip.split('.')]
    results = []
    for _ in range(count):
      octets[3] += 1
      ip = '.'.join(str(v) for v in octets)
      results.append(
          self.messages.NetworkEndpoint(ipAddress=ip, port=int(port)))
    return results

  def GetTestLocation(self, name='us-east1'):
    return self.messages.Location(
        name=name,
        locationId='projects/{}/locations/{}'.format(self.Project(), name))

  def GetTestTFVersion(self, version='1.6'):
    return self.messages.TensorFlowVersion(
        version=version,
        name=('projects/{project}/locations/{zone}/tensorflowVersions/{version}'
              .format(project=self.Project(), zone=self.zone, version=version)))

  def GetTestAccType(self, acc_type='v2-8'):
    return self.messages.AcceleratorType(
        type=acc_type,
        name=('projects/{project}/locations/{zone}/acceleratorTypes/{acc_type}'
              .format(project=self.Project(), zone=self.zone,
                      acc_type=acc_type)))

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
    op_ref = resources.REGISTRY.Parse(
        op_name,
        params={
            'projectsId': self.Project(),
            'locationsId': self.zone},
        collection='tpu.projects.locations.operations')
    for _ in range(poll_count):
      op_polling_response = self.GetOperationResponse(op_name, is_done=False)
      self.mock_client.projects_locations_operations.Get.Expect(
          self.messages.TpuProjectsLocationsOperationsGetRequest(
              name=op_ref.RelativeName()),
          op_polling_response
      )

    op_done_response = self.GetOperationResponse(op_ref.RelativeName(),
                                                 is_done=True,
                                                 error_json=error_json)

    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name=op_ref.RelativeName()),
        op_done_response
    )
    return op_done_response
