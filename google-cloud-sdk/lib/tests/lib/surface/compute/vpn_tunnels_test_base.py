# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Base class for all VPN Tunnel tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class VpnTunnelsTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for all VPN Tunnels test."""

  REGION = 'my-region'
  REGION2 = 'my-region-2'
  REGION3 = 'my-region-3'

  def _GetApiName(self):
    """Returns the API name for the specified release track."""
    if self.track == calliope_base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif self.track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  def SetUp(self):
    """Setup common test components."""
    api_name = self._GetApiName()
    self.base_uri = 'https://compute.googleapis.com/compute/{}/projects/{}'.format(
        api_name, self.Project())

    apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_name),
        real_client=core_apis.GetClientInstance(
            'compute', api_name, no_http=True))
    apitools_client.Mock()
    self.addCleanup(apitools_client.Unmock)
    self.messages = apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_name)
    self.service = apitools_client.vpnTunnels
    self.region_operations = apitools_client.regionOperations

  def GetRegionUri(self, region_name):
    return '{}/regions/{}'.format(self.base_uri, region_name)

  def GetVpnTunnelRef(self, name, region=REGION):
    """Returns the specified VPN Tunnel reference."""
    params = {'project': self.Project(), 'region': region}
    collection = 'compute.vpnTunnels'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetTargetVpnGatewayRef(self, name, region=REGION):
    """Returns the specified Target VPN Gateway reference."""
    params = {'project': self.Project(), 'region': region}
    collection = 'compute.targetVpnGateways'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetVpnGatewayRef(self, name, region=REGION):
    """Returns the specified VPN Gateway reference."""
    params = {'project': self.Project(), 'region': region}
    collection = 'compute.vpnGateways'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetRouterRef(self, name, region=REGION):
    """Returns the specified Router reference."""
    params = {'project': self.Project(), 'region': region}
    collection = 'compute.routers'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetExternalVpnGatewayRef(self, name):
    """Returns the specified external VPN Gateway reference."""
    params = {'project': self.Project()}
    collection = 'compute.externalVpnGateways'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetOperationRef(self, name, region=REGION):
    """Returns the operation reference."""
    params = {'project': self.Project(), 'region': region}
    collection = 'compute.regionOperations'
    return self.resources.Parse(name, params=params, collection=collection)

  def MakeOperationMessage(self, operation_ref, status=None, resource_ref=None):
    """Returns the operation message for the specified operation reference."""
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=status or self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def MakeLabelsMessage(self, labels_message, labels):
    return labels_message(additionalProperties=[
        labels_message.AdditionalProperty(key=key, value=value)
        for key, value in labels
    ])

  def ExpectInsertRequest(self,
                          vpn_tunnel_ref,
                          vpn_tunnel,
                          response=None,
                          exception=None):
    """Expects the VPN Tunnel Insert request to be invoked."""
    request = self.messages.ComputeVpnTunnelsInsertRequest(
        project=vpn_tunnel_ref.project,
        region=vpn_tunnel_ref.region,
        vpnTunnel=vpn_tunnel)
    self.service.Insert.Expect(
        request=request, response=response, exception=exception)

  def ExpectGetRequest(self, vpn_tunnel_ref, vpn_tunnel=None, exception=None):
    """Expects the VPN Tunnel Get request to be invoked."""
    self.service.Get.Expect(
        request=self.messages.ComputeVpnTunnelsGetRequest(
            **vpn_tunnel_ref.AsDict()),
        response=vpn_tunnel,
        exception=exception)

  def ExpectListRequest(self,
                        scoped_vpn_tunnels=(),
                        filter_expr=None,
                        exception=None):
    """Expects the VPN Tunnel List request to be invoked."""
    vpn_tunnels = []
    for scope, vpn_tunnels_in_scope in scoped_vpn_tunnels:
      scoped_list = self.messages.VpnTunnelsScopedList(
          vpnTunnels=vpn_tunnels_in_scope, warning=None)
      vpn_tunnels.append(
          self.messages.VpnTunnelAggregatedList.ItemsValue.AdditionalProperty(
              key='regions/{}'.format(scope), value=scoped_list))
    self.service.AggregatedList.Expect(
        request=self.messages.ComputeVpnTunnelsAggregatedListRequest(
            filter=filter_expr, project=self.Project()),
        response=self.messages.VpnTunnelAggregatedList(
            items=self.messages.VpnTunnelAggregatedList.ItemsValue(
                additionalProperties=vpn_tunnels)),
        exception=exception)

  def ExpectDeleteRequest(self, vpn_tunnel_ref, response, exception=None):
    """Expects the VPN Tunnel Delete request to be invoked."""
    request = self.messages.ComputeVpnTunnelsDeleteRequest(
        project=vpn_tunnel_ref.project,
        region=vpn_tunnel_ref.region,
        vpnTunnel=vpn_tunnel_ref.Name())
    self.service.Delete.Expect(
        request=request, response=response, exception=exception)

  def ExpectSetLabelsRequest(self,
                             vpn_tunnel_ref,
                             labels,
                             fingerprint,
                             vpn_tunnel_response,
                             exception=None):
    """Expects the VPN Tunnel SetLabels request to be invoked."""
    set_labels_request = self.messages.RegionSetLabelsRequest(
        labelFingerprint=fingerprint,
        labels=self.MakeLabelsMessage(
            self.messages.RegionSetLabelsRequest.LabelsValue, labels))
    request = self.messages.ComputeVpnTunnelsSetLabelsRequest(
        project=vpn_tunnel_ref.project,
        region=vpn_tunnel_ref.region,
        resource=vpn_tunnel_ref.vpnTunnel,
        regionSetLabelsRequest=set_labels_request)
    self.service.SetLabels.Expect(
        request=request, response=vpn_tunnel_response, exception=exception)

  def ExpectOperationGetRequest(self, operation_ref, operation):
    """Expects the operation Get request to be invoked."""
    self.region_operations.Get.Expect(
        self.messages.ComputeRegionOperationsGetRequest(
            operation=operation_ref.operation,
            project=operation_ref.project,
            region=operation_ref.region), operation)

  def ExpectOperationWaitRequest(self, operation_ref, operation):
    """Expects the operation WaIt request to be invoked."""
    self.region_operations.Wait.Expect(
        self.messages.ComputeRegionOperationsWaitRequest(
            operation=operation_ref.operation,
            project=operation_ref.project,
            region=operation_ref.region), operation)

  def ExpectOperationPollingRequest(self, operation_ref, operation):
    self.ExpectOperationWaitRequest(operation_ref, operation)
