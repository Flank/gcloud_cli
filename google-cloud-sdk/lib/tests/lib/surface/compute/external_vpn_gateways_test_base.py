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
"""Base class for all external VPN gateways tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ExternalVpnGatewaysTestBase(sdk_test_base.WithFakeAuth,
                                  cli_test_base.CliTestBase):
  """Base class for all External VPN gateway test."""

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

    apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_name),
        real_client=core_apis.GetClientInstance(
            'compute', api_name, no_http=True))
    apitools_client.Mock()
    self.addCleanup(apitools_client.Unmock)
    self.messages = apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_name)
    self.service = apitools_client.externalVpnGateways
    self.global_operations = apitools_client.globalOperations

  def ExpectInsertRequest(self,
                          external_vpn_gateway_ref,
                          external_vpn_gateway,
                          response=None,
                          exception=None):
    """Expects the VPN Tunnel Insert request to be invoked."""
    request = self.messages.ComputeExternalVpnGatewaysInsertRequest(
        project=external_vpn_gateway_ref.project,
        externalVpnGateway=external_vpn_gateway)
    self.service.Insert.Expect(
        request=request, response=response, exception=exception)

  def GetExternalVpnGatewayRef(self, name):
    """Returns the specified external VPN Gateway reference."""
    params = {'project': self.Project()}
    collection = 'compute.externalVpnGateways'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetOperationRef(self, name):
    """Returns the operation reference."""
    params = {'project': self.Project()}
    collection = 'compute.globalOperations'
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

  def ExpectOperationGetRequest(self, operation_ref, operation):
    """Expects the operation Get request to be invoked."""
    self.global_operations.Get.Expect(
        self.messages.ComputeGlobalOperationsGetRequest(
            operation=operation_ref.operation, project=operation_ref.project),
        operation)

  def ExpectGetRequest(self,
                       external_vpn_gateway_ref,
                       external_vpn_gateway=None,
                       exception=None):
    """Expects the External gateway Get request to be invoked."""
    self.service.Get.Expect(
        request=self.messages.ComputeExternalVpnGatewaysGetRequest(
            **external_vpn_gateway_ref.AsDict()),
        response=external_vpn_gateway,
        exception=exception)

  def ExpectDeleteRequest(self,
                          external_vpn_gateway_ref,
                          response,
                          exception=None):
    """Expects the external_vpn_gateway_ref Delete request to be invoked."""
    request = self.messages.ComputeExternalVpnGatewaysDeleteRequest(
        project=external_vpn_gateway_ref.project,
        externalVpnGateway=external_vpn_gateway_ref.Name())
    self.service.Delete.Expect(
        request=request, response=response, exception=exception)

  def ExpectListRequest(self, external_vpn_gateways=None, exception=None):
    """Expects the external VPN gateways List request to be invoked."""
    self.service.List.Expect(
        request=self.messages.ComputeExternalVpnGatewaysListRequest(
            project=self.Project()),
        response=self.messages.ExternalVpnGatewayList(
            items=external_vpn_gateways),
        exception=exception)

  def ExpectSetLabelsRequest(self,
                             gateway_ref,
                             labels,
                             fingerprint,
                             gateway_response,
                             exception=None):
    """Expects the VPN Tunnel SetLabels request to be invoked."""
    set_labels_request = self.messages.GlobalSetLabelsRequest(
        labelFingerprint=fingerprint,
        labels=self.MakeLabelsMessage(
            self.messages.GlobalSetLabelsRequest.LabelsValue, labels))
    request = self.messages.ComputeExternalVpnGatewaysSetLabelsRequest(
        project=gateway_ref.project,
        resource=gateway_ref.externalVpnGateway,
        globalSetLabelsRequest=set_labels_request)
    self.service.SetLabels.Expect(
        request=request, response=gateway_response, exception=exception)
