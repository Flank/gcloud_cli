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

"""Tests for the networks list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute.networks import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock


def MakeV1NetworksForTest():
  messages = apis.GetMessagesModule('compute', 'v1')
  return [
      # Legacy
      messages.Network(
          name='network-1',
          gatewayIPv4='10.240.0.1',
          IPv4Range='10.240.0.0/16',
          routingConfig=messages.NetworkRoutingConfig(
              routingMode=(messages.NetworkRoutingConfig.
                           RoutingModeValueValuesEnum.REGIONAL)),
          selfLink=('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/network-1')),
      # Custom
      messages.Network(
          name='network-2',
          autoCreateSubnetworks=False,
          routingConfig=messages.NetworkRoutingConfig(
              routingMode=(messages.NetworkRoutingConfig.
                           RoutingModeValueValuesEnum.REGIONAL)),
          selfLink=('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/network-2'),
          subnetworks=[
              'https://www.googleapis.com/compute/v1/projects/'
              'my-project/regions/region-1/subnetworks/subnetwork-1',
              'https://www.googleapis.com/compute/v1/projects/'
              'my-project/regions/region-1/subnetworks/subnetwork-2'
          ]),
      # Auto
      messages.Network(
          name='network-3',
          autoCreateSubnetworks=True,
          routingConfig=messages.NetworkRoutingConfig(
              routingMode=(messages.NetworkRoutingConfig.
                           RoutingModeValueValuesEnum.GLOBAL)),
          selfLink=('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/network-3'),
          subnetworks=[])
  ]


def SetUp(test, api):
  test_networks = {
      'v1': MakeV1NetworksForTest(),
  }
  lister_patcher = mock.patch(
      'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
      autospec=True)
  test.addCleanup(lister_patcher.stop)
  test.mock_get_global_resources = lister_patcher.start()
  test.mock_get_global_resources.return_value = (
      resource_projector.MakeSerializable(test_networks[api]))
  test.SelectApi(api)


class NetworksListTest(test_base.BaseTest,
                       completer_test_base.CompleterBase):

  def SetUp(self):
    SetUp(self, 'v1')

  def testClusterDevFlag(self):
    properties.VALUES.api_endpoint_overrides.compute.Set(
        'http://localhost:3990/')

    self.Run('compute networks list --uri')
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.networks,
        project='my-project',
        filter_expr=None,
        http=self.mock_http(),
        batch_url='http://localhost:3990/batch/compute/v1',
        errors=[])

  def testTableOutput(self):
    self.Run("""
        compute networks list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.networks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME  SUBNET_MODE  BGP_ROUTING_MODE  IPV4_RANGE  GATEWAY_IPV4
            network-1  LEGACY  REGIONAL 10.240.0.0/16 10.240.0.1
            network-2  CUSTOM  REGIONAL
            network-3  AUTO  GLOBAL
            """),
        normalize_space=True)

  def testNetworksCompleter(self):
    self.RunCompleter(
        flags.NetworksCompleter,
        expected_command=[
            'compute',
            'networks',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'network-1',
            'network-2',
            'network-3',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
