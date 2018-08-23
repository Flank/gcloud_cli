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
"""Tests for the backend services update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class UpdateTestBase(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')

    self._backend_services = test_resources.BACKEND_SERVICES_V1

    self._http_backend_services_with_legacy_health_check = (
        test_resources.HTTP_BACKEND_SERVICES_WITH_LEGACY_HEALTH_CHECK_V1)
    self._https_backend_services_with_legacy_health_check = (
        test_resources.HTTPS_BACKEND_SERVICES_WITH_LEGACY_HEALTH_CHECK_V1)

    self._http_backend_services_with_health_check = (
        test_resources.HTTP_BACKEND_SERVICES_WITH_HEALTH_CHECK_V1)
    self._https_backend_services_with_health_check = (
        test_resources.HTTPS_BACKEND_SERVICES_WITH_HEALTH_CHECK_V1)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)


class BackendServiceUpdateTest(UpdateTestBase):

  def testScopeWarning(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])
    self.RunUpdate('backend-service-1 --description "my new description"')
    self.AssertErrNotContains('WARNING:')

  def testWithNoFlags(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.RunUpdate('backend-service-1')

    self.CheckRequests()

  def testNoChange(self):
    messages = self.messages
    self.make_requests.side_effect = [[self._backend_services[0]]]

    self.RunUpdate('backend-service-1 --port-name http')

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1',
              project='my-project'))],
    )

    self.AssertErrEquals(
        'No change requested; skipping update for [backend-service-1].\n',
        normalize_space=True)

  def testWithNewDescription(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],

        [],
    ])

    self.RunUpdate('backend-service-1 --description "my new description"')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my new description',
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
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithDescriptionRemoval(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],

        [],
    ])

    self.RunUpdate('backend-service-1 --description ""')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  description='',
                  backends=[],
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
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithHttpHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],

        [],
    ])

    self.RunUpdate('backend-service-1 --http-health-checks '
                   'http-health-check-1,http-health-check-2')

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
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'http-health-check-1'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'http-health-check-2')],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithDeprectatedFlag(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--http-health-checks my-other-health-check')

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
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'my-other-health-check')],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithTimeout(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --timeout 10s')

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
                  timeoutSec=10),
              project='my-project'))],
    )

  def testWithPortName(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --port-name my-port-name')

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
                  portName='my-port-name',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBothHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._https_backend_services_with_legacy_health_check[0]],
        [],
    ])

    self.RunUpdate(
        'backend-service-1 '
        '--http-health-checks http-health-check-1,http-health-check-2 '
        '--https-health-checks https-health-check-1,https-health-check-2')

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
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'http-health-check-1'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'http-health-check-2'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/httpsHealthChecks/'
                                 'https-health-check-1'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/httpsHealthChecks/'
                                 'https-health-check-2')],
                  name='backend-service-1',
                  portName='https',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTPS),
                  selfLink=(self.compute_uri + ''
                            '/projects/my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithProtocolHttp(self):
    self.templateTestWithProtocol(
        'backend-service-1 --protocol HTTP',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        self._https_backend_services_with_legacy_health_check[0])

  def testWithProtocolHttpLowerCase(self):
    self.templateTestWithProtocol(
        'backend-service-1 --protocol http',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        self._https_backend_services_with_legacy_health_check[0])

  def testWithProtocolHttps(self):
    self.templateTestWithProtocol(
        'backend-service-1 --protocol HTTPS',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS,
        self._http_backend_services_with_legacy_health_check[0])

  def templateTestWithProtocol(self, cmd, protocol_enum,
                               original_backend_service):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [original_backend_service],
        [],
    ])

    self.RunUpdate(cmd)

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
                       'my-project/global/httpHealthChecks/'
                       'http-health-check'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/'
                       'https-health-check'),
                  ],
                  name='backend-service-1',
                  portName='https',
                  protocol=protocol_enum,
                  selfLink=(self.compute_uri +
                            '/projects/my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testEnableCdn(self):
    self.make_requests.side_effect = [[self._backend_services[0]], []]

    self.RunUpdate('backend-service-1 --enable-cdn')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          self.messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          self.messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=self.messages.BackendService(
                  backends=[],
                  description='my backend service',
                  enableCDN=True,
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=(self.messages.BackendService.
                            ProtocolValueValuesEnum.HTTP),
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testNoEnableCdn(self):
    self.make_requests.side_effect = [[self._backend_services[0]], []]

    self.RunUpdate('backend-service-1 --no-enable-cdn')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          self.messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          self.messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=self.messages.BackendService(
                  backends=[],
                  description='my backend service',
                  enableCDN=False,
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=(self.messages.BackendService.
                            ProtocolValueValuesEnum.HTTP),
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )


class SessionAffinityApiUpdateTest(UpdateTestBase):

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


class SessionAffinityApiUpdateAlphaTest(SessionAffinityApiUpdateTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._backend_services = test_resources.BACKEND_SERVICES_ALPHA
    self._backend_services_with_gen_cookie_session_affinity = (
        test_resources.BACKEND_SERVICES_WITH_GEN_COOKIE_SESSION_AFFINITY_ALPHA)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)


class SessionAffinityApiUpdateBetaTest(SessionAffinityApiUpdateTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self._backend_services = test_resources.BACKEND_SERVICES_BETA
    self._backend_services_with_gen_cookie_session_affinity = (
        test_resources.BACKEND_SERVICES_WITH_GEN_COOKIE_SESSION_AFFINITY_BETA)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)


class BackendServiceWithConnectionDrainingTimeoutApiUpdateTest(UpdateTestBase):

  def SetUp(self):
    self._backend_services_with_connection_draining_timeout = (
        test_resources.BACKEND_SERVICES_WITH_CONNECTION_DRAINING_TIMEOUT)

  def testChangeConnectionDrainingTimeout(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_with_connection_draining_timeout[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--connection-draining-timeout 200')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  connectionDraining=messages.ConnectionDraining(
                      drainingTimeoutSec=200),
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
                            'backend-service-1')),
              project='my-project'))],
    )

  def testChangeConnectionDrainingTimeoutInMinutes(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_with_connection_draining_timeout[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--connection-draining-timeout 3m')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  connectionDraining=messages.ConnectionDraining(
                      drainingTimeoutSec=180),
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
                            'backend-service-1')),
              project='my-project'))],
    )

  def testChangeOnlyConnectionDrainingTimeout(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_with_connection_draining_timeout[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--connection-draining-timeout 180')

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
                  connectionDraining=messages.ConnectionDraining(
                      drainingTimeoutSec=180),
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1')),
              project='my-project'))],
    )

  def testChangeOnlyConnectionDrainingTimeoutToZero(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_with_connection_draining_timeout[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--connection-draining-timeout 0')

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
                  connectionDraining=messages.ConnectionDraining(
                      drainingTimeoutSec=0),
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1')),
              project='my-project'))],
    )


class WithHealthcheckApiTest(UpdateTestBase):

  def testWithHttpHealthChecksUpdatedToHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate(
        'backend-service-1 --health-checks health-check-1,health-check-2')

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
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/healthChecks/'
                                 'health-check-1'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/healthChecks/'
                                 'health-check-2')],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithHttpsHealthChecksUpdatedToHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._https_backend_services_with_health_check[0]],
        [],
    ])

    self.RunUpdate('backend-service-3 --health-checks health-check-1')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-3', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/healthChecks/'
                                 'health-check-1')],
                  name='backend-service-3',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTPS),
                  selfLink=(self.compute_uri +
                            '/projects/my-project/global/backendServices/'
                            'backend-service-3'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithHealthChecksUpdatedToHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._http_backend_services_with_health_check[0]],
        [],
    ])

    self.RunUpdate('backend-service-3 --health-checks new-health-check')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-3', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/healthChecks/'
                                 'new-health-check')],
                  name='backend-service-3',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  selfLink=(self.compute_uri +
                            '/projects/my-project/global/backendServices/'
                            'backend-service-3'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testMixingHealthCheckAndHttpHealthCheck(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])
    with self.AssertRaisesToolExceptionRegexp(
        'Mixing --health-checks with --http-health-checks or with '
        '--https-health-checks is not supported.'):
      self.RunUpdate('my-backend-service '
                     '--health-checks foo '
                     '--http-health-checks bar')

  def testMixingHealthCheckAndHttpsHealthCheck(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])
    with self.AssertRaisesToolExceptionRegexp(
        'Mixing --health-checks with --http-health-checks or with '
        '--https-health-checks is not supported.'):
      self.RunUpdate('my-backend-service --health-checks foo '
                     '--https-health-checks bar')

  def testRegionWithHealthChecksUpdatedToHealthChecks(self):
    messages = self.messages
    orig_backend_service = messages.BackendService(
        backends=[],
        description='my backend service',
        healthChecks=[
            (self.compute_uri + '/projects/my-project/global'
             '/httpHealthChecks/my-health-check')
        ],
        name='backend-service-3',
        portName='http',
        protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=(self.compute_uri + '/projects/my-project'
                  '/region/alaska/backendServices/backend-service-1'),
        timeoutSec=30)
    self.make_requests.side_effect = iter([
        [orig_backend_service],
        [],
    ])

    updated_backend_service = copy.deepcopy(orig_backend_service)
    updated_backend_service.healthChecks = [
        self.compute_uri +
        '/projects/my-project/global/healthChecks/new-health-check'
    ]

    self.RunUpdate('backend-service-3 --region alaska '
                   '--health-checks new-health-check',
                   use_global=False)

    self.CheckRequests(
        [(self.compute.regionBackendServices, 'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='backend-service-3',
              region='alaska',
              project='my-project'))],
        [(self.compute.regionBackendServices, 'Patch',
          messages.ComputeRegionBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=updated_backend_service,
              region='alaska',
              project='my-project'))],
    )


class WithCustomCacheKeysApiUpdateTest(UpdateTestBase):
  """Tests custom cache key update flags.

  Cache key policy attributes:
    backend_services_include_all_custom_cache_key:
      Cache keys include host, protocol, and query strings with no white list
      or black list set.
    backend_services_exclude_all_custom_cache_key:
      Cache keys exclude host, protocol, and query strings. This is a contrived
      case used for testing.
    backend_services_include_all_custom_cache_key_with_whitelist:
      Cache keys include host, protocol, and query strings and the whitelist is
      set to be nonempty.
    backend_services_include_all_custom_cache_key_with_blacklist:
      Cache keys include host, protocol, and query strings and the blacklist is
      set to be nonempty.
  """

  def SetUp(self):
    self._backend_services_include_all_custom_cache_key = (
        test_resources.MakeBackendServicesWithCustomCacheKey(
            self.messages, 'v1'))
    self._backend_services_exclude_all_custom_cache_key = (
        test_resources.MakeBackendServicesWithCustomCacheKey(
            self.messages,
            'v1',
            include_host=False,
            include_protocol=False,
            include_query_string=False))
    self._backend_services_include_all_custom_cache_key_with_whitelist = (
        test_resources.MakeBackendServicesWithCustomCacheKey(
            self.messages, 'v1'))
    self._backend_services_include_all_custom_cache_key_with_blacklist = (
        test_resources.MakeBackendServicesWithCustomCacheKey(
            self.messages, 'v1', blacklist=['contentid', 'language']))

  def testUnchanged(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=True))),
              project='my-project'))],
    )

  def testCacheKeyIncludeHost(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_exclude_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--cache-key-include-host')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=False,
                          includeQueryString=False))),
              project='my-project'))],
    )

  def testCacheKeyExcludeHost(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--no-cache-key-include-host')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=False,
                          includeProtocol=True,
                          includeQueryString=True))),
              project='my-project'))],
    )

  def testCacheKeyIncludeProtocol(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_exclude_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--cache-key-include-protocol')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=False,
                          includeProtocol=True,
                          includeQueryString=False))),
              project='my-project'))],
    )

  def testCacheKeyExcludeProtocol(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--no-cache-key-include-protocol')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=False,
                          includeQueryString=True))),
              project='my-project'))],
    )

  def testCacheKeyIncludeQueryString(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_exclude_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--cache-key-include-query-string')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=False,
                          includeProtocol=False,
                          includeQueryString=True))),
              project='my-project'))],
    )

  def testCacheKeyExcludeQueryString(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--no-cache-key-include-query-string')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=False))),
              project='my-project'))],
    )

  def testCacheKeyQueryStringBlacklist(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--cache-key-query-string-blacklist=contentid,language')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=True,
                          queryStringBlacklist=['contentid', 'language'],
                          queryStringWhitelist=[]))),
              project='my-project'))],
    )

  def testCacheKeyQueryStringBlacklistEmpty(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--cache-key-query-string-blacklist=')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=True,
                          queryStringBlacklist=[],
                          queryStringWhitelist=[]))),
              project='my-project'))],
    )

  def testCacheKeyQueryStringWhitelist(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--cache-key-query-string-whitelist=contentid,language')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=True,
                          queryStringBlacklist=[],
                          queryStringWhitelist=['contentid', 'language']))),
              project='my-project'))],
    )

  def testExcludeQueryStringShouldRemoveBlacklist(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key_with_blacklist],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--no-cache-key-include-query-string')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=False,
                          queryStringBlacklist=[],
                          queryStringWhitelist=[]))),
              project='my-project'))],
    )

  def testExcludeQueryStringShouldRemoveWhitelist(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key_with_whitelist],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--description "whatever" '
                   '--no-cache-key-include-query-string')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=False,
                          queryStringBlacklist=[],
                          queryStringWhitelist=[]))),
              project='my-project'))],
    )

  def testEnableWhitelistWithExcludedQueryString(self):
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
        [],
    ])
    with self.assertRaisesRegex(
        backend_services_utils.CacheKeyQueryStringException,
        'cache-key-query-string-whitelist and cache-key-query-string-blacklist'
        ' may only be set when cache-key-include-query-string is enabled.'):
      self.RunUpdate('my-backend-service '
                     '--no-cache-key-include-query-string '
                     '--cache-key-query-string-whitelist=contentid,language')

  def testEnableBlacklistWithExcludedQueryString(self):
    self.make_requests.side_effect = iter([
        [self._backend_services_include_all_custom_cache_key],
        [],
    ])
    with self.assertRaisesRegex(
        backend_services_utils.CacheKeyQueryStringException,
        'cache-key-query-string-whitelist and cache-key-query-string-blacklist'
        ' may only be set when cache-key-include-query-string is enabled.'):
      self.RunUpdate('my-backend-service '
                     '--no-cache-key-include-query-string '
                     '--cache-key-query-string-blacklist=campaignid')

  def testEnableWhitelistWithExistingExcludedQueryString(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_exclude_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--cache-key-query-string-whitelist=contentid,language')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=False,
                          includeProtocol=False,
                          includeQueryString=True,
                          queryStringBlacklist=[],
                          queryStringWhitelist=['contentid', 'language']))),
              project='my-project'))],
    )

  def testEnableBlacklistWithExistingExcludedQueryString(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services_exclude_all_custom_cache_key],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--cache-key-query-string-blacklist=campaignid')

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
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=False,
                          includeProtocol=False,
                          includeQueryString=True,
                          queryStringBlacklist=['campaignid'],
                          queryStringWhitelist=[]))),
              project='my-project'))],
    )


class WithIAPApiTest(UpdateTestBase):

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self._lb_warning = (
        'WARNING: IAP only protects requests that go through the Cloud Load '
        'Balancer. See the IAP documentation for important security best '
        'practices: https://cloud.google.com/iap/\n')
    self._non_https_warning = (
        'WARNING: IAP has been enabled for a backend service that does not use '
        'HTTPS. Data sent from the Load Balancer to your VM will not be '
        'encrypted.\n')

  def CheckResults(self, expected_message):
    self.CheckResultsWithProtocol(
        expected_message,
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP)

  def CheckResultsWithProtocol(self, expected_message, protocol):
    messages = self.messages
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
                  iap=expected_message,
                  name='backend-service-1',
                  portName='http',
                  protocol=protocol,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithIAPDisabled(self):
    self.RunUpdate(
        'backend-service-1 --iap disabled')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False))
    self.AssertErrEquals('')

  def testWithIAPEnabled(self):
    self.RunUpdate(
        'backend-service-1 --iap enabled')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True))

  def testWithIAPEnabledAndNonHttpsProtocol(self):
    self.RunUpdate(
        'backend-service-1 --iap enabled --protocol=HTTP')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True))
    self.AssertErrEquals(self._lb_warning + self._non_https_warning)

  def testWithIAPEnabledAndHttpsProtocol(self):
    self.RunUpdate(
        'backend-service-1 --iap enabled --protocol=HTTPS')
    self.CheckResultsWithProtocol(
        self.messages.BackendServiceIAP(enabled=True),
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS)
    self.AssertErrEquals(self._lb_warning)

  def testWithIAPDisabledAndNonHttpsProtocol(self):
    self.RunUpdate(
        'backend-service-1 --iap disabled --protocol=HTTP')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False))
    self.AssertErrEquals('')

  def testWithIAPDisabledAndHttpsProtocol(self):
    self.RunUpdate(
        'backend-service-1 --iap disabled --protocol=HTTPS')
    self.CheckResultsWithProtocol(
        self.messages.BackendServiceIAP(enabled=False),
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS)
    self.AssertErrEquals('')

  def testWithIAPEnabledWithCredentials(self):
    self.RunUpdate(
        'backend-service-1 '
        '--iap enabled,oauth2-client-id=CLIENTID,oauth2-client-secret=SECRET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True,
        oauth2ClientId='CLIENTID',
        oauth2ClientSecret='SECRET'))

  def testWithIAPEnabledWithCredentialsWithEmbeddedEquals(self):
    self.RunUpdate(
        'backend-service-1 '
        '--iap enabled,oauth2-client-id=CLIENT=ID,oauth2-client-secret=SEC=RET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True,
        oauth2ClientId='CLIENT=ID',
        oauth2ClientSecret='SEC=RET'))

  def testWithIAPCredentialsOnly(self):
    # If enabled isn't specified, it isn't modified.

    # Previous state has enabled=False.
    self.RunUpdate(
        'backend-service-1 '
        '--iap oauth2-client-id=NEW-ID,oauth2-client-secret=NEW-SECRET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False,
        oauth2ClientId='NEW-ID',
        oauth2ClientSecret='NEW-SECRET'))

    # Previous state has enabled=True.
    old_iap = self._backend_services[0].iap
    try:
      self._backend_services[0].iap = self.messages.BackendServiceIAP(
          enabled=True,
          oauth2ClientId='ID',
          oauth2ClientSecret='SECRET')
      self.make_requests.side_effect = [[self._backend_services[0]], []]
      self.RunUpdate(
          'backend-service-1 '
          '--iap oauth2-client-id=NEW-ID,oauth2-client-secret=NEW-SECRET')
      self.CheckResults(self.messages.BackendServiceIAP(
          enabled=True,
          oauth2ClientId='NEW-ID',
          oauth2ClientSecret='NEW-SECRET'))
    finally:
      self._backend_services[0].iap = old_iap

  def testInvalidIAPEmpty(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'^Invalid value for \[--iap\]: Must provide value when specifying '
        r'--iap$',
        self.RunUpdate, 'backend-service-1 --iap=""')

  def testInvalidIapArgCombinationEnabledDisabled(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Must specify only one '
        'of \\[enabled\\] or \\[disabled\\]$',
        self.RunUpdate, 'backend-service-1 --iap enabled,disabled')

  def testInvalidIapArgCombinationEnabledOnlyClientId(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.RunUpdate,
        'backend-service-1 --iap enabled,oauth2-client-id=CLIENTID')

  def testInvalidIapArgCombinationEnabledOnlyClientSecret(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.RunUpdate,
        'backend-service-1 --iap enabled,oauth2-client-secret=SECRET')

  def testInvalidIapArgCombinationEmptyIdValue(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.RunUpdate,
        'backend-service-1 '
        '--iap enabled,oauth2-client-id=,oauth2-client-secret=SECRET')

  def testInvalidIapArgCombinationEmptySecretValue(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.RunUpdate,
        'backend-service-1 '
        '--iap enabled,oauth2-client-id=CLIENTID,oauth2-client-secret=')

  def testInvalidIapArgInvalidSubArg(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'^Invalid value for \[--iap\]: Invalid sub-argument \'invalid-arg1\'$',
        self.RunUpdate,
        'backend-service-1 --iap enabled,invalid-arg1=VAL1,invalid-arg2=VAL2')


class WithCdnSignedUrlApiUpdateTest(UpdateTestBase):
  """Tests CDN Signed URL update flags."""

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

  def CheckRequestMadeWithCdnPolicy(self, expected_message):
    """Verifies the request was made with the expected CDN policy."""
    messages = self.messages
    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  cdnPolicy=expected_message,
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
                  timeoutSec=30),
              project='my-project'))],
    )

  def testSetValidCacheMaxAge(self):
    """Tests updating backend service with a valid cache max age."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 456789
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=456789))

  def testUpdateWithCacheMaxAgeZero(self):
    """Tests updating backend service with a cache max age of 0."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 0
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=0))

  def testUpdateWithCacheMaxAgeSeconds(self):
    """Tests updating backend service with a cache max age in seconds."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 7890s
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=7890))

  def testUpdateWithCacheMaxAgeMinutes(self):
    """Tests updating backend service with a cache max age in minutes."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 234m
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=234 * 60))

  def testUpdateWithCacheMaxAgeHours(self):
    """Tests updating backend service with a cache max age in hours."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 38h
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=38 * 60 *
                                              60))

  def testUpdateWithCacheMaxAgeDays(self):
    """Tests updating backend service with a cache max age in days."""
    self.RunUpdate("""
        backend-service-1 --signed-url-cache-max-age 99d
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=99 * 24 *
                                              60 * 60))

  def testSetInvalidCacheMaxAge(self):
    """Tests updating backend service with an invalid cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --signed-url-cache-max-age: given value must be of the form '
        r'INTEGER\[UNIT\] where units can be one of s, m, h, d; received: '
        r'invalid-value'):
      self.RunUpdate("""
          backend-service-1 --signed-url-cache-max-age invalid-value
          """)

  def testSetCacheMaxAgeNegative(self):
    """Tests updating backend service with a negative cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --signed-url-cache-max-age: given value must be of the form '
        r'INTEGER\[UNIT\] where units can be one of s, m, h, d; received: -1'):
      self.RunUpdate("""
          backend-service-1 --signed-url-cache-max-age -1
          """)


if __name__ == '__main__':
  test_case.main()
