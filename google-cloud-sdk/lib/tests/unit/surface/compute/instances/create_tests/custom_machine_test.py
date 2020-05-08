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

from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_resources
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateCustomMachineTest(create_test_base.InstancesCreateTestBase
                                      ):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCustomVMCreate(self):
    m = self.messages

    instance_name = 'vmtest'
    custom_cpu = '2'
    custom_ram_mib = '3500'
    project_name = 'my-project'
    custom_vm_type = 'n2'
    zone_name = 'central2-a'

    self.make_requests.side_effect = iter(
        [[
            m.Zone(name=zone_name),
        ],
         [
             self.messages.Project(
                 defaultServiceAccount='default@service.account'),
         ],
         [
             m.MachineType(
                 creationTimestamp='2013-09-06T17:54:10.636-07:00',
                 guestCpus=int(custom_cpu),
                 memoryMb=int(custom_ram_mib)),
         ], []])

    self.Run("""
        compute instances create {0}
        --custom-cpu {1}
        --custom-memory {2}MiB
        --zone {3}
        --custom-vm-type {4}
        """.format(instance_name, custom_cpu, custom_ram_mib, zone_name,
                   custom_vm_type))

    custom_type_string = instance_utils.GetNameForCustom(
        custom_cpu, custom_ram_mib, vm_type=custom_vm_type)
    custom_machine_type = (
        'https://compute.googleapis.com/compute/v1/projects/{0}/'
        'zones/{1}/machineTypes/'
        '{2}'.format(project_name, zone_name, custom_type_string))

    custom_machine_type_name = '{0}-custom-{1}-{2}'.format(
        custom_vm_type, custom_cpu, custom_ram_mib)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.machineTypes, 'Get',
          m.ComputeMachineTypesGetRequest(
              machineType=custom_machine_type_name,
              project=project_name,
              zone=zone_name))],
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
                  machineType=custom_machine_type,
                  metadata=m.Metadata(),
                  name=instance_name,
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
              project=project_name,
              zone=zone_name,
          ))],
    )

  def testCustomVMNoUnitsCreate(self):
    m = self.messages

    instance_name = 'vmtest'
    custom_cpu = '2'
    custom_ram_gib = '3'
    custom_ram_mib = int(custom_ram_gib) * 1024
    project_name = 'my-project'
    zone_name = 'central2-a'

    self.make_requests.side_effect = iter(
        [[
            m.Zone(name=zone_name),
        ],
         [
             self.messages.Project(
                 defaultServiceAccount='default@service.account'),
         ],
         [
             m.MachineType(
                 creationTimestamp='2013-09-06T17:54:10.636-07:00',
                 guestCpus=int(custom_cpu),
                 memoryMb=int(custom_ram_mib)),
         ], []])

    self.Run("""
        compute instances create {0}
        --custom-cpu {1}
        --custom-memory {2}
        --zone {3}
        """.format(instance_name, custom_cpu, custom_ram_gib, zone_name))

    custom_type_string = instance_utils.GetNameForCustom(
        custom_cpu, custom_ram_mib)
    custom_machine_type = (
        'https://compute.googleapis.com/compute/v1/projects/{0}/'
        'zones/{1}/machineTypes/'
        '{2}'.format(project_name, zone_name, custom_type_string))

    custom_machine_type_name = 'custom-{0}-{1}'.format(custom_cpu,
                                                       custom_ram_mib)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.machineTypes, 'Get',
          m.ComputeMachineTypesGetRequest(
              machineType=custom_machine_type_name,
              project=project_name,
              zone=zone_name))],
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
                  machineType=custom_machine_type,
                  metadata=m.Metadata(),
                  name=instance_name,
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
              project=project_name,
              zone=zone_name,
          ))],
    )

  def testExtendedCustomVMCreate(self):
    m = self.messages

    instance_name = 'vmtest'
    custom_cpu = '2'
    custom_ram_mib = '3500'
    project_name = 'my-project'
    zone_name = 'central2-a'

    self.make_requests.side_effect = iter([[
        m.Zone(name=zone_name),
    ], [
        self.messages.Project(defaultServiceAccount='default@service.account'),
    ], [
        m.MachineType(
            creationTimestamp='2013-09-06T17:54:10.636-07:00',
            guestCpus=int(custom_cpu),
            memoryMb=int(custom_ram_mib)),
    ], []])

    self.Run("""
        compute instances create {instance_name}
          --custom-cpu {custom_cpu}
          --custom-memory {custom_ram_mib}MiB
          --custom-extensions
          --zone {zone_name}
        """.format(
            instance_name=instance_name,
            custom_cpu=custom_cpu,
            custom_ram_mib=custom_ram_mib,
            zone_name=zone_name))

    custom_type_string = instance_utils.GetNameForCustom(
        custom_cpu, custom_ram_mib, True)
    custom_machine_type = ('https://compute.googleapis.com/compute/v1/projects/'
                           '{0}/zones/{1}/machineTypes/'
                           '{2}'.format(project_name, zone_name,
                                        custom_type_string))

    custom_machine_type_name = 'custom-{0}-{1}-ext'.format(
        custom_cpu, custom_ram_mib)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.machineTypes, 'Get',
          m.ComputeMachineTypesGetRequest(
              machineType=custom_machine_type_name,
              project=project_name,
              zone=zone_name))],
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
                  machineType=custom_machine_type,
                  metadata=m.Metadata(),
                  name=instance_name,
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=m.AccessConfig.TypeValueValuesEnum
                                  .ONE_TO_ONE_NAT)
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
              project=project_name,
              zone=zone_name,
          ))],
    )

  def testCustomAndMachineTypeCreateError(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Cannot set both \[--machine-type\] and \[--custom-cpu\]/'
        r'\[--custom-memory\] for the same instance.'):
      self.Run("""
        compute instances create vmtest
          --custom-cpu 2
          --custom-memory 8
          --machine-type n1-standard-1
          --zone central2-a
        """)

  def testCustomFlagMissingCreateError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-cpu: --custom-memory must be specified.'):
      self.Run("""
        compute instances create vmtest
          --custom-cpu 2
          --zone central2-a
        """)

  def testCustomZonePrompt(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    m = self.messages

    instance_name = 'vmtest'
    custom_cpu = '2'
    custom_ram_mib = '3500'
    project_name = 'my-project'
    zone_name = test_resources.ZONES[1].name

    self.WriteInput('4\n')

    self.make_requests.side_effect = iter([
        test_resources.ZONES, [
            m.Zone(name=zone_name),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [
            m.MachineType(
                creationTimestamp='2013-09-06T17:54:10.636-07:00',
                guestCpus=int(custom_cpu),
                memoryMb=int(custom_ram_mib)),
        ], []
    ])

    self.Run("""
        compute instances create {0}
        --custom-cpu {1}
        --custom-memory {2}MiB
        """.format(instance_name, custom_cpu, custom_ram_mib))

    custom_type_string = instance_utils.GetNameForCustom(
        custom_cpu, custom_ram_mib)
    custom_machine_type = (
        'https://compute.googleapis.com/compute/v1/projects/{0}/'
        'zones/{1}/machineTypes/'
        '{2}'.format(project_name, zone_name, custom_type_string))

    custom_machine_type_name = 'custom-{0}-{1}'.format(custom_cpu,
                                                       custom_ram_mib)

    self.CheckRequests(
        self.zones_list_request,
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project=project_name, zone=zone_name))],
        self.project_get_request,
        [(self.compute.machineTypes, 'Get',
          m.ComputeMachineTypesGetRequest(
              machineType=custom_machine_type_name,
              project=project_name,
              zone=zone_name))],
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
                  machineType=custom_machine_type,
                  metadata=m.Metadata(),
                  name=instance_name,
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
              project=project_name,
              zone=zone_name,
          ))],
    )


if __name__ == '__main__':
  test_case.main()
