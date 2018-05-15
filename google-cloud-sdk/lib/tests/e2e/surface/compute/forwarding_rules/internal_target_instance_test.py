# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration tests for forwarding rules."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import e2e_resource_managers
from tests.lib import parameterized
from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import resource_managers


class InternalTargetInstanceTest(e2e_test_base.BaseTest,
                                 parameterized.TestCase):

  def SetUp(self):
    # A new prefix added here should also be added to resources.yaml
    self.instance_prefix = 'gcloud-compute-test-instance'
    self.target_instance_prefix = 'gcloud-compute-test-target-instance'
    self.health_check_prefix = 'gcloud-compute-test-health-check'
    self.backend_service_prefix = 'gcloud-compute-test-backend-service'
    self.forwarding_rule_prefix = 'gcloud-compute-test-forwarding-rule'

  def _GetInstanceRef(self, prefix):
    return resources.REGISTRY.Create(
        'compute.instances',
        instance=prefix,
        zone=self.zone,
        project=self.Project())

  def _GetInstanceParameters(self):
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetInstanceRef(self.instance_prefix))

  def _GetTargetInstanceRef(self, prefix):
    return resources.REGISTRY.Create(
        'compute.targetInstances',
        targetInstance=prefix,
        zone=self.zone,
        project=self.Project())

  def _GetTargetInstanceParameters(self, instance):
    extra_target_instance_creation_flags = [
        ('--instance', instance),
    ]
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetTargetInstanceRef(self.target_instance_prefix),
        extra_creation_flags=extra_target_instance_creation_flags)

  def _GetHealthCheckRef(self, prefix):
    return resources.REGISTRY.Create(
        'compute.healthChecks', healthCheck=prefix, project=self.Project())

  def _GetHealthCheckParameters(self):
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetHealthCheckRef(self.health_check_prefix))

  def _GetBackendServiceRef(self, prefix):
    return resources.REGISTRY.Create(
        'compute.regionBackendServices',
        backendService=prefix,
        region=self.region,
        project=self.Project())

  def _GetBackendServiceParameters(self, health_check):
    extra_backend_service_creation_flags = [
        ('--health-checks', health_check),
        ('--load-balancing-scheme', 'INTERNAL'),
        ('--protocol', 'TCP'),
    ]
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetBackendServiceRef(self.backend_service_prefix),
        extra_creation_flags=extra_backend_service_creation_flags)

  def _GetForwardingRuleRef(self, prefix):
    return resources.REGISTRY.Create(
        'compute.forwardingRules',
        forwardingRule=prefix,
        region=self.region,
        project=self.Project())

  def _GetForwardingRuleParameters(self, target_instance, balancing_scheme):
    extra_forwarding_rule_creation_flags = [
        ('--target-instance', target_instance),
        ('--target-instance-zone', self.zone),
        ('--load-balancing-scheme', balancing_scheme),
        ('--ports', '80'),
    ]
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetForwardingRuleRef(self.forwarding_rule_prefix),
        extra_creation_flags=extra_forwarding_rule_creation_flags)

  @parameterized.parameters(
      (base.ReleaseTrack.GA, 'EXTERNAL'),
      (base.ReleaseTrack.BETA, 'INTERNAL'),
  )
  def testForwardingRules(self, track, balancing_scheme):
    self.track = track
    with \
        resource_managers.Instance(
            self.Run, self._GetInstanceParameters()) as instance, \
        resource_managers.TargetInstance(
            self.Run,
            self._GetTargetInstanceParameters(instance.ref.Name())
        ) as target_instance, \
        resource_managers.HealthCheck(
            self.Run, self._GetHealthCheckParameters()
        ) as health_check, \
        resource_managers.BackendService(
            self.Run,
            self._GetBackendServiceParameters(health_check.ref.Name())
        ) as backend_service, \
        resource_managers.ForwardingRule(
            self.Run,
            self._GetForwardingRuleParameters(target_instance.ref.Name(),
                                              balancing_scheme)
        ) as forwarding_rule:
      # Verify that forwarding with target instance is successfully created
      fr = self.Run('compute forwarding-rules describe {0} --region {1}'.format(
          forwarding_rule.ref.Name(), self.region))
      self.assertEqual(forwarding_rule.ref.Name(), fr.name)
      self.assertEqual(balancing_scheme, str(fr.loadBalancingScheme))
      self.assertTrue(fr.region.endswith(self.region))
      self.assertTrue(fr.target.endswith(target_instance.ref.Name()))

      # Target cannot be changed if balancing scheme is external.
      if balancing_scheme == 'INTERNAL':
        # Verify that we can set a backend service as a new target.
        self.Run('compute forwarding-rules set-target {0} '
                 '--backend-service {1} '
                 '--backend-service-region {2} '
                 '--region {2}'.format(forwarding_rule.ref.Name(),
                                       backend_service.ref.Name(), self.region))
        fr_bs_target = self.Run(
            'compute forwarding-rules describe {0} --region {1}'.format(
                forwarding_rule.ref.Name(), self.region))
        self.assertTrue(
            backend_service.ref.Name() in fr_bs_target.backendService)
        self.assertTrue(fr_bs_target.target is None)

        # Verify that we can set target back to a target instance.
        self.Run('compute forwarding-rules set-target {0} '
                 '--target-instance {1} '
                 '--target-instance-zone {2} '
                 '--region {3}'.format(
                     forwarding_rule.ref.Name(),
                     target_instance.ref.Name(), self.zone, self.region))
        fr_ti_target = self.Run(
            'compute forwarding-rules describe {0} --region {1}'.format(
                forwarding_rule.ref.Name(), self.region))
        self.assertTrue(target_instance.ref.Name() in fr_ti_target.target)
        self.assertTrue(fr_ti_target.backendService is None)


if __name__ == '__main__':
  e2e_test_base.main()
