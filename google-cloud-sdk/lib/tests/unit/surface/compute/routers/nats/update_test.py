# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base
from tests.lib.surface.compute import router_test_utils


class UpdateTest(router_test_base.RouterTestBase):

  def SetUp(self):
    self.api_version = 'v1'
    self.SelectApi(calliope_base.ReleaseTrack.GA, 'v1')

    self.orig = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='v1')
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
    self.ExpectOperationsPolling()
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
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.MANUAL_ONLY,
            natIps=[
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-1') %
                self.api_version,
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-2') %
                self.api_version,
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-3') %
                self.api_version,
            ],
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsPolling()
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
    self.ExpectOperationsPolling()
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
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum.LIST_OF_SUBNETWORKS,
            subnetworks=[
                self.messages.RouterNatSubnetworkToNat(
                    name=(
                        'https://compute.googleapis.com/compute/%s/projects/'
                        'fake-project/regions/us-central1/subnetworks/subnet-1')
                    % self.api_version,
                    sourceIpRangesToNat=[
                        self.messages.RouterNatSubnetworkToNat
                        .SourceIpRangesToNatValueListEntryValuesEnum
                        .PRIMARY_IP_RANGE
                    ]),
                self.messages.RouterNatSubnetworkToNat(
                    name=(
                        'https://compute.googleapis.com/compute/%s/projects/'
                        'fake-project/regions/us-central1/subnetworks/subnet-2')
                    % self.api_version,
                    sourceIpRangesToNat=[
                        self.messages.RouterNatSubnetworkToNat
                        .SourceIpRangesToNatValueListEntryValuesEnum
                        .LIST_OF_SECONDARY_IP_RANGES
                    ],
                    secondaryIpRangeNames=['range-1']),
                self.messages.RouterNatSubnetworkToNat(
                    name=(
                        'https://compute.googleapis.com/compute/%s/projects/'
                        'fake-project/regions/us-central1/subnetworks/subnet-3')
                    % self.api_version,
                    sourceIpRangesToNat=[
                        self.messages.RouterNatSubnetworkToNat
                        .SourceIpRangesToNatValueListEntryValuesEnum
                        .PRIMARY_IP_RANGE,
                        self.messages.RouterNatSubnetworkToNat
                        .SourceIpRangesToNatValueListEntryValuesEnum
                        .LIST_OF_SECONDARY_IP_RANGES
                    ],
                    secondaryIpRangeNames=['range-1', 'range-2'])
            ])
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsPolling()
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
    self.ExpectOperationsPolling()
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
    self.assertIn('operation-X', result.name)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Update in progress for nat [my-nat] in router [my-router]'
        ' [https://compute.googleapis.com/compute/{}/'
        'projects/fake-project/regions/us-central1/operations/operation-X] '
        'Run the [gcloud compute operations describe] command to check the '
        'status of this operation.\n'.format(self.api_version))

  def testNatNotFound(self):
    self.ExpectGet(self.orig)

    with self.AssertRaisesExceptionMatches(nats_utils.NatNotFoundError,
                                           'NAT `invalid-nat` not found'):
      self.Run("""
          compute routers nats update invalid-nat --router my-router
          --region us-central1 --auto-allocate-nat-external-ips
          --nat-all-subnet-ip-ranges
          """)

  def testLogging(self):
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES,
            logConfig=self.messages.RouterNatLogConfig(
                enable=True,
                filter=self.messages.RouterNatLogConfig.FilterValueValuesEnum
                .TRANSLATIONS_ONLY))
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsPolling()
    self.ExpectGet(expected_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --auto-allocate-nat-external-ips
        --nat-all-subnet-ip-ranges --enable-logging
        --log-filter TRANSLATIONS_ONLY
        """)

  def testChangeLogFilter(self):
    initial_router = copy.deepcopy(self.orig)
    initial_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES,
            logConfig=self.messages.RouterNatLogConfig(
                enable=True,
                filter=self.messages.RouterNatLogConfig.FilterValueValuesEnum
                .TRANSLATIONS_ONLY))
    ]
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES,
            logConfig=self.messages.RouterNatLogConfig(
                enable=True,
                filter=self.messages.RouterNatLogConfig.FilterValueValuesEnum
                .ALL))
    ]

    self.ExpectGet(initial_router)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsPolling()
    self.ExpectGet(expected_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --log-filter ALL
        """)

  def testDisableLogging(self):
    initial_router = copy.deepcopy(self.orig)
    initial_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES,
            logConfig=self.messages.RouterNatLogConfig(
                enable=True,
                filter=self.messages.RouterNatLogConfig.FilterValueValuesEnum
                .ERRORS_ONLY))
    ]
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.AUTO_ONLY,
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES,
            logConfig=self.messages.RouterNatLogConfig(
                enable=False,
                filter=self.messages.RouterNatLogConfig.FilterValueValuesEnum
                .ERRORS_ONLY))
    ]

    self.ExpectGet(initial_router)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsPolling()
    self.ExpectGet(expected_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --no-enable-logging
        """)

  def testDrainIps(self):
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.MANUAL_ONLY,
            natIps=[
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-1') %
                self.api_version,
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-2') %
                self.api_version,
            ],
            drainNatIps=[
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-3') %
                self.api_version,
            ],
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsPolling()
    self.ExpectGet(expected_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --nat-external-ip-pool=address-1,address-2
        --nat-external-drain-ip-pool=address-3
        --nat-all-subnet-ip-ranges
        """)

  def testDrainExistIp(self):
    expected_manual_router = copy.deepcopy(self.orig)
    expected_manual_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.MANUAL_ONLY,
            natIps=[
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-1') %
                self.api_version,
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-2') %
                self.api_version,
            ],
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]

    expected_drained_router = copy.deepcopy(expected_manual_router)
    expected_drained_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.MANUAL_ONLY,
            natIps=[
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-2') %
                self.api_version,
            ],
            drainNatIps=[
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-1') %
                self.api_version,
            ],
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_manual_router)
    self.ExpectOperationsPolling()
    self.ExpectGet(expected_manual_router)

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_drained_router)
    self.ExpectOperationsPolling()
    self.ExpectGet(expected_drained_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1
        --nat-external-ip-pool=address-1,address-2
        --nat-all-subnet-ip-ranges
        """)
    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1
        --nat-external-drain-ip-pool=address-1
        --nat-all-subnet-ip-ranges
        """)

  def testClearDrainIps(self):
    expected_router = copy.deepcopy(self.orig)
    expected_router.nats = [
        self.messages.RouterNat(
            name='my-nat',
            natIpAllocateOption=self.messages.RouterNat
            .NatIpAllocateOptionValueValuesEnum.MANUAL_ONLY,
            natIps=[
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-1') %
                self.api_version,
                ('https://compute.googleapis.com/compute/%s/projects/'
                 'fake-project/regions/us-central1/addresses/address-2') %
                self.api_version,
            ],
            drainNatIps=[
            ],
            sourceSubnetworkIpRangesToNat=self.messages.RouterNat
            .SourceSubnetworkIpRangesToNatValueValuesEnum
            .ALL_SUBNETWORKS_ALL_IP_RANGES)
    ]

    self.ExpectGet(self.orig)
    self.ExpectPatch(expected_router)
    self.ExpectOperationsPolling()
    self.ExpectGet(expected_router)

    self.Run("""
        compute routers nats update my-nat --router my-router
        --region us-central1 --nat-external-ip-pool=address-1,address-2
        --clear-nat-external-drain-ip-pool
        --nat-all-subnet-ip-ranges
        """)


class BetaUpdateTest(UpdateTest):

  def SetUp(self):
    self.api_version = 'beta'
    self.SelectApi(calliope_base.ReleaseTrack.BETA, 'beta')

    self.orig = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='beta')
    self.orig.nats = [self.messages.RouterNat(name='my-nat')]


class AlphaUpdateTest(BetaUpdateTest):

  def SetUp(self):
    self.api_version = 'alpha'
    self.SelectApi(calliope_base.ReleaseTrack.ALPHA, 'alpha')

    self.orig = router_test_utils.CreateEmptyRouterMessage(
        self.messages, track='alpha')
    self.orig.nats = [self.messages.RouterNat(name='my-nat')]


if __name__ == '__main__':
  test_case.main()
