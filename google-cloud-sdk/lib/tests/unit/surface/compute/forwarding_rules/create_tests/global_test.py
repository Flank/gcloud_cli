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
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.forwarding_rules import create_test_base


class GlobalForwardingRulesCreateTest(
    create_test_base.ForwardingRulesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'
    self.internal_self_managed_target_msg = (
        r'You must specify either \[--target-http-proxy\] or '
        r'\[--target-https-proxy\] for an INTERNAL_SELF_MANAGED '
        r'\[--load-balancing-scheme\].')
    self.exactly_one_target_msg = (
        'Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.')

  def testGlobalMutuallyExclusiveWithTargetInstance(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--target-instance\] for a global '
        'forwarding rule.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --global
            --ports 80
            --target-instance target-instance-1
          """)

    self.CheckRequests()

  def testGlobalMutuallyExclusiveWithTargetPool(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--target-pool\] for a global '
        'forwarding rule.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --global
            --ports 80
            --target-pool target-instance-1
          """)

    self.CheckRequests()

  def testMutuallyExclusiveTargetPoolTargetInstance(self):
    with self.AssertRaisesArgumentErrorMatches('argument --target-instance: ' +
                                               self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-pool target-pool-1
            --ports 80
            --target-instance target-instance-1
          """)

    self.CheckRequests()

  def testMutuallyExclusiveTargetInstanceTargetHttpProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-http-proxy: ' + self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-instance target-instance-1
            --ports 80
            --target-http-proxy target-http-proxy-1
          """)

    self.CheckRequests()

  def testRegionGlobalFlagsMutuallyExclusive(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --region '
        'may be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-pool target-pool-1
            --region us-central1
            --ports 80
            --global
          """)

    self.CheckRequests()

  def testSimpleCaseWithGlobalTargetHttpProxy(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-http-proxy target-http-proxy-1
        """)

    self.CheckRequests([(
        self.compute.globalForwardingRules, 'Insert',
        self.messages.ComputeGlobalForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                ipVersion=(
                    self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                portRange='8080',
                target=('{compute_uri}/projects/my-project/global/'
                        'targetHttpProxies/target-http-proxy-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project'))],)

  def testSimpleCaseWithGlobalTargetHttpProxyEsp(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-http-proxy target-http-proxy-1
          --ip-protocol ESP
        """)

    self.CheckRequests([(
        self.compute.globalForwardingRules, 'Insert',
        self.messages.ComputeGlobalForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                ipVersion=(
                    self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                portRange='8080',
                IPProtocol=(self.messages.ForwardingRule
                            .IPProtocolValueValuesEnum('ESP')),
                target=('{compute_uri}/projects/my-project/global/'
                        'targetHttpProxies/target-http-proxy-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project'))],)

  def testSimpleCaseWithGlobalTargetHttpProxyUdp(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-http-proxy target-http-proxy-1
          --ip-protocol UDP
        """)

    self.CheckRequests([(
        self.compute.globalForwardingRules, 'Insert',
        self.messages.ComputeGlobalForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                ipVersion=(
                    self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                portRange='8080',
                IPProtocol=(self.messages.ForwardingRule
                            .IPProtocolValueValuesEnum('UDP')),
                target=('{compute_uri}/projects/my-project/global/'
                        'targetHttpProxies/target-http-proxy-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project'))],)

  def testGlobalRequiresPorts(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--ports\] is required for global forwarding rules'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --global
            --target-http-proxy target-http-proxy-1
          """)

    self.CheckRequests()

  def testHttpProxyUriSupport(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-http-proxy {compute_uri}/projects/my-project/global/targetHttpProxies/target-http-proxy-1
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests([(
        self.compute.globalForwardingRules, 'Insert',
        self.messages.ComputeGlobalForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                ipVersion=(
                    self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                portRange='8080',
                target=('{compute_uri}/projects/my-project/global/'
                        'targetHttpProxies/target-http-proxy-1').format(
                            compute_uri=self.compute_uri),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project'))],)

  def testSimpleCaseWithGlobalTargetHttpsProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-https-proxy target-https-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                  portRange='8080',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetHttpsProxies/'
                          'target-https-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testHttpsProxyUriSupport(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-https-proxy {uri}/projects/my-project/global/targetHttpsProxies/target-https-proxy-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                  portRange='8080',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetHttpsProxies/'
                          'target-https-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testMutuallyExclusiveTargetHttpProxyTargetHttpsProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-http-proxy: ' + self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 80
            --target-http-proxy target-http-proxy-1
            --target-https-proxy target-https-proxy-1
          """)

  def testSimpleCaseWithGlobalTargetSslProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-ssl-proxy target-ssl-proxy-1
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
                          'my-project/global/targetSslProxies/'
                          'target-ssl-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testSslProxyUriSupport(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-ssl-proxy
          {uri}/projects/my-project/global/targetSslProxies/target-ssl-proxy-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
                  portRange='443',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetSslProxies/'
                          'target-ssl-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testMutuallyExclusiveTargetHttpProxyTargetSslProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-http-proxy: ' + self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-http-proxy target-http-proxy-1
            --target-ssl-proxy target-ssl-proxy-1
          """)

  def testMutuallyExclusiveTargetHttpsProxyTargetSslProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-https-proxy: ' + self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-https-proxy target-https-proxy-1
            --target-ssl-proxy target-ssl-proxy-1
          """)

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

  def testTcpProxyUriSupport(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-tcp-proxy
          {uri}/projects/my-project/global/targetTcpProxies/target-ssl-proxy-1
        """.format(uri=self.compute_uri))

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
                          'target-ssl-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testMutuallyExclusiveTargetHttpProxyTargetTcpProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-http-proxy: ' + self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-http-proxy target-http-proxy-1
            --target-tcp-proxy target-tcp-proxy-1
          """)

  def testMutuallyExclusiveTargetHttpsProxyTargetTcpProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-https-proxy: ' + self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-https-proxy target-https-proxy-1
            --target-tcp-proxy target-tcp-proxy-1
          """)

  def testMutuallyExclusiveTargetSslProxyTargetTcpProxy(self):
    with self.AssertRaisesArgumentErrorMatches('argument --target-ssl-proxy: ' +
                                               self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-ssl-proxy target-ssl-proxy-1
            --target-tcp-proxy target-tcp-proxy-1
          """)

  def testIpAddressGlobalResource(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --target-http-proxy target-proxy-1
          --ports 8080
          --address foo
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/global/addresses/foo'
                  ).format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-proxy-1').format(
                              compute_uri=self.compute_uri),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testIpAddressGlobalURI(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --target-http-proxy target-proxy-1
          --ports 8080
          --address {compute_uri}/projects/my-project/global/addresses/foo
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/global/addresses/foo'
                  ).format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-proxy-1').format(
                              compute_uri=self.compute_uri),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testInternalLoadBalancingWithInvalidTarget(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--load-balancing-scheme]: Only target instances '
        'and backend services should be specified as a target for internal '
        'load balancing.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --load-balancing-scheme internal
            --target-pool target-pool-1
            --region us-central1
            --ports 80
            --network my-network
            --subnet my-subnet
          """)

    self.CheckRequests()

  def testInternalSelfManagedWithTargetHttpProxy(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --address {compute_uri}/projects/my-project/global/addresses/foo
          --target-http-proxy target-proxy-1
          --network network1
          --ports 80-80
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/global/addresses/foo'
                  ).format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-proxy-1').format(
                              compute_uri=self.compute_uri),
                  network=('{compute_uri}/projects/my-project/global/networks/'
                           'network1'.format(compute_uri=self.compute_uri)),
                  portRange='80',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.INTERNAL_SELF_MANAGED),
              project='my-project'))],)

  def testInternalSelfManagedWithTargetHttpsProxy(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --address {compute_uri}/projects/my-project/global/addresses/foo
          --target-https-proxy target-proxy-1
          --network network1
          --ports 80-80
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/global/addresses/foo'
                  ).format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpsProxies/target-proxy-1').format(
                              compute_uri=self.compute_uri),
                  network=('{compute_uri}/projects/my-project/global/networks/'
                           'network1'.format(compute_uri=self.compute_uri)),
                  portRange='80',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.INTERNAL_SELF_MANAGED),
              project='my-project'))],)

  def testInternalSelfManagedWithTargetTcpProxyFails(self):
    with self.AssertRaisesToolExceptionRegexp(
        self.internal_self_managed_target_msg):
      self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --address {compute_uri}/projects/my-project/global/addresses/foo
          --target-tcp-proxy target-proxy-1
          --ports 80
        """.format(compute_uri=self.compute_uri))
    self.CheckRequests()

  def testInternalSelfManagedWithTargetSslProxyFails(self):
    with self.AssertRaisesToolExceptionRegexp(
        self.internal_self_managed_target_msg):
      self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --address {compute_uri}/projects/my-project/global/addresses/foo
          --target-ssl-proxy target-proxy-1
          --ports 80
        """.format(compute_uri=self.compute_uri))
    self.CheckRequests()

  def testInternalSelfManagedWithSubnetFails(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--subnet\] for an INTERNAL_SELF_MANAGED '
        r'\[--load-balancing-scheme\].'):
      self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --address {compute_uri}/projects/my-project/global/addresses/foo
          --target-http-proxy target-proxy-1
          --ports 80
          --subnet subnet-1
        """.format(compute_uri=self.compute_uri))
    self.CheckRequests()

  def testInternalSelfManagedWithMissingAddressFails(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You must specify \[--address\] for an INTERNAL_SELF_MANAGED '
        r'\[--load-balancing-scheme\]'):
      self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --target-http-proxy target-proxy-1
          --ports 80
        """.format(compute_uri=self.compute_uri))
    self.CheckRequests()

  #  For Beta and GA, --target-grpc-proxy won't be supported
  def testInternalSelfManagedWithTargetGrpcProxy(self):
    with self.AssertRaisesArgumentErrorMatches('unrecognized arguments'):
      self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --address {compute_uri}/projects/my-project/global/addresses/foo
          --target-grpc-proxy target-proxy-1
          --ports 80
        """.format(compute_uri=self.compute_uri))
    self.CheckRequests()


class GlobalForwardingRulesCreateTestBeta(GlobalForwardingRulesCreateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class GlobalForwardingRulesCreateTestAlpha(GlobalForwardingRulesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.internal_self_managed_target_msg = (
        r'You must specify either \[--target-http-proxy\], '
        r'\[--target-https-proxy\] or \[--target-grpc-proxy\] for an '
        r'INTERNAL_SELF_MANAGED \[--load-balancing-scheme\].')
    self.exactly_one_target_msg = (
        'Exactly one of (--backend-service | --target-google-apis-bundle | '
        '--target-grpc-proxy | --target-http-proxy | --target-https-proxy | '
        '--target-instance | --target-pool | --target-ssl-proxy | '
        '--target-tcp-proxy | --target-vpn-gateway) must be specified.')

  def testInternalSelfManagedWithTargetGrpcProxy(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --address {compute_uri}/projects/my-project/global/addresses/foo
          --target-grpc-proxy target-proxy-1
          --network network1
          --ports 80-80
        """.format(compute_uri=self.compute_uri))
    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/global/addresses/foo'
                  ).format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetGrpcProxies/target-proxy-1').format(
                              compute_uri=self.compute_uri),
                  network=('{compute_uri}/projects/my-project/global/networks/'
                           'network1'.format(compute_uri=self.compute_uri)),
                  portRange='80',
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.INTERNAL_SELF_MANAGED),
              project='my-project'))],)

  def testMutuallyExclusiveTargetHttpProxyTargetGrpcProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-grpc-proxy: ' + self.exactly_one_target_msg):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-http-proxy target-http-proxy-1
            --target-grpc-proxy target-grpc-proxy-1
          """)

  def testGrpcProxyUriSupport(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=INTERNAL_SELF_MANAGED
          --ports 80
          --address {uri}/projects/my-project/global/addresses/foo
          --target-grpc-proxy
          {uri}/projects/my-project/global/targetGrpcProxies/target-grpc-proxy-1
        """.format(uri=self.compute_uri))
    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  IPAddress=('{uri}/projects/my-project/global/addresses/foo'
                            ).format(uri=self.compute_uri),
                  portRange='80',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetGrpcProxies/'
                          'target-grpc-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.INTERNAL_SELF_MANAGED),
              project='my-project'))],)


if __name__ == '__main__':
  test_case.main()
