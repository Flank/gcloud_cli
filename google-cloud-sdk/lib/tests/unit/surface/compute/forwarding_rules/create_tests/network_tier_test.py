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
from tests.lib import test_case
from tests.lib.surface.compute.forwarding_rules import create_test_base


class ForwardingRuleCreateWithNetworkTierTest(
    create_test_base.ForwardingRulesCreateTestBase):

  def testSimpleCaseWithPremiumNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --network-tier PREMIUM
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                networkTier=(self.messages.ForwardingRule
                             .NetworkTierValueValuesEnum.PREMIUM),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testSimpleCaseWithTargetPoolAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --network-tier standard
        """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/us-central2/'
                        'targetPools/target-pool-1').format(
                            compute_uri=self.compute_uri),
                networkTier=(self.messages.ForwardingRule
                             .NetworkTierValueValuesEnum.STANDARD),
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
            project='my-project',
            region='us-central2'))],)

  def testSimpleCaseWithTargetHttpProxyAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-http-proxy target-http-proxy-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule
                               .NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithTargetHttpsProxyAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-https-proxy target-https-proxy-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpsProxies/target-https-proxy-1').format(
                              compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule
                               .NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithTargetSslProxyAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-ssl-proxy target-ssl-proxy-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetSslProxies/target-ssl-proxy-1').format(
                              compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule
                               .NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithTargetTcpProxyAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-tcp-proxy target-tcp-proxy-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetTcpProxies/target-tcp-proxy-1').format(
                              compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule
                               .NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithMissingNetworkTier(self):
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

  def testSimpleCaseWithInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[INVALID-TIER\]'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-central2
            --network-tier invalid-tier
            --target-pool target-pool-1
          """)


class ForwardingRuleCreateWithNetworkTierBetaTest(
    ForwardingRuleCreateWithNetworkTierTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class ForwardingRuleCreateWithNetworkTierAlphaTest(
    ForwardingRuleCreateWithNetworkTierBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
