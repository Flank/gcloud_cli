# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the forwarding-rules create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute.forwarding_rules import create_test_base


class RegionalForwardingRulesCreateTest(
    create_test_base.ForwardingRulesCreateTestBase):

  def SetUp(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)

  def testSimpleCaseWithRegion(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testIpAddressOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --address 162.222.178.83
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                IPAddress='162.222.178.83',
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testIpAddressResource(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --address foo
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                IPAddress=(
                    '{compute_uri}/projects/my-project/regions/us-central2/'
                    'addresses/foo').format(compute_uri=self.compute_uri),
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testIpAddressURI(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --address {compute_uri}/projects/my-project/regions/us-central2/addresses/foo
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                IPAddress=(
                    '{compute_uri}/projects/my-project/regions/us-central2/'
                    'addresses/foo').format(compute_uri=self.compute_uri),
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testIpProtocolOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --ip-protocol TCP
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                IPProtocol=(
                    self.messages.ForwardingRule.IPProtocolValueValuesEnum.TCP),
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testIcmpProtocolOption(self):
    self.SelectApi('alpha')
    self.Run("""
        alpha compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --ip-protocol ICMP
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                IPProtocol=(self.messages.ForwardingRule
                            .IPProtocolValueValuesEnum.ICMP),
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)
    self.SelectApi('v1')

  def testIpProtocolOptionWithIllegalProtocol(self):
    with self.AssertRaisesArgumentErrorMatches(
        "argument --ip-protocol: Invalid choice: 'TCPTCP'"):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-central2
            --target-pool target-pool-1
            --ip-protocol TCPTCP
          """)

    self.CheckRequests()

  def testPortRangeOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --ports 1-1000
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                portRange='1-1000',
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testDeprecatedPortRangeOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --port-range 1-1000
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                portRange='1-1000',
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)
    self.AssertErrEquals('WARNING: The --port-range flag is deprecated. '
                         'Use equivalent --ports=1-1000 flag.\n')

  def testDescriptionOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --description hello
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                description='hello',
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testTargetInstanceOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-instance target-instance-1
          --target-instance-zone us-central2-a
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/zones/us-central2-a/'
                        'targetInstances/target-instance-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testTargetInstanceZoneWithoutInstanceOption(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--target-instance-zone\] unless you are '
        r'specifying \[--target-instance\].'):
      self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --target-instance-zone us-central2-a
          """)
    self.CheckRequests()

  def testWithConflictingContext(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--backend-service | --target-http-proxy | '
        '--target-https-proxy | --target-instance | --target-pool | '
        '--target-ssl-proxy | --target-tcp-proxy | --target-vpn-gateway) '
        'must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-central2
            --global
          """)
    self.CheckRequests()

  def testTargetPoolUriSupport(self):
    self.Run("""
        compute forwarding-rules create {compute_uri}/projects/my-project/regions/us-central2/forwardingRules/forwarding-rule-1
          --target-pool {compute_uri}/projects/my-project/regions/us-central2/targetPools/target-pool-1
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testTargetInstanceUriSupport(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-instance {compute_uri}/projects/my-project/zones/us-central2-a/targetInstances/target-instance-1
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/zones/us-central2-a/'
                        'targetInstances/target-instance-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testTargetInstanceZoneUriSupport(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-instance target-instance-1
          --target-instance-zone {compute_uri}/projects/my-project/zones/us-central2-a
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/zones/us-central2-a/'
                        'targetInstances/target-instance-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testRegionalPrompting(self):
    self.WriteInput('3\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2'),
        ],
        [],
    ])
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --target-pool target-pool-1
        """)

    self.CheckRequests(
        self.regions_list_request,
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],
    )
    self.AssertErrContains('forwarding rule')
    self.AssertErrContains('forwarding-rule-1')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')

  def testZonalPromptingForTargetInstance(self):
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='us-central2-a'),
            self.messages.Zone(name='us-central2-b'),
        ],
        [],
    ])
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --target-instance target-instance-1
          --region us-central2
        """)

    self.CheckRequests(
        self.filtered_zones_list_request,
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/zones/us-central2-b/'
                      'targetInstances/target-instance-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],
    )
    self.AssertErrContains('target instance:')
    self.AssertErrContains('target-instance-1')
    self.AssertErrContains('us-central2-a')
    self.AssertErrContains('us-central2-b')

  def testPromptingErrorForTargetInstance(self):
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        'Unable to fetch a list of zones. Specifying '
        r'\[--target-instance-zone\] may fix this issue.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-central2
            --target-instance target-instance-1
          """)

    self.CheckRequests(self.filtered_zones_list_request,)

  def testDefaultUsedForTargetInstanceZone(self):
    properties.VALUES.compute.zone.Set('us-central2-b')
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --target-instance target-instance-1
          --region us-central2
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/zones/us-central2-b/'
                        'targetInstances/target-instance-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testSimpleTargetVpnGateway(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-vpn-gateway target-vpn-gateway-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(self.compute_uri + '/projects/'
                          'my-project/regions/us-central2/targetVpnGateways/'
                          'target-vpn-gateway-1'),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testMutuallyExclusiveTargetInstanceWithTargetVpnGateway(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-instance: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-instance target-instance-1
            --ports 80
            --target-vpn-gateway target-vpn-gateway1
          """)

  def testInstanceRegionalWithPorts(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --ports 80-82,85
          --load-balancing-scheme internal
          --target-instance target-instance-1
          --target-instance-zone us-central2-a
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/zones/us-central2-a/'
                        'targetInstances/target-instance-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.INTERNAL,
                ports=['80', '81', '82', '85']),
            project='my-project',
            region='us-central2'))],)

  def testInstanceRegionalWithPortRange(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --port-range 80-82
          --target-instance target-instance-1
          --target-instance-zone us-central2-a
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/zones/us-central2-a/'
                        'targetInstances/target-instance-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL,
                portRange='80-82'),
            project='my-project',
            region='us-central2'))],)


class RegionalForwardingRulesCreateAlphaTest(
    create_test_base.ForwardingRulesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def SetUp(self):
    properties.VALUES.core.check_gce_metadata.Set(False)

  def testL7IlbForwardingRuleWithTargetHttpProxy(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --region region1
                --ports 80,81-82
                --network default
                --subnet default
                --target-http-proxy proxy1
                --target-http-proxy-region region1
                --load-balancing-scheme internal""")

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ports=['80', '81', '82'],
                  network=(
                      '{0}/projects/my-project/global/networks/default'.format(
                          self.compute_uri)),
                  subnetwork=('{0}/projects/my-project/regions/region1/'
                              'subnetworks/default'.format(self.compute_uri)),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.INTERNAL,
                  target='https://compute.googleapis.com/compute/alpha/'
                  'projects/my-project/regions/region1/targetHttpProxies/'
                  'proxy1'),
              project='my-project',
              region='region1'))],)

  def testL7IlbForwardingRuleWithRegionTargetHttpsProxy(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
            --region region1
            --ports 80,81-82
            --network default
            --subnet default
            --target-https-proxy proxy1
            --target-https-proxy-region region1
            --load-balancing-scheme internal""")

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ports=['80', '81', '82'],
                  network=(
                      '{0}/projects/my-project/global/networks/default'.format(
                          self.compute_uri)),
                  subnetwork=('{0}/projects/my-project/regions/region1/'
                              'subnetworks/default'.format(self.compute_uri)),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.INTERNAL,
                  target='https://compute.googleapis.com/compute/alpha/'
                  'projects/my-project/regions/region1/targetHttpsProxies/'
                  'proxy1'),
              project='my-project',
              region='region1'))],)


if __name__ == '__main__':
  test_case.main()
