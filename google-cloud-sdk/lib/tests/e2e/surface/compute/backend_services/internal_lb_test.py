# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Integration tests for creating/deleting firewalls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


def _UniqueName(name):
  return next(
      e2e_utils.GetResourceNameGenerator(prefix='compute-internal-lb-test-' +
                                         name))


class InternalLoadBalancingTest(e2e_base.WithServiceAuth):

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    try:
      cmd = tuple(subcommand) + ('delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass

  @contextlib.contextmanager
  def _HealthCheck(self, name):
    try:
      yield self.RunCompute('health-checks', 'create', 'tcp', name)
    finally:
      self.CleanUpResource(['health-checks'], name)

  @contextlib.contextmanager
  def _BackendService(self, name, health_check, region):
    try:
      yield self.RunCompute('backend-services', 'create', name,
                            '--load-balancing-scheme=internal',
                            '--health-checks={0}'.format(health_check),
                            '--protocol=TCP',
                            '--timeout=30',
                            '--region', region)
    finally:
      self.CleanUpResource(['backend-services'], name,
                           '--region', region)

  @contextlib.contextmanager
  def _ForwardingRule(self, name, backend_service, region):
    if self.track is base.ReleaseTrack.GA:
      try:
        yield self.RunCompute('forwarding-rules', 'create', name,
                              '--load-balancing-scheme', 'internal',
                              '--backend-service', backend_service,
                              '--ports', '80-82,85',
                              '--network', 'default',
                              '--region', region)
      finally:
        self.CleanUpResource(['forwarding-rules'], name,
                             '--region', region)
    else:
      try:
        yield self.RunCompute('forwarding-rules', 'create', name,
                              '--load-balancing-scheme', 'internal',
                              '--backend-service', backend_service,
                              '--service-label', 'label1',
                              '--ports', '80-82,85',
                              '--network', 'default',
                              '--region', region)
      finally:
        self.CleanUpResource(['forwarding-rules'], name,
                             '--region', region)

  @contextlib.contextmanager
  def _InstanceGroup(self, name, zone):
    try:
      yield self.RunCompute('instance-groups', 'unmanaged',
                            'create', name, '--zone', zone)

    finally:
      self.CleanUpResource(['instance-groups', 'unmanaged'], name,
                           '--zone', zone)

  @contextlib.contextmanager
  def _VmInstance(self, name, zone):
    try:
      yield self.RunCompute('instances', 'create', name, '--zone', zone)

    finally:
      self.CleanUpResource(['instances'], name,
                           '--zone', zone)

  def _TestInternalLb_WithForwardingRule(self):
    """Run common scenario of creating internal load balanced backend service.

    This test sets up internal regional load balancer with global health check
    and regional forwarding rule. It is checking internal load balancer in
      backend-services create/delete/describe/list
      forwarding-rules create
    commands.
    """

    properties.VALUES.core.user_output_enabled.Set(False)
    health_check = _UniqueName('health-check')
    backend_service = _UniqueName('backend-service')
    instance_group = _UniqueName('instance-group')
    vm = _UniqueName('vm')
    region = 'us-central1'
    zone = 'us-central1-f'

    with self._HealthCheck(health_check), self._VmInstance(
        vm,
        zone), self._InstanceGroup(instance_group, zone), self._BackendService(
            backend_service, health_check, region) as backend_services:

      # Check that created backend services matches intended one.
      self.assertEqual(1, len(backend_services))
      self.assertEqual(backend_service, backend_services[0].name)
      self.assertEqual('INTERNAL',
                       str(backend_services[0].loadBalancingScheme))
      self.assertTrue(backend_services[0].region.endswith(region))

      # Check that we can list it.
      backend_services = self.RunCompute('backend-services', 'list',
                                         '--regions', region)
      self.assertIn(backend_service, [b['name'] for b in backend_services])

      # Check that we can describe it.
      bs = self.RunCompute('backend-services', 'describe', backend_service,
                           '--region', region)
      self.assertEqual(backend_service, bs.name)
      self.assertEqual('INTERNAL', str(bs.loadBalancingScheme))
      self.assertTrue(bs.region.endswith(region))
      self.assertEqual(30, bs.timeoutSec)
      self.assertEqual(bs.backends, [], bs)

      # Add backend.
      self.RunCompute('instance-groups', 'unmanaged',
                      'add-instances', instance_group,
                      '--instances', vm, '--zone', zone)

      backend = self.RunCompute(
          'backend-services', 'add-backend', backend_service,
          '--region', region, '--instance-group', instance_group,
          '--instance-group-zone', zone,
          '--description', 'initial-test backend')
      self.assertEqual(1, len(backend))
      self.assertEqual('initial-test backend',
                       backend[0].backends[0].description)

      # Make sure backend is there.
      bs = self.RunCompute('backend-services', 'describe', backend_service,
                           '--region', region)
      self.assertTrue(
          bs.backends[0].group.endswith(
              '/zones/{0}/instanceGroups/{1}'.format(zone, instance_group)), bs)

      # Update backend.
      backend_update = self.RunCompute(
          'backend-services', 'update-backend', backend_service,
          '--region', region, '--instance-group', instance_group,
          '--instance-group-zone', zone,
          '--description', 'updated-test backend')
      self.assertEqual('updated-test backend',
                       backend_update[0].backends[0].description)

      # Make sure backend update worked.
      # TODO(b/35870200): this seems to be eventually consistent.
      # bs = self.RunCompute('backend-services', 'describe', backend_service,
      #                     '--region', region)
      # self.assertEqual('updated-test backend',
      #                   backend[0]['backends'][0]['description'])

      # Remove Backend.
      backend_remove = list(self.RunCompute(
          'backend-services', 'remove-backend', backend_service,
          '--region', region, '--instance-group', instance_group,
          '--instance-group-zone', zone))
      self.assertFalse('backends' in backend_remove, backend_remove)

      # Make sure backend remove worked.
      bs = self.RunCompute('backend-services', 'describe', backend_service,
                           '--region', region)
      self.assertEqual(bs.backends, [], bs)

      # Check backend-services update.
      backend_update = list(self.RunCompute(
          'backend-services', 'update', backend_service,
          '--region', region, '--timeout=20'))
      bs = self.RunCompute('backend-services', 'describe', backend_service,
                           '--region', region)
      self.assertEqual(20, bs.timeoutSec)

      # Check that we can point forwarding rule to it.
      forwarding_rule = _UniqueName('forwarding-rule')
      with self._ForwardingRule(forwarding_rule, backend_service, region):
        rule = self.RunCompute(
            'forwarding-rules', 'describe', forwarding_rule,
            '--region', region)
        self.assertEqual(forwarding_rule, rule.name)
        self.assertTrue(rule.region.endswith(region))
        self.assertEqual('INTERNAL', str(rule.loadBalancingScheme))
        self.assertTrue(
            rule.backendService.endswith(
                'regions/{0}/backendServices/{1}'.format(
                    region, backend_service)))

    # Check that delete worked
    with self.assertRaisesRegex(exceptions.ToolException,
                                'Could not fetch resource'):
      self.RunCompute('backend-services', 'describe', backend_service,
                      '--region', region)

  def testInternalLb_WithForwardingRuleGA(self):
    self.track = base.ReleaseTrack.GA
    self._TestInternalLb_WithForwardingRule()

  def testInternalLb_WithForwardingRuleBeta(self):
    self.track = base.ReleaseTrack.BETA
    self._TestInternalLb_WithForwardingRule()


if __name__ == '__main__':
  test_case.main()
