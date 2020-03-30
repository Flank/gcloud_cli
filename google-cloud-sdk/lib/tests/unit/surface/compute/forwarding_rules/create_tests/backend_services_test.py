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


class RegionalForwardingRulesCreateBackendServicesTest(
    create_test_base.ForwardingRulesCreateTestBase):

  def SetUp(self):
    properties.VALUES.core.check_gce_metadata.Set(False)

  def testBackendServiceMutuallyExclusiveWithGlobal(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--backend-service\] for a global '
        'forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --backend-service BS1
                  --global
                  --ports 80""")

    self.CheckRequests()

  def testInternalMutuallyExclusiveWithGlobal(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify internal \[--load-balancing-scheme\] for a global '
        'forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --load-balancing-scheme internal
                  --target-http-proxy target-http-proxy-1
                  --global
                  --ports 80""")

    self.CheckRequests()

  def testExternalMutuallyExclusiveWithSubnet(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--subnet\] or \[--network\] for non-internal '
        r'\[--load-balancing-scheme\] forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --subnet subnet-abc
                  --load-balancing-scheme external
                  --backend-service BS1
                  --ports 80
                  --region alaska""")

    self.CheckRequests()

  def testExternalMutuallyExclusiveWithNetwork(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--subnet\] or \[--network\] for non-internal '
        r'\[--load-balancing-scheme\] forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --network network-abc
                  --load-balancing-scheme external
                  --backend-service BS1
                  --ports 80
                  --region alaska""")

    self.CheckRequests()

  def testInternalWithAddressAndPorts(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --address 162.222.178.83
                --ports 80-82,85
                --subnet subdefault
                --network default
                --backend-service BS1
                --region alaska
                --load-balancing-scheme internal""")

    load_balancing_scheme = (
        self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
    )

    self.CheckRequests([
        (self.compute.forwardingRules, 'Insert',
         self.messages.ComputeForwardingRulesInsertRequest(
             forwardingRule=self.messages.ForwardingRule(
                 name='forwarding-rule-1',
                 IPAddress='162.222.178.83',
                 ports=['80', '81', '82', '85'],
                 network=(
                     '{0}/projects/my-project/global/networks/default'.format(
                         self.compute_uri)),
                 subnetwork=('{0}/projects/my-project/regions/alaska/'
                             'subnetworks/subdefault'.format(self.compute_uri)),
                 loadBalancingScheme=load_balancing_scheme,
                 backendService='https://compute.googleapis.com/compute/{api}/'
                 'projects/my-project/regions/alaska/'
                 'backendServices/'
                 'BS1'.format(api=self.resource_api),
             ),
             project='my-project',
             region='alaska'))
    ],)

  def testInternalIsMirroringCollector(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --address 162.222.178.83
                --ports 80
                --subnet subdefault
                --network default
                --backend-service BS1
                --region alaska
                --load-balancing-scheme internal
                --is-mirroring-collector""")

    load_balancing_scheme = (
        self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
    )

    self.CheckRequests([
        (self.compute.forwardingRules, 'Insert',
         self.messages.ComputeForwardingRulesInsertRequest(
             forwardingRule=self.messages.ForwardingRule(
                 name='forwarding-rule-1',
                 IPAddress='162.222.178.83',
                 ports=['80'],
                 network=(
                     '{0}/projects/my-project/global/networks/default'.format(
                         self.compute_uri)),
                 subnetwork=('{0}/projects/my-project/regions/alaska/'
                             'subnetworks/subdefault'.format(self.compute_uri)),
                 loadBalancingScheme=load_balancing_scheme,
                 backendService='https://compute.googleapis.com/compute/{api}/'
                 'projects/my-project/regions/alaska/'
                 'backendServices/'
                 'BS1'.format(api=self.resource_api),
                 isMirroringCollector=True,
             ),
             project='my-project',
             region='alaska'))
    ],)

  def testExternalWithPortsMerge(self):
    """Tests ports merge for regional external load balancing."""
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --address 162.222.178.83
                --ports 80,81-82,83
                --target-pool TP1
                --region alaska
                --load-balancing-scheme external""")

    load_balancing_scheme = (
        self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.EXTERNAL
    )

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  IPAddress='162.222.178.83',
                  portRange='80-83',
                  loadBalancingScheme=load_balancing_scheme,
                  target='https://compute.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'targetPools/'
                  'TP1'.format(api=self.resource_api),
              ),
              project='my-project',
              region='alaska'))],)

  def testInternalBackendServiceWithPortRange(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--port-range\] for a forwarding rule whose '
        r'\[--load-balancing-scheme\] is internal, please use '
        r'\[--ports\] flag instead.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --port-range 100-105
                  --load-balancing-scheme internal
                  --backend-service BS1
                  --region alaska""")

  def testInternalBackendService(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --load-balancing-scheme internal
                --backend-service BS1
                --region alaska""")

    load_balancing_scheme = (
        self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
    )
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  loadBalancingScheme=load_balancing_scheme,
                  backendService='https://compute.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'backendServices/'
                  'BS1'.format(api=self.resource_api),
              ),
              project='my-project',
              region='alaska'))],)

  def testInternalTargetInstance(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --load-balancing-scheme internal
                --target-instance ti
                --region us-central2
                --target-instance-zone us-central2-b
                --ports 80""")

    load_balancing_scheme = (
        self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
    )
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  loadBalancingScheme=load_balancing_scheme,
                  target='https://compute.googleapis.com/compute/{api}/'
                  'projects/my-project/zones/us-central2-b/'
                  'targetInstances/'
                  'ti'.format(api=self.resource_api),
                  ports=['80'],
              ),
              project='my-project',
              region='us-central2'))],)

  def testInternalTargetHttpProxy(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify internal \[--load-balancing-scheme\] '
        'for a global forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --load-balancing-scheme internal
                  --target-http-proxy TP1
                  --ports 80
                  --global""")

  def testExternalBackendService(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --backend-service BS1
                --region alaska""")

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  backendService='https://compute.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'backendServices/'
                  'BS1'.format(api=self.resource_api),
                  loadBalancingScheme=self.messages.ForwardingRule
                  .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='alaska'))],)

  def testBackendServiceWithServiceLabel(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --load-balancing-scheme internal
                --backend-service BS1
                --service-label label1
               --region alaska""")

    load_balancing_scheme = (
        self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
    )
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  loadBalancingScheme=load_balancing_scheme,
                  backendService='https://compute.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'backendServices/'
                  'BS1'.format(api=self.resource_api),
                  serviceLabel='label1',
              ),
              project='my-project',
              region='alaska'))],)


class RegionalForwardingRulesCreateBackendServicesBetaTest(
    RegionalForwardingRulesCreateBackendServicesTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testBackendServiceWithServiceLabel(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --load-balancing-scheme internal
                --backend-service BS1
                --service-label label1
                --region alaska""")

    load_balancing_scheme = (
        self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
    )
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  loadBalancingScheme=load_balancing_scheme,
                  backendService='https://compute.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'backendServices/'
                  'BS1'.format(api=self.resource_api),
                  serviceLabel='label1',
              ),
              project='my-project',
              region='alaska'))],)


class RegionalForwardingRulesCreateBackendServicesAlphaTest(
    RegionalForwardingRulesCreateBackendServicesBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
