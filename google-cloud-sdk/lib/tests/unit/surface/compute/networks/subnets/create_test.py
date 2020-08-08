# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

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
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False),
              region='us-central1',
              project='my-project'))],)

  def testDescription(self):
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1 --description "haha"
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
                  privateIpGoogleAccess=False),
              region='us-central1',
              project='my-project'))],)

  def testRegionalPrompting(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
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
        [(self.compute.subnetworks, 'Insert',
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

    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["region-1 (DEPRECATED)", "region-2", "region-3"]')

  def testCreateWithGoogleAccessEnabled(self):
    """Test creating a subnet with privateIpGoogleAccess enabled."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --enable-private-ip-google-access
        """)

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=True),
              region='us-central1',
              project='my-project'))],)

  def testCreateWithGoogleAccessDisabled(self):
    """Test creating a subnet with privateIpGoogleAccess disabled."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --no-enable-private-ip-google-access
        """)

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False),
              region='us-central1',
              project='my-project'))],)

  def testCreateWithoutGoogleAccess(self):
    """Test creating a subnet with no value given for privateIpGoogleAccess."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        """)

    # The subnet create request should use the default value of False for
    # privateIpGoogleAccess.
    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False),
              region='us-central1',
              project='my-project'))],)

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

    log_config = self.messages.SubnetworkLogConfig(
        enable=enable_flow_logs) if enable_flow_logs is not None else None
    subnetwork = self.messages.Subnetwork(
        name='my-subnet',
        network=self.compute_uri +
        '/projects/my-project/global/networks/my-network',
        ipCidrRange='10.240.0.0/16',
        privateIpGoogleAccess=False,
        logConfig=log_config)
    self.CheckRequests([
        (self.compute.subnetworks, 'Insert',
         self.messages.ComputeSubnetworksInsertRequest(
             subnetwork=subnetwork, region='us-central1', project='my-project'))
    ],)

  def testCreateWithFlowLogsAggregationAndSampling(self):
    """Test creating a subnet with enableFlowLogs in various states."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1 --enable-flow-logs
        --logging-aggregation-interval interval-10-min
        --logging-flow-sampling 0.7 --logging-metadata exclude-all
        """)

    self.CheckRequests([
        (self.compute.subnetworks, 'Insert',
         self.messages.ComputeSubnetworksInsertRequest(
             subnetwork=self.messages.Subnetwork(
                 name='my-subnet',
                 network=self.compute_uri +
                 '/projects/my-project/global/networks/my-network',
                 ipCidrRange='10.240.0.0/16',
                 privateIpGoogleAccess=False,
                 logConfig=self.messages.SubnetworkLogConfig(
                     enable=True,
                     aggregationInterval=(
                         self.messages.SubnetworkLogConfig
                         .AggregationIntervalValueValuesEnum.INTERVAL_10_MIN),
                     flowSampling=0.7,
                     metadata=(self.messages.SubnetworkLogConfig
                               .MetadataValueValuesEnum.EXCLUDE_ALL_METADATA))),
             region='us-central1',
             project='my-project'))
    ],)

  def testCreateWithFlowLogsFilterExpr(self):
    """Test creating a subnet with a filter expr for flow logs."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1 --enable-flow-logs
        --logging-filter-expr 'src_location.asn != 36647'
        """)

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False,
                  logConfig=self.messages.SubnetworkLogConfig(
                      enable=True, filterExpr='src_location.asn != 36647')),
              region='us-central1',
              project='my-project'))],)

  def testCreateWithFlowLogsCustomMetadata(self):
    """Test creating a subnet with custom metadata fields for flow logs."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1 --enable-flow-logs
        --logging-metadata custom --logging-metadata-fields
         'src_instance,dest_instance'
        """)

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False,
                  logConfig=self.messages.SubnetworkLogConfig(
                      enable=True,
                      metadata=(self.messages.SubnetworkLogConfig
                                .MetadataValueValuesEnum.CUSTOM_METADATA),
                      metadataFields=['src_instance', 'dest_instance'])),
              region='us-central1',
              project='my-project'))],)

  def testCreateWithPrivateIpv6GoogleAccessDisable(self):
    """Test creating a subnet with DISABLE_GOOGLE_ACCESS private ipv6 access."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --private-ipv6-google-access-type disable
        """)

    self.CheckRequests([
        (self.compute.subnetworks, 'Insert',
         self.messages.ComputeSubnetworksInsertRequest(
             subnetwork=self.messages.Subnetwork(
                 name='my-subnet',
                 network=self.compute_uri +
                 '/projects/my-project/global/networks/my-network',
                 ipCidrRange='10.240.0.0/16',
                 privateIpGoogleAccess=False,
                 privateIpv6GoogleAccess=(self.messages.Subnetwork.
                                          PrivateIpv6GoogleAccessValueValuesEnum
                                          .DISABLE_GOOGLE_ACCESS)),
             region='us-central1',
             project='my-project'))
    ],)

  def testCreateWithPrivateIpv6GoogleAccessEnableOutbound(self):
    """Test creating a subnet with ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE private ipv6 access."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --private-ipv6-google-access-type enable-outbound-vm-access
        """)

    self.CheckRequests([(
        self.compute.subnetworks, 'Insert',
        self.messages.ComputeSubnetworksInsertRequest(
            subnetwork=self.messages.Subnetwork(
                name='my-subnet',
                network=self.compute_uri +
                '/projects/my-project/global/networks/my-network',
                ipCidrRange='10.240.0.0/16',
                privateIpGoogleAccess=False,
                privateIpv6GoogleAccess=(self.messages.Subnetwork
                                         .PrivateIpv6GoogleAccessValueValuesEnum
                                         .ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE)),
            region='us-central1',
            project='my-project'))],)

  def testCreateWithPrivateIpv6GoogleAccessEnableBidirectional(self):
    """Test creating a subnet with ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE private ipv6 access."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --private-ipv6-google-access-type enable-bidirectional-access
        """)

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False,
                  privateIpv6GoogleAccess=(
                      self.messages.Subnetwork
                      .PrivateIpv6GoogleAccessValueValuesEnum
                      .ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE)),
              region='us-central1',
              project='my-project'))],)


class SubnetsCreateTestBeta(SubnetsCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')


class SubnetsCreateTestAlpha(SubnetsCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')

  def testCreateWithFlowLogsAggregationAndSampling(self):
    """Test creating a subnet with enableFlowLogs in various states."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1 --enable-flow-logs
        --aggregation-interval interval-10-min
        --flow-sampling 0.7 --metadata exclude-all-metadata
        """)

    self.CheckRequests([
        (self.compute.subnetworks, 'Insert',
         self.messages.ComputeSubnetworksInsertRequest(
             subnetwork=self.messages.Subnetwork(
                 name='my-subnet',
                 network=self.compute_uri +
                 '/projects/my-project/global/networks/my-network',
                 ipCidrRange='10.240.0.0/16',
                 privateIpGoogleAccess=False,
                 logConfig=self.messages.SubnetworkLogConfig(
                     enable=True,
                     aggregationInterval=(
                         self.messages.SubnetworkLogConfig
                         .AggregationIntervalValueValuesEnum.INTERVAL_10_MIN),
                     flowSampling=0.7,
                     metadata=(self.messages.SubnetworkLogConfig
                               .MetadataValueValuesEnum.EXCLUDE_ALL_METADATA))),
             region='us-central1',
             project='my-project'))
    ],)


class SubnetsCreateAggregateRangesAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')

  def testCreateWithPurposeAggregate(self):
    """Test to create an aggregate subnetwork."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --purpose aggregate
        """)
    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  purpose=self.messages.Subnetwork.PurposeValueValuesEnum
                  .AGGREGATE),
              region='us-central1',
              project='my-project'))],)


class SubnetsCreateInternalHttpsLoadBalancerTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateWithPurposeAndRole(self):
    """Test creating a subnet with privateIpGoogleAccess disabled."""
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --purpose internal-https-load-balancer --role active
        """)

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  purpose=self.messages.Subnetwork.PurposeValueValuesEnum
                  .INTERNAL_HTTPS_LOAD_BALANCER,
                  role=self.messages.Subnetwork.RoleValueValuesEnum.ACTIVE),
              region='us-central1',
              project='my-project'))],)

  def testCreateWithPurposeAndNoRole(self):
    self.Run("""
        compute networks subnets create my-subnet --network my-network
        --range 10.240.0.0/16 --region us-central1
        --purpose private
        """)

    self.CheckRequests(
        [(self.compute.subnetworks, 'Insert',
          self.messages.ComputeSubnetworksInsertRequest(
              subnetwork=self.messages.Subnetwork(
                  name='my-subnet',
                  network=self.compute_uri +
                  '/projects/my-project/global/networks/my-network',
                  ipCidrRange='10.240.0.0/16',
                  privateIpGoogleAccess=False,
                  purpose=self.messages.Subnetwork.PurposeValueValuesEnum
                  .PRIVATE),
              region='us-central1',
              project='my-project'))],)


class SubnetsCreateInternalHttpsLoadBalancerBetaTest(
    SubnetsCreateInternalHttpsLoadBalancerTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')


class SubnetsCreateInternalHttpsLoadBalancerAlphaTest(
    SubnetsCreateInternalHttpsLoadBalancerBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')


if __name__ == '__main__':
  test_case.main()
