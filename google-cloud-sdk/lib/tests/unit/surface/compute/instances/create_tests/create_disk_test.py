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


class InstancesCreateCreateDiskTest(create_test_base.InstancesCreateTestBase):
  """Test creation of VM instances with create disk(s)."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateDiskWithAllProperties(self):
    m = self.messages

    self.Run(
        'compute instances create hamlet '
        '  --zone central2-a '
        '  --create-disk name=disk-1,size=10GB,mode=ro,type=SSD,image=debian-8,'
        'image-project=debian-cloud,device-name=data,auto-delete=yes,boot=yes')

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
                          deviceName='data',
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskName='disk-1',
                              diskSizeGb=10,
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/debian-cloud/global/images'
                                  '/debian-8'),
                              diskType=(self.compute_uri +
                                        '/projects/my-project/zones/central2-a/'
                                        'diskTypes/SSD')),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='hamlet',
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
                          scopes=create_test_base.DEFAULT_SCOPES,
                      ),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testCreateDisksWithDefaultProperties(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1 instance-2
          --zone central2-a
          --create-disk size=10GB
          --create-disk image=foo
          --create-disk image-family=bar
          --create-disk description='This is a test disk'
        """)

    self.CheckRequests(self.zone_get_request, self.project_get_request, [
        (self.compute.instances, 'Insert',
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
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             diskSizeGb=10,),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=(self.compute_uri +
                                          '/projects/my-project/global/images/'
                                          'foo'),),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=(self.compute_uri +
                                          '/projects/my-project/global/images/'
                                          'family/bar'),),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             description='This is a test disk'),
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
                                 name='external-nat', type=self._one_to_one_nat)
                         ],
                         network=self._default_network)
                 ],
                 serviceAccounts=[
                     m.ServiceAccount(
                         email='default',
                         scopes=create_test_base.DEFAULT_SCOPES,
                     ),
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
                         autoDelete=True,
                         boot=True,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=self._default_image,),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             diskSizeGb=10,),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=(self.compute_uri +
                                          '/projects/my-project/global/images/'
                                          'foo'),),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             sourceImage=(self.compute_uri +
                                          '/projects/my-project/global/images/'
                                          'family/bar'),),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                     m.AttachedDisk(
                         autoDelete=True,
                         boot=False,
                         initializeParams=m.AttachedDiskInitializeParams(
                             description='This is a test disk'),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                 ],
                 machineType=self._default_machine_type,
                 metadata=m.Metadata(),
                 name='instance-2',
                 networkInterfaces=[
                     m.NetworkInterface(
                         accessConfigs=[
                             m.AccessConfig(
                                 name='external-nat', type=self._one_to_one_nat)
                         ],
                         network=self._default_network)
                 ],
                 serviceAccounts=[
                     m.ServiceAccount(
                         email='default',
                         scopes=create_test_base.DEFAULT_SCOPES,
                     ),
                 ],
                 scheduling=m.Scheduling(automaticRestart=True),
             ),
             project='my-project',
             zone='central2-a',
         ))
    ])

  def testImageFamilyFlagCreateDisk(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --create-disk image-family=yorik
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=False,
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=(self.compute_uri +
                                           '/projects/my-project/global/images/'
                                           'family/yorik'),),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testImageFamilyURICreateDisk(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --create-disk
              image-family='{0}/projects/my-project/global/images/family/yorik'
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=False,
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=(self.compute_uri +
                                           '/projects/my-project/global/images/'
                                           'family/yorik'),),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateDiskTestBeta(create_test_base.InstancesCreateTestBase):
  """Test creation of VM instances with create disk(s)."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testCreateDiskWithAllProperties(self):

    m = self.messages
    self.track = calliope_base.ReleaseTrack.BETA

    self.Run(
        'compute instances create testrp '
        '  --zone central2-a '
        '  --create-disk name=disk-1,size=10GB,mode=ro,type=SSD,image=debian-8,'
        'image-project=debian-cloud,device-name=data,auto-delete=yes,boot=yes,'
        'multi-writer=yes,disk-resource-policy='
        'https://compute.googleapis.com/compute/projects/'
        'cloudsdktest/regions/central2-a/resourcePolicies/testpolicy',
        self.track)

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
                          deviceName='data',
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskName='disk-1',
                              diskSizeGb=10,
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/debian-cloud/global/images'
                                  '/debian-8'),
                              diskType=(self.compute_uri +
                                        '/projects/my-project/zones/central2-a/'
                                        'diskTypes/SSD'),
                              multiWriter=True,
                              resourcePolicies=[
                                  'https://compute.googleapis.com/'
                                  'compute/projects/'
                                  'cloudsdktest/regions/central2-a/'
                                  'resourcePolicies/testpolicy'
                              ]),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='testrp',
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
                          scopes=create_test_base.DEFAULT_SCOPES,
                      ),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )


if __name__ == '__main__':
  test_case.main()
