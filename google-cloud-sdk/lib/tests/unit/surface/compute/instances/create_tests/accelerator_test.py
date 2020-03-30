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


class InstancesCreateWithAccelerator(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateInstanceWithAcceleratorNoType(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--accelerator\]: accelerator type must be '
        r'specified\. e\.g\. --accelerator type=nvidia-tesla-k80,count=2'):
      self.Run("""
          compute instances create instance
            --zone central2-a
            --accelerator count=2
          """)

  def testCreateInstanceWithAcceleratorRequest(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --accelerator type=nvidia-tesla-k80,count=2
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
                  ],
                  guestAccelerators=[
                      m.AcceleratorConfig(
                          acceleratorType=create_test_base.AcceleratorTypeOf(
                              'v1', 'nvidia-tesla-k80'),
                          acceleratorCount=2,
                      )
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

  def testCreateInstanceWithAcceleratorCountOmittedRequest(self):
    m = self.messages

    self.Run("""
        compute instances create instance
          --zone central2-a
          --accelerator type=nvidia-tesla-k80
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
                  ],
                  guestAccelerators=[
                      m.AcceleratorConfig(
                          acceleratorType=create_test_base.AcceleratorTypeOf(
                              'v1', 'nvidia-tesla-k80'),
                          acceleratorCount=1,
                      )
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


if __name__ == '__main__':
  test_case.main()
