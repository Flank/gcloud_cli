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
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateMetadataTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testWithMetadata(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --metadata x=y,z=1,a=b,c=d
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
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(items=[
                      m.Metadata.ItemsValueListEntry(key='a', value='b'),
                      m.Metadata.ItemsValueListEntry(key='c', value='d'),
                      m.Metadata.ItemsValueListEntry(key='x', value='y'),
                      m.Metadata.ItemsValueListEntry(key='z', value='1'),
                  ]),
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

  def testWithMetadataFromFile(self):
    m = self.messages

    metadata_file1 = self.Touch(self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute instances create instance-1
          --metadata-from-file x={},y={}
          --zone central2-a
        """.format(metadata_file1, metadata_file2))

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
                  metadata=m.Metadata(items=[
                      m.Metadata.ItemsValueListEntry(key='x', value='hello'),
                      m.Metadata.ItemsValueListEntry(
                          key='y', value='hello\nand\ngoodbye'),
                  ]),
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

  def testWithMetadataAndMetadataFromFile(self):
    m = self.messages

    metadata_file1 = self.Touch(self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute instances create instance-1
          --metadata a=x,b=y,z=d
          --metadata-from-file x={},y={}
          --zone central2-a
        """.format(metadata_file1, metadata_file2))

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
                  metadata=m.Metadata(items=[
                      m.Metadata.ItemsValueListEntry(key='a', value='x'),
                      m.Metadata.ItemsValueListEntry(key='b', value='y'),
                      m.Metadata.ItemsValueListEntry(key='x', value='hello'),
                      m.Metadata.ItemsValueListEntry(
                          key='y', value='hello\nand\ngoodbye'),
                      m.Metadata.ItemsValueListEntry(key='z', value='d'),
                  ]),
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

  def testWithMetadataContainingDuplicateKeys(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Encountered duplicate metadata key \[x\].'):
      self.Run("""
          compute instances create instance-1
            --metadata x=y,z=1
            --metadata-from-file x=file-1
            --zone central2-a
          """)

    self.CheckRequests([(self.compute.zones, 'Get',
                         self.messages.ComputeZonesGetRequest(
                             project='my-project', zone='central2-a'))])

  def testWithMetadataFromNonExistentFile(self):
    metadata_file = self.Touch(self.temp_path, 'file-1', contents='hello')

    with self.assertRaisesRegex(
        files.Error,
        r'Unable to read file \[garbage\]: .*No such file or directory'):
      self.Run("""
          compute instances create instance-1
            --metadata-from-file x={},y=garbage
            --zone central2-a
          """.format(metadata_file))

    self.CheckRequests([(self.compute.zones, 'Get',
                         self.messages.ComputeZonesGetRequest(
                             project='my-project', zone='central2-a'))])

  def testMultipleMetadataArgumentsShouldFail(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
      compute instances create nvme-template-vm
        --zone central2-a
        --metadata block-project-ssh-keys=TRUE
        --metadata sshKeys=''
        --metadata ssh-keys=''
      """)


if __name__ == '__main__':
  test_case.main()
