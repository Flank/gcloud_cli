# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Integration tests for forwarding rules create|update with global access."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import logging

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class ForwardingRulesGlobalAccessTest(e2e_test_base.BaseTest):
  """Forwarding rule global access beta e2e test."""

  SUBNET_RANGE = '192.168.0.0/24'

  def _GetResourceName(self):
    return next(e2e_utils.GetResourceNameGenerator(prefix='ilb-global-access'))

  def SetupCommon(self):
    """Setup network and subnet for global access test.

    Global access feature does not work with default network (legacy network).
    Therefore, create custom-mode subnet for the test.
    """
    self.network_name = self._GetResourceName()
    self.subnetwork_name = self._GetResourceName()

    self.Run('compute networks create {} --subnet-mode=custom'.format(
        self.network_name))
    self.Run('compute networks subnets create {0} --network {1} '
             '--region {2} --range {3}'.format(self.subnetwork_name,
                                               self.network_name, self.region,
                                               self.SUBNET_RANGE))

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.backend_service_name = self._GetResourceName()
    self.health_check_name = self._GetResourceName()
    self.forwarding_rule_name = self._GetResourceName()
    self.SetupCommon()

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    self.CleanUpResource(
        self.subnetwork_name, 'networks subnets', scope=e2e_test_base.REGIONAL)
    self.CleanUpResource(
        self.network_name, 'networks', scope=e2e_test_base.GLOBAL)

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResourceQuiet(self, subcommand, name, *args):
    try:
      cmd = (subcommand, 'delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass

  @contextlib.contextmanager
  def _HealthCheck(self, name):
    try:
      yield self.RunCompute('health-checks', 'create', 'tcp', name, '--global')
    finally:
      self.CleanUpResourceQuiet('health-checks', name, '--global')

  @contextlib.contextmanager
  def _BackendService(self, name, hc_name, region):
    try:
      yield self.RunCompute('backend-services', 'create', name,
                            '--health-checks', hc_name, '--region', region,
                            '--global-health-checks', '--load-balancing-scheme',
                            'internal')
    finally:
      self.CleanUpResourceQuiet('backend-services', name, '--region', region)

  @contextlib.contextmanager
  def _ForwardingRule(self, name, network, subnet, backend_service, region,
                      global_access):
    try:
      create_fwd_args = [
          'forwarding-rules', 'create', name, '--backend-service',
          backend_service, '--region', region, '--load-balancing-scheme',
          'internal', '--network', network, '--subnet', subnet, '--ports',
          '8080'
      ]
      if global_access:
        create_fwd_args.append('--allow-global-access')
      yield self.RunCompute(*create_fwd_args)
    finally:
      self.CleanUpResourceQuiet('forwarding-rules', name, '--region', region)

  def _AssertForwardingRuleHasGlobalAccess(self, fwd_name, region):
    self.Run('compute forwarding-rules describe {0} --region {1}'.format(
        fwd_name, region))
    self.AssertNewOutputContains('allowGlobalAccess: true', reset=True)

  def _AssertForwardingRuleDoesNotHaveGlobalAccess(self, fwd_name, region):
    self.Run('compute forwarding-rules describe {0} --region {1}'.format(
        fwd_name, region))
    self.AssertNewOutputNotContains('allowGlobalAccess: true', reset=True)

  def testCreateForwardingRuleWithGlobalAccess(self):
    """Test creating forwarding rule with global access."""
    allow_global_access = True
    with \
        self._HealthCheck(self.health_check_name), \
        self._BackendService(
            name=self.backend_service_name,
            hc_name=self.health_check_name,
            region=self.region), \
        self._ForwardingRule(
            name=self.forwarding_rule_name,
            network=self.network_name,
            subnet=self.subnetwork_name,
            backend_service=self.backend_service_name,
            region=self.region,
            global_access=allow_global_access):
      self._AssertForwardingRuleHasGlobalAccess(self.forwarding_rule_name,
                                                self.region)

  def testUpdateForwardingRuleWithGlobalAccess(self):
    """Test promote and demote forwarding rule with and without global access.

    The test update a regular forwarding rule with global access, and then
    update it back to regular forwarding rule.
    """
    initial_allow_global_access = False
    with \
        self._HealthCheck(self.health_check_name), \
        self._BackendService(
            name=self.backend_service_name,
            hc_name=self.health_check_name,
            region=self.region), \
        self._ForwardingRule(
            name=self.forwarding_rule_name,
            network=self.network_name,
            subnet=self.subnetwork_name,
            backend_service=self.backend_service_name,
            region=self.region,
            global_access=initial_allow_global_access):
      self._AssertForwardingRuleDoesNotHaveGlobalAccess(
          self.forwarding_rule_name, self.region)
      self.Run('compute forwarding-rules update {0} --region {1} '
               '--allow-global-access'.format(self.forwarding_rule_name,
                                              self.region))
      self._AssertForwardingRuleHasGlobalAccess(self.forwarding_rule_name,
                                                self.region)
      # Demotes the global access forwarding rule.
      self.Run('compute forwarding-rules update {0} --region {1} '
               '--no-allow-global-access'.format(self.forwarding_rule_name,
                                                 self.region))
      self._AssertForwardingRuleDoesNotHaveGlobalAccess(
          self.forwarding_rule_name, self.region)


if __name__ == '__main__':
  e2e_test_base.main()
