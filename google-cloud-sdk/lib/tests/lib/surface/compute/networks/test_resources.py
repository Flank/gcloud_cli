# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

messages = core_apis.GetMessagesModule('compute', 'v1')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')

NETWORKS_V1 = [
    # Legacy
    messages.Network(
        name='network-1',
        gatewayIPv4='10.240.0.1',
        IPv4Range='10.240.0.0/16',
        routingConfig=messages.NetworkRoutingConfig(
            routingMode=(messages.NetworkRoutingConfig
                         .RoutingModeValueValuesEnum.REGIONAL)),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-1')),

    # Custom
    messages.Network(
        name='network-2',
        autoCreateSubnetworks=False,
        routingConfig=messages.NetworkRoutingConfig(
            routingMode=(messages.NetworkRoutingConfig
                         .RoutingModeValueValuesEnum.REGIONAL)),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-2'),
        subnetworks=[
            'https://compute.googleapis.com/compute/v1/projects/'
            'my-project/regions/region-1/subnetworks/subnetwork-1',
            'https://compute.googleapis.com/compute/v1/projects/'
            'my-project/regions/region-1/subnetworks/subnetwork-2'
        ]),

    # Auto
    messages.Network(
        name='network-3',
        autoCreateSubnetworks=True,
        routingConfig=messages.NetworkRoutingConfig(
            routingMode=(messages.NetworkRoutingConfig
                         .RoutingModeValueValuesEnum.GLOBAL)),
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-3'),
        subnetworks=[])
]

NETWORK_PEERINGS_V1 = [
    messages.Network(
        name='network-1',
        autoCreateSubnetworks=True,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-1'),
        subnetworks=[],
        peerings=[
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-1',
                network='https://compute.googleapis.com/compute/v1/'
                'projects/my-project/global/networks/network-2',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer network.'
            ),
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-2',
                network='https://compute.googleapis.com/compute/v1/'
                'projects/my-project-2/global/networks/network-3',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer '
                'network.'),
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-3',
                network='https://compute.googleapis.com/compute/v1/'
                'projects/my-project-3/global/networks/network-3',
                state=(messages.NetworkPeering.StateValueValuesEnum.INACTIVE),
                stateDetails='Peering is created.')
        ]),
    messages.Network(
        name='network-2',
        autoCreateSubnetworks=True,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-2'),
        subnetworks=[],
        peerings=[
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='my-peering-1',
                network='https://compute.googleapis.com/compute/v1/projects/'
                'my-project/global/networks/network-1',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer network.')
        ])
]

BETA_SUBNETWORKS = [
    beta_messages.Subnetwork(
        name='my-subnet1',
        network=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'global/networks/my-network'),
        ipCidrRange='10.0.0.0/24',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/us-central1/subnetworks/my-subnet1'),
    ),
    beta_messages.Subnetwork(
        name='my-subnet2',
        network=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'global/networks/my-other-network'),
        ipCidrRange='10.0.0.0/24',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/us-central1/subnetworks/my-subnet2'),
    ),
]
