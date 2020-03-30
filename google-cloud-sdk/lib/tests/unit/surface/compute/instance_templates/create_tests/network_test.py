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
from googlecloudsdk.command_lib.compute import flags
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateTest(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testMultipleNetworkInterfaceCards(self):
    msg = self.messages

    self.Run("""
        compute instance-templates create template-1
          --network-interface network=default,address=
          --network-interface network=some-net,address=8.8.8.8
          --network-interface subnet=some-subnet
          --region central1
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        msg.NetworkInterface(
            accessConfigs=[self._default_access_config],
            network=self._default_network),
        msg.NetworkInterface(
            accessConfigs=[
                msg.AccessConfig(
                    name='external-nat',
                    natIP='8.8.8.8',
                    type=self._one_to_one_nat)
            ],
            network=(self.compute_uri + '/projects/my-project/global/networks/'
                     'some-net')),
        msg.NetworkInterface(
            subnetwork=(self.compute_uri +
                        '/projects/my-project/regions/central1/'
                        'subnetworks/some-subnet')),
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          msg.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testNetworkInterfaceWithSubnetAndNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --network-interface subnet=my-subnetwork,network=my-network
          --region my-region
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[],
            network=('{compute}/projects/my-project/global/'
                     'networks/my-network'.format(compute=self.compute_uri)),
            subnetwork=('{compute}/projects/my-project/regions/my-region/'
                        'subnetworks/my-subnetwork'.format(
                            compute=self.compute_uri)))
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testMultiNicFlagAndOneNicFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'^arguments not allowed simultaneously: --network-interface, all of '
        r'the following: --address, --network$'):
      self.Run("""
          compute instance-templates create instance-1
            --network-interface ''
            --address 8.8.8.8
            --network net
          """)

  def testAliasIpRanges(self):
    msg = self.messages

    self.Run("""
        compute instance-templates create template-1
          --network-interface network=default,address=,aliases=range1:/24;/24
          --network-interface network=some-net,address=,aliases=/24
          --network-interface subnet=some-subnet
          --region central1
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        msg.NetworkInterface(
            accessConfigs=[self._default_access_config],
            network=self._default_network,
            aliasIpRanges=[
                msg.AliasIpRange(
                    subnetworkRangeName='range1', ipCidrRange='/24'),
                msg.AliasIpRange(ipCidrRange='/24')
            ]),
        msg.NetworkInterface(
            accessConfigs=[self._default_access_config],
            network=(self.compute_uri + '/projects/my-project/global/networks/'
                     'some-net'),
            aliasIpRanges=[msg.AliasIpRange(ipCidrRange='/24')]),
        msg.NetworkInterface(
            subnetwork=(self.compute_uri +
                        '/projects/my-project/regions/central1/'
                        'subnetworks/some-subnet'))
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          msg.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testInvalidAliasIpRangeFormat(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'An alias IP range must contain range name and IP '
        r'CIDR net mask'):
      self.Run("""
          compute instance-templates create instance-1
            --network-interface network=default,aliases=range1:abc:def;
          """)

  def testWithMinCpuPlatform(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --min-cpu-platform cpu-platform
        """)

    template = self._MakeInstanceTemplate(minCpuPlatform='cpu-platform')

    self.CheckRequests(self.get_default_image_requests,
                       [(self.compute.instanceTemplates, 'Insert',
                         m.ComputeInstanceTemplatesInsertRequest(
                             instanceTemplate=template, project='my-project'))])

    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testWithPremiumNetworkTier(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --network-tier PREMIUM
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[
                m.AccessConfig(
                    name='external-nat',
                    networkTier=(self.messages.AccessConfig
                                 .NetworkTierValueValuesEnum.PREMIUM),
                    type=self._one_to_one_nat)
            ],
            network=self._default_network)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithStandardNetworkTier(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --network-tier standard
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[
                m.AccessConfig(
                    name='external-nat',
                    networkTier=(self.messages.AccessConfig
                                 .NetworkTierValueValuesEnum.STANDARD),
                    type=self._one_to_one_nat)
            ],
            network=self._default_network)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[RANDOM-NETWORK-TIER\]'):
      self.Run("""
          compute instance-templates create template-1
          --network-tier random-network-tier
          """)

  def testWithNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --network some-other-network
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[self._default_access_config],
            network=('{compute}/projects/my-project/global/networks/'
                     'some-other-network'.format(compute=self.compute_uri)))
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithPrivateIP(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --private-network-ip=1.1.1.1
          """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[self._default_access_config],
            network=self._default_network,
            networkIP='1.1.1.1')
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithPrivateNetworkInterfaceIP(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --network-interface=private-network-ip=1.1.1.1
          """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[],
            network=self._default_network,
            networkIP='1.1.1.1')
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithNoAddress(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --no-address
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(accessConfigs=[], network=self._default_network)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithAddress(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --address 74.125.28.139
        """)

    access_config = m.AccessConfig(
        name='external-nat', type=self._one_to_one_nat, natIP='74.125.28.139')

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[access_config], network=self._default_network)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testAddressAndNoAddressMutualExclusion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --address: At most one of --address | --no-address '
        'may be specified.'):
      self.Run("""
          compute instance-templates create template-1
            --address 74.125.28.139
            --no-address
          """)

    self.CheckRequests()


class InstanceTemplatesCreateTestBeta(InstanceTemplatesCreateTest,
                                      parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateTestAlpha(InstanceTemplatesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testWithSelectNetworkTier(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        --network-tier select
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[
                m.AccessConfig(
                    name='external-nat',
                    networkTier=(self.messages.AccessConfig
                                 .NetworkTierValueValuesEnum.SELECT),
                    type=self._one_to_one_nat)
            ],
            network=self._default_network)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testSubnetAndNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --subnet my-subnetwork
          --network my-network
          --region my-region
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[self._default_access_config],
            network=('{compute}/projects/my-project/global/'
                     'networks/my-network'.format(compute=self.compute_uri)),
            subnetwork=('{compute}/projects/my-project/regions/my-region/'
                        'subnetworks/my-subnetwork'.format(
                            compute=self.compute_uri)))
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithSubnetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --subnet my-subnetwork
          --region my-region
        """)

    template = self._MakeInstanceTemplate(networkInterfaces=[
        m.NetworkInterface(
            accessConfigs=[self._default_access_config],
            subnetwork=('{compute}/projects/my-project/regions/my-region/'
                        'subnetworks/my-subnetwork'.format(
                            compute=self.compute_uri)))
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testRegionPromptAttemptedWithSubnet(self):

    # This is very dirty, but at least verifies an attempt to prompt.
    with self.assertRaisesRegex(
        flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[my-subnetwork\]. Specify the \[--region\] '
        r'flag.'):
      self.Run("""
          compute instance-templates create template-1
            --subnet my-subnetwork
          """)


if __name__ == '__main__':
  test_case.main()
