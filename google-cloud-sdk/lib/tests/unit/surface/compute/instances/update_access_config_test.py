# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for the instances update-access-config subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InstancesUpdateAccessConfigTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.track = self.track = calliope_base.ReleaseTrack.GA

  def CreateAccessConfig(self, set_ptr, ptr_domain_name):
    access_config = self.messages.AccessConfig(
        name='external-nat',
        natIP='1.2.3.4',
        type=self.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return access_config

  def CreateNetworkInterface(self,
                             network_interface_name='nic0',
                             set_ptr=None,
                             ptr_domain_name=None):
    access_config = self.CreateAccessConfig(
        set_ptr=set_ptr,
        ptr_domain_name=ptr_domain_name)

    return self.messages.NetworkInterface(
        name=network_interface_name,
        accessConfigs=[access_config],
        network='fake-network-url')

  def CreateUpdateAccessConfigRequest(self, network_interface_name, set_ptr,
                                      ptr_domain_name):
    access_config = self.CreateAccessConfig(
        set_ptr=set_ptr,
        ptr_domain_name=ptr_domain_name)

    return self.messages.ComputeInstancesUpdateAccessConfigRequest(
        accessConfig=access_config,
        instance='my-instance',
        networkInterface=network_interface_name,
        project='my-project',
        zone='central1-a')

  def VerifyRequests(self,
                     network_interface_name,
                     set_ptr=None,
                     ptr_domain_name=None):
    self.CheckRequests(
        [(self.compute.instances, 'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='my-instance', project='my-project',
              zone='central1-a'))],
        [(self.compute.instances, 'UpdateAccessConfig',
          self.CreateUpdateAccessConfigRequest(
              network_interface_name=network_interface_name,
              set_ptr=set_ptr,
              ptr_domain_name=ptr_domain_name))],)

  def testEnablePublicPtrWithDefaultNetworkInterface(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --public-ptr --public-ptr-domain example.com
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_ptr=True,
        ptr_domain_name='example.com')

  def testEnablePublicPtrWithNetworkInterfaceFlag(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-interface nic0
          --public-ptr --public-ptr-domain example.com
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_ptr=True,
        ptr_domain_name='example.com')

  def testDisablePublicPtr(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(
                        set_ptr=True,
                        ptr_domain_name='example.com'),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-interface nic0
          --no-public-ptr --no-public-ptr-domain
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_ptr=False,
        ptr_domain_name='')

  def testNoUpdate(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(
                        set_ptr=True,
                        ptr_domain_name='example.com')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --public-ptr --public-ptr-domain example.com
          --zone central1-a
        """)

    # UpdateAccessConfig method should not be called since the access config
    # stays the same.
    self.CheckRequests([(self.compute.instances, 'Get',
                         self.messages.ComputeInstancesGetRequest(
                             instance='my-instance',
                             project='my-project',
                             zone='central1-a'))])

  def testNetworkInterfaceNotBeingDefault(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'Public PTR can only be enabled for default network interface '
        r'\'nic0\' rather than \'nic1\'.'):
      self.Run("""
            compute instances update-access-config my-instance
            --network-interface nic1
            --public-ptr --public-ptr-domain example.com
            --zone central1-a
          """)

  def testNetworkInterfaceNotExist(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[])
        ],
        [],
    ])

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-interface\]: The specified network '
        r'interface \'nic0\' does not exist'):
      self.Run("""
            compute instances update-access-config my-instance
            --network-interface nic0
            --public-ptr --public-ptr-domain example.com
            --zone central1-a
          """)

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr: At most one of --public-ptr | --no-public-ptr '
        'may be specified.'):
      self.Run("""
          compute instances update-access-config instance-1 --no-public-ptr
            --public-ptr
            --zone central2-a
          """)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr-domain: At most one of --public-ptr-domain | '
        '--no-public-ptr-domain may be specified.'):
      self.Run("""
          compute instances update-access-config instance-1
            --no-public-ptr-domain
            --public-ptr-domain example.com
            --zone central2-a
          """)

    with self.assertRaisesRegex(
        exceptions.ConflictingArgumentsException,
        r'arguments not allowed simultaneously: --public-ptr-domain, '
        r'--no-public-ptr'):
      self.Run("""
          compute instances update-access-config instance-1 --no-public-ptr
            --public-ptr-domain example.com
            --zone central2-a
          """)


class InstancesUpdateAccessConfigBetaTest(InstancesUpdateAccessConfigTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = self.track = calliope_base.ReleaseTrack.BETA


class InstancesUpdateAccessConfigAlphaTest(InstancesUpdateAccessConfigTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = self.track = calliope_base.ReleaseTrack.ALPHA

  def CreateAccessConfig(self, set_public_dns, dns_name, set_ptr,
                         ptr_domain_name, network_tier='PREMIUM'):
    network_tier_enum = self.messages.AccessConfig.NetworkTierValueValuesEnum(
        network_tier)
    access_config = self.messages.AccessConfig(
        name='external-nat',
        networkTier=network_tier_enum,
        natIP='1.2.3.4',
        type=self.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    if set_public_dns is not None:
      access_config.setPublicDns = bool(set_public_dns)
    if dns_name is not None:
      access_config.publicDnsName = dns_name
    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return access_config

  def CreateNetworkInterface(self,
                             network_interface_name='nic0',
                             set_public_dns=None,
                             dns_name=None,
                             set_ptr=None,
                             ptr_domain_name=None,
                             network_tier='PREMIUM'):
    access_config = self.CreateAccessConfig(
        set_public_dns=set_public_dns,
        dns_name=dns_name,
        set_ptr=set_ptr,
        ptr_domain_name=ptr_domain_name,
        network_tier=network_tier)

    return self.messages.NetworkInterface(
        name=network_interface_name,
        accessConfigs=[access_config],
        network='fake-network-url')

  def CreateUpdateAccessConfigRequest(self, network_interface_name,
                                      set_public_dns, set_ptr, ptr_domain_name,
                                      network_tier):
    access_config = self.CreateAccessConfig(
        set_public_dns=set_public_dns,
        dns_name=None,
        set_ptr=set_ptr,
        ptr_domain_name=ptr_domain_name,
        network_tier=network_tier)

    return self.messages.ComputeInstancesUpdateAccessConfigRequest(
        accessConfig=access_config,
        instance='my-instance',
        networkInterface=network_interface_name,
        project='my-project',
        zone='central1-a')

  def VerifyRequests(self,
                     network_interface_name,
                     set_public_dns=None,
                     dns_name=None,
                     set_ptr=None,
                     ptr_domain_name=None,
                     network_tier='PREMIUM'):
    self.CheckRequests(
        [(self.compute_alpha.instances, 'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='my-instance', project='my-project',
              zone='central1-a'))],
        [(self.compute_alpha.instances, 'UpdateAccessConfig',
          self.CreateUpdateAccessConfigRequest(
              network_interface_name=network_interface_name,
              set_public_dns=set_public_dns,
              set_ptr=set_ptr,
              ptr_domain_name=ptr_domain_name,
              network_tier=network_tier))],)

  def testEnablePublicDnsWithDefaultNetworkInterface(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --public-dns
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_public_dns=True,
        set_ptr=None,
        ptr_domain_name=None)

  def testEnablePublicDnsAndPtrWithDefaultNetworkInterface(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --public-dns --public-ptr --public-ptr-domain example.com
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_public_dns=True,
        set_ptr=True,
        ptr_domain_name='example.com')

  def testEnablePublicDnsAndPtrWithNetworkTierUnchanged(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(network_tier='SELECT')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --public-dns --public-ptr --public-ptr-domain example.com
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_public_dns=True,
        set_ptr=True,
        ptr_domain_name='example.com',
        network_tier='SELECT')

  def testEnablePublicDnsAndPtrWithNetworkInterfaceFlag(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-interface nic0
          --public-dns --public-ptr --public-ptr-domain example.com
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_public_dns=True,
        set_ptr=True,
        ptr_domain_name='example.com')

  def testDisablePublicDns(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(
                        set_public_dns=True,
                        dns_name='my-instance.zone.c.projet.cloud.goog.',
                        set_ptr=True,
                        ptr_domain_name='example.com',
                        network_tier='SELECT'),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-interface nic0
          --no-public-dns
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_public_dns=False,
        set_ptr=True,
        ptr_domain_name='example.com',
        network_tier='SELECT')

  def testDisablePublicPtr(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(
                        set_public_dns=True,
                        dns_name='my-instance.zone.c.projet.cloud.goog.',
                        set_ptr=True,
                        ptr_domain_name='example.com',
                        network_tier='SELECT'),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-interface nic0
          --no-public-ptr --no-public-ptr-domain
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_public_dns=True,
        set_ptr=False,
        ptr_domain_name='',
        network_tier='SELECT')

  def testNoUpdate(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(
                        set_public_dns=True,
                        set_ptr=True,
                        ptr_domain_name='example.com')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --public-dns --public-ptr --public-ptr-domain example.com
          --network-tier premium
          --zone central1-a
        """)

    # UpdateAccessConfig method should not be called since the access config
    # stays the same.
    self.CheckRequests([(self.compute_alpha.instances, 'Get',
                         self.messages.ComputeInstancesGetRequest(
                             instance='my-instance',
                             project='my-project',
                             zone='central1-a'))])

  def testZonePrompting(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)

    self.WriteInput('1\n')

    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(name='my-instance', zone='central1-a'),
            self.messages.Instance(name='my-instance', zone='central1-b'),
            self.messages.Instance(name='my-instance', zone='central2-a'),
        ],
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[self.CreateNetworkInterface()])
        ],
        [],
    ])
    self.Run("""
        compute instances update-access-config my-instance
          --public-dns
        """)

    self.AssertErrContains('my-instance')
    self.AssertErrContains('central1-a')
    self.AssertErrContains('central1-b')
    self.AssertErrContains('central2-a')

    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('my-instance'),
        [(self.compute_alpha.instances, 'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='my-instance', project='my-project',
              zone='central1-a'))],
        [(self.compute_alpha.instances, 'UpdateAccessConfig',
          self.CreateUpdateAccessConfigRequest(
              network_interface_name='nic0',
              set_public_dns=True,
              set_ptr=None,
              ptr_domain_name=None,
              network_tier='PREMIUM'))],)

  def testNetworkInterfaceNotDefaultForPublicDns(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r"""Public DNS can only be enabled for default network interface """
        r"""'nic0' rather than 'nic1'."""):
      self.Run("""
            compute instances update-access-config my-instance
            --network-interface nic1
             --public-dns
            --zone central1-a
          """)

  def testNetworkInterfaceNotExist(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[])
        ],
        [],
    ])

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-interface\]: The specified network '
        r'interface \'nic0\' does not exist'):
      self.Run("""
            compute instances update-access-config my-instance
            --network-interface nic0
            --public-dns --public-ptr --public-ptr-domain example.com
            --zone central1-a
          """)

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-dns: At most one of --public-dns | '
        '--no-public-dns may be specified.'):
      self.Run("""
          compute instances update-access-config instance-1 --no-public-dns
            --public-dns
            --zone central2-a
          """)

  def testToSelectNetworkTierWithDefaultNetworkInterface(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-tier select
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0', network_tier='SELECT')

  def testToSelectNetworkTierWithDnsSettingsUnchanged(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(
                        set_public_dns=True,
                        dns_name='my-instance.zone.c.projet.cloud.goog.',
                        set_ptr=True,
                        ptr_domain_name='example.com'),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-tier select
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0',
        set_public_dns=True,
        dns_name='my-instance.zone.c.projet.cloud.goog.',
        set_ptr=True,
        ptr_domain_name='example.com',
        network_tier='SELECT')

  def testToSelectNetworkTierWithNetworkInterfaceFlag(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-interface nic1
          --network-tier select
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic1', network_tier='SELECT')

  def testToPremiumNetworkTier(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='my-instance',
                networkInterfaces=[
                    self.CreateNetworkInterface(
                        network_tier='SELECT'),
                    self.CreateNetworkInterface(network_interface_name='nic1')
                ])
        ],
        [],
    ])

    self.Run("""
        compute instances update-access-config my-instance
          --network-interface nic0
          --network-tier premium
          --zone central1-a
        """)

    self.VerifyRequests(
        network_interface_name='nic0', network_tier='PREMIUM')

  def testToInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[INVALID\]'
    ):
      self.Run("""
          compute instances update-access-config my-instance
            --network-interface nic0
            --network-tier invalid
            --zone central1-a
          """)


if __name__ == '__main__':
  test_case.main()
