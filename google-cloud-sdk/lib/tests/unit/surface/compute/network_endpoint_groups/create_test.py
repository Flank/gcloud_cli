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
"""Tests for the network endpoint groups create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NetworkEndpointGroupsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.region = 'us-central1'
    self.zone = 'us-central1-a'
    self.endpoint_type_enum = (
        self.messages.NetworkEndpointGroup.NetworkEndpointTypeValueValuesEnum)

  def _ExpectCreate(self, network_endpoint_group, project=None, zone=None):
    if zone:
      request = self.messages.ComputeNetworkEndpointGroupsInsertRequest(
          project=project or self.Project(),
          zone=zone,
          networkEndpointGroup=network_endpoint_group)
    else:
      request = self.messages.ComputeGlobalNetworkEndpointGroupsInsertRequest(
          project=project or self.Project(),
          networkEndpointGroup=network_endpoint_group)
    self.make_requests.side_effect = [[network_endpoint_group]]
    return request

  # if region is None, this NEG is considered global
  def _CreateNetworkEndpointGroup(self,
                                  name,
                                  default_port=None,
                                  network=None,
                                  subnetwork=None,
                                  project=None,
                                  region=None,
                                  network_endpoint_type=None):
    project = project or self.Project()
    network_endpoint_type = network_endpoint_type or self.endpoint_type_enum.GCE_VM_IP_PORT

    network_uri, subnetwork_uri = None, None
    if network:
      network_uri = (
          self.compute_uri +
          '/projects/{project}/global/networks/{name}'.format(
              project=project, name=network))
    if subnetwork:
      subnetwork_uri = (
          self.compute_uri + '/projects/{project}/regions/'
          '{region}/subnetworks/{name}'.format(
              project=project, region=region, name=subnetwork))

    network_endpoint_group = self.messages.NetworkEndpointGroup(
        name=name,
        networkEndpointType=network_endpoint_type,
        defaultPort=default_port,
        network=network_uri,
        subnetwork=subnetwork_uri)

    return network_endpoint_group

  def testCreate_Default(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(
        name='my-neg1', region=self.region)
    request = self._ExpectCreate(network_endpoint_group, zone=self.zone)

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
        default_port=8888,
        region=self.region)
    request = self._ExpectCreate(network_endpoint_group, zone=self.zone)

    result = self.Run('compute network-endpoint-groups create my-neg1 '
                      '--network my-network --subnet my-subnet '
                      '--default-port 8888 --zone ' + self.zone)

    self.CheckRequests(
        [(self.compute.networkEndpointGroups, 'Insert', request)])
    self.assertEqual(result, network_endpoint_group)

  def testCreate_EnumFlagFormat(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(
        name='my-neg1', region=self.region)
    request = self._ExpectCreate(network_endpoint_group, zone=self.zone)

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


class AlphaNetworkEndpointGroupsCreateTest(NetworkEndpointGroupsCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.region = 'us-central1'
    self.zone = 'us-central1-a'
    self.endpoint_type_enum = (
        self.messages.NetworkEndpointGroup.NetworkEndpointTypeValueValuesEnum)

  def testCreateGlobal_Default(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(
        name='my-neg1',
        network_endpoint_type=self.endpoint_type_enum.INTERNET_IP_PORT)
    request = self._ExpectCreate(network_endpoint_group)

    result = self.Run('compute network-endpoint-groups create my-neg1 --global '
                      '--network-endpoint-type=internet-ip-port')

    self.CheckRequests([(self.compute.globalNetworkEndpointGroups, 'Insert',
                         request)])
    self.assertEqual(result, network_endpoint_group)
    self.AssertErrContains('Created network endpoint group [my-neg1]')

  def testCreateGlobal_AllOptions(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(
        name='my-neg1',
        default_port=9999,
        network_endpoint_type=self.endpoint_type_enum.INTERNET_IP_PORT)
    request = self._ExpectCreate(network_endpoint_group)

    result = self.Run(
        'compute network-endpoint-groups create my-neg1 --global '
        '--network-endpoint-type=internet-ip-port --default-port 9999')

    self.CheckRequests([(self.compute.globalNetworkEndpointGroups, 'Insert',
                         request)])
    self.assertEqual(result, network_endpoint_group)

  def testCreateGlobal_EnumFlagFormat(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(
        name='my-neg1',
        network_endpoint_type=self.endpoint_type_enum.INTERNET_FQDN_PORT)
    request = self._ExpectCreate(network_endpoint_group)

    result = self.Run('compute network-endpoint-groups create my-neg1 --global '
                      '--network-endpoint-type INTERNET_FQDN_PORT')

    self.CheckRequests([(self.compute.globalNetworkEndpointGroups, 'Insert',
                         request)])
    self.assertEqual(result, network_endpoint_group)

  def testCreateGlobal_RelativeNameProjectOverride(self):
    network_endpoint_group = self._CreateNetworkEndpointGroup(
        name='my-neg1',
        network_endpoint_type=self.endpoint_type_enum.INTERNET_IP_PORT)
    request = self._ExpectCreate(
        network_endpoint_group, project='my-other-project')

    result = self.Run(
        'compute network-endpoint-groups create '
        'projects/my-other-project/global/networkEndpointGroups/my-neg1 '
        '--global --network-endpoint-type=internet-ip-port')

    self.CheckRequests([(self.compute.globalNetworkEndpointGroups, 'Insert',
                         request)])
    self.assertEqual(result, network_endpoint_group)

  def testCreateGlobal_GceVmIpPortType_fails(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-endpoint-type\]: GCE_VM_IP_PORT '
        r'network endpoint type not supported for global NEGs.'):
      self.Run("""
      compute network-endpoint-groups create my-neg1 --global
        --network-endpoint-type GCE_VM_IP_PORT
      """)

  def testCreateZonal_InternetIpPortType_fails(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-endpoint-type\]: Internet '
        r'network endpoint types not supported for zonal NEGs.'):
      self.Run("""
      compute network-endpoint-groups create my-neg1 --zone {0}
        --network-endpoint-type INTERNET_IP_PORT
      """.format(self.zone))

  def testCreateZonal_InternetFqdnPortType_fails(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-endpoint-type\]: Internet '
        r'network endpoint types not supported for zonal NEGs.'):
      self.Run("""
      compute network-endpoint-groups create my-neg1 --zone {0}
        --network-endpoint-type INTERNET_FQDN_PORT
      """.format(self.zone))

  def testCreateGlobal_InternetType_NetworkSet_fails(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network\]: Global NEGs cannot specify '
        r'network.'):
      self.Run("""
      compute network-endpoint-groups create my-neg1 --global
        --network-endpoint-type INTERNET_IP_PORT
        --network default
      """)


if __name__ == '__main__':
  test_case.main()
