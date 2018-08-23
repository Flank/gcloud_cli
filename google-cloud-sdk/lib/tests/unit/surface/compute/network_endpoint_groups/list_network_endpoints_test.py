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
"""Tests for the network-endpoint-groups list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class NetworkEndpointGroupsListEndpointsTest(sdk_test_base.WithFakeAuth,
                                             cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.client = mock.Client(
        core_apis.GetClientClass('compute', 'beta'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

    self.expected_endpoints = [
        self.messages.NetworkEndpointWithHealthStatus(
            networkEndpoint=self.messages.NetworkEndpoint(
                instance='my-instance1',
                ipAddress='127.0.0.1',
                port=8888)),
        self.messages.NetworkEndpointWithHealthStatus(
            networkEndpoint=self.messages.NetworkEndpoint(
                instance='my-instance2',
                ipAddress='10.0.0.1',
                port=10001)),
        self.messages.NetworkEndpointWithHealthStatus(
            networkEndpoint=self.messages.NetworkEndpoint(
                instance='my-instance1')),
    ]

  def testTableOutput(self):

    self.client.networkEndpointGroups.ListNetworkEndpoints.Expect(
        self.messages.ComputeNetworkEndpointGroupsListNetworkEndpointsRequest(
            networkEndpointGroup='my-neg1',
            project=self.Project(),
            zone='us-central1-a'),
        self.messages.NetworkEndpointGroupsListNetworkEndpoints(
            items=self.expected_endpoints))
    self.Run('compute network-endpoint-groups list-network-endpoints my-neg1 '
             '--zone us-central1-a')

    self.AssertOutputEquals("""\
INSTANCE IP_ADDRESS PORT
my-instance1 127.0.0.1 8888
my-instance2 10.0.0.1 10001
my-instance1
""", normalize_space=True)

  def testCommandOutput(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.client.networkEndpointGroups.ListNetworkEndpoints.Expect(
        self.messages.ComputeNetworkEndpointGroupsListNetworkEndpointsRequest(
            networkEndpointGroup='my-neg1',
            project=self.Project(),
            zone='us-central1-a'),
        self.messages.NetworkEndpointGroupsListNetworkEndpoints(
            items=self.expected_endpoints))
    result = list(
        self.Run('compute network-endpoint-groups list-network-endpoints '
                 'my-neg1 --zone us-central1-a'))

    self.assertEqual(self.expected_endpoints, result)


if __name__ == '__main__':
  test_case.main()
