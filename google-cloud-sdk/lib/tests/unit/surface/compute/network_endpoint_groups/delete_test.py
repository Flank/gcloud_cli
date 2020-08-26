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
"""Tests for the network-endpoint-groups delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NetworkEndpointGroupsDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([[
        self.messages.Operation(
            operationType='delete',
            status=self.messages.Operation.StatusValueValuesEnum.DONE)]])
    self.WriteInput('y\n')
    self.Run('compute network-endpoint-groups delete my-neg1 --zone zone-1')
    self.CheckRequests(
        [(self.compute.networkEndpointGroups, 'Delete',
          self.messages.ComputeNetworkEndpointGroupsDeleteRequest(
              networkEndpointGroup='my-neg1',
              project='my-project',
              zone='zone-1'))],)
    self.AssertErrContains('Deleted network endpoint group [my-neg1]')

  def testGlobal(self):
    self.make_requests.side_effect = iter([[
        self.messages.Operation(
            operationType='delete',
            status=self.messages.Operation.StatusValueValuesEnum.DONE)
    ]])
    self.WriteInput('y\n')
    self.Run('compute network-endpoint-groups delete my-neg1 --global')
    self.CheckRequests(
        [(self.compute.globalNetworkEndpointGroups, 'Delete',
          self.messages.ComputeGlobalNetworkEndpointGroupsDeleteRequest(
              networkEndpointGroup='my-neg1', project='my-project'))],)
    self.AssertErrContains('Deleted network endpoint group [my-neg1]')

  def testRegional(self):
    self.make_requests.side_effect = iter([[
        self.messages.Operation(
            operationType='delete',
            status=self.messages.Operation.StatusValueValuesEnum.DONE)
    ]])
    self.WriteInput('y\n')
    self.Run(
        'compute network-endpoint-groups delete my-neg1 --region us-central1')
    self.CheckRequests(
        [(self.compute.regionNetworkEndpointGroups, 'Delete',
          self.messages.ComputeRegionNetworkEndpointGroupsDeleteRequest(
              networkEndpointGroup='my-neg1',
              project='my-project',
              region='us-central1'))],)
    self.AssertErrContains('Deleted network endpoint group [my-neg1]')


class BetaNetworkEndpointGroupsDeleteTest(NetworkEndpointGroupsDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')


class AlphaNetworkEndpointGroupsDeleteTest(BetaNetworkEndpointGroupsDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')


if __name__ == '__main__':
  test_case.main()
