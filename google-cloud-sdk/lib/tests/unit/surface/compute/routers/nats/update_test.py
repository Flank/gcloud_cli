# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for the update subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
import copy

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base
from tests.lib.surface.compute import router_test_utils


class AlphaUpdateTest(router_test_base.RouterTestBase):

  def SetUp(self):
    self.SelectApi(base.ReleaseTrack.ALPHA, 'alpha')

    self.orig = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='alpha')
    self.orig.nats = [self.messages.RouterNat(name='my-nat')]

  def testAutoAllocateExternalIps(self):
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat.
            NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat.
            SourceSubnetworkIpRangesToNatValueValuesEnum.
            ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsGet()
    self.ExpectGet(expected_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --auto-allocate-nat-external-ips
        --nat-all-subnet-ip-ranges
        """)

  def testSpecifyExternalIpPool(self):
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat.
            NatIpAllocateOptionValueValuesEnum.MANUAL_ONLY,
            natIps=[
                ('https://www.googleapis.com/compute/alpha/projects/'
                 'fake-project/regions/us-central1/addresses/address-1'),
                ('https://www.googleapis.com/compute/alpha/projects/'
                 'fake-project/regions/us-central1/addresses/address-2'),
                ('https://www.googleapis.com/compute/alpha/projects/'
                 'fake-project/regions/us-central1/addresses/address-3'),
            ],
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat.
            SourceSubnetworkIpRangesToNatValueValuesEnum.
            ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsGet()
    self.ExpectGet(expected_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --nat-external-ip-pool=address-1,address-2,address-3
        --nat-all-subnet-ip-ranges
        """)

  def testPrimarySubnetRangesOnly(self):
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat.
            NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat.
            SourceSubnetworkIpRangesToNatValueValuesEnum.
            ALL_SUBNETWORKS_ALL_PRIMARY_IP_RANGES)
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsGet()
    self.ExpectGet(expected_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --auto-allocate-nat-external-ips
        --nat-primary-subnet-ip-ranges
        """)

  def testCustomSubnetRanges(self):
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat.
            NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat.
            SourceSubnetworkIpRangesToNatValueValuesEnum.LIST_OF_SUBNETWORKS,
            subnetworks=[
                self.messages.RouterNatSubnetworkToNat(
                    name=(
                        'https://www.googleapis.com/compute/alpha/projects/'
                        'fake-project/regions/us-central1/subnetworks/subnet-1'
                    ),
                    sourceIpRangesToNat=[
                        self.messages.RouterNatSubnetworkToNat.
                        SourceIpRangesToNatValueListEntryValuesEnum.
                        PRIMARY_IP_RANGE
                    ]),
                self.messages.RouterNatSubnetworkToNat(
                    name=(
                        'https://www.googleapis.com/compute/alpha/projects/'
                        'fake-project/regions/us-central1/subnetworks/subnet-2'
                    ),
                    sourceIpRangesToNat=[
                        self.messages.RouterNatSubnetworkToNat.
                        SourceIpRangesToNatValueListEntryValuesEnum.
                        LIST_OF_SECONDARY_IP_RANGES
                    ],
                    secondaryIpRangeNames=['range-1']),
                self.messages.RouterNatSubnetworkToNat(
                    name=(
                        'https://www.googleapis.com/compute/alpha/projects/'
                        'fake-project/regions/us-central1/subnetworks/subnet-3'
                    ),
                    sourceIpRangesToNat=[
                        self.messages.RouterNatSubnetworkToNat.
                        SourceIpRangesToNatValueListEntryValuesEnum.
                        PRIMARY_IP_RANGE,
                        self.messages.RouterNatSubnetworkToNat.
                        SourceIpRangesToNatValueListEntryValuesEnum.
                        LIST_OF_SECONDARY_IP_RANGES
                    ],
                    secondaryIpRangeNames=['range-1', 'range-2'])
            ])
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsGet()
    self.ExpectGet(expected_router)

    self.Run("""
      compute routers nats update my-nat --router my-router
      --region us-central1 --auto-allocate-nat-external-ips
      --nat-custom-subnet-ip-ranges=subnet-1,subnet-2:range-1,subnet-3,subnet-3:range-1,subnet-3:range-2
        """)

  def testClearFields(self):
    self.orig.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat.
            NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat.
            SourceSubnetworkIpRangesToNatValueValuesEnum.
            ALL_SUBNETWORKS_ALL_IP_RANGES,
            minPortsPerVm=256,
            icmpIdleTimeoutSec=120,
            udpIdleTimeoutSec=180,
            tcpTransitoryIdleTimeoutSec=300,
            tcpEstablishedIdleTimeoutSec=600)
    ]
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat.
            NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat.
            SourceSubnetworkIpRangesToNatValueValuesEnum.
            ALL_SUBNETWORKS_ALL_IP_RANGES,
            minPortsPerVm=None,
            icmpIdleTimeoutSec=None,
            udpIdleTimeoutSec=None,
            tcpTransitoryIdleTimeoutSec=None,
            tcpEstablishedIdleTimeoutSec=None)
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsGet()
    self.ExpectGet(expected_router)

    self.Run("""
      compute routers nats update my-nat --router my-router
      --region us-central1 --clear-min-ports-per-vm --clear-udp-idle-timeout
      --clear-icmp-idle-timeout --clear-tcp-established-idle-timeout
      --clear-tcp-transitory-idle-timeout
        """)

  def testAsync(self):
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat.
            NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat.
            SourceSubnetworkIpRangesToNatValueValuesEnum.
            ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]
    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)

    result = self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --auto-allocate-nat-external-ips
        --nat-all-subnet-ip-ranges --async
        """)
    self.assertEqual('operation-X', result.name)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Update in progress for nat [my-nat] in router [my-router]'
        ' [https://www.googleapis.com/compute/v1/'
        'projects/fake-project/regions/us-central1/operations/operation-X] '
        'Run the [gcloud compute operations describe] command to check the '
        'status of this operation.\n')

  def testNatNotFound(self):
    self.ExpectGet(self.orig)

    with self.AssertRaisesExceptionMatches(nats_utils.NatNotFoundError,
                                           'NAT `invalid-nat` not found'):
      self.Run("""
          compute routers nats update invalid-nat --router my-router
          --region us-central1 --auto-allocate-nat-external-ips
          --nat-all-subnet-ip-ranges
          """)


if __name__ == '__main__':
  test_case.main()
