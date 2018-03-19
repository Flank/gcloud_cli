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
"""Tests for the addresses list subcommand."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.compute.addresses import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock

messages = core_apis.GetMessagesModule('compute', 'v1')


class AddressesListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testTableOutput(self):
    command = 'compute addresses list'
    return_value = (test_resources.ADDRESSES
                    + test_resources.GLOBAL_ADDRESSES)
    output = ("""\
        NAME             REGION   ADDRESS        STATUS
        address-1        region-1 23.251.134.124 IN_USE
        address-2        region-1 23.251.134.125 RESERVED
        global-address-1          23.251.134.126 IN_USE
        global-address-2          23.251.134.127 RESERVED
        """)
    self.RequestAggregate(command, return_value, output)

  def testGlobalOption(self):
    command = 'compute addresses list --uri --global'
    return_value = test_resources.GLOBAL_ADDRESSES
    output = ("""\
        https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-1
        https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-2
        """)

    self.RequestOnlyGlobal(command, return_value, output)

  def testRegionsWithNoArgs(self):
    command = 'compute addresses list --uri --regions ""'
    return_value = test_resources.ADDRESSES
    output = ("""\
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-2
        """)

    self.RequestAggregate(command, return_value, output)

  def testOneRegion(self):
    command = 'compute addresses list --uri --regions region-1'
    return_value = test_resources.ADDRESSES
    output = ("""\
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-2
        """)

    self.RequestOneRegion(command, return_value, output)

  def testMultipleRegions(self):
    command = 'compute addresses list --uri --regions region-1,region-2'
    return_value = test_resources.ADDRESSES
    output = ("""\
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-2
        """)

    self.RequestTwoRegions(command, return_value, output)

  def testRegionsAndGlobal(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --regions '
        'may be specified'):
      self.Run("""\
          compute addresses list --regions '' --global
          """)
    self.CheckRequests()

  def testPositionalArgsWithSimpleNames(self):
    command = """
        compute addresses list
          address-1 global-address-1
          --uri
        """
    return_value = test_resources.ADDRESSES + test_resources.GLOBAL_ADDRESSES
    output = """\
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
        https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-1
        """

    self.RequestAggregate(command, return_value, output)

  def testPositionalArgsWithUris(self):
    command = """
        compute addresses list
          https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
          https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-1
          --uri
        """
    return_value = test_resources.ADDRESSES + test_resources.GLOBAL_ADDRESSES
    output = """\
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
        https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-1
        """

    self.RequestAggregate(command, return_value, output)

  def testPositionalArgsWithSimpleNamesAndRegionsFlag(self):
    command = """
        compute addresses list
          address-1 address-2 global-address-1
          --regions region-1,region-2
          --uri
        """
    return_value = test_resources.ADDRESSES
    output = """\
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-1
        https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/addresses/address-2
        """

    self.RequestTwoRegions(command, return_value, output)

  def testPositionalArgsWithSimpleNamesAndGlobalFlag(self):
    command = """
        compute addresses list
          address-1 address-2 global-address-1 global-address-2
          --global
          --uri
        """
    return_value = test_resources.GLOBAL_ADDRESSES
    output = """\
        https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-1
        https://www.googleapis.com/compute/v1/projects/my-project/global/addresses/global-address-2
        """

    self.RequestOnlyGlobal(command, return_value, output)

  def RequestOnlyGlobal(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.globalAddresses,
                   'List',
                   messages.ComputeGlobalAddressesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestAggregate(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.addresses,
                   'AggregatedList',
                   messages.ComputeAddressesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestOneRegion(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.addresses,
                   'List',
                   messages.ComputeAddressesListRequest(
                       project='my-project',
                       region='region-1'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestTwoRegions(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.addresses,
                   'List',
                   messages.ComputeAddressesListRequest(
                       project='my-project',
                       region='region-1')),
                  (self.compute_v1.addresses,
                   'List',
                   messages.ComputeAddressesListRequest(
                       project='my-project',
                       region='region-2'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def testAddressesCompleterRegional(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.ADDRESSES),
        []]
    self.RunCompleter(
        flags.AddressesCompleter,
        expected_command=[
            [
                'compute',
                'addresses',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'alpha',
                'compute',
                'addresses',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            'address-1',
            'address-2',
        ],
        cli=self.cli,
    )

  def testAddressesCompleterGlobal(self):
    self.list_json.side_effect = [
        [],
        resource_projector.MakeSerializable(test_resources.GLOBAL_ADDRESSES)]
    self.RunCompleter(
        flags.AddressesCompleter,
        expected_command=[
            [
                'compute',
                'addresses',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'alpha',
                'compute',
                'addresses',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            'global-address-1',
            'global-address-2',
        ],
        cli=self.cli,
    )

  def testAddressesCompleterRegionalAndGlobal(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.ADDRESSES),
        resource_projector.MakeSerializable(test_resources.GLOBAL_ADDRESSES)]
    self.RunCompleter(
        flags.AddressesCompleter,
        expected_command=[
            [
                'compute',
                'addresses',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
            [
                'alpha',
                'compute',
                'addresses',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=[
            'address-1',
            'address-2',
            'global-address-1',
            'global-address-2',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
