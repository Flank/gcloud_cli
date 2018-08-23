# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for backend services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class BackendServicesTest(e2e_test_base.BaseTest):

  def UniqueName(self, name):
    return next(
        e2e_utils.GetResourceNameGenerator(prefix='compute-backend-test-' +
                                           name))

  def _SetUpReleaseTrack(self, track, api_version):
    self.track = track
    properties.VALUES.core.user_output_enabled.Set(False)
    # Containers for created resources
    self.backend_service_names = []
    self.http_health_check_names = []
    self.health_check_names = []
    self.instance_names = []
    self.instance_group_names = []
    self.msgs = apis.GetMessagesModule('compute', api_version)

  def SetUp(self):
    self._SetUpReleaseTrack(calliope_base.ReleaseTrack.GA, 'v1')

  def CreateInstance(self):
    """Creates an instance and returns its name."""
    name = self.UniqueName('instance')
    result = self.Run('compute instances create {0} --zone {1}'.format(
        name, self.zone))
    result_list = resource_projector.MakeSerializable(result)
    self.assertEqual(1, len(result_list))
    self.assertEqual(name, result_list[0]['name'])
    self.instance_names.append(name)
    return name

  def CreateInstanceGroup(self):
    """Creates an instance group and returns its name."""
    name = self.UniqueName('instance-group')
    result = self.Run('compute instance-groups unmanaged create {0} --zone {1}'
                      .format(name, self.zone))
    result_list = list(result)
    self.assertEqual(1, len(result_list))
    self.assertEqual(name, result_list[0].name)
    self.instance_group_names.append(name)
    return name

  def CreateHttpHealthCheck(self):
    """Creates a HTTP health check and returns its name."""
    name = self.UniqueName('http-hc')
    result = self.Run('compute http-health-checks create {0}'.format(name))
    result_list = list(result)
    self.assertEqual(1, len(result_list))
    self.assertEqual(name, result_list[0].name)
    self.http_health_check_names.append(name)
    return name

  def CreateHealthCheck(self):
    """Creates a TCP health check and returns its name."""
    name = self.UniqueName('tcp-hc')
    global_flag = (' --global'
                   if self.track == calliope_base.ReleaseTrack.ALPHA else '')
    result = self.Run('compute health-checks create tcp {0} {1}'.format(
        name, global_flag))
    result_list = list(result)
    self.assertEqual(1, len(result_list))
    self.assertEqual(name, result_list[0].name)
    self.health_check_names.append(name)
    return name

  def CreateHttpBackendService(self,
                               http_health_check_name,
                               cache_max_age_sec=None):
    """Creates a backend service with HTTP health check and returns its name."""
    name = self.UniqueName('http-bs')
    signed_url_args = '--signed-url-cache-max-age {0} '.format(
        cache_max_age_sec) if cache_max_age_sec else ''

    # Create the resource and verify the result.
    result = self.Run('compute backend-services create {0} '
                      '--protocol HTTP --enable-cdn '
                      '{1} '
                      '--http-health-checks {2} '
                      '--global'.format(name, signed_url_args,
                                        http_health_check_name))
    self.backend_service_names.append(name)

    self.assertEqual(1, len(result))
    self.assertEqual(name, result[0].name)
    self.assertTrue(result[0].enableCDN)
    if cache_max_age_sec:
      self.assertEqual(cache_max_age_sec,
                       result[0].cdnPolicy.signedUrlCacheMaxAgeSec)

    # Update the resource and verify the result.
    result = self.Run(
        'compute backend-services describe {0} --global'.format(name))
    self.assertTrue(result.enableCDN)
    if cache_max_age_sec:
      self.assertEqual(cache_max_age_sec,
                       result.cdnPolicy.signedUrlCacheMaxAgeSec)

    return name

  def CreateTcpBackendService(self, health_check_name):
    """Creates a backend service with TCP health check and returns its name."""
    name = self.UniqueName('tcp-bs')
    global_health_check_flag = (' --global-health-checks' if
                                self.track == calliope_base.ReleaseTrack.ALPHA
                                else '')
    result = self.Run('compute backend-services create {0} '
                      '--protocol TCP '
                      '--health-checks {1} '
                      '--connection-draining-timeout 10 '
                      '--global {2}'.format(name, health_check_name,
                                            global_health_check_flag))
    self.assertEqual(1, len(result))
    self.assertEqual(name, result[0].name)
    self.backend_service_names.append(name)
    return name

  def testHttpBackendServiceLb(self):
    """Verifies backend service operations when using a HTTP health check."""
    vm_name = self.CreateInstance()
    ig_name = self.CreateInstanceGroup()
    hc_name = self.CreateHttpHealthCheck()
    bs_name = self.CreateHttpBackendService(hc_name, cache_max_age_sec=1234)

    # Add instance to instance group.
    self.Run('compute instance-groups unmanaged add-instances {0} '
             '--instances {1} --zone {2}'.format(ig_name, vm_name, self.zone))

    # Add backend to backend service
    result = self.Run('compute backend-services add-backend {0} '
                      '--instance-group {1} --instance-group-zone {2} '
                      '--balancing-mode RATE --max-rate 100 --global'.format(
                          bs_name, ig_name, self.zone))
    self.assertEqual(1, len(result))
    self.assertEqual('RATE', str(result[0].backends[0].balancingMode))
    self.assertEqual(100, result[0].backends[0].maxRate)

    # Update backend
    result = self.Run('compute backend-services update-backend {0} '
                      '--instance-group {1} --instance-group-zone {2} '
                      '--balancing-mode UTILIZATION '
                      '--max-utilization 0.5 --global'.format(
                          bs_name, ig_name, self.zone))
    self.assertEqual(1, len(result))
    self.assertEqual('UTILIZATION', str(result[0].backends[0].balancingMode))
    self.assertEqual(100, result[0].backends[0].maxRate)
    self.assertEqual(0.5, result[0].backends[0].maxUtilization)

    result = self.Run('compute backend-services update-backend {0} '
                      '--instance-group {1} --instance-group-zone {2} '
                      '--balancing-mode RATE --max-rate-per-instance 10 '
                      '--global'.format(bs_name, ig_name, self.zone))

    self.assertEqual(1, len(result))
    self.assertEqual('RATE', str(result[0].backends[0].balancingMode))
    self.assertEqual(10, result[0].backends[0].maxRatePerInstance)
    self.assertIsNone(result[0].backends[0].maxRate)

  def testTcpBackendServiceLb(self):
    """Verifies backend service operations when using a TCP health check."""
    vm_name = self.CreateInstance()
    ig_name = self.CreateInstanceGroup()
    hc_name = self.CreateHealthCheck()
    bs_name = self.CreateTcpBackendService(hc_name)

    # Add instance to instance group.
    self.Run('compute instance-groups unmanaged add-instances {0} '
             '--instances {1} --zone {2}'.format(ig_name, vm_name, self.zone))

    # Add backend to backend service
    result = self.Run('compute backend-services add-backend {0} '
                      '--instance-group {1} --instance-group-zone {2} '
                      '--balancing-mode CONNECTION '
                      '--max-connections-per-instance 100 '
                      '--global'.format(bs_name, ig_name, self.zone))

    self.assertEqual(1, len(result))
    self.assertEqual('CONNECTION', str(result[0].backends[0].balancingMode))
    self.assertEqual(100, result[0].backends[0].maxConnectionsPerInstance)

    # Update backend
    result = self.Run('compute backend-services update-backend {0} '
                      '--instance-group {1} --instance-group-zone {2} '
                      '--balancing-mode UTILIZATION --max-connections '
                      '200 --global'.format(bs_name, ig_name, self.zone))
    self.assertEqual(1, len(result))
    self.assertEqual('UTILIZATION', str(result[0].backends[0].balancingMode))
    self.assertEqual(200, result[0].backends[0].maxConnections)
    self.assertIsNone(result[0].backends[0].maxConnectionsPerInstance)

    result = self.Run('compute backend-services update-backend {0} '
                      '--instance-group {1} --instance-group-zone {2} '
                      '--balancing-mode CONNECTION '
                      '--global'.format(bs_name, ig_name, self.zone))

    self.assertEqual(1, len(result))
    self.assertEqual('CONNECTION', str(result[0].backends[0].balancingMode))
    self.assertEqual(200, result[0].backends[0].maxConnections)

  def testPatch(self):
    """Verifies backend service update via PATCH API."""
    hc_name = self.CreateHealthCheck()
    bs_name = self.CreateTcpBackendService(hc_name)

    # Update description
    result = self.Run('compute backend-services update {0} --description {1} '
                      '--global'.format(bs_name, 'new-desc'))
    self.assertEqual(1, len(result))
    self.assertEqual('new-desc', result[0].description)

    # Clear description
    result = self.Run('compute backend-services update {0} --description {1} '
                      '--global'.format(bs_name, '""'))
    self.assertEqual(1, len(result))
    self.assertEqual('', result[0].description)

  def TearDown(self):
    for name in self.backend_service_names:
      self.CleanUpResource(
          name, 'backend-services', scope=e2e_test_base.EXPLICIT_GLOBAL)
    for name in self.health_check_names:
      self.CleanUpResource(
          name,
          'health-checks',
          scope=e2e_test_base.EXPLICIT_GLOBAL
          if self.track == calliope_base.ReleaseTrack.ALPHA else
          e2e_test_base.GLOBAL)
    for name in self.http_health_check_names:
      self.CleanUpResource(
          name, 'http-health-checks', scope=e2e_test_base.GLOBAL)
    self.DeleteResources(self.instance_names, self.DeleteInstance, 'instance')
    self.DeleteResources(self.instance_group_names, self.DeleteInstanceGroup,
                         'instance group')


class BackendServicesTestBeta(BackendServicesTest):

  def SetUp(self):
    self._SetUpReleaseTrack(calliope_base.ReleaseTrack.BETA, 'beta')

  def testCustomRequestHeadersBackendServiceLb(self):
    hc_name = self.CreateHttpHealthCheck()
    bs_name = self.CreateHttpBackendService(hc_name)

    # Update backend service with custom request headers
    self.Run('compute backend-services update {0} --global '
             '--custom-request-header \"Test:\"'.format(bs_name))

    result = self.Run('compute backend-services describe {0} --global'
                      .format(bs_name))
    result_list = resource_projector.MakeSerializable(result)
    self.assertEqual('Test:', result_list['customRequestHeaders'][0])

    # Clear custom request headers
    result = self.Run('compute backend-services update {0} --global '
                      '--no-custom-request-headers'.format(bs_name))
    self.assertEqual(0, len(result[0].customRequestHeaders))


class BackendServicesTestAlpha(BackendServicesTestBeta):

  def SetUp(self):
    self._SetUpReleaseTrack(calliope_base.ReleaseTrack.ALPHA, 'alpha')


if __name__ == '__main__':
  e2e_test_base.main()
