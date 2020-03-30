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


class InstancesCreateDiskTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testSimpleDiskOptionWithSingleDiskAndSingleInstance(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --disk name=disk-1
          --zone central2-a
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
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-1')),
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

  def testComplexDiskOptionWithSingleDiskAndSingleInstance(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --zone central2-a
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
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-1')),
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

  def testComplexDiskOptionsWithManyDisksAndSingleInstance(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --disk name=disk-2,mode=ro,device-name=y,auto-delete=yes
          --disk boot=no,device-name=z,name=disk-3,mode=rw
          --zone central2-a
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
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-1')),
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=False,
                          deviceName='y',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-2')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='z',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-3')),
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

  def testDiskOptionWithNoName(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[name\] is missing in \[--disk\]. \[--disk\] value must be of the '
        r'form \[name=NAME \[mode={ro,rw}\] \[boot={yes,no}\] '
        r'\[device-name=DEVICE_NAME\] \[auto-delete={yes,no}\]\].'):
      self.Run("""
          compute instances create instance-1
            --disk mode=rw,device-name=x,boot=no
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithBadMode(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[mode\] in \[--disk\] must be \[rw\] or \[ro\], not '
        r'\[READ_WRITE\].'):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-1,mode=READ_WRITE,device-name=x
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithBadBoot(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[boot\] in \[--disk\] must be \[yes\] or \[no\], not '
        r'\[No\].'):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-1,device-name=x,boot=No
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithReadWriteDisksAndMultipleInstances(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Cannot attach disk \[disk-1\] in read-write mode to more than one '
        'instance.'):
      self.Run("""
          compute instances create instance-1 instance-2
            --disk name=disk-1,mode=rw
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithBootDiskAndImageOption(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Each instance can have exactly one boot disk. One boot disk was '
        r'specified through \[--disk\] and another through \[--image\].'):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-1,mode=rw,boot=yes
            --image image-1
            --zone central2-a
          """)

    self.CheckRequests()

  def testDiskOptionWithManyBootDisks(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Each instance can have exactly one boot disk. At least two boot disks '
        r'were specified through \[--disk\].'):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-1,mode=rw,boot=yes
            --disk name=disk-2,mode=ro,boot=no
            --disk name=disk-3,mode=rw,boot=yes
            --zone central2-a
          """)

    self.CheckRequests()

  def testComplexDiskOptionsWithManyDisksAndManyInstances(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [m.Zone(name='central2-a')],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1 instance-2 instance-3
          --boot-disk-device-name boot-disk
          --boot-disk-size 100GB
          --boot-disk-type pd-ssd
          --no-boot-disk-auto-delete
          --disk name=disk-1,mode=ro,device-name=x,boot=no
          --disk name=disk-2,mode=ro,device-name=y
          --disk boot=no,device-name=z,name=disk-3,mode=ro
          --image image-1
          --zone central2-a
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
                          autoDelete=False,
                          boot=True,
                          deviceName='boot-disk',
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/my-project/global/images/image-1'),
                              diskSizeGb=100,
                              diskType=(self.compute_uri +
                                        '/projects/my-project/zones/central2-a/'
                                        'diskTypes/pd-ssd')),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-1')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='y',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-2')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='z',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-3')),
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
          )),
         (self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          deviceName='boot-disk',
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/my-project/global/images/image-1'),
                              diskSizeGb=100,
                              diskType=(self.compute_uri +
                                        '/projects/my-project/zones/central2-a/'
                                        'diskTypes/pd-ssd')),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-1')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='y',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-2')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='z',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-3')),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-2',
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
          )),
         (self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=True,
                          deviceName='boot-disk',
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/my-project/global/images/image-1'),
                              diskSizeGb=100,
                              diskType=(self.compute_uri +
                                        '/projects/my-project/zones/central2-a/'
                                        'diskTypes/pd-ssd')),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='x',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-1')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='y',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-2')),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          deviceName='z',
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/disks/'
                                  'disk-3')),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-3',
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


if __name__ == '__main__':
  test_case.main()
