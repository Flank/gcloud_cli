# -*- coding: utf-8 -*- #
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
"""Common component for instances labels testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class InstancesLabelsTestBase(sdk_test_base.WithFakeAuth,
                              cli_test_base.CliTestBase):
  """Base class for testing instance labels."""

  def SetUp(self):
    api_version = 'v1'
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_version),
        real_client=core_apis.GetClientInstance(
            'compute', api_version, no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_version)
    self.track = calliope_base.ReleaseTrack.GA
    self.service = self.apitools_client.instances
    self.zone_operations = self.apitools_client.zoneOperations

  def _GetInstanceRef(self, name, zone=None):
    params = {'project': self.Project()}
    params['zone'] = zone

    return self.resources.Parse(
        name, params=params, collection='compute.instances')

  def _GetOperationRef(self, name, zone):
    params = {'project': self.Project()}
    params['zone'] = zone
    return self.resources.Parse(
        name, params=params, collection='compute.zoneOperations')

  def _MakeOperationMessage(self, operation_ref, resource_ref=None):
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def _MakeInstanceProto(self, instance_ref, labels=None, fingerprint=None):
    msg = self.messages.Instance()
    if labels is not None:
      labels_value = msg.LabelsValue
      msg.labels = labels_value(additionalProperties=[
          labels_value.AdditionalProperty(key=pair[0], value=pair[1])
          for pair in labels])
    if fingerprint:
      msg.labelFingerprint = fingerprint
    return msg

  def _MakeLabelsProto(self, labels):
    labels_value = self.messages.InstancesSetLabelsRequest.LabelsValue
    return labels_value(additionalProperties=[
        labels_value.AdditionalProperty(key=pair[0], value=pair[1])
        for pair in labels])

  def _ExpectGetRequest(self, instance_ref, instance=None, exception=None):
    request_type = self.messages.ComputeInstancesGetRequest
    self.service.Get.Expect(
        request=request_type(**instance_ref.AsDict()),
        response=instance,
        exception=exception)

  def _ExpectOperationGetRequest(self, operation_ref, operation):
    self.zone_operations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation=operation_ref.operation,
            zone=operation_ref.zone,
            project=self.Project()),
        operation)

  def _ExpectLabelsSetRequest(
      self, instance_ref, labels, fingerprint, response=None, exception=None):
    labels_value = self._MakeLabelsProto(labels)

    request = self.messages.ComputeInstancesSetLabelsRequest(
        project=instance_ref.project,
        instance=instance_ref.instance,
        zone=instance_ref.zone,
        instancesSetLabelsRequest=
        self.messages.InstancesSetLabelsRequest(
            labelFingerprint=fingerprint,
            labels=labels_value)
    )

    self.service.SetLabels.Expect(
        request=request, response=response, exception=exception)
