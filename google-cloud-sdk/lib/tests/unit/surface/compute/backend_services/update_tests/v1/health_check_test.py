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

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.backend_services.update import test_base


class WithHealthcheckApiTest(test_base.UpdateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

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

  def testClearHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._http_backend_services_with_health_check[0]],
        [],
    ])

    self.RunUpdate('backend-service-3 --no-health-checks')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-3', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  healthChecks=[],
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

  def testClearHttpHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --no-health-checks')

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
                  healthChecks=[],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testCombiningHealthChecksAndNoHealthChecks(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])
    with self.AssertRaisesToolExceptionRegexp(
        'Combining --health-checks, --http-health-checks, or '
        '--https-health-checks with --no-health-checks is not supported'):
      self.RunUpdate(
          'my-backend-service --health-checks foo --no-health-checks')

  def testCombiningHttpHealthChecksAndNoHealthChecks(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])
    with self.AssertRaisesToolExceptionRegexp(
        'Combining --health-checks, --http-health-checks, or '
        '--https-health-checks with --no-health-checks is not supported'):
      self.RunUpdate(
          'my-backend-service --http-health-checks foo --no-health-checks')

  def testWithUpdateCustomRequestHeaders(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate(
        'backend-service-1 --global --custom-request-header \'test: \' '
        '--custom-request-header \'another: {client_country}\'')

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
                  customRequestHeaders=['test: ', 'another: {client_country}']),
              project='my-project'))],
    )

  def testWithClearingCustomRequestHeaders(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.BackendService(
                backends=[],
                description='my backend service',
                healthChecks=[
                    ('https://compute.googleapis.com/compute/v1/projects/'
                     'my-project/global/httpHealthChecks/my-health-check')
                ],
                name='backend-service-1',
                portName='http',
                protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                selfLink=(
                    'https://compute.googleapis.com/compute/v1/projects/'
                    'my-project/global/backendServices/backend-service-1'),
                timeoutSec=30,
                customRequestHeaders=['test: '])
        ],
        [],
    ])
    self.RunUpdate('backend-service-1 --no-custom-request-headers')

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
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithHttp2Protocol(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._http_backend_services_with_health_check[0]],
        [],
    ])

    self.RunUpdate('backend-service-3 --protocol http2')

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
                                 'orig-health-check')],
                  name='backend-service-3',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP2),
                  selfLink=(self.compute_uri +
                            '/projects/my-project/global/backendServices/'
                            'backend-service-3'),
                  timeoutSec=30),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
