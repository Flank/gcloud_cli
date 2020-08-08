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
"""Test for the backend services update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.backend_services import test_resources
from tests.lib.surface.compute.backend_services.update import test_base


class SessionAffinityApiUpdateTest(test_base.UpdateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self._backend_services_with_gen_cookie_session_affinity = (
        test_resources.BACKEND_SERVICES_WITH_GEN_COOKIE_SESSION_AFFINITY_V1)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)

  # Test that an update request which does not mention session
  # affinity does not change anything
  def testUnchanged(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_with_gen_cookie_session_affinity[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --description "whatever"')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='whatever',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30,
                  sessionAffinity=(
                      messages.BackendService.SessionAffinityValueValuesEnum.
                      GENERATED_COOKIE),
                  affinityCookieTtlSec=18),
              project='my-project'))],
    )

  # Test that setting session affinity to "none" works
  def testNone(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_with_gen_cookie_session_affinity[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --session-affinity none')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30,
                  sessionAffinity=(messages.BackendService.
                                   SessionAffinityValueValuesEnum.NONE),
                  affinityCookieTtlSec=18),
              project='my-project'))],
    )

  # Test that setting session affinity to "client_ip" works
  def testClientIp(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_with_gen_cookie_session_affinity[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --session-affinity client_ip')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30,
                  sessionAffinity=(messages.BackendService.
                                   SessionAffinityValueValuesEnum.CLIENT_IP),
                  affinityCookieTtlSec=18),
              project='my-project'))],
    )

  # Test that setting session affinity to "generated_cookie" works
  def testGeneratedCookie(self):
    messages = self.messages
    self.make_requests.side_effect = iter([[self._backend_services[0]], [],])

    self.RunUpdate('backend-service-1 --session-affinity generated_cookie')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30,
                  sessionAffinity=(
                      messages.BackendService.SessionAffinityValueValuesEnum.
                      GENERATED_COOKIE)),
              project='my-project'))],
    )

  # Test that setting session affinity cookie TTL works
  def testAffinityTtl(self):
    messages = self.messages
    self.make_requests.side_effect = iter([[self._backend_services[0]], [],])

    self.RunUpdate('backend-service-1 --affinity-cookie-ttl 18')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30,
                  affinityCookieTtlSec=18),
              project='my-project'))],
    )

  # Test that setting session affinity and cookie TTL at the same time
  # works
  def testGeneratedCookieAffinityTtl(self):
    messages = self.messages
    self.make_requests.side_effect = iter([[self._backend_services[0]], [],])

    self.RunUpdate('backend-service-1 '
                   '--session-affinity generated_cookie '
                   '--affinity-cookie-ttl 18')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30,
                  sessionAffinity=(
                      messages.BackendService.SessionAffinityValueValuesEnum.
                      GENERATED_COOKIE),
                  affinityCookieTtlSec=18),
              project='my-project'))])


class SessionAffinityApiUpdateBetaTest(SessionAffinityApiUpdateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self._backend_services = test_resources.BACKEND_SERVICES_BETA
    self._backend_services_with_gen_cookie_session_affinity = (
        test_resources.BACKEND_SERVICES_WITH_GEN_COOKIE_SESSION_AFFINITY_BETA)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)


class SessionAffinityApiUpdateAlphaTest(SessionAffinityApiUpdateBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._backend_services = test_resources.BACKEND_SERVICES_ALPHA
    self._backend_services_with_gen_cookie_session_affinity = (
        test_resources.BACKEND_SERVICES_WITH_GEN_COOKIE_SESSION_AFFINITY_ALPHA)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)

  # Test that setting session affinity to "client_ip_no_destination" works
  def testClientIpNoDestination(self):
    messages = self.messages
    orig_backend_service = messages.BackendService(
        backends=[],
        description='my backend service',
        healthChecks=[(self.compute_uri + '/projects/my-project/global'
                       '/httpHealthChecks/my-health-check')],
        name='backend-service-1',
        portName='tcp',
        loadBalancingScheme=(messages.BackendService
                             .LoadBalancingSchemeValueValuesEnum.INTERNAL),
        sessionAffinity=messages.BackendService.SessionAffinityValueValuesEnum
        .NONE,
        protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=(self.compute_uri + '/projects/my-project'
                  '/region/alaska/backendServices/backend-service-1'),
        timeoutSec=30)
    self.make_requests.side_effect = iter([
        [orig_backend_service],
        [],
    ])

    self.RunUpdate(
        'backend-service-1 --region alaska '
        '--session-affinity client_ip_no_destination',
        use_global=False)

    self.CheckRequests(
        [(self.compute.regionBackendServices, 'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='backend-service-1',
              project='my-project',
              region='alaska'))],
        [(self.compute.regionBackendServices, 'Patch',
          messages.ComputeRegionBackendServicesPatchRequest(
              backendService='backend-service-1',
              region='alaska',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='tcp',
                  loadBalancingScheme=messages.BackendService
                  .LoadBalancingSchemeValueValuesEnum.INTERNAL,
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/region/alaska/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30,
                  sessionAffinity=(
                      messages.BackendService.SessionAffinityValueValuesEnum
                      .CLIENT_IP_NO_DESTINATION)),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
