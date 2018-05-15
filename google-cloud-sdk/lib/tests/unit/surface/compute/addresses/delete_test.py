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
"""Tests for the addresses delete subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class AddressesDeleteTest(test_base.BaseTest):

  def testWithSingleAddress(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute addresses delete address-1
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-1',
              project='my-project',
              region='us-central2'))],
    )

  def testWithManyAddresses(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute addresses delete address-1 address-2 address-3
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-1',
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-2',
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-3',
              project='my-project',
              region='us-central2'))],
    )

  def testUriSupport(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
      compute addresses delete
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
        address-2
        --region https://www.googleapis.com/compute/v1/projects/my-project/regions/region-2
      """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-1',
              project='my-project',
              region='region-1')),

         (self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-2',
              project='my-project',
              region='region-2'))],
    )

  def testRegionPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Region(name='region-1'),
            messages.Region(name='region-2'),
            messages.Region(name='region-3'),
        ],

        [],
    ])
    self.WriteInput('2\ny\n')  # Option 1 is for global.

    self.Run("""
        compute addresses delete address-1
        """)

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-1',
              project='my-project',
              region='region-1'))],
    )
    self.AssertErrContains('region-1')
    self.AssertErrContains('region-2')
    self.AssertErrContains('region-3')
    self.AssertErrContains(textwrap.dedent("""\
        The following addresses will be deleted:
         - [address-1] in [region-1]


        Do you want to continue (Y/n)? """))

  def testPromptingWithYes(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('y\n')
    self.Run("""
        compute addresses delete address-1 address-2 address-3
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-1',
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-2',
              project='my-project',
              region='us-central2')),

         (self.compute_v1.addresses,
          'Delete',
          messages.ComputeAddressesDeleteRequest(
              address='address-3',
              project='my-project',
              region='us-central2'))],
    )
    self.AssertErrContains(textwrap.dedent("""\
        The following addresses will be deleted:
         - [address-1] in [us-central2]
         - [address-2] in [us-central2]
         - [address-3] in [us-central2]


        Do you want to continue (Y/n)? """))

  def testPromptingWithNo(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)

    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute addresses delete address-1 address-2 address-3
            --region us-central2
          """)

    self.CheckRequests()
    self.AssertErrContains(textwrap.dedent("""\
        The following addresses will be deleted:
         - [address-1] in [us-central2]
         - [address-2] in [us-central2]
         - [address-3] in [us-central2]


        Do you want to continue (Y/n)? """))


class GlobalAddressesDeleteTest(test_base.BaseTest):

  def testWithSingleAddress(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute addresses delete address-1
          --global
        """)

    self.CheckRequests(
        [(self.compute_v1.globalAddresses,
          'Delete',
          messages.ComputeGlobalAddressesDeleteRequest(
              address='address-1',
              project='my-project'))],
    )

  def testMultipleAddressSupport(self):
    self.Run("""\
      compute addresses delete
        https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/address-1
        address-2
        --global
      """)

    self.CheckRequests(
        [(self.compute_v1.globalAddresses,
          'Delete',
          messages.ComputeGlobalAddressesDeleteRequest(
              address='address-1',
              project='my-project')),

         (self.compute_v1.globalAddresses,
          'Delete',
          messages.ComputeGlobalAddressesDeleteRequest(
              address='address-2',
              project='my-project'))],
    )
    self.AssertErrContains(textwrap.dedent("""\
        The following global addresses will be deleted:
         - [address-1]
         - [address-2]


        Do you want to continue (Y/n)? """))

  def testUriSupport(self):
    self.Run("""\
      compute addresses delete
        https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/address-1
      """)

    self.CheckRequests(
        [(self.compute_v1.globalAddresses,
          'Delete',
          messages.ComputeGlobalAddressesDeleteRequest(
              address='address-1',
              project='my-project'))],
    )
    self.AssertErrContains(textwrap.dedent("""\
        The following global addresses will be deleted:
         - [address-1]


        Do you want to continue (Y/n)? """))


if __name__ == '__main__':
  test_case.main()
