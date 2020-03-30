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
"""Tests for the instances create-with-container subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_with_container_test_base as test_base


class InstancesCreateFromContainerContainerMountDiskTestGA(
    test_base.InstancesCreateWithContainerTestBase, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def GetDiskMessage(self,
                     initialize_params=None,
                     mode=None,
                     source=None,
                     auto_delete=False,
                     device_name='disk-1'):
    m = self.messages
    return m.AttachedDisk(
        autoDelete=auto_delete,
        boot=False,
        deviceName=device_name,
        licenses=[],
        initializeParams=initialize_params,
        mode=mode or m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        source=source,
        type=(m.AttachedDisk.TypeValueValuesEnum.PERSISTENT))

  def _CheckCallsForCreateInstanceWithContainer(self, disk, container_manifest):
    m = self.messages
    metadata = m.Metadata(items=[
        m.Metadata.ItemsValueListEntry(
            key='gce-container-declaration',
            value=containers_utils.DumpYaml(container_manifest)),
        m.Metadata.ItemsValueListEntry(
            key='google-logging-enabled', value='true')
    ])
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  disks=[self.default_attached_disk, disk],
                  labels=self.default_labels,
                  machineType=self.default_machine_type,
                  metadata=metadata,
                  name='instance-1',
                  networkInterfaces=[self.default_network_interface],
                  scheduling=m.Scheduling(automaticRestart=True),
                  serviceAccounts=[self.default_service_account],
                  tags=self.default_tags),
              project='my-project',
              zone='central2-a',
          ))],
    )

  @parameterized.named_parameters(
      ('DeviceNameGiven', 'name=disk-1,mode=rw,device-name=disk-1',
       'name=disk-1,mount-path="/mounted"', False),
      ('DeviceNameNotGiven', 'name=disk-1,mode=rw',
       'name=disk-1,mount-path="/mounted"', True),
      ('DeviceNameNotGivenAndDiskNameNotGiven', 'name=disk-1,mode=rw',
       'mount-path="/mounted"', True),
      ('ContainerNameNotGiven', 'name=disk-1,mode=rw,device-name=disk-1',
       'mount-path="/mounted"', False))
  def testContainerMountDiskCreate(self, disk_flag_value, container_flag_value,
                                   expect_warning):
    m = self.messages
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --create-disk {}
          --container-mount-disk {}
        """.format(disk_flag_value, container_flag_value))
    disk = self.GetDiskMessage(
        initialize_params=m.AttachedDiskInitializeParams(diskName='disk-1'),
        auto_delete=True)
    container_manifest = {
        'spec': {
            'containers': [{
                'name':
                    'instance-1',
                'image':
                    'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin':
                    False,
                'tty':
                    False,
                'volumeMounts': [{
                    'name': 'pd-0',
                    'mountPath': '/mounted',
                    'readOnly': False
                }]
            }],
            'restartPolicy':
                'Always',
            'volumes': [{
                'name': 'pd-0',
                'gcePersistentDisk': {
                    'pdName': 'disk-1',
                    'fsType': 'ext4'
                }
            }]
        }
    }
    self._CheckCallsForCreateInstanceWithContainer(disk, container_manifest)
    warning_text = (
        'Default device-name for disk name [disk-1] will be [disk-1] because '
        'it is being mounted to a container with [`--container-mount-disk`]')
    if expect_warning:
      self.AssertErrContains(warning_text)
    else:
      self.AssertErrNotContains(warning_text)

  @parameterized.named_parameters(
      ('DeviceNameGiven', 'name=disk-1,mode=rw,device-name=disk-1',
       'name=disk-1,mount-path="/mounted"', False),
      ('DeviceNameNotGiven', 'name=disk-1,mode=rw',
       'name=disk-1,mount-path="/mounted"', True),
      ('DeviceNameNotGivenAndDiskNameNotGiven', 'name=disk-1,mode=rw',
       'mount-path="/mounted"', True),
      ('ContainerNameNotGiven', 'name=disk-1,mode=rw,device-name=disk-1',
       'mount-path="/mounted"', False))
  def testContainerMountDiskAttach(self, disk_flag_value, container_flag_value,
                                   expect_warning):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --disk {}
          --container-mount-disk {}
        """.format(disk_flag_value, container_flag_value))
    disk = self.GetDiskMessage(
        source='{}/projects/my-project/zones/central2-a/disks/disk-1'.format(
            self.compute_uri))
    container_manifest = {
        'spec': {
            'containers': [{
                'name':
                    'instance-1',
                'image':
                    'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin':
                    False,
                'tty':
                    False,
                'volumeMounts': [{
                    'name': 'pd-0',
                    'mountPath': '/mounted',
                    'readOnly': False
                }]
            }],
            'restartPolicy':
                'Always',
            'volumes': [{
                'name': 'pd-0',
                'gcePersistentDisk': {
                    'pdName': 'disk-1',
                    'fsType': 'ext4'
                }
            }]
        }
    }
    self._CheckCallsForCreateInstanceWithContainer(disk, container_manifest)
    warning_text = (
        'Default device-name for disk name [disk-1] will be [disk-1] because '
        'it is being mounted to a container with [`--container-mount-disk`]')
    if expect_warning:
      self.AssertErrContains(warning_text)
    else:
      self.AssertErrNotContains(warning_text)

  def testContainerMountDiskWithOptions(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --disk name=disk-1,mode=rw,device-name=disk-1
          --container-mount-disk
          name=disk-1,mode=ro,mount-path="/mounted",partition=1
          --container-mount-disk
          name=disk-1,mode=ro,mount-path="/mounted-1",partition=2
        """)
    disk = self.GetDiskMessage(
        source=('{0}/projects/my-project/zones/central2-a/'
                'disks/disk-1'.format(self.compute_uri)))
    container_manifest = {
        'spec': {
            'containers': [{
                'name':
                    'instance-1',
                'image':
                    'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin':
                    False,
                'tty':
                    False,
                'volumeMounts': [{
                    'name': 'pd-0',
                    'mountPath': '/mounted',
                    'readOnly': True
                }, {
                    'name': 'pd-1',
                    'mountPath': '/mounted-1',
                    'readOnly': True
                }]
            }],
            'restartPolicy':
                'Always',
            'volumes': [{
                'name': 'pd-0',
                'gcePersistentDisk': {
                    'pdName': 'disk-1',
                    'fsType': 'ext4',
                    'partition': 1
                }
            }, {
                'name': 'pd-1',
                'gcePersistentDisk': {
                    'pdName': 'disk-1',
                    'fsType': 'ext4',
                    'partition': 2
                }
            }]
        }
    }
    self._CheckCallsForCreateInstanceWithContainer(disk, container_manifest)

  @parameterized.named_parameters(
      ('NameGivenWithPartition', '--container-mount-disk '
       'name=disk-1,mode=ro,mount-path="/mounted",partition=1 '
       '--container-mount-disk '
       'name=disk-1,mode=ro,mount-path="/mounted-1",partition=1', {
           'pdName': 'disk-1',
           'fsType': 'ext4',
           'partition': 1
       }),
      ('NameNotGivenWithPartition',
       '--container-mount-disk mode=ro,mount-path="/mounted",partition=1 '
       '--container-mount-disk mode=ro,mount-path="/mounted-1",partition=1', {
           'pdName': 'disk-1',
           'fsType': 'ext4',
           'partition': 1
       }),
      ('NameGivenNoPartition',
       '--container-mount-disk name=disk-1,mode=ro,mount-path="/mounted" '
       '--container-mount-disk name=disk-1,mode=ro,mount-path="/mounted-1"', {
           'pdName': 'disk-1',
           'fsType': 'ext4'
       }), ('NameNotGivenNoPartition',
            '--container-mount-disk mode=ro,mount-path="/mounted" '
            '--container-mount-disk mode=ro,mount-path="/mounted-1"', {
                'pdName': 'disk-1',
                'fsType': 'ext4'
            }))
  def testContainerMountDiskWithRepeatedDiskAndPartition(
      self, container_mount_disk_flag, volume_pd_config):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --disk name=disk-1,mode=rw,device-name=disk-1
          {}
        """.format(container_mount_disk_flag))
    disk = self.GetDiskMessage(
        source=('{0}/projects/my-project/zones/central2-a/'
                'disks/disk-1'.format(self.compute_uri)))
    container_manifest = {
        'spec': {
            'containers': [{
                'name':
                    'instance-1',
                'image':
                    'gcr.io/my-docker/test-image',
                'securityContext': {
                    'privileged': False
                },
                'stdin':
                    False,
                'tty':
                    False,
                'volumeMounts': [{
                    'name': 'pd-0',
                    'mountPath': '/mounted',
                    'readOnly': True
                }, {
                    'name': 'pd-0',
                    'mountPath': '/mounted-1',
                    'readOnly': True
                }]
            }],
            'restartPolicy': 'Always',
            'volumes': [{
                'name': 'pd-0',
                'gcePersistentDisk': volume_pd_config
            }]
        }
    }
    self._CheckCallsForCreateInstanceWithContainer(disk, container_manifest)

  @parameterized.named_parameters(
      # device-name, if given, must be the same as name.
      ('AttachMismatched', '--disk name=disk-1,mode=rw,device-name=pd-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)\[disk-1\](.*)\[pd-1\]'),
      ('CreateMismatched', '--create-disk name=disk-1,mode=rw,device-name=pd-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)\[disk-1\](.*)\[pd-1\]'),
      # --disk or --create-disk must have a disk whose name matches.
      ('NoDisk', '', '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)Must be used with `--disk` or '
       r'`--create-disk`'),
      ('AttachNotFound', '--disk name=disk-2,mode=rw,device-name=disk-2',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)\[disk-1\]'),
      ('CreateNotFound', '--create-disk name=disk-2,mode=rw,device-name=disk-2',
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)\[disk-1\]'),
      # If no name is given for --container-mount-disk, there can be only one
      # disk specified with --disk or --create-disk.
      ('NoNameSpecified', '--disk name=disk-1,mode=rw,device-name=disk-1 '
       '--disk name=disk-2,mode=rw,device-name=disk-2',
       '--container-mount-disk mount-path="/mounted"',
       r'--container-mount-disk(.*)Must specify the name of the disk to be '
       r'mounted'),
      # If no name is given for --create-disk, should fail.
      ('DiskNameNotGiven', '--create-disk mode=rw',
       '--container-mount-disk mount-path="/mounted"', r'--container-mount-disk'
      ),
      # attached disk mode must be rw if --container-mount-disk mode is rw.
      ('MismatchedModeAttach', '--disk name=disk-1,mode=ro,device-name=disk-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted",mode=rw',
       r'--container-mount-disk(.*)\[rw\](.*)\[ro\](.*)disk name \[disk-1\], '
       r'partition \[None\]'),
      ('MismatchedModeCreate',
       '--create-disk name=disk-1,mode=ro,device-name=disk-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted",mode=rw',
       r'--container-mount-disk(.*)\[rw\](.*)\[ro\](.*)disk name \[disk-1\], '
       r'partition \[None\]'),
      ('CreatedInROMode',
       '--create-disk name=disk-1,mode=ro,device-name=disk-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted",mode=ro',
       r'--container-mount-disk(.*)disk named \[disk-1\](.*)disk is created '
       r'in \[ro\] mode'),
      ('PartitionWithCreateDisk',
       '--create-disk name=disk-1,device-name=disk-1',
       '--container-mount-disk name=disk-1,mount-path="/mounted",partition=1',
       r'--container-mount-disk(.*)partition'))
  def testContainerMountDiskInvalid(self, disk_flag, container_mount_flag,
                                    regexp):
    with self.assertRaisesRegexp(calliope_exceptions.InvalidArgumentException,
                                 regexp):
      self.Run("""
          compute instances create-with-container instance-1
            --zone central2-a
            --container-image=gcr.io/my-docker/test-image
            {}
            {}
          """.format(disk_flag, container_mount_flag))


class InstancesCreateFromContainerContainerMountDiskTestBeta(
    InstancesCreateFromContainerContainerMountDiskTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstancesCreateFromContainerContainerMountDiskTestAlpha(
    InstancesCreateFromContainerContainerMountDiskTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
