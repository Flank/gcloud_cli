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


class InternalManagedForwardingRulesCreateTestBeta(
    create_test_base.ForwardingRulesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testInternalManagedWithTargetHttpProxy(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
        --region us-central2
        --load-balancing-scheme=INTERNAL_MANAGED
        --target-http-proxy target-proxy-1
        --target-http-proxy-region us-central2
        --address '10.140.0.100'
        --network network1
        --port-range 80
    """)

    self.CheckRequests([
        (self.compute.forwardingRules, 'Insert',
         self.messages.ComputeForwardingRulesInsertRequest(
             forwardingRule=self.messages.ForwardingRule(
                 name='forwarding-rule-1',
                 target=('{compute_uri}/projects/my-project/regions/'
                         'us-central2/targetHttpProxies/target-proxy-1').format(
                             compute_uri=self.compute_uri),
                 IPAddress='10.140.0.100',
                 network=('{compute_uri}/projects/my-project/global/networks/'
                          'network1'.format(compute_uri=self.compute_uri)),
                 portRange='80',
                 loadBalancingScheme=self.messages.ForwardingRule
                 .LoadBalancingSchemeValueValuesEnum.INTERNAL_MANAGED),
             region='us-central2',
             project='my-project'))
    ],)

  def testInternalManagedWithTargetHttpsProxy(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
        --region us-central2
        --load-balancing-scheme=INTERNAL_MANAGED
        --target-https-proxy target-proxy-1
        --target-https-proxy-region us-central2
        --address '10.140.0.100'
        --network network1
        --port-range 80
    """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/'
                        'us-central2/targetHttpsProxies/target-proxy-1').format(
                            compute_uri=self.compute_uri),
                IPAddress='10.140.0.100',
                network=('{compute_uri}/projects/my-project/global/networks/'
                         'network1'.format(compute_uri=self.compute_uri)),
                portRange='80',
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.INTERNAL_MANAGED),
            region='us-central2',
            project='my-project'))],)

  def testInternalManagedWithSubnetWithoutAddress(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
        --region us-central2
        --load-balancing-scheme=INTERNAL_MANAGED
        --target-https-proxy target-proxy-1
        --target-https-proxy-region us-central2
        --subnet subnet1
        --network network1
        --port-range 80
    """)

    self.CheckRequests([(
        self.compute.forwardingRules, 'Insert',
        self.messages.ComputeForwardingRulesInsertRequest(
            forwardingRule=self.messages.ForwardingRule(
                name='forwarding-rule-1',
                target=('{compute_uri}/projects/my-project/regions/'
                        'us-central2/targetHttpsProxies/target-proxy-1').format(
                            compute_uri=self.compute_uri),
                network=('{compute_uri}/projects/my-project/global/networks/'
                         'network1'.format(compute_uri=self.compute_uri)),
                subnetwork=(
                    '{compute_uri}/projects/my-project/regions/us-central2/'
                    'subnetworks/subnet1'.format(compute_uri=self.compute_uri)),
                portRange='80',
                loadBalancingScheme=self.messages.ForwardingRule
                .LoadBalancingSchemeValueValuesEnum.INTERNAL_MANAGED),
            region='us-central2',
            project='my-project'))],)


class InternalManagedForwardingRulesCreateTestAlpha(
    InternalManagedForwardingRulesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
