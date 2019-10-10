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
"""Tests for the global access forwarding-rules create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GlobalAccessApiBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testAllowGlobalAccessInGlobalRequest(self):
    """Tests specifying global access in creating global l7 lb request."""
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --load-balancing-scheme=EXTERNAL
          --target-https-proxy target-proxy-1
          --allow-global-access
          --ports 80-80
        """.format(compute_uri=self.compute_uri))

    target_url = ('{compute_uri}/projects/my-project/global/targetHttpsProxies'
                  '/target-proxy-1').format(compute_uri=self.compute_uri)

    expected_forwarding_rule = \
        self.messages.ForwardingRule(
            name='forwarding-rule-1',
            target=target_url,
            portRange='80',
            allowGlobalAccess=True,
            ipVersion=(
                self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4),
            loadBalancingScheme=self.messages.ForwardingRule.
            LoadBalancingSchemeValueValuesEnum.EXTERNAL)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=expected_forwarding_rule, project='my-project'))],)

  def testAllowGlobalAccessInRegionalRequest(self):
    """Tests specifying global access in creating internal load balancing."""
    self.Run("""
      compute forwarding-rules create forwarding-rule-1
        --load-balancing-scheme internal
        --region us-central1
        --backend-service bs-1
        --ports 80
        --allow-global-access
    """)

    target_url = (
        '{compute_uri}/projects/my-project/regions/us-central1/backendServices/'
        'bs-1').format(compute_uri=self.compute_uri)

    expected_forwarding_rule = \
        self.messages.ForwardingRule(
            name='forwarding-rule-1',
            backendService=target_url,
            ports=['80'],
            allowGlobalAccess=True,
            loadBalancingScheme=self.messages.ForwardingRule.
            LoadBalancingSchemeValueValuesEnum.INTERNAL)

    self.CheckRequests([(self.compute.forwardingRules, 'Insert',
                         self.messages.ComputeForwardingRulesInsertRequest(
                             forwardingRule=expected_forwarding_rule,
                             project='my-project',
                             region='us-central1'))],)

  def testNotSpecifyAllowGlobalAccess(self):
    """Tests not specifying global access in creating internal lb request."""
    self.Run("""
      compute forwarding-rules create forwarding-rule-1
        --load-balancing-scheme internal
        --region us-central1
        --backend-service bs-1
        --ports 80
    """)

    target_url = (
        '{compute_uri}/projects/my-project/regions/us-central1/backendServices/'
        'bs-1').format(compute_uri=self.compute_uri)

    expected_forwarding_rule = \
        self.messages.ForwardingRule(
            name='forwarding-rule-1',
            backendService=target_url,
            ports=['80'],
            loadBalancingScheme=self.messages.ForwardingRule.
            LoadBalancingSchemeValueValuesEnum.INTERNAL)

    self.CheckRequests([(self.compute.forwardingRules, 'Insert',
                         self.messages.ComputeForwardingRulesInsertRequest(
                             forwardingRule=expected_forwarding_rule,
                             project='my-project',
                             region='us-central1'))],)


class GlobalAccessApiAlphaTest(GlobalAccessApiBetaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
