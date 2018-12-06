# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the addresses create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock

messages = core_apis.GetMessagesModule('compute', 'v1')


class AddressesCreateTest(test_base.BaseTest):

  def SetUp(self):
    random.seed(1)  # Sets the seed for the random module, so our
    # tests run under deterministic conditions.

  def testOneAddressFromEphemeralPool(self):
    self.Run("""
        compute addresses create address-1
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  name='address-1',
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testOneAddressFromEphemeralPoolWithDescription(self):
    self.Run("""
        compute addresses create address-1
          --description my-address
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  name='address-1',
                  description='my-address',
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testManyAddressesFromEphemeralPool(self):
    self.Run("""
        compute addresses create address-1 address-2 address-3
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  name='address-1',
              ),
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  name='address-2',
              ),
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  name='address-3',
              ),
              project='my-project',
              region='us-central2'))],
    )

  @mock.patch(
      'googlecloudsdk.api_lib.compute.name_generator.GenerateRandomName',
      side_effect=['d41jrqx2db4p'])
  def testOneAddressPromotionWithoutName(self, mock_method):
    self.Run("""
        compute addresses create
          --addresses 23.251.146.189
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  address='23.251.146.189',
                  name='d41jrqx2db4p',
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testOneAddressPromotionWithName(self):
    self.Run("""
        compute addresses create address-1
          --addresses 23.251.146.189
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  address='23.251.146.189',
                  name='address-1',
              ),
              project='my-project',
              region='us-central2'))],
    )

  @mock.patch(
      'googlecloudsdk.api_lib.compute.name_generator.GenerateRandomName',
      side_effect=['d41jrqx2db4p', 'taqzi86bat7n', 'fpbhpriihqka'])
  def testManyAddressPromotionsWithoutNames(self, mock_method):
    self.Run("""
        compute addresses create
          --addresses 23.251.146.189,162.222.181.198,162.222.179.207
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  address='23.251.146.189',
                  name='d41jrqx2db4p',
              ),
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  address='162.222.181.198',
                  name='taqzi86bat7n',
              ),
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  address='162.222.179.207',
                  name='fpbhpriihqka',
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testManyAddressPromotionsWithNames(self):
    self.Run("""
        compute addresses create address-1 address-2 address-3
          --addresses 23.251.146.189,162.222.181.198,162.222.179.207
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  address='23.251.146.189',
                  name='address-1',
              ),
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  address='162.222.181.198',
                  name='address-2',
              ),
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  address='162.222.179.207',
                  name='address-3',
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testManyAddressPromotionsWithWrongNumberOfNames(self):
    with self.AssertRaisesToolExceptionRegexp(
        'If providing both, you must specify the same number of names as '
        'addresses.'):
      self.Run("""
          compute addresses create address-1 address-2
            --addresses 23.251.146.189,162.222.181.198,162.222.179.207
            --region us-central2
          """)
    self.CheckRequests()

  def testWithNoAddressesAndNoNames(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one name or address must be provided.'):
      self.Run("""
            compute addresses create
              --region us-central2
            """)
    self.CheckRequests()

  def testRegionalPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('3\n')
    self.make_requests.side_effect = iter([
        test_resources.REGIONS,
        [],
    ])
    self.Run(
        'compute addresses create address-1')

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  name='address-1',
              ),
              project='my-project',
              region='region-2'))],
    )

    self.AssertErrContains(
        r'{"ux": "PROMPT_CHOICE", "message": "For the following address:\n'
        r' - [address-1]\nchoose a region or global:", '
        r'"choices": ["global", "region: region-1 (DEPRECATED)", '
        r'"region: region-2", "region: region-3"]}'
    )

  def testUriSupport(self):
    self.Run("""
        compute addresses create
          https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central2/addresses/address-1
          --region https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Insert',
          messages.ComputeAddressesInsertRequest(
              address=messages.Address(
                  name='address-1',
              ),
              project='my-project',
              region='us-central2'))],
    )


class AddressesGlobalCreateTest(test_base.BaseTest):

  def testOneAddressFromEphemeralPool(self):
    self.Run("""
        compute addresses create address-1
          --global
        """)

    self.CheckRequests(
        [(self.compute_v1.globalAddresses, 'Insert',
          messages.ComputeGlobalAddressesInsertRequest(
              address=messages.Address(
                  name='address-1',
                  ipVersion=(messages.Address.IpVersionValueValuesEnum.IPV4),),
              project='my-project'))],)

  def testUriSupport(self):
    self.Run("""
        compute addresses create
          https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/address-1
          --global
        """)

    self.CheckRequests(
        [(self.compute_v1.globalAddresses, 'Insert',
          messages.ComputeGlobalAddressesInsertRequest(
              address=messages.Address(
                  name='address-1',
                  ipVersion=(messages.Address.IpVersionValueValuesEnum.IPV4),),
              project='my-project'))])


class AddressesCreateWithNetworkTierAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testOneAddressWithPremiumNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --network-tier PREMIUM
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  name='address-1',
                  networkTier=self.messages.Address.NetworkTierValueValuesEnum.
                  PREMIUM,),
              project='my-project',
              region='us-central2'))],)

  def testOneAddressWithSelectNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --network-tier select
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  name='address-1',
                  networkTier=self.messages.Address.NetworkTierValueValuesEnum.
                  SELECT,),
              project='my-project',
              region='us-central2'))],)

  def testOneAddressWithStandardNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --network-tier standard
          --region us-central2
        """)

    self.CheckRequests([(self.compute.addresses, 'Insert',
                         self.messages.ComputeAddressesInsertRequest(
                             address=self.messages.Address(
                                 name='address-1',
                                 networkTier=self.messages.Address.
                                 NetworkTierValueValuesEnum.STANDARD,
                             ),
                             project='my-project',
                             region='us-central2'))],)

  def testOneAddressWithMissingNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --region us-central2
        """)

    self.CheckRequests([(self.compute.addresses, 'Insert',
                         self.messages.ComputeAddressesInsertRequest(
                             address=self.messages.Address(name='address-1',),
                             project='my-project',
                             region='us-central2'))],)

  def testOneAddressWithInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[INVALID-TIER\]'):
      self.Run("""
          compute addresses create address-1
            --network-tier invalid-tier
            --region us-central2
          """)


class AddressesCreateWithNetworkTierBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testOneAddressWithPremiumNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --network-tier PREMIUM
          --region us-central2
        """)

    self.CheckRequests([(self.compute.addresses, 'Insert',
                         self.messages.ComputeAddressesInsertRequest(
                             address=self.messages.Address(
                                 name='address-1',
                                 networkTier=self.messages.Address.
                                 NetworkTierValueValuesEnum.PREMIUM,
                             ),
                             project='my-project',
                             region='us-central2'))],)

  def testOneAddressWithStandardNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --network-tier standard
          --region us-central2
        """)

    self.CheckRequests([(self.compute.addresses, 'Insert',
                         self.messages.ComputeAddressesInsertRequest(
                             address=self.messages.Address(
                                 name='address-1',
                                 networkTier=self.messages.Address.
                                 NetworkTierValueValuesEnum.STANDARD,
                             ),
                             project='my-project',
                             region='us-central2'))],)

  def testOneAddressWithMissingNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --region us-central2
        """)

    self.CheckRequests([(self.compute.addresses, 'Insert',
                         self.messages.ComputeAddressesInsertRequest(
                             address=self.messages.Address(name='address-1',),
                             project='my-project',
                             region='us-central2'))],)

  def testOneAddressWithInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[INVALID-TIER\]'):
      self.Run("""
          compute addresses create address-1
            --network-tier invalid-tier
            --region us-central2
          """)


class AddressesCreateWithNetworkTierTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testOneAddressWithPremiumNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --network-tier PREMIUM
          --region us-central2
        """)

    self.CheckRequests([(self.compute.addresses, 'Insert',
                         self.messages.ComputeAddressesInsertRequest(
                             address=self.messages.Address(
                                 name='address-1',
                                 networkTier=self.messages.Address.
                                 NetworkTierValueValuesEnum.PREMIUM,
                             ),
                             project='my-project',
                             region='us-central2'))],)

  def testOneAddressWithStandardNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --network-tier standard
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  name='address-1',
                  networkTier=self.messages.Address.NetworkTierValueValuesEnum.
                  STANDARD,),
              project='my-project',
              region='us-central2'))],)

  def testOneAddressWithMissingNetworkTier(self):
    self.Run("""
        compute addresses create address-1
          --region us-central2
        """)

    self.CheckRequests([(self.compute.addresses, 'Insert',
                         self.messages.ComputeAddressesInsertRequest(
                             address=self.messages.Address(name='address-1',),
                             project='my-project',
                             region='us-central2'))],)

  def testOneAddressWithInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[INVALID-TIER\]'):
      self.Run("""
          compute addresses create address-1
            --network-tier invalid-tier
            --region us-central2
          """)


class CreateWithIPVersionTest(test_base.BaseTest):

  # When no --ip-version specified, default value of IPV4 should be specified.
  def testDefault(self):
    self.Run("""
        compute addresses create address-1
          --description my-address
          --global
        """)

    self.CheckRequests(
        [(self.compute.globalAddresses, 'Insert',
          self.messages.ComputeGlobalAddressesInsertRequest(
              address=self.messages.Address(
                  name='address-1',
                  description='my-address',
                  ipVersion=(
                      self.messages.Address.IpVersionValueValuesEnum.IPV4),),
              project='my-project'))],)

  def testIPv4(self):
    self.Run("""
        compute addresses create address-1
          --description my-address
          --global
          --ip-version ipv4
        """)

    self.CheckRequests(
        [(self.compute.globalAddresses, 'Insert',
          self.messages.ComputeGlobalAddressesInsertRequest(
              address=self.messages.Address(
                  name='address-1',
                  description='my-address',
                  ipVersion=(
                      self.messages.Address.IpVersionValueValuesEnum.IPV4),),
              project='my-project'))],)

  def testIPv6(self):
    self.Run("""
        compute addresses create address-1
          --description my-address
          --global
          --ip-version ipV6
        """)

    self.CheckRequests(
        [(self.compute.globalAddresses, 'Insert',
          self.messages.ComputeGlobalAddressesInsertRequest(
              address=self.messages.Address(
                  name='address-1',
                  description='my-address',
                  ipVersion=(
                      self.messages.Address.IpVersionValueValuesEnum.IPV6),),
              project='my-project'))],)

  def testWithAddressFlag(self):
    self.Run("""
        compute addresses create address-1
          --addresses 23.251.146.189
          --global
        """)

    self.CheckRequests(
        [(self.compute.globalAddresses, 'Insert',
          self.messages.ComputeGlobalAddressesInsertRequest(
              address=self.messages.Address(
                  address='23.251.146.189',
                  name='address-1',),
              project='my-project'))],)

  def testWithMultipleAddresses(self):
    self.Run("""
        compute addresses create address-1 address-2
          --addresses 23.251.146.189,23.251.146.190
          --global
        """)

    self.CheckRequests(
        [(self.compute.globalAddresses, 'Insert',
          self.messages.ComputeGlobalAddressesInsertRequest(
              address=self.messages.Address(
                  address='23.251.146.189',
                  name='address-1',),
              project='my-project')),
         (self.compute.globalAddresses, 'Insert',
          self.messages.ComputeGlobalAddressesInsertRequest(
              address=self.messages.Address(
                  address='23.251.146.190',
                  name='address-2',),
              project='my-project'))],)

  def testWithAddressAndRegionFlag(self):
    self.Run("""
        compute addresses create address-1
          --addresses 23.251.146.189
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='23.251.146.189',
                  name='address-1',),
              project='my-project',
              region='us-central2'))],)


class CreateWithSubnetAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def RunCreate(self, command):
    self.Run('compute addresses create ' + command)

  def testBasic(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet default
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum.
                  INTERNAL,
                  purpose=self.messages.Address.PurposeValueValuesEnum.
                  GCE_ENDPOINT,
                  subnetwork='https://www.googleapis.com/compute/alpha/'
                  'projects/my-project/regions/us-central2/'
                  'subnetworks/default',
              ),
              project='my-project',
              region='us-central2',
          ))],)

  def testNonDefaultSubnet(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet fancy
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum.
                  INTERNAL,
                  purpose=self.messages.Address.PurposeValueValuesEnum.
                  GCE_ENDPOINT,
                  subnetwork='https://www.googleapis.com/compute/alpha/'
                  'projects/my-project/regions/us-central2/'
                  'subnetworks/fancy',
              ),
              project='my-project',
              region='us-central2',
          ))],)

  # Works here, but will be rejected by the API.
  def testDifferentRegionSubnet(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet fancy
          --subnet-region us-east1
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum.
                  INTERNAL,
                  purpose=self.messages.Address.PurposeValueValuesEnum.
                  GCE_ENDPOINT,
                  subnetwork='https://www.googleapis.com/compute/alpha/'
                  'projects/my-project/regions/us-east1/'
                  'subnetworks/fancy',
              ),
              project='my-project',
              region='us-central2',
          ))],)

  def testGlobalAddress(self):
    with self.AssertRaisesToolExceptionRegexp(
        '[--subnet] may not be specified for global addresses.'):
      self.RunCreate("""
          address-1
            --addresses 10.100.1.1
            --global
            --subnet fancy
          """)


class CreateWithSubnetBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def RunCreate(self, command):
    self.Run('compute addresses create ' + command)

  def testBasic(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet default
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum
                  .INTERNAL,
                  purpose=self.messages.Address.PurposeValueValuesEnum
                  .GCE_ENDPOINT,
                  subnetwork='https://www.googleapis.com/compute/beta/'
                  'projects/my-project/regions/us-central2/'
                  'subnetworks/default'),
              project='my-project',
              region='us-central2',
          ))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testNonDefaultSubnet(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet fancy
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum
                  .INTERNAL,
                  purpose=self.messages.Address.PurposeValueValuesEnum
                  .GCE_ENDPOINT,
                  subnetwork='https://www.googleapis.com/compute/beta/'
                  'projects/my-project/regions/us-central2/'
                  'subnetworks/fancy'),
              project='my-project',
              region='us-central2',
          ))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  # Works here, but will be rejected by the API.
  def testDifferentRegionSubnet(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet fancy
          --subnet-region us-east1
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum
                  .INTERNAL,
                  purpose=self.messages.Address.PurposeValueValuesEnum
                  .GCE_ENDPOINT,
                  subnetwork='https://www.googleapis.com/compute/beta/'
                  'projects/my-project/regions/us-east1/'
                  'subnetworks/fancy'),
              project='my-project',
              region='us-central2',
          ))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testGlobalAddress(self):
    with self.AssertRaisesToolExceptionRegexp(
        '[--subnet] may not be specified for global addresses.'):
      self.RunCreate("""
          address-1
            --addresses 10.100.1.1
            --global
            --subnet fancy
          """)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'ERROR: (gcloud.beta.compute.addresses.create) [--subnet] may not be '
        'specified for global addresses.\n'
    )


class CreateWithSubnetTest(test_base.BaseTest):

  def RunCreate(self, command):
    self.Run('compute addresses create ' + command)

  def testBasic(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet default
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum.
                  INTERNAL,
                  subnetwork='https://www.googleapis.com/compute/v1/'
                  'projects/my-project/regions/us-central2/'
                  'subnetworks/default'),
              project='my-project',
              region='us-central2',))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testNonDefaultSubnet(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet fancy
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum.
                  INTERNAL,
                  subnetwork='https://www.googleapis.com/compute/v1/'
                  'projects/my-project/regions/us-central2/'
                  'subnetworks/fancy'),
              project='my-project',
              region='us-central2',))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  # Works here, but will be rejected by the API.
  def testDifferentRegionSubnet(self):
    self.RunCreate("""
        address-1
          --addresses 10.100.1.1
          --region us-central2
          --subnet fancy
          --subnet-region us-east1
        """)

    self.CheckRequests(
        [(self.compute.addresses, 'Insert',
          self.messages.ComputeAddressesInsertRequest(
              address=self.messages.Address(
                  address='10.100.1.1',
                  name='address-1',
                  addressType=self.messages.Address.AddressTypeValueValuesEnum.
                  INTERNAL,
                  subnetwork='https://www.googleapis.com/compute/v1/'
                  'projects/my-project/regions/us-east1/'
                  'subnetworks/fancy'),
              project='my-project',
              region='us-central2',))],)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testGlobalAddress(self):
    with self.AssertRaisesToolExceptionRegexp(
        '[--subnet] may not be specified for global addresses.'):
      self.RunCreate("""
          address-1
            --addresses 10.100.1.1
            --global
            --subnet fancy
          """)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'ERROR: (gcloud.compute.addresses.create) [--subnet] may not be '
        'specified for global addresses.\n')


class GlobalPeeringRangesCreateAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testReserveRangeForPeering(self):
    self.Run("""
        compute addresses create range-1
          --global
          --addresses 10.100.1.0
          --prefix-length 24
          --network default
          --purpose VPC_PEERING
        """)

    self.CheckRequests(
        [(self.compute.globalAddresses, 'Insert',
          self.messages.ComputeGlobalAddressesInsertRequest(
              address=self.messages.Address(
                  name='range-1',
                  address='10.100.1.0',
                  prefixLength=24,
                  addressType=self.messages.Address.AddressTypeValueValuesEnum.
                  INTERNAL,
                  purpose=self.messages.Address.PurposeValueValuesEnum.
                  VPC_PEERING,
                  network='https://www.googleapis.com/compute/alpha/'
                  'projects/my-project/global/networks/default'),
              project='my-project'))],)

  def testWithNetworkAndSubnetwork(self):
    with self.assertRaises(calliope_exceptions.ConflictingArgumentsException):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 24
            --network default
            --subnet fancy
            --purpose VPC_PEERING
          """)

  def testPurposeWithoutNetworkAndSubnetwork(self):
    with self.assertRaises(calliope_exceptions.MinimumArgumentException):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 24
            --purpose VPC_PEERING
          """)

  def testVpcPeeringWithSubnetwork(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run("""
          compute addresses create address-1
            --region us-central2
            --subnet fancy
            --purpose VPC_PEERING
          """)

  def testRegionalWithNetwork(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run("""
          compute addresses create address-1
            --region us-central2
            --network default
            --purpose GCE_ENDPOINT
          """)

  def testGceEndpointWithNetwork(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 24
            --network default
            --purpose GCE_ENDPOINT
          """)

  def testWithoutPrefixLengthForRange(self):
    with self.assertRaises(calliope_exceptions.RequiredArgumentException):
      self.Run("""
          compute addresses create address-1
            --global
            --network default
            --purpose VPC_PEERING
          """)

  def testSubnetWithPrefixLength(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run("""
          compute addresses create address-1
            --region us-central2
            --prefix-length 24
            --subnet fancy
            --purpose GCE_ENDPOINT
          """)

  def testPrefixLengthTooSmall(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --prefix-length: Value must be greater than or equal to 8'):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 7
            --network default
            --purpose VPC_PEERING
          """)

  def testPrefixLengthTooLarge(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --prefix-length: Value must be less than or equal to 30'):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 31
            --network default
            --purpose VPC_PEERING
          """)


class GlobalPeeringRangesCreateBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testReserveRangeForPeering(self):
    self.Run("""
        compute addresses create range-1
          --global
          --addresses 10.100.1.0
          --prefix-length 24
          --network default
          --purpose VPC_PEERING
        """)

    self.CheckRequests(
        [(self.compute.globalAddresses, 'Insert',
          self.messages.ComputeGlobalAddressesInsertRequest(
              address=self.messages.Address(
                  name='range-1',
                  address='10.100.1.0',
                  prefixLength=24,
                  addressType=self.messages.Address.AddressTypeValueValuesEnum
                  .INTERNAL,
                  purpose=self.messages.Address.PurposeValueValuesEnum
                  .VPC_PEERING,
                  network='https://www.googleapis.com/compute/beta/'
                  'projects/my-project/global/networks/default'),
              project='my-project'))],)

  def testWithNetworkAndSubnetwork(self):
    with self.assertRaises(calliope_exceptions.ConflictingArgumentsException):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 24
            --network default
            --subnet fancy
            --purpose VPC_PEERING
          """)

  def testPurposeWithoutNetworkAndSubnetwork(self):
    with self.assertRaises(calliope_exceptions.MinimumArgumentException):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 24
            --purpose VPC_PEERING
          """)

  def testVpcPeeringWithSubnetwork(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run("""
          compute addresses create address-1
            --region us-central2
            --subnet fancy
            --purpose VPC_PEERING
          """)

  def testRegionalWithNetwork(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run("""
          compute addresses create address-1
            --region us-central2
            --network default
            --purpose GCE_ENDPOINT
          """)

  def testGceEndpointWithNetwork(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 24
            --network default
            --purpose GCE_ENDPOINT
          """)

  def testWithoutPrefixLengthForRange(self):
    with self.assertRaises(calliope_exceptions.RequiredArgumentException):
      self.Run("""
          compute addresses create address-1
            --global
            --network default
            --purpose VPC_PEERING
          """)

  def testSubnetWithPrefixLength(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      self.Run("""
          compute addresses create address-1
            --region us-central2
            --prefix-length 24
            --subnet fancy
            --purpose GCE_ENDPOINT
          """)

  def testPrefixLengthTooSmall(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --prefix-length: Value must be greater than or equal to 8'):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 7
            --network default
            --purpose VPC_PEERING
          """)

  def testPrefixLengthTooLarge(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --prefix-length: Value must be less than or equal to 30'):
      self.Run("""
          compute addresses create address-1
            --global
            --prefix-length 31
            --network default
            --purpose VPC_PEERING
          """)


if __name__ == '__main__':
  test_case.main()
