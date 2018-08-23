# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import e2e_resource_managers
from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import resource_managers


class FailoverTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

    # A new prefix added here should also be added to resources.yaml
    self.instance_prefix = 'gcloud-compute-test-instance'
    self.instance_group_prefix = 'gcloud-compute-test-instance-groups'
    self.health_check_prefix = 'gcloud-compute-test-health-check'
    self.backend_service_prefix = 'gcloud-compute-test-backend-service'

  def _GetInstanceRef(self, prefix):
    return resources.REGISTRY.Create(
        'compute.instances',
        instance=prefix,
        zone=self.zone,
        project=self.Project())

  def _GetInstanceParameters(self):
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetInstanceRef(self.instance_prefix))

  def _GetInstanceGroupRef(self, prefix):
    return resources.REGISTRY.Create(
        'compute.instanceGroups',
        instanceGroup=prefix,
        zone=self.zone,
        project=self.Project())

  def _GetInstanceGroupParameters(self):
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetInstanceGroupRef(self.instance_group_prefix))

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
        ('--global-health-checks', ''),
        ('--load-balancing-scheme', 'INTERNAL'),
        ('--protocol', 'TCP'),
    ]
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetBackendServiceRef(self.backend_service_prefix),
        extra_creation_flags=extra_backend_service_creation_flags)

  def _GetBackendServiceParametersWithFailoverPolicy(self, health_check):
    extra_backend_service_creation_flags = [
        ('--health-checks', health_check),
        ('--global-health-checks', ''),
        ('--load-balancing-scheme', 'INTERNAL'),
        ('--protocol', 'TCP'),
        ('--no-connection-drain-on-failover', ''),
        ('--drop-traffic-if-unhealthy', ''),
        ('--failover-ratio', '0.5'),
    ]
    return e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetBackendServiceRef(self.backend_service_prefix),
        extra_creation_flags=extra_backend_service_creation_flags)

  def testCreateWithFailoverPolicy(self):
    with resource_managers.HealthCheck(
        self.Run, self._GetHealthCheckParameters()) as health_check:
      with resource_managers.BackendService(
          self.Run, self._GetBackendServiceParametersWithFailoverPolicy(
              health_check.ref.Name())) as backend_service:
        # Verify that we can create a backend service with a failover policy.
        bs = self.Run(
            'compute backend-services describe {0} --region {1}'.format(
                backend_service.ref.Name(), self.region))
        self.assertEqual(backend_service.ref.Name(), bs.name)
        self.assertEqual('INTERNAL', str(bs.loadBalancingScheme))
        self.assertTrue(bs.region.endswith(self.region))
        self.assertTrue(bs.failoverPolicy.disableConnectionDrainOnFailover)
        self.assertTrue(bs.failoverPolicy.dropTrafficIfUnhealthy)
        self.assertEqual(bs.failoverPolicy.failoverRatio, 0.5)

  def testUpdateFailoverPolicy(self):
    with resource_managers.HealthCheck(
        self.Run, self._GetHealthCheckParameters()) as health_check:
      with resource_managers.BackendService(
          self.Run, self._GetBackendServiceParameters(
              health_check.ref.Name())) as backend_service:
        # Verify the backend service is successfully created
        bs = self.Run(
            'compute backend-services describe {0} --region {1}'.format(
                backend_service.ref.Name(), self.region))
        self.assertEqual(backend_service.ref.Name(), bs.name)
        self.assertEqual('INTERNAL', str(bs.loadBalancingScheme))
        self.assertTrue(bs.region.endswith(self.region))
        self.assertFalse(bs.failoverPolicy)

        # Verify that we can update a backend service with a failover policy.
        self.Run('compute backend-services update {0} '
                 '--no-connection-drain-on-failover '
                 '--drop-traffic-if-unhealthy '
                 '--failover-ratio 0.5 '
                 '--region {1}'.format(backend_service.ref.Name(), self.region))
        bs = self.Run(
            'compute backend-services describe {0} --region {1}'.format(
                backend_service.ref.Name(), self.region))
        self.assertEqual(backend_service.ref.Name(), bs.name)
        self.assertEqual('INTERNAL', str(bs.loadBalancingScheme))
        self.assertTrue(bs.region.endswith(self.region))
        self.assertTrue(bs.failoverPolicy.disableConnectionDrainOnFailover)
        self.assertTrue(bs.failoverPolicy.dropTrafficIfUnhealthy)
        self.assertEqual(bs.failoverPolicy.failoverRatio, 0.5)

  def testAddBackendWithFailover(self):
    with \
        resource_managers.Instance(
            self.Run, self._GetInstanceParameters()) as instance, \
        resource_managers.UnmanagedInstanceGroup(
            self.Run, self._GetInstanceGroupParameters()) as instance_group, \
        resource_managers.HealthCheck(
            self.Run, self._GetHealthCheckParameters()) as health_check, \
        resource_managers.BackendService(
            self.Run,
            self._GetBackendServiceParameters(health_check.ref.Name())
        ) as backend_service:
      # Verify the backend service is successfully created
      bs = self.Run('compute backend-services describe {0} --region {1}'.format(
          backend_service.ref.Name(), self.region))
      self.assertEqual(backend_service.ref.Name(), bs.name)
      self.assertEqual('INTERNAL', str(bs.loadBalancingScheme))
      self.assertTrue(bs.region.endswith(self.region))

      # Verify that we can add a backend with failover specified.
      self.Run('compute instance-groups unmanaged add-instances {0} '
               '--instances {1} '
               '--zone {2}'.format(instance_group.ref.Name(),
                                   instance.ref.Name(), self.zone))
      self.Run('compute backend-services add-backend {0} '
               '--instance-group {1} '
               '--instance-group-zone {2} '
               '--failover '
               '--region {3}'.format(backend_service.ref.Name(),
                                     instance_group.ref.Name(), self.zone,
                                     self.region))
      bs_with_backend = self.Run(
          'compute backend-services describe {0} --region {1}'.format(
              backend_service.ref.Name(), self.region))
      self.assertTrue(bs_with_backend.backends[0].failover)

  def testUpdateBackendWithFailover(self):
    with \
        resource_managers.Instance(
            self.Run, self._GetInstanceParameters()) as instance, \
        resource_managers.UnmanagedInstanceGroup(
            self.Run, self._GetInstanceGroupParameters()) as instance_group, \
        resource_managers.HealthCheck(
            self.Run, self._GetHealthCheckParameters()) as health_check, \
        resource_managers.BackendService(
            self.Run,
            self._GetBackendServiceParameters(health_check.ref.Name())
        ) as backend_service:
      # Verify the backend service is successfully created
      bs = self.Run('compute backend-services describe {0} --region {1}'.format(
          backend_service.ref.Name(), self.region))
      self.assertEqual(backend_service.ref.Name(), bs.name)
      self.assertEqual('INTERNAL', str(bs.loadBalancingScheme))
      self.assertTrue(bs.region.endswith(self.region))

      # Add a backend without failover specified.
      self.Run('compute instance-groups unmanaged add-instances {0} '
               '--instances {1} '
               '--zone {2}'.format(instance_group.ref.Name(),
                                   instance.ref.Name(), self.zone))
      self.Run('compute backend-services add-backend {0} '
               '--instance-group {1} '
               '--instance-group-zone {2} '
               '--region {3}'.format(backend_service.ref.Name(),
                                     instance_group.ref.Name(), self.zone,
                                     self.region))
      bs_with_backend = self.Run(
          'compute backend-services describe {0} --region {1}'.format(
              backend_service.ref.Name(), self.region))
      self.assertFalse(bs_with_backend.backends[0].failover)

      # Update a backend with failover specified.
      self.Run('compute backend-services update-backend {0} '
               '--instance-group {1} '
               '--instance-group-zone {2} '
               '--failover '
               '--region {3}'.format(backend_service.ref.Name(),
                                     instance_group.ref.Name(), self.zone,
                                     self.region))
      bs_with_backend = self.Run(
          'compute backend-services describe {0} --region {1}'.format(
              backend_service.ref.Name(), self.region))
      self.assertTrue(bs_with_backend.backends[0].failover)


if __name__ == '__main__':
  e2e_test_base.main()
