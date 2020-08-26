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
"""Tests for the network-endpoint-groups describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.network_endpoint_groups import test_resources


class NetworkEndpointGroupsDescribeTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.zonal_neg_test_resource = test_resources.NETWORK_ENDPOINT_GROUPS[0]
    self.region_neg_test_resource = test_resources.REGION_NETWORK_ENDPOINT_GROUPS[
        0]
    self.global_neg_test_resource = test_resources.GLOBAL_NETWORK_ENDPOINT_GROUPS[
        0]

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([[self.zonal_neg_test_resource]])
    result = self.Run('compute network-endpoint-groups describe my-neg1 '
                      '--zone zone-1')

    self.CheckRequests([(self.compute.networkEndpointGroups, 'Get',
                         self.messages.ComputeNetworkEndpointGroupsGetRequest(
                             networkEndpointGroup='my-neg1',
                             project='my-project',
                             zone='zone-1'))],)

    self.assertEqual(self.zonal_neg_test_resource, result)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
           description: My NEG 1
           kind: compute#networkEndpointGroup
           name: my-neg1
           network: https://compute.googleapis.com/compute/v1/projects/my-project/global/networks/network-1
           networkEndpointType: GCE_VM_IP_PORT
           selfLink: https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg1
           size: 5
           zone: zone-1
            """.format(api=self.api)))

  def testGlobalCase(self):
    self.make_requests.side_effect = iter([[self.global_neg_test_resource]])
    result = self.Run(
        'compute network-endpoint-groups describe my-global-neg --global')

    self.CheckRequests(
        [(self.compute.globalNetworkEndpointGroups, 'Get',
          self.messages.ComputeGlobalNetworkEndpointGroupsGetRequest(
              networkEndpointGroup='my-global-neg', project='my-project'))],)
    self.assertEqual(self.global_neg_test_resource, result)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
           description: My Global NEG
           kind: compute#networkEndpointGroup
           name: my-global-neg
           networkEndpointType: INTERNET_IP_PORT
           selfLink: https://compute.googleapis.com/compute/{api}/projects/my-project/global/networkEndpointGroups/my-global-neg
           size: 1
            """.format(api=self.api)))

  def testRegionalCase(self):
    self.make_requests.side_effect = iter([[self.region_neg_test_resource]])
    result = self.Run(
        'compute network-endpoint-groups describe my-cloud-run-neg '
        '--region region-1')

    self.CheckRequests(
        [(self.compute.regionNetworkEndpointGroups, 'Get',
          self.messages.ComputeRegionNetworkEndpointGroupsGetRequest(
              networkEndpointGroup='my-cloud-run-neg',
              project='my-project',
              region='region-1'))],)
    self.assertEqual(self.region_neg_test_resource, result)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            cloudRun:
              service: cloud-run-service
              tag: cloud-run-tag
            description: My Cloud Run Serverless NEG
            kind: compute#networkEndpointGroup
            name: my-cloud-run-neg
            networkEndpointType: SERVERLESS
            region: region-1
            selfLink: https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-1/networkEndpointGroups/my-cloud-run-neg
            size: 0
        """.format(api=self.api)))


class BetaNetworkEndpointGroupsDescribeTest(NetworkEndpointGroupsDescribeTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.zonal_neg_test_resource = test_resources.NETWORK_ENDPOINT_GROUPS_BETA[
        0]
    self.region_neg_test_resource = test_resources.REGION_NETWORK_ENDPOINT_GROUPS_BETA[
        0]
    self.global_neg_test_resource = test_resources.GLOBAL_NETWORK_ENDPOINT_GROUPS_BETA[
        0]


class AlphaNetworkEndpointGroupsDescribeTest(
    BetaNetworkEndpointGroupsDescribeTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.zonal_neg_test_resource = test_resources.NETWORK_ENDPOINT_GROUPS_ALPHA[
        0]
    self.global_neg_test_resource = test_resources.GLOBAL_NETWORK_ENDPOINT_GROUPS_ALPHA[
        0]
    self.region_neg_test_resource = test_resources.REGION_NETWORK_ENDPOINT_GROUPS_ALPHA[
        0]


if __name__ == '__main__':
  test_case.main()
