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
"""Tests for the backend services create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class BackendServiceCreateTestBase(test_base.BaseTest):

  def _GetApiName(self, release_track):
    """Returns the API name for the specified release track."""
    if release_track == calliope_base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif release_track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  def _SetUp(self, release_track):
    """Setup common test components.

    Args:
      release_track: Release track the test is targeting.
    """
    self.SelectApi(self._GetApiName(release_track))
    self.track = release_track

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)


class HttpBackendServiceCreateTest(BackendServiceCreateTestBase):

  def testSimpleCase(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-2')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],
    )

    self.AssertErrNotContains('WARNING: ')

  def testProtocolFlag(self):
    self.templateTestProtocolFlag("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1,my-health-check-2
          --protocol HTTP
          --global
        """)

  def testProtocolFlagLowerCase(self):
    self.templateTestProtocolFlag("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1,my-health-check-2
          --protocol http
          --global
        """)

  def templateTestProtocolFlag(self, cmd):
    messages = self.messages
    self.Run(cmd)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-2')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testDeprecatedFlag(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testDeprecatedFlagUri(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks {uri}/projects/my-project/global/httpHealthChecks/my-health-check
          --global
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithPortName(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check
          --port-name http1
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='http1',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithTimeout(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check
          --timeout 1m
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=60),
              project='my-project'))],
    )

  def testUriSupport(self):
    messages = self.messages
    self.Run("""
        compute backend-services create
          {uri}/projects/my-project/global/backendServices/my-backend-service
          --http-health-checks
            {uri}/projects/my-project/global/httpHealthChecks/my-health-check-1,{uri}/projects/my-project/global/httpHealthChecks/my-health-check-2
          --global
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-2')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithoutHealthChecks(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one health check required.'):
      self.Run("""
          compute backend-services create my-backend-service
          --global
          """)
    self.CheckRequests()

  def testSimpleHttpsCase(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --protocol HTTPS
          --https-health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/my-health-check-2')
                  ],
                  name='my-backend-service',
                  portName='https',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTPS),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testBothHealthChecks(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --protocol HTTPS
          --http-health-checks http-check-1,http-check-2
          --https-health-checks https-check-1,https-check-2
          --description "My backend service"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/http-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/http-check-2'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/https-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/https-check-2')
                  ],
                  name='my-backend-service',
                  portName='https',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTPS),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testHttpsWithPortName(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --protocol HTTPS
          --https-health-checks my-health-check
          --port-name https1
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='https1',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTPS),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testHttpsWithTimeout(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --protocol HTTPS
          --https-health-checks my-health-check
          --timeout 1m
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='https',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTPS),
                  timeoutSec=60),
              project='my-project'))],
    )

  def testHttpsUriSupport(self):
    messages = self.messages
    self.Run("""
        compute backend-services create
          {uri}/projects/my-project/global/backendServices/my-backend-service
          --protocol HTTPS
          --https-health-checks
            {uri}/projects/my-project/global/httpsHealthChecks/my-health-check-1,{uri}/projects/my-project/global/httpsHealthChecks/my-health-check-2
          --global
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/my-health-check-2'),
                  ],
                  name='my-backend-service',
                  portName='https',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTPS),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testHttpsWithDeprecatedFlag(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --protocol HTTPS
          --http-health-checks my-health-check
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check'),
                  ],
                  name='my-backend-service',
                  portName='https',
                  protocol=(messages.BackendService
                            .ProtocolValueValuesEnum.HTTPS),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testEnableCdn(self):
    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check
          --enable-cdn
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        self.messages.ComputeBackendServicesInsertRequest(
            backendService=self.messages.BackendService(
                backends=[],
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check')
                ],
                name='my-backend-service',
                enableCDN=True,
                portName='http',
                protocol=(
                    self.messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30),
            project='my-project'))],)


class BetaBackendServiceCreateTest(BackendServiceCreateTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)

  def testEnableCdnNotSpecified(self):
    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          self.messages.ComputeBackendServicesInsertRequest(
              backendService=self.messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(self.messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testEnableCdn(self):
    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check
          --enable-cdn
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Insert',
          self.messages.ComputeBackendServicesInsertRequest(
              backendService=self.messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  enableCDN=True,
                  portName='http',
                  protocol=(self.messages.BackendService
                            .ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],
    )


class WithSessionAffinityApiTest(BackendServiceCreateTestBase):

  # Tests that default settings are applied to affinity and cookie TTL
  # if not specified
  def testDefault(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30),
            project='my-project'))],)

  # Test setting client IP-based affinity
  def testClientIp(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --session-affinity client_ip
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                sessionAffinity=
                (messages.BackendService.SessionAffinityValueValuesEnum
                 .CLIENT_IP)),
            project='my-project'))],)

  # Test setting generated cookie affinity with the default TTL (0)
  def testGeneratedCookieNoTtl(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --session-affinity generated_cookie
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                sessionAffinity=
                (messages.BackendService.SessionAffinityValueValuesEnum
                 .GENERATED_COOKIE)),
            project='my-project'))],)

  # Test setting generated cookie affinity with a specific TTL
  def testGeneratedCookieWithTtl(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --session-affinity generated_cookie
          --affinity-cookie-ttl 18
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                sessionAffinity=
                (messages.BackendService.SessionAffinityValueValuesEnum
                 .GENERATED_COOKIE),
                affinityCookieTtlSec=18),
            project='my-project'))],)


class WithSessionAffinityApiBetaTest(WithSessionAffinityApiTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class WithSessionAffinityApiAlphaTest(WithSessionAffinityApiBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


class WithConnectionDrainingTimeoutApiTest(BackendServiceCreateTestBase):

  def testConnectionDrainingTimeout(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --connection-draining-timeout 120
          --global
        """)
    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                connectionDraining=messages.ConnectionDraining(
                    drainingTimeoutSec=120)),
            project='my-project'))],)

  def testConnectionDrainingTimeoutInMinutes(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --connection-draining-timeout 2m
          --global
        """)
    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                connectionDraining=messages.ConnectionDraining(
                    drainingTimeoutSec=120)),
            project='my-project'))],)

  def testConnectionDrainingDisabled(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --connection-draining-timeout 0
          --global
        """)
    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                connectionDraining=messages.ConnectionDraining(
                    drainingTimeoutSec=0)),
            project='my-project'))],)


class WithHealthcheckApiAlphaTest(BackendServiceCreateTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)

  def testGlobalBackendServiceWithGlobalHealthCheck(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --global --global-health-checks
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/healthChecks/my-health-check-1'),
                    (self.compute_uri + '/projects/'
                     'my-project/global/healthChecks/my-health-check-2')
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30),
            project='my-project'))],)

  def testGlobalBackendServiceWithRegionalHealthCheck(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --global --health-checks-region region1
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/my-project/'
                     'regions/region1/healthChecks/my-health-check-1'),
                    (self.compute_uri + '/projects/my-project/'
                     'regions/region1/healthChecks/my-health-check-2')
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30),
            project='my-project'))],)

  def testRegionalBackendServiceWithRegionalHealthCheck(self):
    messages = self.messages
    self.Run("""
           compute backend-services create my-backend-service
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --region region1 --health-checks-region region1
        """)

    self.CheckRequests([
        (self.compute.regionBackendServices, 'Insert',
         messages.ComputeRegionBackendServicesInsertRequest(
             backendService=messages.BackendService(
                 backends=[],
                 loadBalancingScheme=messages.BackendService.
                 LoadBalancingSchemeValueValuesEnum.EXTERNAL,
                 description='My backend service',
                 healthChecks=[
                     (self.compute_uri + '/projects/my-project/'
                      'regions/region1/healthChecks/my-health-check-1'),
                     (self.compute_uri + '/projects/my-project/'
                      'regions/region1/healthChecks/my-health-check-2')
                 ],
                 name='my-backend-service',
                 protocol=(messages.BackendService.ProtocolValueValuesEnum.TCP),
                 timeoutSec=30),
             project='my-project',
             region='region1'))
    ],)

  def testRegionalBackendServiceWithGlobalHealthCheck(self):
    messages = self.messages
    self.Run("""
           compute backend-services create my-backend-service
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --region region1 --global-health-checks
        """)

    self.CheckRequests([
        (self.compute.regionBackendServices, 'Insert',
         messages.ComputeRegionBackendServicesInsertRequest(
             backendService=messages.BackendService(
                 backends=[],
                 loadBalancingScheme=messages.BackendService.
                 LoadBalancingSchemeValueValuesEnum.EXTERNAL,
                 description='My backend service',
                 healthChecks=[(self.compute_uri + '/projects/my-project/'
                                'global/healthChecks/my-health-check-1'),
                               (self.compute_uri + '/projects/my-project/'
                                'global/healthChecks/my-health-check-2')],
                 name='my-backend-service',
                 protocol=(messages.BackendService.ProtocolValueValuesEnum.TCP),
                 timeoutSec=30),
             project='my-project',
             region='region1'))
    ],)


class WithHealthcheckApiTest(BackendServiceCreateTestBase):

  def testSimpleCase(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-2')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],)

  def testHealthCheckUri(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service --health-checks
        {uri}/projects/my-project/global/healthChecks/my-health-check
        --global
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],)

  def testMixingHealthCheckAndHttpHealthCheck(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Mixing --health-checks with --http-health-checks or with '
        '--https-health-checks is not supported.'):
      self.Run("""
            compute backend-services create my-backend-service --health-checks foo
            --http-health-checks bar
            --global
          """)
    self.CheckRequests()

  def testMixingHealthCheckAndHttpsHealthCheck(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Mixing --health-checks with --http-health-checks or with '
        '--https-health-checks is not supported.'):
      self.Run("""
            compute backend-services create my-backend-service --health-checks foo
            --https-health-checks bar
            --global
          """)
    self.CheckRequests()

  def testSimpleTcpCase(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --protocol TCP
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-2')
                  ],
                  name='my-backend-service',
                  portName='tcp',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.TCP),
                  timeoutSec=30),
              project='my-project'))],)

  def testSimpleSslCase(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --protocol SSL
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-2')
                  ],
                  name='my-backend-service',
                  portName='ssl',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.SSL),
                  timeoutSec=30),
              project='my-project'))],)

  def testSslWithPortName(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --protocol SSL
          --health-checks my-health-check
          --port-name ssl1
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='ssl1',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.SSL),
                  timeoutSec=30),
              project='my-project'))],)

  def testSslWithTimeout(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --protocol SSL
          --health-checks my-health-check
          --timeout 1m
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='ssl',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.SSL),
                  timeoutSec=60),
              project='my-project'))],)

  def testSslUriSupport(self):
    messages = self.messages
    self.Run("""
          compute backend-services create {uri}/projects/my-project/global/backendServices/my-backend-service
          --protocol SSL
          --health-checks
            {uri}/projects/my-project/global/healthChecks/my-health-check-1,{uri}/projects/my-project/global/healthChecks/my-health-check-2
          --global
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-2'),
                  ],
                  name='my-backend-service',
                  portName='ssl',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.SSL),
                  timeoutSec=30),
              project='my-project'))],)

  def testInternalWithoutRegionFlag(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Must specify --region for internal load balancer.'):
      self.Run("""compute backend-services create backend-service-24
                  --load-balancing-scheme=internal
                  --health-checks=main-hc --protocol=TCP
                  --global""")

  def testInternalWithAllValidFlags(self):
    messages = self.messages

    self.Run("""compute backend-services create backend-service-25
                --description cheesecake
                --load-balancing-scheme=internal
                --region=alaska
                --health-checks=my-health-check-1
                --protocol TCP
                --connection-draining-timeout=120""")

    self.CheckRequests([(
        self.compute.regionBackendServices, 'Insert',
        messages.ComputeRegionBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/healthChecks/my-health-check-1'),
                ],
                name='backend-service-25',
                description='cheesecake',
                loadBalancingScheme=(
                    messages.BackendService.LoadBalancingSchemeValueValuesEnum
                    .INTERNAL),
                protocol=(messages.BackendService.ProtocolValueValuesEnum.TCP),
                connectionDraining=messages.ConnectionDraining(
                    drainingTimeoutSec=120),
                timeoutSec=30,
            ),
            project='my-project',
            region='alaska',
        )
    )],)

  def testInternalProtocolDefault(self):
    messages = self.messages

    self.Run("""compute backend-services create backend-service-25
                --description cheesecake
                --load-balancing-scheme=internal
                --region=alaska
                --health-checks=my-health-check-1
                --connection-draining-timeout=120""")

    self.CheckRequests([(
        self.compute.regionBackendServices, 'Insert',
        messages.ComputeRegionBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/healthChecks/my-health-check-1'),
                ],
                name='backend-service-25',
                description='cheesecake',
                loadBalancingScheme=(
                    messages.BackendService.LoadBalancingSchemeValueValuesEnum
                    .INTERNAL),
                protocol=(messages.BackendService.ProtocolValueValuesEnum.TCP),
                connectionDraining=messages.ConnectionDraining(
                    drainingTimeoutSec=120),
                timeoutSec=30,
            ),
            project='my-project',
            region='alaska',
        )
    )],)

  def testWithRegionalHealthCheck(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)
    messages = self.messages

    self.Run("""compute backend-services create backend-service-25
                --load-balancing-scheme=internal
                --region=alaska
                --health-checks=my-health-check-1
                --health-checks-region us-central1
                --protocol TCP
                --connection-draining-timeout=120""")

    self.CheckRequests(
        [(self.compute_alpha.regionBackendServices, 'Insert',
          messages.ComputeRegionBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      ('https://www.googleapis.com/compute/alpha/projects/'
                       'my-project/regions/us-central1/healthChecks/'
                       'my-health-check-1'),
                  ],
                  name='backend-service-25',
                  loadBalancingScheme=(
                      messages.BackendService.
                      LoadBalancingSchemeValueValuesEnum.INTERNAL),
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum('TCP')),
                  connectionDraining=messages.ConnectionDraining(
                      drainingTimeoutSec=120),
                  timeoutSec=30,
              ),
              project='my-project',
              region='alaska',
          ))],)


class WithCustomCacheKeyApiTest(BackendServiceCreateTestBase):

  # When no custom cache keys flags are specified, no custom cache key flags
  # should appear in the request.
  def testDefault(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30),
              project='my-project'))],)

  def testCacheKeyExcludeHost(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --no-cache-key-include-host
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=False,
                          includeProtocol=True,
                          includeQueryString=True))),
              project='my-project'))],)

  def testCacheKeyExcludeProtocol(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --no-cache-key-include-protocol
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=False,
                          includeQueryString=True))),
              project='my-project'))],)

  def testCacheKeyExcludeQueryString(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --no-cache-key-include-query-string
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=False))),
              project='my-project'))],)

  def testCacheKeyQueryStringWhitelist(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --cache-key-query-string-whitelist=contentid,language
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=True,
                          queryStringWhitelist=['contentid', 'language']))),
              project='my-project'))],)

  def testCacheKeyQueryStringBlacklist(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
        --http-health-checks my-health-check-1
        --description "My backend service"
        --cache-key-query-string-blacklist=campaign
        --global
        """)
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  timeoutSec=30,
                  cdnPolicy=messages.BackendServiceCdnPolicy(
                      cacheKeyPolicy=messages.CacheKeyPolicy(
                          includeHost=True,
                          includeProtocol=True,
                          includeQueryString=True,
                          queryStringBlacklist=['campaign']))),
              project='my-project'))],)

  def testEnableWhitelistWithExcludeQueryString(self):
    with self.assertRaisesRegex(
        backend_services_utils.CacheKeyQueryStringException,
        'cache-key-query-string-whitelist and cache-key-query-string-blacklist'
        ' may only be set when cache-key-include-query-string is enabled.'):
      self.Run("""compute backend-services create my-backend-service
                  --health-checks my-health-check
                  --no-cache-key-include-query-string
                  --cache-key-query-string-whitelist=contentid,language
                  --global""")
    self.CheckRequests()

  def testEnableBlacklistWithExcludeQueryString(self):
    with self.assertRaisesRegex(
        backend_services_utils.CacheKeyQueryStringException,
        'cache-key-query-string-whitelist and cache-key-query-string-blacklist'
        ' may only be set when cache-key-include-query-string is enabled.'):
      self.Run("""
          compute backend-services create my-backend-service
          --health-checks my-health-check
          --no-cache-key-include-query-string
          --cache-key-query-string-blacklist=campaignid
          --global
          """)
    self.CheckRequests()


class WithIAPApiTest(BackendServiceCreateTestBase):

  def SetUp(self):
    self._create_service_cmd_line = (
        'compute backend-services create backend-service-1 '
        '--http-health-checks my-health-check-1 '
        '--description "My backend service" '
        '--global')
    self._lb_warning = (
        'WARNING: IAP only protects requests that go through the Cloud Load '
        'Balancer. See the IAP documentation for important security best '
        'practices: https://cloud.google.com/iap/\n')
    self._non_https_warning = (
        'WARNING: IAP has been enabled for a backend service that does not use '
        'HTTPS. Data sent from the Load Balancer to your VM will not be '
        'encrypted.\n')

  def CheckResultsWithProtocol(self, expected_message, protocol):
    messages = self.messages
    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                iap=expected_message,
                name='backend-service-1',
                portName='http',
                protocol=protocol,
                timeoutSec=30),
            project='my-project'))])

  def CheckResults(self, expected_message):
    self.CheckResultsWithProtocol(
        expected_message,
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP)

  def testWithIAPDisabled(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap disabled')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False))
    self.AssertErrEquals('')

  def testWithIAPEnabled(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True))
    self.AssertErrEquals(self._lb_warning + self._non_https_warning)

  def testWithIAPEnabledAndNonHttpsProtocol(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled --protocol=HTTP')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True))
    self.AssertErrEquals(self._lb_warning + self._non_https_warning)

  def testWithIAPEnabledAndHttpsProtocol(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled --protocol=HTTPS --port-name=http')
    self.CheckResultsWithProtocol(
        self.messages.BackendServiceIAP(enabled=True),
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS)
    self.AssertErrEquals(self._lb_warning)

  def testWithIAPDisabledAndNonHttpsProtocol(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap disabled --protocol=HTTP')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False))
    self.AssertErrEquals('')

  def testWithIAPDisabledAndHttpsProtocol(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap disabled --protocol=HTTPS --port-name=http')
    self.CheckResultsWithProtocol(
        self.messages.BackendServiceIAP(enabled=False),
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS)
    self.AssertErrEquals('')

  def testWithIAPEnabledWithCredentials(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=CLIENTID,oauth2-client-secret=SECRET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True,
        oauth2ClientId='CLIENTID',
        oauth2ClientSecret='SECRET'))

  def testWithIAPEnabledWithCredentialsWithEmbeddedEquals(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=CLIENT=ID,'
        'oauth2-client-secret=SEC=RET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=True,
        oauth2ClientId='CLIENT=ID',
        oauth2ClientSecret='SEC=RET'))

  def testWithIapCredentialsOnly(self):
    self.Run(
        self._create_service_cmd_line +
        ' --iap oauth2-client-id=ID,oauth2-client-secret=SECRET')
    self.CheckResults(self.messages.BackendServiceIAP(
        enabled=False,
        oauth2ClientId='ID',
        oauth2ClientSecret='SECRET'))

  def testInvalidIAPEmpty(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'^Invalid value for \[--iap\]: Must provide value when specifying '
        r'--iap$',
        self.Run, self._create_service_cmd_line + ' --iap=""')

  def testInvalidIapArgCombinationEnabledDisabled(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Must specify only one '
        'of \\[enabled\\] or \\[disabled\\]$',
        self.Run,
        self._create_service_cmd_line + ' --iap enabled,disabled')

  def testInvalidIapArgCombinationEnabledOnlyClientId(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=CLIENTID')

  def testInvalidIapArgCombinationEnabledOnlyClientSecret(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-secret=SECRET')

  def testInvalidIapArgCombinationEmptyIdValue(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=,oauth2-client-secret=SECRET')

  def testInvalidIapArgCombinationEmptySecretValue(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--iap\\]: Both \\[oauth2-client-id\\] and '
        '\\[oauth2-client-secret\\] must be specified together$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,oauth2-client-id=CLIENTID,oauth2-client-secret=')

  def testInvalidIapArgInvalidSubArg(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'^Invalid value for \[--iap\]: Invalid sub-argument \'invalid-arg1\'$',
        self.Run,
        self._create_service_cmd_line +
        ' --iap enabled,invalid-arg1=VAL1,invalid-arg2=VAL2')


class WithCdnSignedUrlApiTest(BackendServiceCreateTestBase):

  def CheckRequestMadeWithCdnPolicy(self, expected_message):
    """Verifies the request was made with the expected CDN policy."""
    messages = self.messages
    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  cdnPolicy=expected_message,
                  description='My backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check-1'),
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  timeoutSec=30),
              project='my-project'))])

  def testCreateWithoutCacheMaxAge(self):
    """Tests creating backend service without cache max age."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        """)
    self.CheckRequestMadeWithCdnPolicy(None)

  def testCreateWithCacheMaxAgeZero(self):
    """Tests creating backend service with cache max age of 0."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 0
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=0))

  def testCreateWithCacheMaxAgeSeconds(self):
    """Tests creating backend service with cache max age in seconds."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 7890s
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=7890))

  def testCreateWithCacheMaxAgeMinutes(self):
    """Tests creating backend service with cache max age in minutes."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 234m
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=234 * 60))

  def testCreateWithCacheMaxAgeHours(self):
    """Tests creating backend service with cache max age in hours."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 38h
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=38 * 60 *
                                              60))

  def testCreateWithCacheMaxAgeDays(self):
    """Tests creating backend service with cache max age in days."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 99d
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(signedUrlCacheMaxAgeSec=99 * 24 *
                                              60 * 60))

  def testSetInvalidCacheMaxAge(self):
    """Tests creating backend service with an invalid cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --signed-url-cache-max-age: given value must be of the form '
        r'INTEGER\[UNIT\] where units can be one of s, m, h, d; received: '
        r'invalid-value'):
      self.Run("""
          compute backend-services create backend-service-1
          --global
          --http-health-checks my-health-check-1
          --signed-url-cache-max-age invalid-value
          """)

  def testSetCacheMaxAgeNegative(self):
    """Tests creating backend service with a negative cache max age."""
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --signed-url-cache-max-age: given value must be of the form '
        r'INTEGER\[UNIT\] where units can be one of s, m, h, d; received: -1'):
      self.Run("""
          compute backend-services create backend-service-1
          --global
          --http-health-checks my-health-check-1
          --description "My backend service"
          --signed-url-cache-max-age -1
          """)

  def testWithCacheMaxAgeAndCacheKeyPolicy(self):
    """Tests creating backend service with both cache max age and cache keys."""
    self.Run("""
        compute backend-services create backend-service-1
        --global
        --http-health-checks my-health-check-1
        --description "My backend service"
        --signed-url-cache-max-age 1234
        --cache-key-query-string-whitelist=foo,bar,baz
        """)
    self.CheckRequestMadeWithCdnPolicy(
        self.messages.BackendServiceCdnPolicy(
            signedUrlCacheMaxAgeSec=1234,
            cacheKeyPolicy=self.messages.CacheKeyPolicy(
                includeHost=True,
                includeProtocol=True,
                includeQueryString=True,
                queryStringWhitelist=['foo', 'bar', 'baz'])))


if __name__ == '__main__':
  test_case.main()
