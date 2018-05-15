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
"""Common component for addresses labels testing."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class AddressesLabelsTestBase(sdk_test_base.WithFakeAuth,
                              cli_test_base.CliTestBase):
  """Base class for addresses labels test."""

  def SetUp(self):
    api_name = 'beta'
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_name),
        real_client=core_apis.GetClientInstance(
            'compute', api_name, no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_name)
    self.track = calliope_base.ReleaseTrack.BETA
    self.global_operations = self.apitools_client.globalOperations
    self.region_operations = self.apitools_client.regionOperations
    self.StartPatch('time.sleep')

  def _GetAddressRef(self, name, region=None):
    params = {'project': self.Project()}
    if region:
      collection = 'compute.addresses'
      params['region'] = region
    else:
      collection = 'compute.globalAddresses'

    return self.resources.Parse(name, params=params, collection=collection)

  def _GetOperationRef(self, name, region=None):
    params = {'project': self.Project()}
    if region:
      collection = 'compute.regionOperations'
      params['region'] = region
    else:
      collection = 'compute.globalOperations'
    return self.resources.Parse(name, params=params, collection=collection)

  def _MakeOperationMessage(self, operation_ref, resource_ref=None):
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def _MakeAddressProto(self, labels=None, fingerprint=None):
    msg = self.messages.Address()
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
    return labels_value(additionalProperties=[
        labels_value.AdditionalProperty(key=pair[0], value=pair[1])
        for pair in labels
    ])

  def _ExpectGetRequest(self, address_ref, address=None, exception=None):
    if address_ref.Collection() == 'compute.globalAddresses':
      service = self.apitools_client.globalAddresses
      request_type = self.messages.ComputeGlobalAddressesGetRequest
    else:
      service = self.apitools_client.addresses
      request_type = self.messages.ComputeAddressesGetRequest

    service.Get.Expect(
        request=request_type(**address_ref.AsDict()),
        response=address,
        exception=exception)

  def _ExpectOperationGetRequest(self, operation_ref, operation):
    if operation_ref.Collection() == 'compute.globalOperations':
      self.global_operations.Get.Expect(
          self.messages.ComputeGlobalOperationsGetRequest(
              operation=operation_ref.operation, project=self.Project()),
          operation)
    else:
      self.region_operations.Get.Expect(
          self.messages.ComputeRegionOperationsGetRequest(
              operation=operation_ref.operation,
              region=operation_ref.region,
              project=self.Project()), operation)

  def _ExpectLabelsSetRequest(self,
                              address_ref,
                              labels,
                              fingerprint,
                              address=None,
                              exception=None):
    if address_ref.Collection() == 'compute.globalAddresses':
      service = self.apitools_client.globalAddresses
      request_type = self.messages.ComputeGlobalAddressesSetLabelsRequest
      scoped_set_labels_request = self.messages.GlobalSetLabelsRequest
    else:
      service = self.apitools_client.addresses
      request_type = self.messages.ComputeAddressesSetLabelsRequest
      scoped_set_labels_request = self.messages.RegionSetLabelsRequest

    labels_value = self._MakeLabelsProto(scoped_set_labels_request.LabelsValue,
                                         labels)
    request = request_type(
        project=address_ref.project,
        resource=address_ref.address,)
    if address_ref.Collection() == 'compute.globalAddresses':
      request.globalSetLabelsRequest = scoped_set_labels_request(
          labelFingerprint=fingerprint,
          labels=labels_value,)
    else:
      request.region = address_ref.region
      request.regionSetLabelsRequest = scoped_set_labels_request(
          labelFingerprint=fingerprint,
          labels=labels_value,)

    service.SetLabels.Expect(
        request=request, response=address, exception=exception)
