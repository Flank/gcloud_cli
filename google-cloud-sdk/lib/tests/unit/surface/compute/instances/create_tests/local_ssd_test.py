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
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateLocalSsdTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testLocalSSDRequestNoDeviceNames(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --local-ssd ''
          --local-ssd interface=NVME
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

  def testLocalSSDRequestBadInterface(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Unexpected local SSD interface: \[SATA\]. '
        r'Legal values are \[NVME, SCSI\].'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --local-ssd device-name=foo,interface=SATA
          """)

  def testLocalSSDRequest(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --local-ssd device-name=foo
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
                          deviceName='foo',
                          initializeParams=(m.AttachedDiskInitializeParams(
                              diskType=self._ssd_disk_type)),
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

  def templateTestLocalSSDRequestTwoSSDs(self, cmd):
    m = self.messages

    self.Run(cmd)

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
                          deviceName='foo',
                          initializeParams=(m.AttachedDiskInitializeParams(
                              diskType=self._ssd_disk_type)),
                          mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
                          type=(m.AttachedDisk.TypeValueValuesEnum.SCRATCH)),
                      m.AttachedDisk(
                          autoDelete=True,
                          deviceName='bar',
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

  def testLocalSSDRequestTwoSSDs(self):
    self.templateTestLocalSSDRequestTwoSSDs("""
        compute instances create instance
          --zone central2-a
          --local-ssd device-name=foo
          --local-ssd device-name=bar,interface=NVME
        """)

  def testLowerCaseNvme(self):
    self.templateTestLocalSSDRequestTwoSSDs("""
        compute instances create instance
          --zone central2-a
          --local-ssd device-name=foo
          --local-ssd device-name=bar,interface=nvme
        """)

if __name__ == '__main__':
  test_case.main()
