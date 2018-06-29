# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the instances move subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class SubnetsCreateTest(test_base.BaseTest, parameterized.TestCase):

  def testSimple(self):
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        """)

    self.CheckRequests(
        [(self.compute.subnetworks,
          'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False),
              region='us-central1',
              project='my-project'))],
    )

  def testDescription(self):
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1 --description "haha"
        """)

    self.CheckRequests(
        [(self.compute.subnetworks,
          'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  description='haha',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False),
              region='us-central1',
              project='my-project'))],
    )

  def testRegionalPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        test_resources.REGIONS,
        [],
    ])
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16
        """)

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute.subnetworks,
          'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False),
              project='my-project',
              region='region-2'))],
    )

    self.AssertErrContains(textwrap.dedent("""\
        For the following subnetwork:
         - [my-subnet]
        choose a region:
         [1] region-1 (DEPRECATED)
         [2] region-2
         [3] region-3
        Please enter your numeric choice:  \n"""))

  def testCreateWithGoogleAccessEnabled(self):
    """Test creating a subnet with privateIpGoogleAccess enabled."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --enable-private-ip-google-access
        """)

    self.CheckRequests(
        [(self.compute.subnetworks,
          'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=True),
              region='us-central1',
              project='my-project'))],
    )

  def testCreateWithGoogleAccessDisabled(self):
    """Test creating a subnet with privateIpGoogleAccess disabled."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --no-enable-private-ip-google-access
        """)

    self.CheckRequests(
        [(self.compute.subnetworks,
          'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False),
              region='us-central1',
              project='my-project'))],
    )

  def testCreateWithoutGoogleAccess(self):
    """Test creating a subnet with no value given for privateIpGoogleAccess."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        """)

    # The subnet create request should use the default value of False for
    # privateIpGoogleAccess.
    self.CheckRequests(
        [(self.compute.subnetworks,
          'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False),
              region='us-central1',
              project='my-project'))],
    )

  def testSecondaryRanges(self):
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1 --description "haha"
        --secondary-range "cool-range=10.241.0.0/24,long-range=10.243.0.0/16"
        --secondary-range "tiny-range=10.242.0.0/31"
        """)

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  description='haha',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False,
                  secondaryIpRanges=[
                      self.messages.SubnetworkSecondaryRange(
                          rangeName='cool-range', ipCidrRange='10.241.0.0/24'),
                      self.messages.SubnetworkSecondaryRange(
                          rangeName='long-range', ipCidrRange='10.243.0.0/16'),
                      self.messages.SubnetworkSecondaryRange(
                          rangeName='tiny-range', ipCidrRange='10.242.0.0/31'),
                  ]),
              region='us-central1',
              project='my-project'))],)

  @parameterized.named_parameters(('Enabled', '--enable-flow-logs', True),
                                  ('Disabled', '--no-enable-flow-logs', False),
                                  ('NotSpecified', '', None))
  def testCreateWithEnableFlowLogs(self, enable_flow_logs_flag,
                                   enable_flow_logs):
    """Test creating a subnet with enableFlowLogs in various states."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1 {0}
        """.format(enable_flow_logs_flag))

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False,
                  enableFlowLogs=enable_flow_logs),
              region='us-central1',
              project='my-project'))],)


class SubnetsCreateTestBeta(SubnetsCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')


class SubnetsCreateTestAlpha(SubnetsCreateTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')


if __name__ == '__main__':
  test_case.main()
