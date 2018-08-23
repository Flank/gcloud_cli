# -*- coding: utf-8 -*- #
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
"""Tests for the networks list-ip-owners subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class NetworksListIpOwnersTest(sdk_test_base.WithFakeAuth,
                               cli_test_base.CliTestBase):
  api_version = 'alpha'
  release_track = base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.track = self.release_track
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

    self.item1 = self.messages.InternalIpOwner(
        ipCidrRange='10.128.0.0/32',
        systemOwned=True,
        owners=['projects/my-project/regions/us-central1/subnetworks/subnet-1'])
    self.item2 = self.messages.InternalIpOwner(
        ipCidrRange='10.128.0.2/32',
        systemOwned=False,
        owners=[
            'projects/my-project/zones/us-central1-b/instances/vm-1',
            'projects/my-project/zones/us-central1-b/addresses/address-1'
        ])

  def testListIpOwners(self):
    network_name = 'network-1'
    filters = {
        '--subnet-name': 'subnet-1',
        '--subnet-region': 'us-central1',
        '--ip-cidr-range': '10.128.0.0/24',
        '--owner-projects': 'my-project,other-project',
        '--owner-types': 'instance,forwardingRule,address,subnetwork'
    }
    self._SetupMock(
        self.Project(), network_name, filters, items=[self.item1, self.item2])
    self._RunCommand(network_name, filters)
    system_owner = (
        'projects/my-project/regions/us-central1/subnetworks/subnet-1')
    non_system_owners = (
        'projects/my-project/zones/us-central1-b/instances/vm-1,'
        'projects/my-project/zones/us-central1-b/addresses/address-1')
    self.AssertOutputEquals(
        """\
IP_CIDR_RANGE SYSTEM_OWNED OWNERS
10.128.0.0/32 True {}
10.128.0.2/32 False {}
""".format(system_owner, non_system_owners),
        normalize_space=True)

  def testListIpOwnersOfAnotherProject(self):
    project_id = 'another-project'
    network_name = 'network-1'
    filters = {
        '--subnet-name': 'subnet-1',
        '--subnet-region': 'us-central1',
        '--ip-cidr-range': '10.128.0.0/24',
        '--owner-projects': 'my-project,other-project',
        '--owner-types': 'instance,forwardingRule,address,subnetwork'
    }
    self._SetupMock(
        project_id, network_name, filters, items=[self.item1, self.item2])
    self._RunCommand(network_name, filters, project_id)
    system_owner = (
        'projects/my-project/regions/us-central1/subnetworks/subnet-1')
    non_system_owners = (
        'projects/my-project/zones/us-central1-b/instances/vm-1,'
        'projects/my-project/zones/us-central1-b/addresses/address-1')
    self.AssertOutputEquals(
        """\
IP_CIDR_RANGE SYSTEM_OWNED OWNERS
10.128.0.0/32 True {}
10.128.0.2/32 False {}
""".format(system_owner, non_system_owners),
        normalize_space=True)

  def testListIpOwnersEmptyResult(self):
    network_name = 'network-1'
    filters = {}
    self._SetupMock(self.Project(), network_name, filters, items=[])
    self._RunCommand(network_name, filters)
    self.AssertOutputEquals('', normalize_space=True)

  def _SetupMock(self, project_id, network_name, filters, items):
    self.client.networks.ListIpOwners.Expect(
        self.messages.ComputeNetworksListIpOwnersRequest(
            network=network_name,
            project=project_id,
            subnetName=filters.get('--subnet-name', None),
            subnetRegion=filters.get('--subnet-region', None),
            ipCidrRange=filters.get('--ip-cidr-range', None),
            ownerProjects=filters.get('--owner-projects', None),
            ownerTypes=filters.get('--owner-types', None)),
        response=self.messages.IpOwnerList(items=items))

  def _RunCommand(self, network_name, filters, project_id=None):
    flags = ' '.join('{flag}={value}'.format(flag=flag, value=filters[flag])
                     for flag in filters)
    command = 'compute networks list-ip-owners {name} {flags} {project}'.format(
        name=network_name,
        project='--project=' + project_id if project_id else '',
        flags=flags)
    self.Run(command.strip())


if __name__ == '__main__':
  test_case.main()
