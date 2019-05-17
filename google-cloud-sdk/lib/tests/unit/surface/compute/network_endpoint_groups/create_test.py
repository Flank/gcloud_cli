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
"""Tests for the network endpoint groups create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NetworkEndpointGroupsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.region = 'us-central1'
    self.zone = 'us-central1-a'

  def _ExpectCreate(self, network_endpoint_group, project=None, zone=None):
    request = self.messages.ComputeNetworkEndpointGroupsInsertRequest(
        project=project or self.Project(),
        zone=zone or self.zone,
        networkEndpointGroup=network_endpoint_group)
    self.make_requests.side_effect = [[network_endpoint_group]]
    return request

  def _CreateNetworkEndpointGroup(self, name, default_port=None, network=None,
                                  subnetwork=None, project=None, region=None):
    project = project or self.Project()
    region = region or self.region

    compute_prefix = 'https://www.googleapis.com/compute/v1/'
    network_uri, subnetwork_uri = None, None
    if network:
      network_uri = (
          compute_prefix + 'projects/{project}/global/networks/{name}'.format(
              project=project, name=network))
    if subnetwork:
      subnetwork_uri = (
          compute_prefix + 'projects/{project}/regions/'
          '{region}/subnetworks/{name}'.format(
              project=project, region=region, name=subnetwork))

    endpoint_type_enum = (self.messages.NetworkEndpointGroup
                          .NetworkEndpointTypeValueValuesEnum)
    network_endpoint_group = self.messages.NetworkEndpointGroup(
        name=name,
        networkEndpointType=endpoint_type_enum.GCE_VM_IP_PORT,
        defaultPort=default_port,
        network=network_uri,
        subnetwork=subnetwork_uri)

    return network_endpoint_group

  def testCreate_Default(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(name='my-neg1')
    request = self._ExpectCreate(network_endpoint_group)

    result = self.Run('compute network-endpoint-groups create my-neg1 '
                      '--zone ' + self.zone)

    self.CheckRequests(
        [(self.compute.networkEndpointGroups, 'Insert', request)])
    self.assertEqual(result, network_endpoint_group)
    self.AssertErrContains('Created network endpoint group [my-neg1]')

  def testCreate_AllOptions(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(
        name='my-neg1',
        network='my-network',
        subnetwork='my-subnet',
        default_port=8888)
    request = self._ExpectCreate(network_endpoint_group)

    result = self.Run('compute network-endpoint-groups create my-neg1 '
                      '--network my-network --subnet my-subnet '
                      '--default-port 8888 --zone ' + self.zone)

    self.CheckRequests(
        [(self.compute.networkEndpointGroups, 'Insert', request)])
    self.assertEqual(result, network_endpoint_group)

  def testCreate_EnumFlagFormat(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(name='my-neg1')
    request = self._ExpectCreate(network_endpoint_group)

    result = self.Run('compute network-endpoint-groups create my-neg1 '
                      '--network-endpoint-type GCE_VM_IP_PORT '
                      '--zone ' + self.zone)

    self.CheckRequests(
        [(self.compute.networkEndpointGroups, 'Insert', request)])
    self.assertEqual(result, network_endpoint_group)

  def testCreate_RelativeNameProjectOverride(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(
        name='my-neg1', project='my-other-project', region='my-region1',
        network='my-net', subnetwork='my-subnet')
    request = self._ExpectCreate(
        network_endpoint_group, project='my-other-project', zone='my-region1-a')

    result = self.Run('compute network-endpoint-groups create '
                      'projects/my-other-project/zones/my-region1-a/'
                      'networkEndpointGroups/my-neg1 '
                      '--network my-net --subnet my-subnet')

    self.CheckRequests(
        [(self.compute.networkEndpointGroups, 'Insert', request)])
    self.assertEqual(result, network_endpoint_group)


if __name__ == '__main__':
  test_case.main()
