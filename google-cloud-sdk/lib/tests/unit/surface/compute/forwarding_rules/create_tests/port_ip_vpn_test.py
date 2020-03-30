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


class IpVersionTest(create_test_base.ForwardingRulesCreateTestBase):

  def SetUp(self):
    properties.VALUES.core.check_gce_metadata.Set(False)

  def testSimpleCaseWithGlobalTargetTcpProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-tcp-proxy target-tcp-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                  portRange='443',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetTcpProxies/'
                          'target-tcp-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)


class VpnTestsBeta(create_test_base.ForwardingRulesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

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

    self.CheckRequests()


class CreateWithIPVersionApiTest(create_test_base.ForwardingRulesCreateTestBase
                                ):

  def RunCreate(self, command):
    self.Run('compute forwarding-rules create %s' % command)

  # When no --ip-version specified, default value of IPV4 should be specified.
  def testDefault(self):
    messages = self.messages

    self.RunCreate("""
        forwarding-rule-1
          --description my-forwarding-rule
          --global
          --target-http-proxy target-http-proxy-1
          --ports 8080
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  description='my-forwarding-rule',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testIPv4(self):
    messages = self.messages

    self.RunCreate("""
        forwarding-rule-1
          --description my-forwarding-rule
          --global
          --ip-version ipv4
          --target-http-proxy target-http-proxy-1
          --ports 8080
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  description='my-forwarding-rule',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testIPv6(self):
    messages = self.messages

    self.RunCreate("""
        forwarding-rule-1
          --description my-forwarding-rule
          --global
          --ip-version ipV6
          --target-http-proxy target-http-proxy-1
          --ports 8080
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  description='my-forwarding-rule',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV6),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testWithAddressFlag(self):
    self.RunCreate("""
        forwarding-rule-1
          --description my-forwarding-rule
          --global
          --target-http-proxy target-http-proxy-1
          --ports 8080
          --address 23.251.146.189
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  description='my-forwarding-rule',
                  IPAddress='23.251.146.189',
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)


class FlexPortApiTestGA(create_test_base.ForwardingRulesCreateTestBase):

  def testFlexPortWithBackendService(self):
    """Tests all ports support in internal load balancing."""
    self.Run("""
      compute forwarding-rules create forwarding-rule-1
        --load-balancing-scheme internal
        --region us-central1
        --backend-service bs-1
        --ports all
    """)
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  backendService=(
                      '{compute_uri}/projects/my-project/regions/us-central1/'
                      'backendServices/bs-1').format(
                          compute_uri=self.compute_uri),
                  allPorts=True,
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.INTERNAL),
              project='my-project',
              region='us-central1'))],)

  def testAllPortWithNetworkLoadBalance(self):
    """Tests all ports support in regional external load balancing."""
    self.Run("""
      compute forwarding-rules create forwarding-rule-1
        --load-balancing-scheme external
        --region us-central1
        --target-pool tp-1
        --ports all
    """)
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central1/'
                      'targetPools/tp-1').format(compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central1'))],)

  def testGlobalNotSupportAllPorts(self):
    """Tests all ports not to be supported in global load balancing."""
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--ports\] can not be specified to all for global forwarding '
        r'rules.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --global
            --target-http-proxy target-http-proxy-1
            --ports all
          """)

    self.CheckRequests()

  def testAllPortWithOtherPorts(self):
    """Tests all ports can not be combined with other port ranges."""
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --ports: Expected a non-negative integer value or a range '
        r'of such values instead of "all"'):
      self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --load-balancing-scheme internal
          --region us-central1
          --backend-service bs-1
          --ports all,8000-10000
          """)


class FlexPortApiTestBeta(FlexPortApiTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class FlexPortApiTestAlpha(FlexPortApiTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
