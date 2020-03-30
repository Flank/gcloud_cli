# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Common component for disks labels testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class DisksLabelsTestBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):
  """Base class for disks labels test."""

  def _SetUp(self, release_track):
    """Setup common test components.

    Args:
      release_track: Release track the test is targeting.
    """
    api_name = 'v1'
    if release_track == calliope_base.ReleaseTrack.ALPHA:
      api_name = 'alpha'
    elif release_track == calliope_base.ReleaseTrack.BETA:
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
    self.track = release_track
    self.zone_operations = self.apitools_client.zoneOperations
    self.region_operations = getattr(self.apitools_client, 'regionOperations',
                                     None)
    self.StartPatch('time.sleep')

  def _GetDiskRef(self, name, zone=None, region=None):
    params = {'project': self.Project()}
    if region:
      collection = 'compute.regionDisks'
      params['region'] = region
    else:
      collection = 'compute.disks'
      params['zone'] = zone

    return self.resources.Parse(
        name, params=params, collection=collection)

  def _GetOperationRef(self, name, zone=None, region=None):
    params = {'project': self.Project()}
    if zone:
      params['zone'] = zone
      collection = 'compute.zoneOperations'
    if region:
      params['region'] = region
      collection = 'compute.regionOperations'
    return self.resources.Parse(
        name, params=params, collection=collection)

  def _MakeOperationMessage(self, operation_ref, resource_ref=None):
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def _MakeDiskProto(self, disk_ref, labels=None, fingerprint=None):
    msg = self.messages.Disk()
    if labels is not None:
      labels_value = msg.LabelsValue
      msg.labels = labels_value(additionalProperties=[
          labels_value.AdditionalProperty(key=pair[0], value=pair[1])
          for pair in labels])
    if fingerprint:
      msg.labelFingerprint = fingerprint
    return msg

  def _MakeLabelsProto(self, labels_value, labels):
    return labels_value(additionalProperties=[
        labels_value.AdditionalProperty(key=pair[0], value=pair[1])
        for pair in labels])

  def _ExpectGetRequest(self, disk_ref, disk=None, exception=None):
    if disk_ref.Collection() == 'compute.disks':
      service = self.apitools_client.disks
      request_type = self.messages.ComputeDisksGetRequest
    elif disk_ref.Collection() == 'compute.regionDisks':
      service = self.apitools_client.regionDisks
      request_type = self.messages.ComputeRegionDisksGetRequest
    else:
      raise ValueError('Unknown disk reference {}'.format(disk_ref))

    service.Get.Expect(
        request=request_type(**disk_ref.AsDict()),
        response=disk,
        exception=exception)

  def _ExpectOperationGetRequest(self, operation_ref, operation):
    if operation_ref.Collection() == 'compute.zoneOperations':
      self.zone_operations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation=operation_ref.operation,
              zone=operation_ref.zone,
              project=self.Project()),
          operation)
    else:
      self.region_operations.Get.Expect(
          self.messages.ComputeRegionOperationsGetRequest(
              operation=operation_ref.operation,
              region=operation_ref.region,
              project=self.Project()),
          operation)

  def _ExpectOperationWaitRequest(self, operation_ref, operation):
    if operation_ref.Collection() == 'compute.zoneOperations':
      self.zone_operations.Wait.Expect(
          self.messages.ComputeZoneOperationsWaitRequest(
              operation=operation_ref.operation,
              zone=operation_ref.zone,
              project=self.Project()),
          operation)
    else:
      self.region_operations.Wait.Expect(
          self.messages.ComputeRegionOperationsWaitRequest(
              operation=operation_ref.operation,
              region=operation_ref.region,
              project=self.Project()),
          operation)

  def _ExpectOperationPollingRequest(self, operation_ref, operation):
    self._ExpectOperationWaitRequest(operation_ref, operation)

  def _ExpectLabelsSetRequest(
      self, disk_ref, labels, fingerprint, disk=None, exception=None):
    if disk_ref.Collection() == 'compute.disks':
      service = self.apitools_client.disks
      request_type = self.messages.ComputeDisksSetLabelsRequest
      scoped_set_labels_request = self.messages.ZoneSetLabelsRequest
    elif disk_ref.Collection() == 'compute.regionDisks':
      service = self.apitools_client.regionDisks
      request_type = self.messages.ComputeRegionDisksSetLabelsRequest
      scoped_set_labels_request = self.messages.RegionSetLabelsRequest
    else:
      raise ValueError('Unknown disk reference {}'.format(disk_ref))

    labels_value = self._MakeLabelsProto(
        scoped_set_labels_request.LabelsValue, labels)
    request = request_type(
        project=disk_ref.project,
        resource=disk_ref.disk,
    )
    if disk_ref.Collection() == 'compute.disks':
      request.zone = disk_ref.zone
      request.zoneSetLabelsRequest = scoped_set_labels_request(
          labelFingerprint=fingerprint,
          labels=labels_value,
      )
    else:
      request.region = disk_ref.region
      request.regionSetLabelsRequest = scoped_set_labels_request(
          labelFingerprint=fingerprint,
          labels=labels_value,
      )

    service.SetLabels.Expect(
        request=request, response=disk, exception=exception)
