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
"""Common component for target VPN gateways labels testing."""

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis

from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class TargetVpnGatewaysLabelsTestBase(sdk_test_base.WithFakeAuth,
                                      cli_test_base.CliTestBase):
  """Base class for target VPN gateways test."""

  def SetUp(self):
    api_name = 'beta'
    self.apitools_client = mock.Client(
        apis.GetClientClass('compute', api_name),
        real_client=apis.GetClientInstance('compute', api_name, no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_name)
    self.track = base.ReleaseTrack.BETA
    self.region_operations = self.apitools_client.regionOperations
    self.StartPatch('time.sleep')

  def _GetTargetVpnGatewayRef(self, name, region=None):
    """Gets a reference to a target VPN gateway.

    Args:
      name: str, name of the target VPN gateway resource.
      region: str, region in which the target VPN gateway is.
    Returns:
      Reference to the target VPN gateway resource.
    """
    params = {'project': self.Project()}
    collection = 'compute.targetVpnGateways'
    params['region'] = region

    return self.resources.Parse(name, params=params, collection=collection)

  def _GetOperationRef(self, name, region=None):
    """Gets a reference to an operation.

    Args:
      name: str, name of the operation.
      region: str, region in which the operation is.
    Returns:
      Reference to the operation.
    """
    params = {'project': self.Project(), 'region': region}
    return self.resources.Parse(
        name, params=params, collection='compute.regionOperations')

  def _MakeOperationMessage(self, operation_ref, resource_ref=None):
    """Constructs an Operation message.

    Args:
      operation_ref: Reference to the operation.
      resource_ref: Reference to the resource that the operation modifies.
    Returns:
      An Operation resource.
    """
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def _MakeTargetVpnGatewayProto(self, labels=None, fingerprint=None):
    """Constructs a target VPN gateway message.

    Args:
      labels: Tuple of labels ((key, value) pairs) on the target VPN Gateway.
      fingerprint: str, label fingerprint of the target VPN gateway.
    Returns:
      A TargetVpnGateway message with the given labels and fingerprint.
    """
    msg = self.messages.TargetVpnGateway()
    if labels is not None:
      labels_value = msg.LabelsValue
      msg.labels = labels_value(additionalProperties=[
          labels_value.AdditionalProperty(key=pair[0], value=pair[1])
          for pair in labels
      ])
    if fingerprint:
      msg.labelFingerprint = fingerprint
    return msg

  def _MakeLabelsProto(self, labels_value, labels):
    """Constructs a Labels message.

    Args:
      labels_value: A LabelsValue message.
      labels: Tuple of labels ((key, value) pairs) that the target VPN gateway
              should have.
    Returns:
      A TargetVpnGateway message with the given labels and fingerprint.
    """
    return labels_value(additionalProperties=[
        labels_value.AdditionalProperty(key=pair[0], value=pair[1])
        for pair in labels
    ])

  def _ExpectGetRequest(self, target_vpn_gateway_ref, target_vpn_gateway=None):
    """Verifies a Get request on a target VPN gateway.

    Args:
      target_vpn_gateway_ref: Resource reference for the target VPN gateway.
      target_vpn_gateway: The TargetVpnGateway message expected to be
                          returned.
    """
    service = self.apitools_client.targetVpnGateways
    request_type = self.messages.ComputeTargetVpnGatewaysGetRequest

    service.Get.Expect(
        request=request_type(**target_vpn_gateway_ref.AsDict()),
        response=target_vpn_gateway)

  def _ExpectOperationGetRequest(self, operation_ref, operation):
    """Verifies a Get request on an operation.

    Args:
      operation_ref: Reference to the operation.
      operation: The Operation message expected to be returned.
    """
    self.region_operations.Get.Expect(
        self.messages.ComputeRegionOperationsGetRequest(
            operation=operation_ref.operation,
            region=operation_ref.region,
            project=self.Project()), operation)

  def _ExpectLabelsSetRequest(self,
                              target_vpn_gateway_ref,
                              labels,
                              fingerprint,
                              target_vpn_gateway=None):
    """Verifies a SetLabels request on a target VPN gateway.

    Args:
      target_vpn_gateway_ref: Resource reference for the target VPN gateway.
      labels: Expected tuple of labels ((key, value) pairs) provided in the
              request.
      fingerprint: str, expected label fingerprint provided in the request.
      target_vpn_gateway: The target VPN gateway expected as the response.
    """
    service = self.apitools_client.targetVpnGateways
    request_type = self.messages.ComputeTargetVpnGatewaysSetLabelsRequest
    scoped_set_labels_request = self.messages.RegionSetLabelsRequest

    labels_value = self._MakeLabelsProto(scoped_set_labels_request.LabelsValue,
                                         labels)
    request = request_type(
        project=target_vpn_gateway_ref.project,
        resource=target_vpn_gateway_ref.targetVpnGateway,)
    request.region = target_vpn_gateway_ref.region
    request.regionSetLabelsRequest = scoped_set_labels_request(
        labelFingerprint=fingerprint,
        labels=labels_value,)

    service.SetLabels.Expect(request=request, response=target_vpn_gateway)
