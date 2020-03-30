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
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesWithMultipleNetworkInterfaceCardsTest(
    create_test_base.InstancesCreateTestBase):
  """Test creation of preemptible VM instances."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default,address=
          --network-interface network=some-net,private-network-ip=10.0.0.1,address=8.8.8.8
          --network-interface subnet=some-subnet
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
                                  networkTier=self._default_network_tier,
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version)),
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  networkTier=self._default_network_tier,
                                  natIP='8.8.8.8',
                                  type=self._one_to_one_nat)
                          ],
                          network=(
                              'https://compute.googleapis.com/compute/alpha/'
                              'projects/my-project/global/networks/'
                              'some-net'),
                          networkIP='10.0.0.1'),
                      msg.NetworkInterface(
                          subnetwork=('https://compute.googleapis.com/compute/'
                                      'alpha/projects/my-project/regions/'
                                      'central2/subnetworks/some-subnet'),
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  networkTier=self._default_network_tier,
                                  type=self._one_to_one_nat)
                          ],
                      ),
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

  def testNetworkAndSubnetOnOneInterface(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-interface network=some-network,subnet=some-subnetwork
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
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  networkTier=self._default_network_tier,
                                  type=self._one_to_one_nat)
                          ],
                          network=(self.compute_uri +
                                   '/projects/my-project/global/'
                                   'networks/some-network'),
                          subnetwork=(
                              self.compute_uri + '/projects/my-project/'
                              'regions/central2/subnetworks/some-subnetwork'))
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

  def testNoAddress(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface no-address
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
                          network=(
                              'https://compute.googleapis.com/compute/alpha/'
                              'projects/my-project/global/networks/'
                              'default')),
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

  def testNetworkTier(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default
          --network-interface network=some-net,address=8.8.8.8,network-tier=SELECT
          --network-interface subnet=some-subnet,network-tier=premium
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
                                  type=self._one_to_one_nat,
                                  networkTier=self._default_network_tier)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version)),
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  natIP='8.8.8.8',
                                  type=self._one_to_one_nat,
                                  networkTier=(
                                      msg.AccessConfig
                                      .NetworkTierValueValuesEnum.SELECT))
                          ],
                          network=(
                              'https://compute.googleapis.com/compute/alpha/'
                              'projects/my-project/global/networks/'
                              'some-net')),
                      msg.NetworkInterface(
                          subnetwork=('https://compute.googleapis.com/compute/'
                                      'alpha/projects/my-project/regions/'
                                      'central2/subnetworks/some-subnet'),
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat,
                                  networkTier=msg.AccessConfig
                                  .NetworkTierValueValuesEnum.PREMIUM)
                          ],
                      ),
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

  def testNoAddreassAndAddressOnOneInterface(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-interface\]: specifies both address '
        r'and no-address for one interface'):
      self.Run("""
          compute instances create hamlet
            --zone central2-a
            --image {0}/projects/my-project/global/images/family/yorik
            --network-interface address=192.168.1.1,no-address
          """.format(self.compute_uri))

  def testMultiNicFlagAndOneNicFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'^arguments not allowed simultaneously: --network-interface, all of '
        r'the following: --address, --network, --private-network-ip$'):
      self.Run("""
          compute instances create instance-1
            compute instances create hamlet
            --network-interface ''
            --address 8.8.8.8
            --network net
            --private-network-ip 10.0.0.2
          """)

  def testMultipleMetadataArgumentsShouldFail(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
      compute instances create nvme-template-vm
        --zone central2-a
        --metadata block-project-ssh-keys=TRUE
        --metadata sshKeys=''
        --metadata ssh-keys=''
      """)

  def testInvalidNetworkTier(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--network-interface]: '
        'Invalid value for network-tier'):
      self.Run("""
          compute instances create hamlet
            --zone central2-a
            --network-interface network=default
            --network-interface subnet=some-subnet,network-tier=RANDOM-TIER
          """)


class InstancesWithMultipleNetworkInterfaceCardsTestBeta(
    create_test_base.InstancesCreateTestBase):
  """Test creation of multinic VM instances for beta."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default,address=
          --network-interface network=some-net,private-network-ip=10.0.0.1,address=8.8.8.8
          --network-interface subnet=some-subnet
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
                              self.api_version)),
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  natIP='8.8.8.8',
                                  type=self._one_to_one_nat)
                          ],
                          network=(self.compute_uri +
                                   '/projects/my-project/global/networks/'
                                   'some-net'),
                          networkIP='10.0.0.1'),
                      msg.NetworkInterface(
                          subnetwork=(self.compute_uri +
                                      '/projects/my-project/regions/'
                                      'central2/subnetworks/some-subnet'),
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                      ),
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

  def testNetworkAndSubnetOnOneInterface(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --network-interface network=some-network,subnet=some-subnetwork
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
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=(self.compute_uri +
                                   '/projects/my-project/global/'
                                   'networks/some-network'),
                          subnetwork=(
                              self.compute_uri + '/projects/my-project/'
                              'regions/central2/subnetworks/some-subnetwork'))
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

  def testNoAddress(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface no-address
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
                          network=(self.compute_uri +
                                   '/projects/my-project/global/networks/'
                                   'default')),
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

  def testNoAddreassAndAddressOnOneInterface(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-interface\]: specifies both address '
        r'and no-address for one interface'):
      self.Run("""
          compute instances create hamlet
            --zone central2-a
            --image {0}/projects/my-project/global/images/family/yorik
            --network-interface address=192.168.1.1,no-address
          """.format(self.compute_uri))

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
