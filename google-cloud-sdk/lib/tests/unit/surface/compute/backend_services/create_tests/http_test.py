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
"""Tests for the backend services create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.backend_services.create import test_base


class HttpBackendServiceCreateTest(test_base.BackendServiceCreateTestBase):

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
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
        --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                healthChecks=[],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30),
            project='my-project'))],)

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

  def testWrongProtocol(self):
    with self.AssertRaisesExceptionRegexp(
        ValueError,
        'HBHBH is not a supported option\. See the help text of --protocol for supported options.'): # pylint:disable=line-too-long
      self.Run("""
      compute backend-services create test --global --protocol HBHBH""")


class BetaBackendServiceCreateTest(test_base.BackendServiceCreateTestBase):

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


if __name__ == '__main__':
  test_case.main()
