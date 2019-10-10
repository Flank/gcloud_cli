# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for the network peering delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class PeeringsDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.mock_get_global_resources = self.StartObjectPatch(
        lister,
        'GetGlobalResources',
        autospec=True,
        return_value=test_resources.NETWORK_PEERINGS_V1)
    self.track = calliope_base.ReleaseTrack.GA

  def testDeletePeering(self):
    self.Run('compute networks peerings delete peering-1 --network '
             'network-1')

    self.CheckRequests(
        [(self.compute.networks, 'RemovePeering',
          self.messages.ComputeNetworksRemovePeeringRequest(
              network='network-1',
              networksRemovePeeringRequest=self.messages.
              NetworksRemovePeeringRequest(name='peering-1'),
              project='my-project'))],)

  def testDeletePeeringNoNetworkError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --network: Must be specified.'):
      self.Run('compute networks peerings delete peering-1')


if __name__ == '__main__':
  test_case.main()
