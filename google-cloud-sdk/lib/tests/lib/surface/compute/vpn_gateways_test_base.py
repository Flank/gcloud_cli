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
"""Base class for all VPN Gateways tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class VpnGatewaysTestBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):
  """Base class for all VPN Gateways test."""

  REGION = 'my-region'
  REGION2 = 'my-region-2'
  REGION3 = 'my-region-3'

  def _GetApiName(self, release_track):
    """Returns the API name for the specified release track."""
    if release_track == calliope_base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif release_track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  def _SetUp(self, release_track):
    """Setup common test components.

    Args:
      release_track: Release track the test is targeting.
    """
    api_name = self._GetApiName(release_track)
    self.track = release_track
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
    self.service = apitools_client.vpnGateways
    self.region_operations = apitools_client.regionOperations
    self.StartPatch('time.sleep')

  def GetRegionUri(self, region_name):
    return '{}/regions/{}'.format(self.base_uri, region_name)

  def GetVpnGatewayRef(self, name, region=REGION):
    """Returns the specified VPN Gateway reference."""
    params = {'project': self.Project(), 'region': region}
    collection = 'compute.vpnGateways'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetNetworkRef(self, name):
    """Returns the specified Network reference."""
    params = {'project': self.Project()}
    collection = 'compute.networks'
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
        labels_message.AdditionalProperty(key=pair[0], value=pair[1])
        for pair in labels
    ])

  def ExpectInsertRequest(self,
                          vpn_gateway_ref,
                          vpn_gateway,
                          response=None,
                          exception=None):
    """Expects the VPN Gateway Insert request to be invoked."""
    request = self.messages.ComputeVpnGatewaysInsertRequest(
        project=vpn_gateway_ref.project,
        region=vpn_gateway_ref.region,
        vpnGateway=vpn_gateway)
    self.service.Insert.Expect(
        request=request, response=response, exception=exception)

  def ExpectGetRequest(self, vpn_gateway_ref, vpn_gateway=None, exception=None):
    """Expects the VPN Gateway Get request to be invoked."""
    self.service.Get.Expect(
        request=self.messages.ComputeVpnGatewaysGetRequest(
            **vpn_gateway_ref.AsDict()),
        response=vpn_gateway,
        exception=exception)

  def ExpectListRequest(self,
                        scoped_vpn_gateways=(),
                        filter_expr=None,
                        exception=None):
    """Expects the VPN Gateway List request to be invoked."""
    vpn_gateways = []
    for scope, vpn_gateways_in_scope in scoped_vpn_gateways:
      scoped_list = self.messages.VpnGatewaysScopedList(
          vpnGateways=vpn_gateways_in_scope, warning=None)
      vpn_gateways.append(
          self.messages.VpnGatewayAggregatedList.ItemsValue.AdditionalProperty(
              key='regions/{}'.format(scope), value=scoped_list))
    self.service.AggregatedList.Expect(
        request=self.messages.ComputeVpnGatewaysAggregatedListRequest(
            filter=filter_expr, project=self.Project()),
        response=self.messages.VpnGatewayAggregatedList(
            items=self.messages.VpnGatewayAggregatedList.ItemsValue(
                additionalProperties=vpn_gateways)),
        exception=exception)

  def ExpectDeleteRequest(self, vpn_gateway_ref, response, exception=None):
    """Expects the VPN Gateway Delete request to be invoked."""
    request = self.messages.ComputeVpnGatewaysDeleteRequest(
        project=vpn_gateway_ref.project,
        region=vpn_gateway_ref.region,
        vpnGateway=vpn_gateway_ref.Name())
    self.service.Delete.Expect(
        request=request, response=response, exception=exception)

  def ExpectSetLabelsRequest(self,
                             vpn_gateway_ref,
                             labels,
                             fingerprint,
                             vpn_gateway_response,
                             exception=None):
    """Expects the VPN Gateway SetLabels request to be invoked."""
    set_labels_request = self.messages.RegionSetLabelsRequest(
        labelFingerprint=fingerprint,
        labels=self.MakeLabelsMessage(
            self.messages.RegionSetLabelsRequest.LabelsValue, labels))
    request = self.messages.ComputeVpnGatewaysSetLabelsRequest(
        project=vpn_gateway_ref.project,
        region=vpn_gateway_ref.region,
        resource=vpn_gateway_ref.vpnGateway,
        regionSetLabelsRequest=set_labels_request)
    self.service.SetLabels.Expect(
        request=request, response=vpn_gateway_response, exception=exception)

  def ExpectOperationGetRequest(self, operation_ref, operation):
    """Expects the operation Get request to be invoked."""
    self.region_operations.Get.Expect(
        self.messages.ComputeRegionOperationsGetRequest(
            operation=operation_ref.operation,
            project=operation_ref.project,
            region=operation_ref.region), operation)
