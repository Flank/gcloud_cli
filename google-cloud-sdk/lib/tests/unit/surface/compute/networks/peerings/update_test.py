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
"""Tests for the network peering update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class PeeringsUpdateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.message_version = self.compute_v1

  def testUpdatePeeringWithCustomRoutesFlagsTrueTrue(self):
    self.Run('compute networks peerings update peering-1 --network '
             'network-1 --export-custom-routes --import-custom-routes')
    self.CheckRequests([(self.compute.networks, 'UpdatePeering',
                         self.messages.ComputeNetworksUpdatePeeringRequest(
                             network='network-1',
                             networksUpdatePeeringRequest=self.messages
                             .NetworksUpdatePeeringRequest(
                                 networkPeering=self.messages.NetworkPeering(
                                     name='peering-1',
                                     exportCustomRoutes=True,
                                     importCustomRoutes=True)),
                             project='my-project'))],)

  def testUpdatePeeringWithCustomRoutesFlagsFalseFalse(self):
    self.Run('compute networks peerings update peering-1 --network '
             'network-1 --no-export-custom-routes --no-import-custom-routes')
    self.CheckRequests([(self.compute.networks, 'UpdatePeering',
                         self.messages.ComputeNetworksUpdatePeeringRequest(
                             network='network-1',
                             networksUpdatePeeringRequest=self.messages
                             .NetworksUpdatePeeringRequest(
                                 networkPeering=self.messages.NetworkPeering(
                                     name='peering-1',
                                     exportCustomRoutes=False,
                                     importCustomRoutes=False)),
                             project='my-project'))],)

  def testWithNoFlags(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run('compute networks peerings update peering-1 --network network-1')

  def testUpdatePeeringWithImportAndExportSubnetRouteWithPublicIp(self):
    self.Run('compute networks peerings update peering-1 --network '
             'network-1 --export-subnet-routes-with-public-ip '
             '--import-subnet-routes-with-public-ip')
    self.CheckRequests([(self.compute.networks, 'UpdatePeering',
                         self.messages.ComputeNetworksUpdatePeeringRequest(
                             network='network-1',
                             networksUpdatePeeringRequest=self.messages
                             .NetworksUpdatePeeringRequest(
                                 networkPeering=self.messages.NetworkPeering(
                                     name='peering-1',
                                     exportSubnetRoutesWithPublicIp=True,
                                     importSubnetRoutesWithPublicIp=True)),
                             project='my-project'))],)

  def testUpdatePeeringDisableImportAndExportSubnetRouteWithPublicIp(self):
    self.Run('compute networks peerings update peering-1 --network '
             'network-1 --no-export-subnet-routes-with-public-ip '
             '--no-import-subnet-routes-with-public-ip')
    self.CheckRequests([(self.compute.networks, 'UpdatePeering',
                         self.messages.ComputeNetworksUpdatePeeringRequest(
                             network='network-1',
                             networksUpdatePeeringRequest=self.messages
                             .NetworksUpdatePeeringRequest(
                                 networkPeering=self.messages.NetworkPeering(
                                     name='peering-1',
                                     exportSubnetRoutesWithPublicIp=False,
                                     importSubnetRoutesWithPublicIp=False)),
                             project='my-project'))],)


if __name__ == '__main__':
  test_case.main()
