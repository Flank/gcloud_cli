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
"""Tests for the instances move subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.command_lib.compute.networks.subnets import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class SubnetsListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('beta')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.BETA_SUBNETWORKS))

  def testSimple(self):
    self.Run("""
        beta compute networks subnets list
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_beta.subnetworks,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME REGION NETWORK RANGE
            my-subnet1 us-central1 my-network 10.0.0.0/24
            my-subnet2 us-central1 my-other-network 10.0.0.0/24
            """), normalize_space=True)

  def testFilterFlag(self):
    self.Run("""
        beta compute networks subnets list --filter network:my-network
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_beta.subnetworks,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME REGION NETWORK RANGE
            my-subnet1 us-central1 my-network 10.0.0.0/24
            """), normalize_space=True)

  def testNetworkFlag(self):
    self.Run("""
        beta compute networks subnets list --network my-network
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_beta.subnetworks,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME REGION NETWORK RANGE
            my-subnet1 us-central1 my-network 10.0.0.0/24
            """), normalize_space=True)

  def testUriFlag(self):
    self.Run("""
        beta compute networks subnets list --uri
        """)
    self.AssertOutputEquals("""\
https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/subnetworks/my-subnet1
https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/subnetworks/my-subnet2
""",
                            normalize_space=True)

  def testFilterUriFlags(self):
    self.Run("""
        beta compute networks subnets list --filter network:my-network --uri
        """)
    self.AssertOutputEquals("""\
https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/subnetworks/my-subnet1
""",
                            normalize_space=True)

  def testNetworkUriFlags(self):
    self.Run("""
        beta compute networks subnets list --network my-network --uri
        """)
    self.AssertOutputEquals("""\
https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/subnetworks/my-subnet1
""",
                            normalize_space=True)

  def testSubnetworksCompleter(self):
    self.RunCompleter(
        flags.SubnetworksCompleter,
        expected_command=[
            'beta',
            'compute',
            'networks',
            'subnets',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'my-subnet1',
            'my-subnet2',
        ],
        cli=self.cli,
    )
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_beta.subnetworks,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])


if __name__ == '__main__':
  test_case.main()
