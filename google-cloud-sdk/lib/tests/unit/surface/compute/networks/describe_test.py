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
"""Tests for the networks describe subcommand."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class NetworksDescribeTest(test_base.BaseTest,
                           completer_test_base.CompleterBase,
                           test_case.WithOutputCapture):

  def testDescribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.NETWORKS_V1)
    self.RunCompletion(
        'compute networks describe n',
        [
            'network-1',
            'network-2',
            'network-3',
        ])

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.NETWORKS_V1[0]],
    ])

    self.Run("""
        compute networks describe my-network
        """)

    self.CheckRequests(
        [(self.compute.networks,
          'Get',
          self.messages.ComputeNetworksGetRequest(
              network='my-network',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            IPv4Range: 10.240.0.0/16
            gatewayIPv4: 10.240.0.1
            name: network-1
            routingConfig:
              routingMode: REGIONAL
            selfLink: {compute}/projects/my-project/global/networks/network-1
            x_gcloud_bgp_routing_mode: REGIONAL
            x_gcloud_subnet_mode: LEGACY
            """.format(compute=self.compute_uri)))

  def testPeeringCase(self):
    messages = core_apis.GetMessagesModule('compute', 'v1')
    self.make_requests.side_effect = iter([
        [
            messages.Network(
                name='network-4',
                autoCreateSubnetworks=True,
                routingConfig=messages.NetworkRoutingConfig(
                    routingMode=(messages.NetworkRoutingConfig.
                                 RoutingModeValueValuesEnum.GLOBAL)),
                selfLink=('https://www.googleapis.com/compute/v1/projects/'
                          'my-project/global/networks/network-4'),
                subnetworks=[],
                peerings=[
                    messages.NetworkPeering(
                        autoCreateRoutes=True,
                        name='peering-1',
                        network='https://www.googleapis.com/compute/v1'
                        '/projects/my-project-2/global/networks/network-5',
                        state=messages.NetworkPeering.StateValueValuesEnum.
                        INACTIVE,
                        stateDetails='Peering is created.')
                ])
        ],
    ])

    self.Run("""
        compute networks describe my-network
        """)

    self.CheckRequests(
        [(self.compute.networks, 'Get', self.messages.ComputeNetworksGetRequest(
            network='my-network', project='my-project'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            autoCreateSubnetworks: true
            name: network-4
            peerings:
            - autoCreateRoutes: true
              name: peering-1
              network: {compute}/projects/my-project-2/global/networks/network-5
              state: INACTIVE
              stateDetails: Peering is created.
            routingConfig:
              routingMode: GLOBAL
            selfLink: {compute}/projects/my-project/global/networks/network-4
            x_gcloud_bgp_routing_mode: GLOBAL
            x_gcloud_subnet_mode: AUTO
            """.format(compute=self.compute_uri)))

if __name__ == '__main__':
  test_case.main()
