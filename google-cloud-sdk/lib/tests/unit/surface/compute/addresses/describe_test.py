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
"""Tests for the addresses describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.addresses import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class AddressesDescribeTest(test_base.BaseTest, test_case.WithOutputCapture):

  def testRegionPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [
            messages.Region(name='region-1'),
            messages.Region(name='region-2'),
            messages.Region(name='region-3'),
        ],

        [test_resources.ADDRESSES[0]],
    ])

    self.Run("""
        compute addresses describe address-1
        """)

    self.AssertErrContains('address-1')
    self.AssertErrContains('region-1')
    self.AssertErrContains('region-2')
    self.AssertErrContains('region-3')
    self.CheckRequests(
        self.regions_list_request,

        [(self.compute_v1.addresses,
          'Get',
          messages.ComputeAddressesGetRequest(
              address='address-1',
              region='region-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            address: 23.251.134.124
            name: address-1
            region: https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1
            selfLink: https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
            status: IN_USE
            """))

  def testWithGlobalFlag(self):
    self.make_requests.side_effect = iter([
        [test_resources.GLOBAL_ADDRESSES[0]],
    ])

    self.Run("""
        compute addresses describe global-address-1 --global
        """)

    self.CheckRequests(
        [(self.compute_v1.globalAddresses,
          'Get',
          messages.ComputeGlobalAddressesGetRequest(
              address='global-address-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            address: 23.251.134.126
            name: global-address-1
            selfLink: https://compute.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-1
            status: IN_USE
            """))

  def testWithRegionFlag(self):
    self.make_requests.side_effect = iter([
        [test_resources.ADDRESSES[0]],
    ])

    self.Run("""
        compute addresses describe address-1 --region region-1
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Get',
          messages.ComputeAddressesGetRequest(
              address='address-1',
              region='region-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            address: 23.251.134.124
            name: address-1
            region: https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1
            selfLink: https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
            status: IN_USE
            """))

  def testUriSupportForRegionalAddresses(self):
    self.make_requests.side_effect = iter([
        [test_resources.ADDRESSES[0]],
    ])

    self.Run("""
        compute addresses describe
          https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Get',
          messages.ComputeAddressesGetRequest(
              address='address-1',
              region='region-1',
              project='my-project'))])

  def testUriSupportForGlobalAddresses(self):
    self.make_requests.side_effect = iter([
        [test_resources.GLOBAL_ADDRESSES[0]],
    ])

    self.Run("""
        compute addresses describe
          https://compute.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-1
        """)

    self.CheckRequests(
        [(self.compute_v1.globalAddresses,
          'Get',
          messages.ComputeGlobalAddressesGetRequest(
              address='global-address-1',
              project='my-project'))])

  def testUriSupportWithIllegalType(self):
    with self.AssertRaisesExceptionRegexp(
        resources.WrongResourceCollectionException, r'.*compute\.networks.*'):
      self.Run("""
          compute addresses describe
            https://compute.googleapis.com/compute/v1/projects/my-project/global/networks/network-1
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
