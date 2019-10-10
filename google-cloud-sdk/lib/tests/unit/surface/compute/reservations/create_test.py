# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""compute reservations create tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import allocations_test_base as base
from tests.lib.surface.compute import test_base


class CreateTest(test_base.BaseTest, base.AllocationTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

  def testSimpleCreate(self):
    self.make_requests.side_effect = iter([[]])
    reservation = self.messages.Reservation(
        name='alloc',
        zone='fake-zone',
        specificReservationRequired=False,
        specificReservation=self.messages.AllocationSpecificSKUReservation(
            count=1,
            instanceProperties=self.messages
            .AllocationSpecificSKUAllocationReservedInstanceProperties(
                machineType='n1-standard-1', minCpuPlatform='Intel Haswell')))

    self.Run('compute reservations create alloc --zone=fake-zone '
             '--vm-count=1 '
             '--machine-type=n1-standard-1 '
             '--min-cpu-platform="Intel Haswell" ')

    self.CheckRequests([(self.compute.reservations, 'Insert',
                         self.messages.ComputeReservationsInsertRequest(
                             reservation=reservation,
                             project='my-project',
                             zone='fake-zone',
                         ))],)

  def testCreateWithAccelerator(self):
    self.make_requests.side_effect = iter([[]])
    reservation = self.messages.Reservation(
        name='alloc',
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
                    self.messages.AcceleratorConfig(
                        acceleratorCount=2, acceleratorType='nvidia-grid-k2'),
                ])))

    self.Run('compute reservations create alloc --zone=fake-zone '
             '--require-specific-reservation '
             '--vm-count=1 '
             '--machine-type=n1-standard-1 '
             '--min-cpu-platform="Intel Haswell" '
             '--accelerator count=1,type=nvidia-tesla-k80 '
             '--accelerator count=2,type=nvidia-grid-k2 ')

    self.CheckRequests([(self.compute.reservations, 'Insert',
                         self.messages.ComputeReservationsInsertRequest(
                             reservation=reservation,
                             project='my-project',
                             zone='fake-zone',
                         ))],)

  def testCreateWithLocalSsd(self):
    self.make_requests.side_effect = iter([[]])
    reservation = self.messages.Reservation(
        name='alloc',
        zone='fake-zone',
        specificReservationRequired=True,
        specificReservation=self.messages.AllocationSpecificSKUReservation(
            count=1,
            instanceProperties=self.messages
            .AllocationSpecificSKUAllocationReservedInstanceProperties(
                machineType='n1-standard-1',
                minCpuPlatform='Intel Haswell',
                guestAccelerators=[],
                localSsds=[
                    self.messages.
                    AllocationSpecificSKUAllocationAllocatedInstancePropertiesReservedDisk(  # pylint: disable=line-too-long
                        diskSizeGb=1,
                        interface=self.messages.
                        AllocationSpecificSKUAllocationAllocatedInstancePropertiesReservedDisk  # pylint: disable=line-too-long
                        .InterfaceValueValuesEnum.SCSI),
                    self.messages.
                    AllocationSpecificSKUAllocationAllocatedInstancePropertiesReservedDisk(  # pylint: disable=line-too-long
                        diskSizeGb=2,
                        interface=self.messages.
                        AllocationSpecificSKUAllocationAllocatedInstancePropertiesReservedDisk  # pylint: disable=line-too-long
                        .InterfaceValueValuesEnum.NVME),
                ])))

    self.Run('compute reservations create alloc --zone=fake-zone '
             '--require-specific-reservation '
             '--vm-count=1 '
             '--machine-type=n1-standard-1 '
             '--min-cpu-platform="Intel Haswell" '
             '--local-ssd interface=scsi,size=1 '
             '--local-ssd interface=nvme,size=2 ')

    self.CheckRequests([(self.compute.reservations, 'Insert',
                         self.messages.ComputeReservationsInsertRequest(
                             reservation=reservation,
                             project='my-project',
                             zone='fake-zone',
                         ))],)


class CreateTestBeta(CreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')


class CreateTestAlpha(CreateTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')


if __name__ == '__main__':
  test_case.main()
