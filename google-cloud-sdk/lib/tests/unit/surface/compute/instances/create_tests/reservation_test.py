# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateReservationTest(create_test_base.InstancesCreateTestBase,
                                     parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testWithAnyReservationAffinity(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1 --zone central2-a
        --reservation-affinity=any
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  reservationAffinity=m.ReservationAffinity(
                      consumeReservationType=m.ReservationAffinity
                      .ConsumeReservationTypeValueValuesEnum.ANY_RESERVATION,),
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithSpecificReservationAffinity(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1 --zone central2-a
        --reservation-affinity=specific --reservation=my-reservation
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  reservationAffinity=m.ReservationAffinity(
                      consumeReservationType=m.ReservationAffinity
                      .ConsumeReservationTypeValueValuesEnum
                      .SPECIFIC_RESERVATION,
                      key='compute.googleapis.com/reservation-name',
                      values=['my-reservation']),
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithNotSpecifiedReservation(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        'The name the specific reservation must be specified.'):
      self.Run("""
        compute instances create instance-1 --zone central2-a
        --reservation-affinity=specific
        """)

  def testWithNoReservationAffinity(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1 --zone central2-a
        --reservation-affinity=none
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  reservationAffinity=m.ReservationAffinity(
                      consumeReservationType=m.ReservationAffinity
                      .ConsumeReservationTypeValueValuesEnum.NO_RESERVATION,),
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithMultipleResourcePolicies(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --resource-policies pol1,pol2
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  resourcePolicies=[
                      self.compute_uri + '/projects/{}/regions/central2/'
                      'resourcePolicies/pol1'.format(self.Project()),
                      self.compute_uri + '/projects/{}/regions/central2/'
                      'resourcePolicies/pol2'.format(self.Project())
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithMinNodeCpus(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --min-node-cpu 10
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True, minNodeCpus=10),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateReservationTestBeta(InstancesCreateReservationTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstancesCreateReservationTestAlpha(InstancesCreateReservationTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testLocalNVDIMMRequest(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --local-nvdimm ''
          --local-nvdimm size=3TB
        """)

    self.CheckRequests(
        self.zone_get_request, self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image)),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=True,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              diskType=self._nvdimm_disk_type)),
                          interface=(
                              m.AttachedDisk.InterfaceValueValuesEnum.NVDIMM),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                      m.AttachedDisk(
                          autoDelete=True,
                          diskSizeGb=3072,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              diskType=self._nvdimm_disk_type)),
                          interface=(
                              m.AttachedDisk.InterfaceValueValuesEnum.NVDIMM),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=(m.AccessConfig.TypeValueValuesEnum
                                        .ONE_TO_ONE_NAT))
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))])

  def testLocalSSDRequestWithSize(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --local-ssd ''
          --local-ssd interface=NVME,size=750
        """)

    self.CheckRequests(
        self.zone_get_request, self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image)),
                          mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)),
                      m.AttachedDisk(
                          autoDelete=True,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              diskType=self._ssd_disk_type)),
                          mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk.TypeValueValuesEnum.SCRATCH)),
                      m.AttachedDisk(
                          autoDelete=True,
                          diskSizeGb=750,
                          initializeParams=(m.AttachedDiskInitializeParams(
                              diskType=self._ssd_disk_type)),
                          interface=(
                              m.AttachedDisk.InterfaceValueValuesEnum.NVME),
                          mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk.TypeValueValuesEnum.SCRATCH)),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=(m.AccessConfig.TypeValueValuesEnum
                                        .ONE_TO_ONE_NAT))
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))])

  def testLocalSSDRequestWithBadSize(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Unexpected local SSD size: \[536870912000\]. '
        r'Legal values are positive multiples of 375GB.'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --local-ssd size=500
          """)

  def createWithOnHostMaintenanceTest(self, flag):
    m = self.messages

    self.Run('compute instances create instance-1 --zone central2-a '
             '{}=TERMINATE'.format(flag))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True,
                      onHostMaintenance=m.Scheduling
                      .OnHostMaintenanceValueValuesEnum.TERMINATE),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithOnHostMaintenance(self):
    self.createWithOnHostMaintenanceTest('--on-host-maintenance')

  def testMaintenancePolicyDeprecation(self):
    self.createWithOnHostMaintenanceTest('--maintenance-policy')
    self.AssertErrContains(
        'WARNING: The --maintenance-policy flag is now deprecated. '
        'Please use `--on-host-maintenance` instead')

  def testWithResourcePolicies(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --resource-policies pol1
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  resourcePolicies=[
                      self.compute_uri + '/projects/{}/regions/central2/'
                      'resourcePolicies/pol1'.format(self.Project())
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithLocationHint(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --location-hint cell1
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True, locationHint='cell1'),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


if __name__ == '__main__':
  test_case.main()
