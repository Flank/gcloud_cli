# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the instances add-access-config subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')

_ONE_TO_ONE_NAT = messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT


class InstancesAddAccessConfigTest(test_base.BaseTest):

  def testWithDefaults(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'AddAccessConfig',
          messages.ComputeInstancesAddAccessConfigRequest(
              accessConfig=messages.AccessConfig(
                  name='external-nat',
                  type=_ONE_TO_ONE_NAT),
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithAllArgs(self):
    self.Run("""
        compute instances add-access-config instance-1
          --access-config-name config
          --address 1.2.3.4
          --network-interface nic123
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'AddAccessConfig',
          messages.ComputeInstancesAddAccessConfigRequest(
              accessConfig=messages.AccessConfig(
                  name='config',
                  natIP='1.2.3.4',
                  type=_ONE_TO_ONE_NAT),
              instance='instance-1',
              networkInterface='nic123',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithConfigNameFlag(self):
    self.Run("""
        compute instances add-access-config instance-1
          --access-config-name config
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'AddAccessConfig',
          messages.ComputeInstancesAddAccessConfigRequest(
              accessConfig=messages.AccessConfig(
                  name='config',
                  type=_ONE_TO_ONE_NAT),
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central2-a'))]
    )

  def testWithNatIpFlag(self):
    self.Run("""
        compute instances add-access-config instance-1
          --address 1.2.3.4
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'AddAccessConfig',
          messages.ComputeInstancesAddAccessConfigRequest(
              accessConfig=messages.AccessConfig(
                  name='external-nat',
                  natIP='1.2.3.4',
                  type=_ONE_TO_ONE_NAT),
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithNetworkInterfaceFlag(self):
    self.Run("""
        compute instances add-access-config instance-1
          --network-interface nic123
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'AddAccessConfig',
          messages.ComputeInstancesAddAccessConfigRequest(
              accessConfig=messages.AccessConfig(
                  name='external-nat',
                  type=_ONE_TO_ONE_NAT),
              instance='instance-1',
              networkInterface='nic123',
              project='my-project',
              zone='central2-a'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute instances add-access-config
          https://compute.googleapis.com/compute/v1/projects/my-project/zones/central2-a/instances/instance-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'AddAccessConfig',
          messages.ComputeInstancesAddAccessConfigRequest(
              accessConfig=messages.AccessConfig(
                  name='external-nat',
                  type=_ONE_TO_ONE_NAT),
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central2-a'))],
    )

  def testZonePrompting(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='instance-1', zone='central1-a'),
            messages.Instance(name='instance-1', zone='central1-b'),
            messages.Instance(name='instance-1', zone='central2-a'),
        ],

        [],
    ])
    self.WriteInput('3\n')

    self.Run("""
        compute instances add-access-config
          instance-1
        """)

    self.AssertErrContains('instance-1')
    self.AssertErrContains('central1-a')
    self.AssertErrContains('central1-b')
    self.AssertErrContains('central2-a')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute_v1.instances,
          'AddAccessConfig',
          messages.ComputeInstancesAddAccessConfigRequest(
              accessConfig=messages.AccessConfig(
                  name='external-nat',
                  type=_ONE_TO_ONE_NAT),
              instance='instance-1',
              networkInterface='nic0',
              project='my-project',
              zone='central2-a'))],
    )

  def testTwoAddressesShouldFail(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
          compute instances add-access-config instance-1
            --address 1.2.3.4
            --address 1.2.3.4
            --zone central2-a
          """)

  def testRepeadedNetworkInterface(self):
    with self.AssertRaisesArgumentError():
      self.Run("""
          compute instances add-access-config instance-1
            --address 1.2.3.4
            --network-interface nic123
            --network-interface nic124
            --zone central2-a
          """)


class InstancesAddAccessConfigWithPublicPtrTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

  def CreateRequestWithPublicDns(self,
                                 set_public_dns=None,
                                 set_ptr=None,
                                 ptr_domain_name=None):
    m = core_apis.GetMessagesModule('compute', self.api)
    access_config = m.AccessConfig(
        name='external-nat',
        type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return m.ComputeInstancesAddAccessConfigRequest(
        accessConfig=access_config,
        instance='instance-1',
        networkInterface='nic0',
        project='my-project',
        zone='central2-a')

  def testEnablePtr(self):
    self.Run("""
        compute instances add-access-config instance-1 --public-ptr
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'AddAccessConfig',
          self.CreateRequestWithPublicDns(set_ptr=True))],
    )

  def testDisablePtr(self):
    self.Run("""
        compute instances add-access-config instance-1 --no-public-ptr
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'AddAccessConfig',
          self.CreateRequestWithPublicDns(set_ptr=False))],
    )

  def testSetPtrDomainName(self):
    self.Run("""
        compute instances add-access-config instance-1 --public-ptr
          --public-ptr-domain example.com
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instances, 'AddAccessConfig',
          self.CreateRequestWithPublicDns(
              set_ptr=True, ptr_domain_name='example.com'))],)

  def testDisablePtrDomainName(self):
    self.Run("""
        compute instances add-access-config instance-1 --no-public-ptr-domain
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'AddAccessConfig',
          self.CreateRequestWithPublicDns())],
    )

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr: At most one of --public-ptr | --no-public-ptr '
        'may be specified.'):
      self.Run("""
          compute instances add-access-config instance-1 --no-public-ptr
            --public-ptr
            --zone central2-a
          """)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr-domain: At most one of --public-ptr-domain | '
        '--no-public-ptr-domain may be specified.'):
      self.Run("""
          compute instances add-access-config instance-1 --no-public-ptr-domain
            --public-ptr-domain example.com
            --zone central2-a
          """)

    with self.assertRaisesRegex(
        exceptions.ConflictingArgumentsException,
        r'arguments not allowed simultaneously: --public-ptr-domain, '
        r'--no-public-ptr'):
      self.Run("""
          compute instances add-access-config instance-1 --no-public-ptr
            --public-ptr-domain example.com
            --zone central2-a
          """)

    with self.AssertRaisesToolExceptionRegexp(
        r'Public PTR can only be enabled for default network interface '
        r'\'nic0\' rather than \'nic100\'.'):
      self.Run("""
          compute instances add-access-config instance-1
            --network-interface nic100
            --public-ptr
            --zone central2-a
          """)


class InstancesAddAccessConfigWithPublicPtrBetaTest(
    InstancesAddAccessConfigWithPublicPtrTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')


class InstancesAddAccessConfigWithPublicPtrAlphaTest(
    InstancesAddAccessConfigWithPublicPtrTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')


class InstancesAddAccessConfigWithPublicDnsTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')

  def CreateRequestWithPublicDns(self,
                                 set_public_dns=None,
                                 set_ptr=None,
                                 ptr_domain_name=None):
    m = core_apis.GetMessagesModule('compute', 'alpha')
    access_config = m.AccessConfig(
        name='external-nat',
        type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    if set_public_dns is not None:
      access_config.setPublicDns = bool(set_public_dns)
    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return m.ComputeInstancesAddAccessConfigRequest(
        accessConfig=access_config,
        instance='instance-1',
        networkInterface='nic0',
        project='my-project',
        zone='central2-a')

  def testPublicDnsDisabledByDefault(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'AddAccessConfig',
          self.CreateRequestWithPublicDns())],
    )

  def testEnablePublicDns(self):
    self.Run("""
        compute instances add-access-config instance-1 --public-dns
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'AddAccessConfig',
          self.CreateRequestWithPublicDns(set_public_dns=True))],
    )

  def testEnablePublicDnsWithSpecifiedNetworkInterface(self):
    self.Run("""
        compute instances add-access-config instance-1 --public-dns
          --network-interface nic0
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'AddAccessConfig',
          self.CreateRequestWithPublicDns(set_public_dns=True))],
    )

  def testDisablePublicDns(self):
    self.Run("""
        compute instances add-access-config instance-1 --no-public-dns
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'AddAccessConfig',
          self.CreateRequestWithPublicDns(set_public_dns=False))],
    )

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-dns: At most one of --public-dns | --no-public-dns '
        'may be specified.'):
      self.Run("""
          compute instances add-access-config instance-1 --no-public-dns
            --public-dns
            --zone central2-a
          """)

    with self.AssertRaisesToolExceptionRegexp(
        r'Public DNS can only be enabled for default network interface '
        r'\'nic0\' rather than \'nic100\'.'):
      self.Run("""
          compute instances add-access-config instance-1
            --network-interface nic100
            --public-dns
            --zone central2-a
          """)


class InstancesAddAccessConfigWithNetworkTierAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')

  def CreateRequestWithNetworkTier(self, network_tier):
    m = core_apis.GetMessagesModule('compute', 'alpha')
    if network_tier:
      network_tier_enum = m.AccessConfig.NetworkTierValueValuesEnum(
          network_tier)
    else:
      network_tier_enum = None
    return m.ComputeInstancesAddAccessConfigRequest(
        accessConfig=m.AccessConfig(
            name='external-nat',
            type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT,
            networkTier=network_tier_enum),
        instance='instance-1',
        networkInterface='nic0',
        project='my-project',
        zone='central2-a')

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
        """)

    self.CheckRequests([(self.compute_alpha.instances, 'AddAccessConfig',
                         self.CreateRequestWithNetworkTier(None))],)

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
          --network-tier PREMIUM
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'AddAccessConfig',
          self.CreateRequestWithNetworkTier('PREMIUM'))],
    )

  def testWithSelectNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
          --network-tier select
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'AddAccessConfig',
          self.CreateRequestWithNetworkTier('SELECT'))],
    )

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute_alpha.instances,
          'AddAccessConfig',
          self.CreateRequestWithNetworkTier('STANDARD'))],
    )

  def testNetworkTierNotSupported(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'):
      self.Run("""
          compute instances add-access-config instance-1
            --zone central2-a
            --network-tier random-network-tier
          """)


class InstancesAddAccessConfigWithNetworkTierBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')

  def CreateRequestWithNetworkTier(self, network_tier):
    m = core_apis.GetMessagesModule('compute', 'beta')
    if network_tier:
      network_tier_enum = m.AccessConfig.NetworkTierValueValuesEnum(
          network_tier)
    else:
      network_tier_enum = None
    return m.ComputeInstancesAddAccessConfigRequest(
        accessConfig=m.AccessConfig(
            name='external-nat',
            type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT,
            networkTier=network_tier_enum),
        instance='instance-1',
        networkInterface='nic0',
        project='my-project',
        zone='central2-a')

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
        """)

    self.CheckRequests([(self.compute_beta.instances, 'AddAccessConfig',
                         self.CreateRequestWithNetworkTier(None))],)

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
          --network-tier PREMIUM
        """)

    self.CheckRequests([(self.compute_beta.instances, 'AddAccessConfig',
                         self.CreateRequestWithNetworkTier('PREMIUM'))],)

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
          --network-tier standard
        """)

    self.CheckRequests([(self.compute_beta.instances, 'AddAccessConfig',
                         self.CreateRequestWithNetworkTier('STANDARD'))],)

  def testNetworkTierNotSupported(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'):
      self.Run("""
          compute instances add-access-config instance-1
            --zone central2-a
            --network-tier random-network-tier
          """)


class InstancesAddAccessConfigWithNetworkTierGaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

  def CreateRequestWithNetworkTier(self, network_tier):
    m = core_apis.GetMessagesModule('compute', 'v1')
    if network_tier:
      network_tier_enum = m.AccessConfig.NetworkTierValueValuesEnum(
          network_tier)
    else:
      network_tier_enum = None
    return m.ComputeInstancesAddAccessConfigRequest(
        accessConfig=m.AccessConfig(
            name='external-nat',
            type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT,
            networkTier=network_tier_enum),
        instance='instance-1',
        networkInterface='nic0',
        project='my-project',
        zone='central2-a')

  def testWithDefaultNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
        """)

    self.CheckRequests([(self.compute.instances, 'AddAccessConfig',
                         self.CreateRequestWithNetworkTier(None))],)

  def testWithPremiumNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
          --network-tier PREMIUM
        """)

    self.CheckRequests([(self.compute.instances, 'AddAccessConfig',
                         self.CreateRequestWithNetworkTier('PREMIUM'))],)

  def testWithStandardNetworkTier(self):
    self.Run("""
        compute instances add-access-config instance-1
          --zone central2-a
          --network-tier standard
        """)

    self.CheckRequests([(self.compute.instances, 'AddAccessConfig',
                         self.CreateRequestWithNetworkTier('STANDARD'))],)

  def testNetworkTierNotSupported(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'
    ):
      self.Run("""
          compute instances add-access-config instance-1
            --zone central2-a
            --network-tier random-network-tier
          """)


if __name__ == '__main__':
  test_case.main()
