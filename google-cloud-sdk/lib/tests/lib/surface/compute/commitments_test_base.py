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
"""Base class for compute commitments tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import test_base as compute_test_base


class TestBase(compute_test_base.BaseTest):
  """Base class for compute commitments unit tests."""

  def _SetUp(self, track):
    if track == calliope_base.ReleaseTrack.ALPHA:
      self.api_version = 'alpha'
    elif track == calliope_base.ReleaseTrack.BETA:
      self.api_version = 'beta'
    else:
      self.api_version = 'v1'
    self.SelectApi(self.api_version)
    self.messages = apis.GetMessagesModule('compute', self.api_version)
    self.mock_client = mock.Client(
        apis.GetClientClass('compute', self.api_version),
        real_client=apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def SetUp(self):
    self._SetUp(self.track)

  def MakeCommitment(self,
                     name='pledge',
                     reservations=None,
                     resource_commitments=None):
    if resource_commitments:
      resources = resource_commitments
    else:
      resources = [
          self.MakeVCPUResourceCommitment(),
          self.MakeMemoryResourceCommitment()
      ]
    commitment = self.messages.Commitment(
        name=name,
        plan=self.messages.Commitment.PlanValueValuesEnum.TWELVE_MONTH,
        resources=resources)

    if self.api_version == 'alpha' or self.api_version == 'beta':
      commitment.type = self.messages.Commitment.TypeValueValuesEnum.GENERAL_PURPOSE

    if reservations:
      commitment.reservations = reservations or []
    return commitment

  def MakeReservation(self, name):
    ssd_msgs = (
        self.messages
        .AllocationSpecificSKUAllocationAllocatedInstancePropertiesReservedDisk)
    return self.messages.Reservation(
        name=name,
        zone='fake-zone',
        specificReservationRequired=True,
        specificReservation=self.messages.AllocationSpecificSKUReservation(
            count=1,
            instanceProperties=self.messages
            .AllocationSpecificSKUAllocationReservedInstanceProperties(
                machineType='n1-standard-1',
                minCpuPlatform='Intel Haswell',
                guestAccelerators=[
                    self.messages.AcceleratorConfig(
                        acceleratorCount=1, acceleratorType='nvidia-tesla-k80'),
                ],
                localSsds=[
                    ssd_msgs(
                        diskSizeGb=375,
                        interface=ssd_msgs.InterfaceValueValuesEnum.SCSI),
                    ssd_msgs(
                        diskSizeGb=375,
                        interface=ssd_msgs.InterfaceValueValuesEnum.NVME),
                ])))

  def MakeAcceleratorResourceCommitment(self, amount=3, acce_type='ace-type'):
    return self.messages.ResourceCommitment(
        amount=amount,
        type=(self.messages.ResourceCommitment.TypeValueValuesEnum.ACCELERATOR),
        acceleratorType=acce_type)

  def MakeLocalSsdResourceCommitment(self, amount=1):
    return self.messages.ResourceCommitment(
        amount=amount,
        type=(self.messages.ResourceCommitment.TypeValueValuesEnum.LOCAL_SSD))

  def MakeVCPUResourceCommitment(self, amount=500):
    return self.messages.ResourceCommitment(
        amount=amount,
        type=(self.messages.ResourceCommitment.TypeValueValuesEnum.VCPU))

  def MakeMemoryResourceCommitment(self, amount=12 * 1024):
    return self.messages.ResourceCommitment(
        amount=amount,
        type=(self.messages.ResourceCommitment.TypeValueValuesEnum.MEMORY))
