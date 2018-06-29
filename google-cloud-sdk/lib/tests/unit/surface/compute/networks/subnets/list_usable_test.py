# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for subnets list-usable subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA, 'alpha'),
                          (calliope_base.ReleaseTrack.BETA, 'beta'))
class SubnetsListUsableTest(cli_test_base.CliTestBase,
                            sdk_test_base.WithFakeAuth, parameterized.TestCase):
  """Unit tests for 'subnets list-usable' fake auth and mocks."""

  COMPUTE_API_BASE = 'https://www.googleapis.com/compute/v1/projects/'
  COMPUTE_DISCOVERY_URL = (
      'https://www.googleapis.com/discovery/v1/apis/compute/v1/rest')
  SUBNET_DISCOVERY_TYPE = 'Subnetwork'
  SUBNET_RESOURCE_TYPE = 'type.googleapis.com/compute.Subnetwork'
  PROJECT_ID = 'project-1'
  HEADER = 'PROJECT REGION NETWORK SUBNET RANGE SECONDARY_RANGES'
  API_NAME = 'compute'

  def _SetUp(self, api_version):
    self.api_version = api_version
    properties.VALUES.compute.use_new_list_usable_subnets_api.Set(True)
    properties.VALUES.core.project.Set(self.PROJECT_ID)
    self.mock_client = mock.Client(
        apis.GetClientClass(self.API_NAME, api_version),
        real_client=apis.GetClientInstance(
            self.API_NAME, api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = apis.GetMessagesModule(self.API_NAME, api_version)

  def testNoUsableSubnets(self, track, api_version):
    self._SetUp(api_version)
    self._SetupMockResults(results=[])
    self._RunCommand()
    self.AssertOutputEquals('', normalize_space=True)

  def testSingleUsableSubnet(self, track, api_version):
    self._SetUp(api_version)
    self._SetupMockResults(results=[
        self._CreateSubnet(
            name='subnet-1',
            region='us-west1',
            project='project-1',
            network='network-1',
            ip_cidr_range='10.128.0.0/16')
    ])
    self._RunCommand()
    expected_output_lines = [
        self.HEADER, ' '.join(
            ['project-1', 'us-west1', 'network-1', 'subnet-1', '10.128.0.0/16'])
    ]
    expected_output = '\n'.join(expected_output_lines) + '\n'
    self.AssertOutputEquals(expected_output, normalize_space=True)

  def testMultipleUsableSubnet(self, track, api_version):
    self._SetUp(api_version)
    self._SetupMockResults(results=[
        self._CreateSubnet(
            name='subnet-1',
            region='us-west1',
            project='project-1',
            network='network-1',
            ip_cidr_range='10.128.0.0/16'),
        self._CreateSubnet(
            name='subnet-2',
            region='us-east1',
            project='project-1',
            network='network-1',
            ip_cidr_range='10.130.0.0/16')
    ])
    self._RunCommand()
    expected_output_lines = [
        self.HEADER, ' '.join([
            'project-1', 'us-west1', 'network-1', 'subnet-1', '10.128.0.0/16'
        ]), ' '.join(
            ['project-1', 'us-east1', 'network-1', 'subnet-2', '10.130.0.0/16'])
    ]
    expected_output = '\n'.join(expected_output_lines) + '\n'
    self.AssertOutputEquals(expected_output, normalize_space=True)

  def testMultipleUsableSubnet_secondaryRanges(self, track, api_version):
    self._SetUp(api_version)
    self._SetupMockResults(results=[
        # subnet-1 has 1 secondary range
        self._CreateSubnet(
            name='subnet-1',
            region='us-west1',
            project='project-1',
            network='network-1',
            ip_cidr_range='10.128.0.0/16',
            secondary_ip_ranges=[
                self._Secondary_Ip_Range('secondary-range-0', '192.168.0.0/24')
            ]),
        # subnet-2 has 2 secondary ranges
        self._CreateSubnet(
            name='subnet-2',
            region='us-east1',
            project='project-1',
            network='network-1',
            ip_cidr_range='10.130.0.0/16',
            secondary_ip_ranges=[
                self._Secondary_Ip_Range('secondary-range-1', '192.168.1.0/24'),
                self._Secondary_Ip_Range('secondary-range-2', '192.168.2.0/24')
            ]),
        # subnet-3 has no secondary ranges
        self._CreateSubnet(
            name='subnet-3',
            region='us-central1',
            project='project-1',
            network='network-1',
            ip_cidr_range='10.132.0.0/16')
    ])
    self._RunCommand()
    expected_output_lines = [
        self.HEADER, ('project-1 us-west1 network-1 subnet-1 10.128.0.0/16 '
                      'secondary-range-0 192.168.0.0/24'),
        ('project-1 us-east1 network-1 subnet-2 10.130.0.0/16 '
         'secondary-range-1 192.168.1.0/24\nsecondary-range-2 192.168.2.0/24 '),
        ('project-1 us-central1 network-1 subnet-3 10.132.0.0/16')
    ]
    expected_output = '\n'.join(expected_output_lines) + '\n'
    self.AssertOutputEquals(expected_output, normalize_space=True)

  def _SetupMockResults(self, results):
    expected_request = self.messages.ComputeSubnetworksListUsableRequest(
        project=properties.VALUES.core.project.Get(required=True))
    result = self.messages.UsableSubnetworksAggregatedList(items=results)
    self.mock_client.subnetworks.ListUsable.Expect(expected_request, result)

  def _RunCommand(self):
    command_template = ('{api_version} compute networks subnets list-usable')
    command = command_template.format(
        api_version=self.api_version if self.api_version else '')
    self.Run(command.strip())

  def _Secondary_Ip_Range(self, range_name, ip_cidr_range):
    return self.messages.UsableSubnetworkSecondaryRange(
        rangeName=range_name, ipCidrRange=ip_cidr_range)

  def _CreateSubnet(self,
                    name,
                    region,
                    project,
                    network,
                    ip_cidr_range,
                    secondary_ip_ranges=None):
    subnet_url = '/'.join([
        self.COMPUTE_API_BASE, project, 'regions', region, 'subnetworks', name
    ])
    return self.messages.UsableSubnetwork(
        subnetwork=subnet_url,
        network=network,
        ipCidrRange=ip_cidr_range,
        secondaryIpRanges=secondary_ip_ranges or
        [])  # no secondary ranges by default


if __name__ == '__main__':
  test_case.main()
