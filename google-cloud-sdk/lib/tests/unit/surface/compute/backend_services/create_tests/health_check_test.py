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


class WithHealthcheckApiTest(test_base.BackendServiceCreateTestBase):

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
                --network default
                --protocol TCP
                --connection-draining-timeout=120""")

    self.CheckRequests([
        (self.compute.regionBackendServices, 'Insert',
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
                 network=self.compute_uri +
                 '/projects/my-project/global/networks/default',
                 connectionDraining=messages.ConnectionDraining(
                     drainingTimeoutSec=120),
                 timeoutSec=30,
             ),
             project='my-project',
             region='alaska',
         ))
    ],)

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
                      ('https://compute.googleapis.com/compute/alpha/projects/'
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

  def testGlobalCustomRequestHeader(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --global
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --custom-request-header 'Test-Header:'
          --custom-request-header 'Test-Header2: {CLIENT_REGION}'
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
                timeoutSec=30,
                customRequestHeaders=[
                    'Test-Header:', 'Test-Header2: {CLIENT_REGION}'
                ]),
            project='my-project'))],)

  def testRegionalCustomRequestHeader(self):
    messages = self.messages
    self.Run("""
          compute backend-services create my-backend-service
          --region=alaska
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --custom-request-header 'Test-Header:'
          --custom-request-header 'Test-Header2: {CLIENT_REGION}'
        """)

    self.CheckRequests([
        (self.compute.regionBackendServices, 'Insert',
         messages.ComputeRegionBackendServicesInsertRequest(
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
                 loadBalancingScheme=(
                     messages.BackendService.LoadBalancingSchemeValueValuesEnum
                     .EXTERNAL),
                 protocol=(messages.BackendService.ProtocolValueValuesEnum.TCP),
                 timeoutSec=30,
                 customRequestHeaders=[
                     'Test-Header:', 'Test-Header2: {CLIENT_REGION}'
                 ]),
             project='my-project',
             region='alaska',
         ))
    ],)


class WithHealthcheckApiBetaTest(test_base.BackendServiceCreateTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)

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


class WithHealthcheckApiAlphaTest(WithHealthcheckApiBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
