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

"""Tests for the backend services update alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute.backend_services.update import test_base


class WithHealthcheckApiTest(test_base.AlphaUpdateTestBase):

  def testWithHttpHealthChecksUpdatedToHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--health-checks health-check-1,health-check-2 '
                   '--global-health-checks')

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

    self.RunUpdate('backend-service-3 '
                   '--health-checks health-check-1 '
                   '--global-health-checks')

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

    self.RunUpdate('backend-service-3 '
                   '--health-checks new-health-check '
                   '--global-health-checks')

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

  def testWithUpdateCustomRequestHeaders(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --custom-request-header \'test: \' '
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
                    ('https://compute.googleapis.com/compute/alpha/projects/'
                     'my-project/global/httpHealthChecks/my-health-check')
                ],
                name='backend-service-1',
                portName='http',
                protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                selfLink=(
                    'https://compute.googleapis.com/compute/alpha/projects/'
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


if __name__ == '__main__':
  test_case.main()
