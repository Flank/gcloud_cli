# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the network peering list command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_resources


class PeeringsListTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.client = mock.Client(core_apis.GetClientClass('compute', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')

  def testTableOutput(self):
    self.client.networks.List.Expect(
        self.messages.ComputeNetworksListRequest(
            pageToken=None,
            project=self.Project(),),
        response=self.messages.NetworkList(
            items=test_resources.NETWORK_PEERINGS_V1,))

    self.Run('compute networks peerings list')

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    NETWORK PEER_PROJECT PEER_NETWORK   AUTO_CREATE_ROUTES STATE STATE_DETAILS
            peering-1 network-1 my-project network-2 True ACTIVE Matching configuration is found on peer network.
            peering-2 network-1 my-project-2 network-3 True ACTIVE Matching configuration is found on peer network.
            peering-3 network-1 my-project-3 network-3 True INACTIVE Peering is created.
            my-peering-1 network-2 my-project network-1 True ACTIVE Matching configuration is found on peer network.
            """), normalize_space=True)

  def testTableOutputNetworkFilter(self):
    self.client.networks.List.Expect(
        self.messages.ComputeNetworksListRequest(
            pageToken=None,
            project=self.Project(),),
        response=self.messages.NetworkList(
            items=test_resources.NETWORK_PEERINGS_V1,))

    self.Run('compute networks peerings list --network network-1')

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    NETWORK PEER_PROJECT PEER_NETWORK   AUTO_CREATE_ROUTES STATE STATE_DETAILS
            peering-1 network-1 my-project network-2 True ACTIVE Matching configuration is found on peer network.
            peering-2 network-1 my-project-2 network-3 True ACTIVE Matching configuration is found on peer network.
            peering-3 network-1 my-project-3 network-3 True INACTIVE Peering is created.
            """), normalize_space=True)

  def testTableOutputNetworkFilterNone(self):
    self.client.networks.List.Expect(
        self.messages.ComputeNetworksListRequest(
            pageToken=None,
            project=self.Project(),),
        response=self.messages.NetworkList(
            items=test_resources.NETWORK_PEERINGS_V1,))

    self.Run('compute networks peerings list --network no-network')

    self.AssertOutputEquals('', normalize_space=True)

if __name__ == '__main__':
  test_case.main()
