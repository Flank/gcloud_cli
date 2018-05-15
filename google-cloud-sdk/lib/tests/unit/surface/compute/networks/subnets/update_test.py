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
"""Tests for the subnets update subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class SubnetsUpdateTest(test_base.BaseTest):

  def testNoUpdates(self):
    """Tests running update with no update parameters."""
    self.Run("""
        compute networks subnets update subnet-1
          --region us-central2
        """)

    # Empty set of updates.
    self.CheckRequests([])

  def testEnableGoogleAccess(self):
    """Tests enabling privateIpGoogleAccess on a subnet."""
    self.Run("""
        compute networks subnets update subnet-1
          --enable-private-ip-google-access
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.subnetworks,
          'SetPrivateIpGoogleAccess',
          self.messages.ComputeSubnetworksSetPrivateIpGoogleAccessRequest(
              project='my-project',
              region='us-central2',
              subnetwork='subnet-1',
              subnetworksSetPrivateIpGoogleAccessRequest=(
                  self.messages.SubnetworksSetPrivateIpGoogleAccessRequest(
                      privateIpGoogleAccess=True)),
          ))]
    )

  def testDisableGoogleAccess(self):
    """Tests disabling privateIpGoogleAccess on a subnet."""
    self.Run("""
        compute networks subnets update subnet-1
          --no-enable-private-ip-google-access
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.subnetworks,
          'SetPrivateIpGoogleAccess',
          self.messages.ComputeSubnetworksSetPrivateIpGoogleAccessRequest(
              project='my-project',
              region='us-central2',
              subnetwork='subnet-1',
              subnetworksSetPrivateIpGoogleAccessRequest=(
                  self.messages.SubnetworksSetPrivateIpGoogleAccessRequest(
                      privateIpGoogleAccess=False)),
          ))],
    )

  def testAddSecondaryRanges(self):
    subnetwork_resource = {
        'name':
            'subnetwork-1',
        'network': ('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/default'),
    }
    self.make_requests.side_effect = iter([
        [self.messages.Subnetwork(**subnetwork_resource)],
        [],
    ])

    self.Run("""
        compute networks subnets update subnet-1
          --add-secondary-ranges range2=192.168.64.0/24,range3=192.168.125.0/24
          --region us-central2
        """)
    subnetwork_resource['secondaryIpRanges'] = [
        self.messages.SubnetworkSecondaryRange(
            rangeName='range2', ipCidrRange='192.168.64.0/24'),
        self.messages.SubnetworkSecondaryRange(
            rangeName='range3', ipCidrRange='192.168.125.0/24'),
    ]

    self.CheckRequests([
        (self.compute.subnetworks, 'Get',
         self.messages.ComputeSubnetworksGetRequest(
             project='my-project', region='us-central2',
             subnetwork='subnet-1')),
    ], [(self.compute.subnetworks, 'Patch',
         self.messages.ComputeSubnetworksPatchRequest(
             project='my-project',
             region='us-central2',
             subnetwork='subnet-1',
             subnetworkResource=subnetwork_resource))])

  def testAddSecondaryRangesToExisting(self):
    subnetwork_resource = {
        'name':
            'subnetwork-1',
        'network': ('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/default'),
        'secondaryIpRanges': [
            self.messages.SubnetworkSecondaryRange(
                rangeName='range1', ipCidrRange='192.168.0.0/24')
        ]
    }
    self.make_requests.side_effect = iter([
        [self.messages.Subnetwork(**subnetwork_resource)],
        [],
    ])

    self.Run("""
        compute networks subnets update subnet-1
          --add-secondary-ranges range2=192.168.64.0/24,range3=192.168.125.0/24
          --region us-central2
        """)
    subnetwork_resource['secondaryIpRanges'] = [
        self.messages.SubnetworkSecondaryRange(
            rangeName='range1', ipCidrRange='192.168.0.0/24'),
        self.messages.SubnetworkSecondaryRange(
            rangeName='range2', ipCidrRange='192.168.64.0/24'),
        self.messages.SubnetworkSecondaryRange(
            rangeName='range3', ipCidrRange='192.168.125.0/24'),
    ]

    self.CheckRequests([
        (self.compute.subnetworks, 'Get',
         self.messages.ComputeSubnetworksGetRequest(
             project='my-project', region='us-central2',
             subnetwork='subnet-1')),
    ], [(self.compute.subnetworks, 'Patch',
         self.messages.ComputeSubnetworksPatchRequest(
             project='my-project',
             region='us-central2',
             subnetwork='subnet-1',
             subnetworkResource=subnetwork_resource))])

  def testAddSecondaryRangeSameName(self):
    """Tests adding secondary ranges."""
    subnetwork_resource = {
        'name':
            'subnetwork-1',
        'network': ('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/default'),
        'secondaryIpRanges': [
            self.messages.SubnetworkSecondaryRange(
                rangeName='range1', ipCidrRange='192.168.0.0/24')
        ]
    }
    self.make_requests.side_effect = iter([
        [self.messages.Subnetwork(**subnetwork_resource)],
        [],
    ])

    # We expect the real API to reject this, but it's important to verify that
    # we do something reasonable, rather than e.g. silently overwriting
    # one of the range specs.
    self.Run("""
        compute networks subnets update subnet-1
          --add-secondary-ranges range1=192.168.64.0/24,range3=192.168.125.0/24
          --region us-central2
        """)
    subnetwork_resource['secondaryIpRanges'] = [
        self.messages.SubnetworkSecondaryRange(
            rangeName='range1', ipCidrRange='192.168.0.0/24'),
        self.messages.SubnetworkSecondaryRange(
            rangeName='range1', ipCidrRange='192.168.64.0/24'),
        self.messages.SubnetworkSecondaryRange(
            rangeName='range3', ipCidrRange='192.168.125.0/24'),
    ]

    self.CheckRequests([
        (self.compute.subnetworks, 'Get',
         self.messages.ComputeSubnetworksGetRequest(
             project='my-project', region='us-central2',
             subnetwork='subnet-1')),
    ], [(self.compute.subnetworks, 'Patch',
         self.messages.ComputeSubnetworksPatchRequest(
             project='my-project',
             region='us-central2',
             subnetwork='subnet-1',
             subnetworkResource=subnetwork_resource))])

  def testRemoveSecondaryRanges(self):
    subnetwork_resource = {
        'name':
            'subnetwork-1',
        'network': ('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/default'),
        'secondaryIpRanges': [
            self.messages.SubnetworkSecondaryRange(
                rangeName='range1', ipCidrRange='192.168.0.0/24'),
            self.messages.SubnetworkSecondaryRange(
                rangeName='range2', ipCidrRange='192.168.64.0/24'),
            self.messages.SubnetworkSecondaryRange(
                rangeName='range3', ipCidrRange='192.168.111.0/24'),
        ]
    }
    self.make_requests.side_effect = iter([
        [self.messages.Subnetwork(**subnetwork_resource)],
        [],
    ])

    self.Run("""
        compute networks subnets update subnet-1
          --remove-secondary-ranges range1,range3
          --region us-central2
        """)
    subnetwork_resource['secondaryIpRanges'] = [
        self.messages.SubnetworkSecondaryRange(
            rangeName='range2', ipCidrRange='192.168.64.0/24'),
    ]

    self.CheckRequests([
        (self.compute.subnetworks, 'Get',
         self.messages.ComputeSubnetworksGetRequest(
             project='my-project', region='us-central2',
             subnetwork='subnet-1')),
    ], [(self.compute.subnetworks, 'Patch',
         self.messages.ComputeSubnetworksPatchRequest(
             project='my-project',
             region='us-central2',
             subnetwork='subnet-1',
             subnetworkResource=subnetwork_resource))])

  def testRemoveAllSecondaryRanges(self):
    subnetwork_resource = {
        'name':
            'subnetwork-1',
        'network': ('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/default'),
        'secondaryIpRanges': [
            self.messages.SubnetworkSecondaryRange(
                rangeName='range1', ipCidrRange='192.168.0.0/24'),
            self.messages.SubnetworkSecondaryRange(
                rangeName='range2', ipCidrRange='192.168.64.0/24'),
            self.messages.SubnetworkSecondaryRange(
                rangeName='range3', ipCidrRange='192.168.111.0/24'),
        ]
    }
    self.make_requests.side_effect = iter([
        [self.messages.Subnetwork(**subnetwork_resource)],
        [],
    ])

    self.Run("""
        compute networks subnets update subnet-1
          --remove-secondary-ranges range1,range2,range3
          --region us-central2
        """)
    subnetwork_resource['secondaryIpRanges'] = []

    self.CheckRequests([
        (self.compute.subnetworks, 'Get',
         self.messages.ComputeSubnetworksGetRequest(
             project='my-project', region='us-central2',
             subnetwork='subnet-1')),
    ], [(self.compute.subnetworks, 'Patch',
         self.messages.ComputeSubnetworksPatchRequest(
             project='my-project',
             region='us-central2',
             subnetwork='subnet-1',
             subnetworkResource=subnetwork_resource))])

  def testRemoveInvalidSecondaryRange(self):
    subnetwork_resource = {
        'name':
            'subnetwork-1',
        'network': ('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/default'),
        'secondaryIpRanges': [
            self.messages.SubnetworkSecondaryRange(
                rangeName='range1', ipCidrRange='192.168.0.0/24'),
        ]
    }
    self.make_requests.side_effect = iter([
        [self.messages.Subnetwork(**subnetwork_resource)],
        [],
    ])
    with self.assertRaisesRegex(calliope_exceptions.UnknownArgumentException,
                                r'Subnetwork does not have a range range9'):
      self.Run("""
          compute networks subnets update subnet-1
            --remove-secondary-ranges range1,range9
            --region us-central2
          """)


class SubnetsUpdateTestBeta(SubnetsUpdateTest, parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')

  @parameterized.named_parameters(('Enabled', '--enable-flow-logs', True),
                                  ('Disabled', '--no-enable-flow-logs', False))
  def testToggleEnableFlowLogs(self, enable_flow_logs_flag, enable_flow_logs):
    """Tests toggling enableFlowLogs on a subnet."""
    subnetwork_resource = {
        'name':
            'subnetwork-1',
        'network': ('https://www.googleapis.com/compute/v1/projects/'
                    'my-project/global/networks/default'),
    }
    self.make_requests.side_effect = iter([
        [self.messages.Subnetwork(**subnetwork_resource)],
        [],
    ])

    self.Run("""
        compute networks subnets update subnet-1
          {0} --region us-central2
        """.format(enable_flow_logs_flag))

    subnetwork_resource['enableFlowLogs'] = enable_flow_logs

    self.CheckRequests([
        (self.compute.subnetworks, 'Get',
         self.messages.ComputeSubnetworksGetRequest(
             project='my-project', region='us-central2',
             subnetwork='subnet-1')),
    ], [(self.compute.subnetworks, 'Patch',
         self.messages.ComputeSubnetworksPatchRequest(
             project='my-project',
             region='us-central2',
             subnetwork='subnet-1',
             subnetworkResource=subnetwork_resource))])


class SubnetsUpdateTestAlpha(SubnetsUpdateTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')


if __name__ == '__main__':
  test_case.main()
